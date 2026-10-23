import crypto from 'crypto';
import { db } from './db.js';

/**
 * 4-Step Modular Agent Decision Engine for SaaS Renewal & Seat Rightsizing
 */
export class SaaSOptimizerEngine {

  /**
   * Step 1: Ingestion & Collection
   * Ingests tools, renewal policies, and credentials with strict schema validation.
   */
  static ingestAndValidateTool(toolId) {
    const tool = db.prepare('SELECT * FROM SaaS_Tool WHERE id = ?').get(toolId);
    if (!tool) {
      throw new Error(`[Step 1 Validation Error] Tool with id '${toolId}' not found.`);
    }

    if (!tool.name || !tool.billing_cycle || tool.total_licenses == null || !tool.renewal_date) {
      throw new Error(`[Step 1 Validation Error] Required schema fields missing for tool '${toolId}'.`);
    }

    const today = new Date();
    const renewal = new Date(tool.renewal_date);
    const diffTime = renewal.getTime() - today.getTime();
    const daysUntilRenewal = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    return {
      tool,
      daysUntilRenewal,
      isValid: true,
      ingestedAt: new Date().toISOString()
    };
  }

  /**
   * Step 2: Information Retrieval & Evidence Snapshotting
   * Reads from mock SaaS Admin billing pages and user activity directory.
   * Records retrieval timestamps and source record IDs in Audit_Evidence.
   */
  static snapshotEvidence(toolId) {
    const { tool, daysUntilRenewal } = this.ingestAndValidateTool(toolId);

    // Read user seats
    const userSeats = db.prepare('SELECT * FROM User_Seat WHERE saas_tool_id = ?').all(toolId);

    // Evidence Completeness check: return UNCERTAIN if users or billing is missing
    if (!userSeats || userSeats.length === 0 || !tool.total_licenses) {
      return {
        state: 'UNCERTAIN',
        reason: 'Missing user activity directory or licensing metadata',
        evidenceId: null
      };
    }

    // Capture raw payload snapshot
    const rawPayload = {
      source_url: tool.mock_admin_url,
      timestamp: new Date().toISOString(),
      tool_id: tool.id,
      tool_name: tool.name,
      total_licenses: tool.total_licenses,
      billing_cycle: tool.billing_cycle,
      renewal_date: tool.renewal_date,
      days_until_renewal: daysUntilRenewal,
      seats_snapshot: userSeats.map(u => ({
        user_id: u.id,
        email: u.user_email,
        role: u.role,
        last_active: u.last_active_timestamp
      }))
    };

    const evidenceId = `evid_${toolId}_${Date.now()}`;
    const insertEvidence = db.prepare(`
      INSERT INTO Audit_Evidence (id, saas_tool_id, source_url, retrieval_timestamp, raw_payload_json)
      VALUES (?, ?, ?, ?, ?)
    `);

    insertEvidence.run(
      evidenceId,
      toolId,
      tool.mock_admin_url,
      rawPayload.timestamp,
      JSON.stringify(rawPayload)
    );

    return {
      state: 'COMPLETE',
      evidenceId,
      tool,
      userSeats,
      daysUntilRenewal,
      rawPayload
    };
  }

