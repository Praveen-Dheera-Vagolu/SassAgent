#!/usr/bin/env python3
"""
SaaSOptimizer AI — Autonomous Renewal & Seat Rightsizing Agent
Comprehensive Verification Test Suite for TC1, TC2, TC3, and TC4.
"""

from __future__ import annotations

import sys
from typing import Any, Dict
from starlette.testclient import TestClient

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from backend.api import app
from backend.mock_saas_provider import mock_saas_provider
from backend.state_store import state_store

# Attempt to import rich for formatted terminal reports
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    console = Console(safe_box=True)
    HAS_RICH = True
except Exception:
    HAS_RICH = False
    console = None


def print_banner(text: str) -> None:
    if HAS_RICH and console:
        console.print(Panel(f"[bold cyan]{text}[/bold cyan]", border_style="bright_blue"))
    else:
        print("\n" + "=" * 70)
        print(f" {text}")
        print("=" * 70)


def print_result(tc_id: str, title: str, passed: bool, details: Dict[str, Any]) -> None:
    status_str = "[PASS]" if passed else "[FAIL]"
    if HAS_RICH and console:
        table = Table(title=f"{tc_id}: {title}", show_header=True, header_style="bold magenta")
        table.add_column("Property", style="dim", width=26)
        table.add_column("Observed Value / Assertion Result", style="bold")
        for k, v in details.items():
            table.add_row(k, str(v))
        console.print(table)
        color = "green" if passed else "red"
        console.print(f"[{color} bold]{status_str} {tc_id} Completed Successfully[/{color} bold]\n")
    else:
        print(f"\n{status_str} {tc_id}: {title}")
        for k, v in details.items():
            print(f"  - {k}: {v}")
        print()


def test_tc1_renewal_in_14_days(client: TestClient) -> bool:
    """
    TC1: Slack Enterprise, 100 seats, renewing in 14 days, alert triggered with utilization.
    """
    resp = client.post("/api/scenarios/TC1/run")
    assert resp.status_code == 200, f"Expected 200 OK, got {resp.status_code}"
    data = resp.json()

    assert data["subscription_id"] == "sub_slack_enterprise"
    alert = data.get("renewal_alert")
    assert alert is not None, "Renewal alert must be triggered!"
    assert alert["days_until_renewal"] == 14, f"Expected 14 days renewal, got {alert['days_until_renewal']}"
    assert alert["urgency"] == "CRITICAL", f"Expected CRITICAL urgency, got {alert['urgency']}"
    assert alert["total_seats"] == 100, f"Expected 100 total seats, got {alert['total_seats']}"
    assert alert["active_seats"] == 82, f"Expected 82 active seats, got {alert['active_seats']}"
    assert alert["idle_seats"] == 18, f"Expected 18 idle seats, got {alert['idle_seats']}"
    assert alert["utilization_pct"] == 82.0, f"Expected 82.0% utilization, got {alert['utilization_pct']}"

    print_result(
        "TC1",
        "Slack Enterprise 14-Day Renewal Alert with Utilization",
        True,
        {
            "Subscription": "Slack Enterprise Grid",
            "Total Seats": alert["total_seats"],
            "Days Until Renewal": alert["days_until_renewal"],
            "Urgency Level": alert["urgency"],
            "Seat Utilization": f"{alert['utilization_pct']}%",
            "Active vs Idle": f"{alert['active_seats']} active / {alert['idle_seats']} idle",
            "Projected Annual Waste": f"${alert['projected_annual_waste_usd']:,.2f}",
            "Alert Trigger Message": alert["message"][:75] + "...",
        },
    )
    return True


