from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Set
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.agent_graph import optimizer_graph
from backend.mock_saas_provider import mock_saas_provider
from backend.models import ProposalStatus
from backend.state_store import state_store

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict) -> None:
        dead_connections = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)
        for dead in dead_connections:
            self.active_connections.discard(dead)


ws_manager = ConnectionManager()

# Hook optimizer_graph broadcast into our async connection manager
def sync_broadcast_bridge(payload: dict) -> None:
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(ws_manager.broadcast(payload))
    except Exception:
        pass


optimizer_graph.broadcast_callback = sync_broadcast_bridge

app = FastAPI(
    title="SaaSOptimizer AI — Autonomous Renewal & Seat Rightsizing Agent",
    description="Agentic SaaS Renewal & Rightsizing System with Google Antigravity Physics Dashboard",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ApproveRequest(BaseModel):
    user_id: str = "ops_lead_admin"
    notes: str = "Approved by Operations Lead via Antigravity Dashboard"


class RejectRequest(BaseModel):
    user_id: str = "ops_lead_admin"
    reason: str = "Headcount expansion planned next quarter"


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await ws_manager.connect(websocket)
    try:
        # Send initial snapshot of subscriptions and audit trail
        subs = [s.model_dump() for s in mock_saas_provider.list_subscriptions()]
        audits = [a.model_dump() for a in state_store.list_audit_logs(limit=25)]
        proposals = [p.model_dump() for p in state_store.list_proposals()]
        await websocket.send_json({
            "type": "initial_state",
            "payload": {
                "subscriptions": subs,
                "audit_logs": audits,
                "proposals": proposals,
            },
        })
        while True:
            data = await websocket.receive_text()
            # Echo heartbeat or handle incoming client ping
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


@app.get("/api/subscriptions")
def get_subscriptions() -> List[Dict[str, Any]]:
    return [s.model_dump() for s in mock_saas_provider.list_subscriptions()]


@app.get("/api/subscriptions/{subscription_id}")
def get_subscription(subscription_id: str) -> Dict[str, Any]:
    sub = mock_saas_provider.get_subscription(subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub.model_dump()


@app.get("/api/proposals")
def get_proposals() -> List[Dict[str, Any]]:
    return [p.model_dump() for p in state_store.list_proposals()]


@app.get("/api/audit-logs")
def get_audit_logs(limit: int = 100) -> List[Dict[str, Any]]:
    return [a.model_dump() for a in state_store.list_audit_logs(limit=limit)]


@app.get("/api/scenarios")
def get_scenarios() -> List[Dict[str, Any]]:
    return [
        {
            "id": "TC1",
            "title": "TC1: Renewal in 14 Days",
            "tool": "Slack Enterprise Grid",
            "subscription_id": "sub_slack_enterprise",
            "summary": "100 seats, renewing in 14 days. Agent triggers critical renewal alert with utilization metrics (18 idle seats, 82% active, $6,912/yr waste) and drafts rightsizing proposal.",
            "expected_behavior": "Triggers CRITICAL renewal alert + utilization report + HITL rightsizing proposal.",
        },
        {
            "id": "TC2",
            "title": "TC2: User Inactive >= 90 Days",
            "tool": "Jira Cloud Enterprise",
            "subscription_id": "sub_jira_cloud",
            "target_user": "dev_user_04",
            "summary": "David Vance (dev_user_04) has 94 days of inactivity. Agent inspects SSO audit logs and flags the seat as idle for reclamation.",
            "expected_behavior": "dev_user_04 explicitly identified and flagged as idle (94 days >= 90 days threshold).",
        },
        {
            "id": "TC3",
            "title": "TC3: Annual Plan Mid-Term Lock",
            "tool": "Google Workspace Business Plus",
            "subscription_id": "sub_google_workspace",
            "summary": "50 seats, 10 idle users, renewal in 210 days. Annual commitment contains mid-term lock clause. Downscaling window opens at renewal - 30 days.",
            "expected_behavior": "Action DEFERRED due to mid-term lock clause. No reduction dispatched to vendor console.",
        },
        {
            "id": "TC4",
            "title": "TC4: Seat Reduced & Verified",
            "tool": "Jira Cloud Enterprise",
            "subscription_id": "sub_jira_cloud",
            "summary": "50 seats with 5 idle. Agent pauses at HITL Gate. Upon Human Approval, reduces to 45 seats in console, re-scrapes live portal, and asserts observed == 45.",
            "expected_behavior": "Pauses for HITL approval -> upon approval executes reduction -> re-scrapes console -> verifies 45 observed seats.",
        },
    ]


@app.post("/api/scenarios/{scenario_id}/run")
async def run_scenario(scenario_id: str, auto_approve_tc4: bool = False) -> Dict[str, Any]:
    scenario_id_upper = scenario_id.upper()
    sub_map = {
        "TC1": "sub_slack_enterprise",
        "TC2": "sub_jira_cloud",
        "TC3": "sub_google_workspace",
        "TC4": "sub_jira_cloud",
    }
    if scenario_id_upper not in sub_map:
        raise HTTPException(status_code=400, detail=f"Invalid scenario {scenario_id}. Choose TC1, TC2, TC3, or TC4.")

    sub_id = sub_map[scenario_id_upper]
    state = optimizer_graph.start(sub_id)

    # For TC4, if auto_approve_tc4 is requested (e.g. in automated tests), we trigger approval
    if scenario_id_upper == "TC4" and auto_approve_tc4 and state.is_paused and state.proposal:
        state = optimizer_graph.resume_with_decision(state.proposal.proposal_id, "APPROVED", "test_runner")

    # Broadcast updated subscriptions to UI
    subs = [s.model_dump() for s in mock_saas_provider.list_subscriptions()]
    await ws_manager.broadcast({"type": "subscriptions_updated", "payload": subs})

    return {
        "scenario": scenario_id_upper,
        "run_id": state.run_id,
        "subscription_id": state.subscription_id,
        "step_name": state.step_name,
        "is_paused": state.is_paused,
        "is_completed": state.is_completed,
        "hitl_required": state.hitl_required,
        "renewal_alert": state.renewal_alert.model_dump() if state.renewal_alert else None,
        "proposal": state.proposal.model_dump() if state.proposal else None,
        "verification": state.verification.model_dump() if state.verification else None,
        "idle_users_count": len(state.idle_users),
        "idle_user_ids": [u.user_id for u in state.idle_users],
    }


@app.post("/api/proposals/{proposal_id}/approve")
async def approve_proposal(proposal_id: str, req: ApproveRequest = ApproveRequest()) -> Dict[str, Any]:
    proposal = state_store.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if proposal.status != ProposalStatus.AWAITING_APPROVAL:
        raise HTTPException(status_code=400, detail=f"Proposal is already {proposal.status.value}")

    state = optimizer_graph.resume_with_decision(proposal_id, "APPROVED", user_id=req.user_id)
    
    # Broadcast refreshed state
    subs = [s.model_dump() for s in mock_saas_provider.list_subscriptions()]
    await ws_manager.broadcast({"type": "subscriptions_updated", "payload": subs})

    return {
        "status": "APPROVED",
        "proposal_id": proposal_id,
        "run_id": state.run_id,
        "is_completed": state.is_completed,
        "verification": state.verification.model_dump() if state.verification else None,
    }


@app.post("/api/proposals/{proposal_id}/reject")
async def reject_proposal(proposal_id: str, req: RejectRequest = RejectRequest()) -> Dict[str, Any]:
    proposal = state_store.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if proposal.status != ProposalStatus.AWAITING_APPROVAL:
        raise HTTPException(status_code=400, detail=f"Proposal is already {proposal.status.value}")

    state = optimizer_graph.resume_with_decision(proposal_id, "REJECTED", user_id=req.user_id)
    return {
        "status": "REJECTED",
        "proposal_id": proposal_id,
        "run_id": state.run_id,
        "is_completed": state.is_completed,
    }


@app.post("/api/reset")
async def reset_system() -> Dict[str, Any]:
    """Resets mock consoles and state store to fresh initial state."""
    mock_saas_provider.reset_to_baseline()
    state_store.clear_all()
    subs = [s.model_dump() for s in mock_saas_provider.list_subscriptions()]
    await ws_manager.broadcast({"type": "system_reset", "payload": {"subscriptions": subs}})
    return {"status": "SUCCESS", "message": "System state reset to baseline."}


# Serve static directory for Antigravity Frontend
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    def serve_index() -> FileResponse:
        return FileResponse(str(STATIC_DIR / "index.html"))