  /**
   * Step 3: Explicit Decision Engine
   * Evaluates Inactivity Rule, Renewal Horizon Rule, and Contract Term Rule.
   */
  static evaluatePolicy(toolId) {
    const snapshot = this.snapshotEvidence(toolId);
    if (snapshot.state === 'UNCERTAIN') {
      return {
        status: 'UNCERTAIN',
        reason: snapshot.reason,
        proposals: []
      };
    }

    const { tool, userSeats, daysUntilRenewal, evidenceId } = snapshot;
    const now = new Date();

    // 1. Inactivity Rule: Mark seats as idle if days_since_last_activity >= 90
    const idleSeats = [];
    const activeSeats = [];

    for (const user of userSeats) {
      const lastActive = new Date(user.last_active_timestamp);
      const daysSinceLastActivity = Math.floor((now.getTime() - lastActive.getTime()) / (1000 * 60 * 60 * 24));

      if (daysSinceLastActivity >= 90) {
        idleSeats.push({
          ...user,
          daysSinceLastActivity
        });
      } else {
        activeSeats.push({
          ...user,
          daysSinceLastActivity
        });
      }
    }

    // 2. Renewal Horizon Rule: Trigger alert if renewal <= 30 days (specifically 14 days for TC1)
    let renewalAlert = null;
    let alertUrgency = 'SAFE';

    if (daysUntilRenewal <= 14) {
      alertUrgency = 'CRITICAL';
      renewalAlert = {
        urgency: 'CRITICAL',
        daysUntilRenewal,
        message: `CRITICAL ALERT: ${tool.name} auto-renews in ${daysUntilRenewal} days. ${idleSeats.length} idle seats detected.`
      };
    } else if (daysUntilRenewal <= 30) {
      alertUrgency = 'URGENT';
      renewalAlert = {
        urgency: 'URGENT',
        daysUntilRenewal,
        message: `URGENT ALERT: ${tool.name} renewal approaching in ${daysUntilRenewal} days. ${idleSeats.length} idle seats detected.`
      };
    }

    // 3. Contract Term Rule: If annual plan is mid-term (renewal > 30 days), do NOT propose immediate reduction
    const isMidTermAnnual = tool.billing_cycle === 'Annual' && tool.contract_has_mid_term_lock && daysUntilRenewal > 30;

    let proposal = null;
    const idleCount = idleSeats.length;

    if (isMidTermAnnual) {
      // Defer action to next renewal window
      const daysToWindow = daysUntilRenewal - 30;
      const deferralReason = `Annual plan contains mid-term lock clause. Downscaling window opens 30 days prior to renewal (in ${daysToWindow} days). Action deferred to prevent early termination penalty fees.`;

      const proposalId = `prop_${tool.id}_deferred_${Date.now()}`;
      db.prepare(`
        INSERT OR REPLACE INTO Action_Proposal (
          id, saas_tool_id, current_seats, proposed_seats, estimated_savings,
          status, deferral_reason, created_at, reviewed_at, reviewed_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `).run(
        proposalId,
        tool.id,
        tool.total_licenses,
        tool.total_licenses, // No change
        0.0,
        'DEFERRED',
        deferralReason,
        now.toISOString(),
        now.toISOString(),
        'SYSTEM_DECISION_ENGINE'
      );

      proposal = {
        proposalId,
        status: 'DEFERRED',
        currentSeats: tool.total_licenses,
        proposedSeats: tool.total_licenses,
        seatsToRemove: 0,
        deferralReason
      };
    } else if (idleCount > 0) {
      // Propose rightsizing to active count
      const proposedSeats = Math.max(0, tool.total_licenses - idleCount);
      const monthlySavings = idleCount * tool.cost_per_seat_monthly;
      const annualSavings = monthlySavings * 12;

      // Check if proposal already pending to ensure idempotency
      const existing = db.prepare(`
        SELECT * FROM Action_Proposal
        WHERE saas_tool_id = ? AND status IN ('PENDING_APPROVAL', 'APPROVED')
      `).get(tool.id);

      let proposalId = existing ? existing.id : `prop_${tool.id}_${Date.now()}`;

      if (!existing) {
        db.prepare(`
          INSERT INTO Action_Proposal (
            id, saas_tool_id, current_seats, proposed_seats, estimated_savings,
            status, deferral_reason, created_at
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        `).run(
          proposalId,
          tool.id,
          tool.total_licenses,
          proposedSeats,
          monthlySavings,
          'PENDING_APPROVAL',
          null,
          now.toISOString()
        );
      }

      proposal = {
        proposalId,
        status: existing ? existing.status : 'PENDING_APPROVAL',
        currentSeats: tool.total_licenses,
        proposedSeats,
        seatsToRemove: idleCount,
        monthlySavings,
        annualSavings
      };
    }

    return {
      status: 'EVALUATED',
      tool,
      daysUntilRenewal,
      totalLicenses: tool.total_licenses,
      activeCount: activeSeats.length,
      idleCount: idleSeats.length,
      utilizationRate: tool.total_licenses > 0 ? ((activeSeats.length / tool.total_licenses) * 100).toFixed(1) : 0,
      idleSeats,
      renewalAlert,
      alertUrgency,
      isMidTermAnnual,
      proposal,
      evidenceId
    };
  }

  /**
   * Step 4: Human-in-the-Loop Approval & Verification
   * Executes mock seat deallocation via API and performs closed-loop re-scrape.
   */
  static executeApprovalAndVerify(proposalId, reviewedBy = 'Operations Admin') {
    const proposal = db.prepare('SELECT * FROM Action_Proposal WHERE id = ?').get(proposalId);
    if (!proposal) {
      throw new Error(`Proposal '${proposalId}' not found.`);
    }

    // Idempotent safeguard: prevent duplicate execution
    if (proposal.status === 'EXECUTED' || proposal.status === 'VERIFIED') {
      return {
        idempotentBypass: true,
        proposal,
        message: `Proposal ${proposalId} has already been verified and executed.`
      };
    }

    if (proposal.status === 'REJECTED' || proposal.status === 'DEFERRED') {
      throw new Error(`Cannot execute proposal with status '${proposal.status}'.`);
    }

    const tool = db.prepare('SELECT * FROM SaaS_Tool WHERE id = ?').get(proposal.saas_tool_id);
    const now = new Date();

    // 1. Mutate mock console seat count
    db.prepare('UPDATE SaaS_Tool SET total_licenses = ? WHERE id = ?').run(
      proposal.proposed_seats,
      tool.id
    );

    // 2. Closed-Loop Verification: Re-read mock admin console
    const reReadTool = db.prepare('SELECT * FROM SaaS_Tool WHERE id = ?').get(tool.id);
    const observedSeats = reReadTool.total_licenses;
    const targetSeats = proposal.proposed_seats;
    const isVerified = (observedSeats === targetSeats);

    // 3. Cryptographic tamper-evident hash
    const rawHashToken = `${proposal.id}:${tool.id}:${targetSeats}:${observedSeats}:${now.toISOString()}`;
    const verificationHash = crypto.createHash('sha256').update(rawHashToken).digest('hex');

    const receipt = {
      verified: isVerified,
      proposal_id: proposal.id,
      saas_tool_id: tool.id,
      target_seats: targetSeats,
      observed_seats: observedSeats,
      equality_assertion: `${targetSeats} === ${observedSeats}`,
      recheck_timestamp: now.toISOString(),
      verification_hash: verificationHash,
      reviewed_by: reviewedBy
    };

    const finalStatus = isVerified ? 'VERIFIED' : 'EXECUTED';

    db.prepare(`
      UPDATE Action_Proposal
      SET status = ?, reviewed_at = ?, reviewed_by = ?, verification_receipt = ?
      WHERE id = ?
    `).run(
      finalStatus,
      now.toISOString(),
      reviewedBy,
      JSON.stringify(receipt),
      proposal.id
    );

    return {
      success: isVerified,
      finalStatus,
      receipt,
      previousSeats: proposal.current_seats,
      newSeats: observedSeats
    };
  }
}