def test_tc2_inactive_user_90_days(client: TestClient) -> bool:
    """
    TC2: User inactive 90 days (dev_user_04 inactive 94 days, flagged as idle seat).
    """
    # Fetch Jira Cloud subscription details directly from API
    resp = client.get("/api/subscriptions/sub_jira_cloud")
    assert resp.status_code == 200
    jira_data = resp.json()

    # Find dev_user_04
    dev_user = next((u for u in jira_data["users"] if u["user_id"] == "dev_user_04"), None)
    assert dev_user is not None, "dev_user_04 must exist in Jira Cloud seat allocation"
    assert dev_user["last_active_days_ago"] == 94, f"Expected 94 days inactive, got {dev_user['last_active_days_ago']}"
    assert dev_user["last_active_days_ago"] >= 90, "User must exceed 90 days threshold"

    # Run agent planning pass on Jira Cloud
    resp_run = client.post("/api/scenarios/TC2/run")
    assert resp_run.status_code == 200
    run_data = resp_run.json()

    assert "dev_user_04" in run_data["idle_user_ids"], "dev_user_04 must be included in flagged idle seats"

    print_result(
        "TC2",
        "Identify Inactive User >= 90 Days (dev_user_04)",
        True,
        {
            "Target User ID": dev_user["user_id"],
            "Name & Email": f"{dev_user['name']} ({dev_user['email']})",
            "Role": dev_user["role"],
            "Inactivity Recorded": f"{dev_user['last_active_days_ago']} days ago",
            "Threshold Condition (>= 90d)": "SATISFIED (94 >= 90)",
            "Activity Source": dev_user["activity_source"],
            "Flagged In Idle List": "True (Included in proposal idle_user_ids)",
        },
    )
    return True


def test_tc3_annual_plan_mid_term_lock(client: TestClient) -> bool:
    """
    TC3: Annual plan mid-term (Google Workspace, 50 seats, 10 idle, renewal in 210 days
    -> action DEFERRED due to mid-term lock clause, no reduction suggested).
    """
    resp = client.post("/api/scenarios/TC3/run")
    assert resp.status_code == 200
    data = resp.json()

    assert data["subscription_id"] == "sub_google_workspace"
    proposal = data.get("proposal")
    assert proposal is not None, "Proposal object must be returned"
    assert proposal["status"] == "DEFERRED", f"Expected status DEFERRED, got {proposal['status']}"
    assert proposal["seats_to_remove"] == 0, f"Expected 0 seats removed, got {proposal['seats_to_remove']}"
    assert proposal["proposed_seats"] == 50, f"Expected 50 proposed seats (no change), got {proposal['proposed_seats']}"
    assert data["is_paused"] is False, "Graph should not pause for approval since action is deferred"
    assert "mid-term lock" in proposal["deferral_reason"].lower(), "Deferral reason must mention mid-term lock clause"

    # Verify no console mutation occurred
    console_state = mock_saas_provider.scrape_live_console("sub_google_workspace")
    assert console_state["observed_total_seats"] == 50, "Console seats must remain unchanged at 50"

    print_result(
        "TC3",
        "Annual Plan Mid-Term Lock Clause (Google Workspace)",
        True,
        {
            "Subscription": "Google Workspace Business Plus",
            "Total Seats": 50,
            "Idle Seats Identified": 10,
            "Days Until Renewal": 210,
            "Contract Term": "Annual commitment with mid-term lock clause",
            "Action Status": proposal["status"],
            "Seats Removed": proposal["seats_to_remove"],
            "Live Console Seats Checked": console_state["observed_total_seats"],
            "Deferral Rationale": proposal["deferral_reason"][:80] + "...",
        },
    )
    return True


