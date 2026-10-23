from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Callable, List, Optional
from backend.mock_saas_provider import mock_saas_provider
from backend.models import (
    AgentState,
    AuditLog,
    EventType,
    ProposalStatus,
    ReductionProposal,
    RenewalAlert,
    UrgencyLevel,
    VerificationResult,
)
from backend.state_store import state_store


class SaaSOptimizerGraph:
    """
    Deterministic Agent State Graph with LangGraph-style checkpointing
    and interrupt_before semantics for Human-in-the-Loop (HITL) approval gates.
    """

    def __init__(self, broadcast_callback: Optional[Callable[[dict], None]] = None) -> None:
        self.broadcast_callback = broadcast_callback

    def _emit(self, event_type: str, payload: dict) -> None:
        if self.broadcast_callback:
            try:
                self.broadcast_callback({"type": event_type, "payload": payload})
            except Exception:
                pass

    def _record_audit(
        self,
        state: AgentState,
        event_type: EventType,
        title: str,
        message: str,
        details: Optional[dict] = None,
    ) -> AuditLog:
        log = AuditLog(
            id=f"audit_{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            subscription_id=state.subscription_id,
            event_type=event_type,
            title=title,
            message=message,
            details=details or {},
        )
        state.audit_trail.append(log)
        state_store.add_audit_log(log)
        self._emit(
            "audit_event",
            {
                "id": log.id,
                "timestamp": log.timestamp,
                "subscription_id": log.subscription_id,
                "event_type": log.event_type.value,
                "title": log.title,
                "message": log.message,
                "details": log.details,
            },
        )
        return log

    def start(self, subscription_id: str) -> AgentState:
        """Initialize and run graph until completion or pause point."""
        run_id = f"run_{subscription_id}_{uuid.uuid4().hex[:6]}"
        state = AgentState(
            run_id=run_id,
            step_name="INITIALIZED",
            subscription_id=subscription_id,
        )

        state_store.save_checkpoint(state)
        self._emit("graph_status", {"run_id": run_id, "step": "INITIALIZED", "state": "STARTED"})

        # Step 1: Ingest
        state = self.node_ingest(state)
        state_store.save_checkpoint(state)

        # Step 2: Plan & Match
        state = self.node_plan_and_match(state)
        state_store.save_checkpoint(state)

        # Step 3: Action Gate (HITL proposal preparation)
        state = self.node_hitl_action_gate(state)
        state_store.save_checkpoint(state)

        # If interrupted before execution (HITL gate), stop here until human approves
        if state.is_paused:
            self._emit("hitl_prompt", {
                "run_id": state.run_id,
                "proposal": state.proposal.model_dump() if state.proposal else None,
            })
            return state

        # If proposal deferred or not requiring execution, complete graph
        state.is_completed = True
        state.step_name = "COMPLETED"
        state_store.save_checkpoint(state)
        self._emit("graph_status", {"run_id": run_id, "step": "COMPLETED", "state": "DONE"})
        return state

    def resume_with_decision(self, proposal_id: str, decision: str, user_id: str = "ops_lead_admin") -> AgentState:
        """
        Resumes graph execution past the HITL interrupt point after human approval or rejection.
        """
        state = state_store.get_checkpoint_by_proposal(proposal_id)
        if not state:
            raise ValueError(f"No checkpoint found associated with proposal {proposal_id}")

        if not state.is_paused:
            return state

        decision_upper = decision.upper()
        state.hitl_decision = decision_upper
        state.is_paused = False

        if decision_upper == "REJECTED":
            if state.proposal:
                state.proposal.status = ProposalStatus.REJECTED
                state.proposal.resolved_at = datetime.now(timezone.utc).isoformat()
                state.proposal.resolved_by = user_id
                state_store.save_proposal(state.proposal)

            self._record_audit(
                state,
                EventType.HITL_REJECTED,
                "HITL Rightsizing Proposal Rejected",
                f"Operator {user_id} rejected proposal {proposal_id}. No console mutations will be performed.",
                {"proposal_id": proposal_id, "resolved_by": user_id},
            )
            state.is_completed = True
            state.step_name = "REJECTED_BY_HUMAN"
            state_store.save_checkpoint(state)
            self._emit("graph_status", {"run_id": state.run_id, "step": state.step_name, "state": "REJECTED"})
            return state

        if decision_upper == "APPROVED":
            if state.proposal:
                state.proposal.status = ProposalStatus.APPROVED
                state.proposal.resolved_at = datetime.now(timezone.utc).isoformat()
                state.proposal.resolved_by = user_id
                state_store.save_proposal(state.proposal)

            self._record_audit(
                state,
                EventType.HITL_APPROVED,
                "HITL Rightsizing Proposal Approved",
                f"Operator {user_id} approved seat reduction to {state.proposal.proposed_seats} seats.",
                {"proposal_id": proposal_id, "resolved_by": user_id, "target_seats": state.proposal.proposed_seats},
            )

            # Step 4: Apply Rightsizing in Console
            state = self.node_apply_rightsizing(state)
            state_store.save_checkpoint(state)

            # Step 5: Closed-Loop Verification
            state = self.node_closed_loop_verify(state)
            state.is_completed = True
            state.step_name = "COMPLETED"
            state_store.save_checkpoint(state)
            self._emit("graph_status", {"run_id": state.run_id, "step": "COMPLETED", "state": "VERIFIED_DONE"})
            return state

        raise ValueError(f"Invalid HITL decision: {decision}. Expected APPROVED or REJECTED.")

    # ---------------- Graph Node Implementations ---------------- #

    def node_ingest(self, state: AgentState) -> AgentState:
        """Ingest tool data, admin access, and renewal policy terms."""
        state.step_name = "INGEST_COLLECT"
        sub = mock_saas_provider.get_subscription(state.subscription_id)
        if not sub:
            state.error = f"Subscription {state.subscription_id} not found."
            return state

        state.subscription = sub
        self._record_audit(
            state,
            EventType.INGEST,
            "SaaS Contract & Seat Inventory Ingested",
            f"Ingested {sub.name}: {sub.total_seats} total seats, renewal in {sub.days_until_renewal} days.",
            {
                "subscription_id": sub.id,
                "total_seats": sub.total_seats,
                "cost_per_seat_monthly": sub.cost_per_seat_monthly,
                "days_until_renewal": sub.days_until_renewal,
                "has_mid_term_lock": sub.contract_terms.has_mid_term_lock,
            },
        )
        self._emit("node_step", {"run_id": state.run_id, "step": "INGEST_COLLECT", "subscription": sub.model_dump()})
        return state

    def node_plan_and_match(self, state: AgentState) -> AgentState:
        """
        Matches seats to active directory & SSO audit logs.
        Flags inactive users (>= 90 days) and computes utilization & renewal alert.
        """
        state.step_name = "PLAN_AND_MATCH"
        sub = state.subscription
        if not sub:
            return state

        # Flag inactive seats
        idle_users = [u for u in sub.users if u.is_idle]
        state.idle_users = idle_users

        # Check renewal alert criteria
        # TC1: renewal <= 30 days generates alert with utilization
        urgency = UrgencyLevel.LOW
        if sub.days_until_renewal <= 14:
            urgency = UrgencyLevel.CRITICAL
        elif sub.days_until_renewal <= 30:
            urgency = UrgencyLevel.HIGH
        elif sub.days_until_renewal <= 60:
            urgency = UrgencyLevel.MEDIUM

        active_count = sub.active_user_count
        utilization = sub.utilization_pct
        projected_waste = len(idle_users) * sub.cost_per_seat_monthly * 12

        alert = RenewalAlert(
            subscription_id=sub.id,
            subscription_name=sub.name,
            days_until_renewal=sub.days_until_renewal,
            urgency=urgency,
            utilization_pct=utilization,
            total_seats=sub.total_seats,
            active_seats=active_count,
            idle_seats=len(idle_users),
            projected_annual_waste_usd=projected_waste,
            message=(
                f"ALERT: {sub.name} renews in {sub.days_until_renewal} days! "
                f"Seat Utilization is {utilization}% ({len(idle_users)} of {sub.total_seats} seats idle >= 90 days). "
                f"Estimated annual waste: ${projected_waste:,.2f}."
            ),
        )
        state.renewal_alert = alert

        # Log audit inspection
        idle_summary = [f"{u.name} ({u.user_id}, {u.last_active_days_ago}d inactive)" for u in idle_users[:5]]
        self._record_audit(
            state,
            EventType.INSPECTION,
            "Seat Activity Matching & Inactivity Inspection",
            f"Inspected {len(sub.users)} seat assignments. Found {len(idle_users)} idle users (>= 90 days).",
            {
                "active_seats": active_count,
                "idle_seats": len(idle_users),
                "utilization_pct": utilization,
                "flagged_idle_sample": idle_summary,
            },
        )

        if sub.days_until_renewal <= 30:
            self._record_audit(
                state,
                EventType.ALERT_TRIGGERED,
                f"Renewal Alert ({urgency.value}): {sub.days_until_renewal} Days Remaining",
                alert.message,
                alert.model_dump(),
            )

        self._emit(
            "node_step",
            {
                "run_id": state.run_id,
                "step": "PLAN_AND_MATCH",
                "idle_count": len(idle_users),
                "alert": alert.model_dump(),
            },
        )
        return state

    def node_hitl_action_gate(self, state: AgentState) -> AgentState:
        """
        HITL Action Gate: Prepares seat-reduction proposal.
        Checks contract clauses (e.g. TC3 mid-term lock vs TC4 renewal reduction window).
        Pauses graph for human approval when reductions are actionable.
        """
        state.step_name = "ACTION_GATE_HITL"
        sub = state.subscription
        idle_count = len(state.idle_users)

        if not sub:
            return state

        proposal_id = f"prop_{sub.id}_{uuid.uuid4().hex[:6]}"

        # TC3 Check: Annual plan mid-term lock clause
        # If renewal is further out than reduction window (e.g. 210 days > 30 days)
        if sub.contract_terms.has_mid_term_lock and sub.days_until_renewal > sub.contract_terms.reduction_window_days_before_renewal:
            days_to_window = sub.days_until_renewal - sub.contract_terms.reduction_window_days_before_renewal
            deferral_reason = (
                f"Annual commitment contract contains an active mid-term lock clause. "
                f"Seat count cannot be decreased mid-term. Downscaling window opens {sub.contract_terms.reduction_window_days_before_renewal} "
                f"days before renewal (in {days_to_window} days). Action DEFERRED to avoid early termination penalties."
            )
            proposal = ReductionProposal(
                proposal_id=proposal_id,
                subscription_id=sub.id,
                subscription_name=sub.name,
                current_seats=sub.total_seats,
                proposed_seats=sub.total_seats,  # No reduction
                seats_to_remove=0,
                idle_user_ids=[u.user_id for u in state.idle_users],
                monthly_savings_usd=0.0,
                annual_savings_usd=0.0,
                status=ProposalStatus.DEFERRED,
                deferral_reason=deferral_reason,
            )
            state.proposal = proposal
            state_store.save_proposal(proposal)

            self._record_audit(
                state,
                EventType.ACTION_DEFERRED,
                "Action Deferred: Mid-Term Contract Lock Enforced",
                deferral_reason,
                {"days_until_renewal": sub.days_until_renewal, "days_until_window": days_to_window},
            )
            self._emit("node_step", {"run_id": state.run_id, "step": "ACTION_GATE_HITL", "proposal": proposal.model_dump()})
            return state

        # If there are idle seats to reduce within the eligible renewal window (e.g. TC4 Jira, TC1 Slack)
        if idle_count > 0:
            target_seats = sub.total_seats - idle_count
            monthly_savings = idle_count * sub.cost_per_seat_monthly
            annual_savings = monthly_savings * 12

            proposal = ReductionProposal(
                proposal_id=proposal_id,
                subscription_id=sub.id,
                subscription_name=sub.name,
                current_seats=sub.total_seats,
                proposed_seats=target_seats,
                seats_to_remove=idle_count,
                idle_user_ids=[u.user_id for u in state.idle_users],
                monthly_savings_usd=monthly_savings,
                annual_savings_usd=annual_savings,
                status=ProposalStatus.AWAITING_APPROVAL,
            )
            state.proposal = proposal
            state.hitl_required = True
            state.is_paused = True  # interrupt_before: node_apply_rightsizing
            state_store.save_proposal(proposal)

            self._record_audit(
                state,
                EventType.PROPOSAL_CREATED,
                f"Rightsizing Proposal Created: Reduce to {target_seats} Seats",
                f"Prepared reduction proposal for {idle_count} idle seats saving ${monthly_savings:,.2f}/mo. Pausing for human authorization.",
                proposal.model_dump(),
            )
            self._record_audit(
                state,
                EventType.HITL_PAUSE,
                "HITL Gate Engaged: Paused For Human Approval",
                f"Execution checkpointed at proposal {proposal_id}. Awaiting operator sign-off.",
                {"proposal_id": proposal_id, "target_seats": target_seats},
            )
            self._emit("node_step", {"run_id": state.run_id, "step": "ACTION_GATE_HITL", "proposal": proposal.model_dump(), "paused": True})
            return state

        # No idle seats found
        self._record_audit(
            state,
            EventType.INSPECTION,
            "Seat Inventory Optimized",
            f"All {sub.total_seats} seats for {sub.name} are actively utilized. No reduction needed.",
            {"total_seats": sub.total_seats, "active_seats": sub.active_user_count},
        )
        return state

    def node_apply_rightsizing(self, state: AgentState) -> AgentState:
        """Applies approved seat reduction to mock SaaS admin console."""
        state.step_name = "APPLY_RIGHTSIZING"
        if not state.proposal or state.proposal.status != ProposalStatus.APPROVED:
            raise RuntimeError("Cannot apply rightsizing without an APPROVED proposal.")

        sub = state.subscription
        if not sub:
            return state

        target_seats = state.proposal.proposed_seats
        idle_ids = state.proposal.idle_user_ids

        # Perform mock mutation
        updated_sub = mock_saas_provider.update_seats(
            subscription_id=sub.id,
            new_total_seats=target_seats,
            deprovision_user_ids=idle_ids,
        )
        state.subscription = updated_sub
        state.proposal.status = ProposalStatus.APPLIED
        state_store.save_proposal(state.proposal)

        self._record_audit(
            state,
            EventType.CONSOLE_APPLIED,
            f"Admin Console Mutation Executed: {sub.name}",
            f"Successfully updated license tier in console from {sub.total_seats} to {target_seats} seats. Deprovisioned {len(idle_ids)} idle accounts.",
            {
                "previous_seats": sub.total_seats,
                "updated_seats": target_seats,
                "deprovisioned_user_ids": idle_ids,
            },
        )
        self._emit("node_step", {"run_id": state.run_id, "step": "APPLY_RIGHTSIZING", "target_seats": target_seats})
        return state

    def node_closed_loop_verify(self, state: AgentState) -> AgentState:
        """
        Re-scrapes live SaaS provider console to assert observed == target seats.
        Produces cryptographic verification certificate.
        """
        state.step_name = "CLOSED_LOOP_VERIFY"
        if not state.proposal:
            return state

        target_seats = state.proposal.proposed_seats
        console_snapshot = mock_saas_provider.scrape_live_console(state.subscription_id)
        observed_seats = console_snapshot.get("observed_total_seats", -1)

        verified = (observed_seats == target_seats)

        # Compute tamper-evident hash receipt
        raw_token = f"{state.proposal.proposal_id}:{state.subscription_id}:{target_seats}:{observed_seats}:{console_snapshot['timestamp']}"
        verification_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

        verification = VerificationResult(
            proposal_id=state.proposal.proposal_id,
            subscription_id=state.subscription_id,
            target_seats=target_seats,
            observed_seats=observed_seats,
            verified=verified,
            recheck_timestamp=console_snapshot["timestamp"],
            verification_hash=verification_hash,
            console_snapshot=console_snapshot,
        )
        state.verification = verification

        if verified:
            self._record_audit(
                state,
                EventType.VERIFICATION_SUCCESS,
                f"Closed-Loop Verification Succeeded (Observed: {observed_seats} == Target: {target_seats})",
                f"Cryptographically verified live console state. Target seats {target_seats} matches observed seats {observed_seats}.",
                verification.model_dump(),
            )
        else:
            self._record_audit(
                state,
                EventType.VERIFICATION_FAILED,
                f"Verification Mismatch! (Observed: {observed_seats} != Target: {target_seats})",
                f"Console scraper reported {observed_seats} seats, but target was {target_seats}.",
                verification.model_dump(),
            )

        self._emit("node_step", {"run_id": state.run_id, "step": "CLOSED_LOOP_VERIFY", "verification": verification.model_dump()})
        return state


# Global optimizer graph instance
optimizer_graph = SaaSOptimizerGraph()
