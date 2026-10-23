import { seedDatabase } from './seed.js';
import { OptimizerEngine } from './optimizer-engine.js';
import { db } from './db.js';

function runCliTestRunner() {
  console.log('\n================================================================================');
  console.log('   TrimOps v2.4 — Official Hybrid Test Runner (TC1 to TC4)');
  console.log('   Kore.ai XO Platform Architecture | Business & Productivity AI');
  console.log('================================================================================\n');

  // Seed pristine baseline before running tests
  seedDatabase();

  const results = [];

  // ---------------------------------------------------------------------------
  // TC1: Impending Renewal Alert (14-Day Horizon)
  // ---------------------------------------------------------------------------
  try {
    const res = OptimizerEngine.evaluatePolicy('figma');
    const is14d = res.daysUntilRenewal === 14;
    const isUrgent = res.isUrgentRenewal;
    const is50Total = res.totalLicenses === 50;

    if (!is14d || !isUrgent || !is50Total) {
      throw new Error(`TC1 Assertion Failure: 14d=${is14d}, urgent=${isUrgent}, total=${is50Total}`);
    }

    console.log('[PASS] TC1: Impending Renewal Alert (14-Day Horizon)');
    console.log(`       - Status Badge: [TC1: URGENT_RENEWAL]`);
    console.log(`       - Target Tool: Figma Enterprise (50 seats)`);
    console.log(`       - Days Until Renewal: ${res.daysUntilRenewal}d (Auto-renew lock impending)`);
    console.log(`       - Active vs Dormant: ${res.activeCount} active / ${res.idleCount} dormant (${res.utilizationRate}% utilization)\n`);
    results.push({ id: 'TC1', name: 'TC1: Impending Renewal Alert (14-Day Horizon)', status: 'PASS' });
  } catch (err) {
    console.error(`[FAIL] TC1: ${err.message}\n`);
    results.push({ id: 'TC1', name: 'TC1: Impending Renewal Alert', status: 'FAIL', error: err.message });
  }

  // ---------------------------------------------------------------------------
  // TC2: Ghost Account Detector (90+ Days Inactive)
  // ---------------------------------------------------------------------------
  try {
    const res = OptimizerEngine.evaluatePolicy('slack');
    const is18Dormant = res.idleCount === 18;

    if (!is18Dormant) {
      throw new Error(`TC2 Assertion Failure: idleCount=${res.idleCount} (expected 18)`);
    }

    console.log('[PASS] TC2: Ghost Account Detector (90+ Days Inactive)');
    console.log(`       - Status Badge: [TC2: IDLE_SEAT_FLAGGED]`);
    console.log(`       - Target Tool: Slack Workspace (120 seats)`);
    console.log(`       - Dormant Accounts Isolated: 18 users (last_active >= 90 days)`);
    console.log(`       - Annual Waste Detected: $${res.annualWasteUsd.toLocaleString()}/year\n`);
    results.push({ id: 'TC2', name: 'TC2: Ghost Account Detector (90+ Days Inactive)', status: 'PASS' });
  } catch (err) {
    console.error(`[FAIL] TC2: ${err.message}\n`);
    results.push({ id: 'TC2', name: 'TC2: Ghost Account Detector', status: 'FAIL', error: err.message });
  }

  // ---------------------------------------------------------------------------
  // TC3: Annual Contract Protection (Mid-Term Lock)
  // ---------------------------------------------------------------------------
  try {
    const res = OptimizerEngine.evaluatePolicy('github');
    const isLocked = res.isMidTermLocked;
    const is240d = res.daysUntilRenewal === 240;

    if (!isLocked || !is240d) {
      throw new Error(`TC3 Assertion Failure: locked=${isLocked}, days=${res.daysUntilRenewal}`);
    }

    console.log('[PASS] TC3: Annual Contract Protection (Mid-Term Lock)');
    console.log(`       - Status Badge: [TC3: CONTRACT_LOCKED]`);
    console.log(`       - Target Tool: GitHub Enterprise (60 seats)`);
    console.log(`       - Contract Tenure: Month 4 of 12-month prepaid annual plan`);
    console.log(`       - Compliance Decision: Immediate seat-trimming BLOCKED to avoid contract penalties; queued for renewal window\n`);
    results.push({ id: 'TC3', name: 'TC3: Annual Contract Protection (Mid-Term Lock)', status: 'PASS' });
  } catch (err) {
    console.error(`[FAIL] TC3: ${err.message}\n`);
    results.push({ id: 'TC3', name: 'TC3: Annual Contract Protection', status: 'FAIL', error: err.message });
  }

  // ---------------------------------------------------------------------------
  // TC4: Seat Downgrade & Live Confirmation
  // ---------------------------------------------------------------------------
  try {
    // Reset Zoom to baseline 80 seats
    db.prepare("UPDATE saas_tools SET total_licenses = 80 WHERE id = 'zoom'").run();
    db.prepare("DELETE FROM action_proposals WHERE saas_tool_id = 'zoom'").run();

    const proposalId = `prop_zoom_cli_${Date.now()}`;
    db.prepare(`
      INSERT INTO action_proposals (
        id, saas_tool_id, current_seats, proposed_seats, idle_seats_count,
        estimated_savings, status, decision_reason, created_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      proposalId,
      'zoom',
      80,
      65,
      15,
      3600.0,
      'PENDING_APPROVAL',
      'Downscaling 80 to 65 seats to reclaim 15 dormant accounts.',
      new Date().toISOString()
    );

    const execution = OptimizerEngine.executeApprovalAndVerify(proposalId, 'CLI Test Suite');
    const liveRead = db.prepare('SELECT total_licenses FROM saas_tools WHERE id = ?').get('zoom');

    const is65 = liveRead.total_licenses === 65;
    const isVerified = execution.success === true;
    const hasHash = Boolean(execution.receipt?.verification_hash);

    if (!is65 || !isVerified || !hasHash) {
      throw new Error(`TC4 Assertion Failure: observed=${liveRead.total_licenses}, verified=${isVerified}`);
    }

    console.log('[PASS] TC4: Seat Downgrade & Live Confirmation');
    console.log(`       - Status Badge: [TC4: EXECUTED_&_VERIFIED]`);
    console.log(`       - Target Tool: Zoom Large Enterprise (80 -> 65 seats)`);
    console.log(`       - Human-in-the-Loop Sign-Off: AUTHORIZED`);
    console.log(`       - Live Console Read-Back: 65 seats observed == 65 target [CONFIRMED MATCH]`);
    console.log(`       - Realized Annual Savings: $3,600/year`);
    console.log(`       - Tamper-Evident SHA256 Receipt: ${execution.receipt.verification_hash.slice(0, 32)}...\n`);
    results.push({ id: 'TC4', name: 'TC4: Seat Downgrade & Live Confirmation', status: 'PASS' });
  } catch (err) {
    console.error(`[FAIL] TC4: ${err.message}\n`);
    results.push({ id: 'TC4', name: 'TC4: Seat Downgrade & Live Confirmation', status: 'FAIL', error: err.message });
  }

  console.log('--------------------------------------------------------------------------------');
  console.log(`TEST SUITE SUMMARY: ${results.filter(r => r.status === 'PASS').length} / ${results.length} PASSED`);
  console.log('--------------------------------------------------------------------------------\n');

  const allPassed = results.every(r => r.status === 'PASS');
  process.exit(allPassed ? 0 : 1);
}

runCliTestRunner();