def test_tc4_seat_reduced_and_verified(client: TestClient) -> bool:
    """
    TC4: Jira Cloud, 50 seats, 5 idle -> pauses for Human Approval -> upon approval reduces to 45
    -> re-scrapes console -> verifies 45 observed seats.
    """
    # Step 4a: Run initial workflow and verify pause at HITL Gate
    resp = client.post("/api/scenarios/TC4/run")
    assert resp.status_code == 200
    data = resp.json()

    assert data["subscription_id"] == "sub_jira_cloud"
    assert data["is_paused"] is True, "Graph MUST pause at HITL Gate"
    assert data["hitl_required"] is True, "HITL flag must be True"
    assert data["step_name"] == "ACTION_GATE_HITL", f"Expected step ACTION_GATE_HITL, got {data['step_name']}"

    proposal = data.get("proposal")
    assert proposal is not None
    assert proposal["status"] == "AWAITING_APPROVAL"
    assert proposal["current_seats"] == 50
    assert proposal["proposed_seats"] == 45
    assert proposal["seats_to_remove"] == 5
    assert proposal["monthly_savings_usd"] == 250.0  # 5 * $50/mo

    proposal_id = proposal["proposal_id"]

    # Step 4b: Simulate Human-In-The-Loop Approval
    resp_approve = client.post(
        f"/api/proposals/{proposal_id}/approve",
        json={"user_id": "ops_lead_admin", "notes": "Approved reduction for departed contractors and dev_user_04"},
    )
    assert resp_approve.status_code == 200
    approve_data = resp_approve.json()

    assert approve_data["status"] == "APPROVED"
    assert approve_data["is_completed"] is True

    # Step 4c: Assert Closed-Loop Verification
    verification = approve_data.get("verification")
    assert verification is not None, "Verification result must be generated"
    assert verification["verified"] is True, "Verification flag must be True"
    assert verification["target_seats"] == 45, f"Target seats must be 45, got {verification['target_seats']}"
    assert verification["observed_seats"] == 45, f"Observed seats must be 45, got {verification['observed_seats']}"
    assert verification["target_seats"] == verification["observed_seats"], "Target and observed seats must match exactly"
    assert len(verification["verification_hash"]) == 64, "SHA-256 verification hash must be 64 characters"

    # Step 4d: Direct independent console scraper check
    live_scrape = mock_saas_provider.scrape_live_console("sub_jira_cloud")
    assert live_scrape["observed_total_seats"] == 45

    print_result(
        "TC4",
        "HITL Seat Reduction & Closed-Loop Verification (Jira Cloud)",
        True,
        {
            "Subscription": "Jira Cloud Enterprise",
            "Initial Seats": 50,
            "Idle Seats Deprovisioned": 5,
            "HITL Gate Checkpoint": "INTERRUPT_BEFORE Execution (Paused successfully)",
            "Human Approval Action": "Approved by ops_lead_admin",
            "Target Seats": verification["target_seats"],
            "Console Observed Seats": verification["observed_seats"],
            "Verification Equality": "45 == 45 [MATCH CONFIRMED]",
            "Monthly Cost Savings": f"${proposal['monthly_savings_usd']:,.2f}/mo",
            "Annual Cost Savings": f"${proposal['annual_savings_usd']:,.2f}/yr",
            "Cryptographic Receipt": f"SHA256:{verification['verification_hash'][:32]}...",
        },
    )
    return True


def run_all_tests() -> int:
    print_banner("SaaSOptimizer AI — Agentic Hackathon 2026 Test Suite")
    client = TestClient(app)

    # Reset state to clean baseline before running
    client.post("/api/reset")

    results = []
    tests = [
        ("TC1: Renewal in 14 Days", test_tc1_renewal_in_14_days),
        ("TC2: Inactive User >= 90 Days", test_tc2_inactive_user_90_days),
        ("TC3: Annual Plan Mid-Term Lock", test_tc3_annual_plan_mid_term_lock),
        ("TC4: Seat Reduced & Verified", test_tc4_seat_reduced_and_verified),
    ]

    for name, test_fn in tests:
        try:
            passed = test_fn(client)
            results.append((name, passed, "OK"))
        except AssertionError as e:
            results.append((name, False, str(e)))
        except Exception as e:
            results.append((name, False, f"Unexpected error: {e}"))

    # Summary
    all_passed = all(r[1] for r in results)
    print_banner("Verification Results Summary")
    if HAS_RICH and console:
        summary_table = Table(show_header=True, header_style="bold cyan")
        summary_table.add_column("Test Scenario", style="bold")
        summary_table.add_column("Status", justify="center")
        summary_table.add_column("Notes")

        for name, passed, note in results:
            status = "[green]PASSED[/green]" if passed else "[red]FAILED[/red]"
            summary_table.add_row(name, status, note)
        console.print(summary_table)

        if all_passed:
            console.print("\n[bold green]ALL MANDATORY TEST CASES (TC1-TC4) PASSED PERFECTLY![/bold green]\n")
        else:
            console.print("\n[bold red]SOME TESTS FAILED![/bold red]\n")
    else:
        for name, passed, note in results:
            print(f"[{'PASSED' if passed else 'FAILED'}] {name} - {note}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
