from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BillingCycle(str, Enum):
    ANNUAL = "annual"
    MONTHLY = "monthly"


class ProposalStatus(str, Enum):
    DRAFT = "DRAFT"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    APPLIED = "APPLIED"
    DEFERRED = "DEFERRED"


class UrgencyLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class EventType(str, Enum):
    INGEST = "INGEST"
    INSPECTION = "INSPECTION"
    ALERT_TRIGGERED = "ALERT_TRIGGERED"
    PROPOSAL_CREATED = "PROPOSAL_CREATED"
    HITL_PAUSE = "HITL_PAUSE"
    HITL_APPROVED = "HITL_APPROVED"
    HITL_REJECTED = "HITL_REJECTED"
    CONSOLE_APPLIED = "CONSOLE_APPLIED"
    VERIFICATION_SUCCESS = "VERIFICATION_SUCCESS"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    ACTION_DEFERRED = "ACTION_DEFERRED"


class UserSeat(BaseModel):
    user_id: str
    email: str
    name: str
    role: str
    last_active_days_ago: int
    activity_source: str = "Okta SSO / Workspace Audit Log"

    @property
    def is_idle(self) -> bool:
        return self.last_active_days_ago >= 90


class ContractTerms(BaseModel):
    has_mid_term_lock: bool = True
    reduction_window_days_before_renewal: int = 30
    auto_renew_enabled: bool = True
    cancellation_notice_days: int = 30


class Subscription(BaseModel):
    id: str
    name: str
    category: str
    total_seats: int
    cost_per_seat_monthly: float
    billing_cycle: BillingCycle
    days_until_renewal: int
    contract_terms: ContractTerms
    users: List[UserSeat] = Field(default_factory=list)
    icon_slug: str = "default"

    @property
    def active_user_count(self) -> int:
        return sum(1 for u in self.users if u.last_active_days_ago < 90)

    @property
    def idle_user_count(self) -> int:
        return sum(1 for u in self.users if u.last_active_days_ago >= 90)

    @property
    def unallocated_seats(self) -> int:
        return max(0, self.total_seats - len(self.users))

    @property
    def total_potential_idle_seats(self) -> int:
        return self.idle_user_count + self.unallocated_seats

    @property
    def utilization_pct(self) -> float:
        if self.total_seats == 0:
            return 0.0
        return round((self.active_user_count / self.total_seats) * 100, 1)

    @property
    def annual_spend(self) -> float:
        return self.total_seats * self.cost_per_seat_monthly * 12


class RenewalAlert(BaseModel):
    subscription_id: str
    subscription_name: str
    days_until_renewal: int
    urgency: UrgencyLevel
    utilization_pct: float
    total_seats: int
    active_seats: int
    idle_seats: int
    projected_annual_waste_usd: float
    message: str


class ReductionProposal(BaseModel):
    proposal_id: str
    subscription_id: str
    subscription_name: str
    current_seats: int
    proposed_seats: int
    seats_to_remove: int
    idle_user_ids: List[str] = Field(default_factory=list)
    monthly_savings_usd: float
    annual_savings_usd: float
    status: ProposalStatus = ProposalStatus.DRAFT
    deferral_reason: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None


class VerificationResult(BaseModel):
    proposal_id: str
    subscription_id: str
    target_seats: int
    observed_seats: int
    verified: bool
    recheck_timestamp: str
    verification_hash: str
    console_snapshot: Dict[str, Any]


class AuditLog(BaseModel):
    id: str
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    subscription_id: str
    event_type: EventType
    title: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class AgentState(BaseModel):
    run_id: str
    step_name: str = "INITIALIZED"
    subscription_id: str
    subscription: Optional[Subscription] = None
    idle_users: List[UserSeat] = Field(default_factory=list)
    renewal_alert: Optional[RenewalAlert] = None
    proposal: Optional[ReductionProposal] = None
    hitl_required: bool = False
    hitl_decision: Optional[str] = None  # "APPROVED" or "REJECTED"
    verification: Optional[VerificationResult] = None
    is_completed: bool = False
    is_paused: bool = False
    error: Optional[str] = None
    audit_trail: List[AuditLog] = Field(default_factory=list)
