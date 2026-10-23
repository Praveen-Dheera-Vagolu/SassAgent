import { db, initDatabase } from './db.js';

export function seedDatabase() {
  initDatabase();

  // Clear existing records
  db.exec(`
    DELETE FROM test_case_runs;
    DELETE FROM action_proposals;
    DELETE FROM audit_evidence;
    DELETE FROM user_seats;
    DELETE FROM saas_tools;
  `);

  const now = new Date();
  const formatIsoDate = (d) => d.toISOString().split('T')[0];
  const dateOffsetDays = (days) => new Date(now.getTime() + days * 86400000);
  const pastDaysIso = (days) => new Date(now.getTime() - days * 86400000).toISOString();

  // 1. Insert SaaS Tools
  const insertTool = db.prepare(`
    INSERT INTO saas_tools (
      id, name, billing_cycle, cost_per_seat_annual, cost_per_seat_monthly,
      total_licenses, contract_start_date, renewal_date, auto_renew_enabled,
      mock_admin_endpoint, contract_has_mid_term_lock
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  // TC1: Figma Enterprise - 50 seats, renewal in 14 days
  insertTool.run(
    'figma',
    'Figma Enterprise',
    'ANNUAL',
    600.0,
    50.0,
    50,
    formatIsoDate(dateOffsetDays(-351)),
    formatIsoDate(dateOffsetDays(14)), // Exactly 14 days
    1,
    '/api/mock-admin/figma',
    1
  );

  // TC2: Slack Workspace - 120 seats, 18 dormant accounts (>= 90 days)
  insertTool.run(
    'slack',
    'Slack Workspace',
    'ANNUAL',
    600.0,
    50.0,
    120,
    formatIsoDate(dateOffsetDays(-330)),
    formatIsoDate(dateOffsetDays(35)),
    1,
    '/api/mock-admin/slack',
    1
  );

  // TC3: GitHub Enterprise - 60 seats, month 4 of 12-month prepaid plan (renewal in 240 days)
  insertTool.run(
    'github',
    'GitHub Enterprise',
    'ANNUAL',
    360.0,
    30.0,
    60,
    formatIsoDate(dateOffsetDays(-120)), // Month 4
    formatIsoDate(dateOffsetDays(240)),  // Mid-term lock
    1,
    '/api/mock-admin/github',
    1
  );

  // TC4: Zoom Large Enterprise - 80 seats, queued for reduction to 65 seats (saving $3,600/yr)
  insertTool.run(
    'zoom',
    'Zoom Large Enterprise',
    'ANNUAL',
    240.0,
    20.0,
    80,
    formatIsoDate(dateOffsetDays(-340)),
    formatIsoDate(dateOffsetDays(25)),
    1,
    '/api/mock-admin/zoom',
    1
  );

  // 2. Insert User Seats
  const insertUser = db.prepare(`
    INSERT INTO user_seats (
      id, saas_tool_id, user_email, role, last_active_timestamp, is_idle
    ) VALUES (?, ?, ?, ?, ?, ?)
  `);

  // Figma: 46 active, 4 idle
  for (let i = 1; i <= 46; i++) {
    insertUser.run(
      `figma_u_${i.toString().padStart(3, '0')}`,
      'figma',
      `designer_${i}@acmecorp.com`,
      i % 2 === 0 ? 'Lead Product Designer' : 'UI/UX Designer',
      pastDaysIso((i % 20) + 1),
      0
    );
  }
  for (let i = 47; i <= 50; i++) {
    insertUser.run(
      `figma_u_${i.toString().padStart(3, '0')}`,
      'figma',
      `contractor_design_${i}@acmecorp.com`,
      'External Consultant (Departed)',
      pastDaysIso(96 + (i - 47) * 8),
      1
    );
  }

  // Slack: 102 active, 18 idle (>= 90 days) - TC2
  for (let i = 1; i <= 102; i++) {
    insertUser.run(
      `slack_u_${i.toString().padStart(3, '0')}`,
      'slack',
      `staff_eng_${i}@acmecorp.com`,
      'Software Engineer',
      pastDaysIso((i % 30) + 1),
      0
    );
  }
  for (let i = 103; i <= 120; i++) {
    const daysAgo = 92 + (i - 103) * 4; // 92 to 160 days
    insertUser.run(
      `slack_u_${i.toString().padStart(3, '0')}`,
      'slack',
      `dormant_dev_${i}@acmecorp.com`,
      'Former Staff / Contractor',
      pastDaysIso(daysAgo),
      1
    );
  }

  // GitHub: 50 active, 10 idle - TC3
  for (let i = 1; i <= 50; i++) {
    insertUser.run(
      `gh_u_${i.toString().padStart(3, '0')}`,
      'github',
      `dev_github_${i}@acmecorp.com`,
      'Platform Developer',
      pastDaysIso((i % 14) + 1),
      0
    );
  }
  for (let i = 51; i <= 60; i++) {
    insertUser.run(
      `gh_u_${i.toString().padStart(3, '0')}`,
      'github',
      `inactive_repo_${i}@acmecorp.com`,
      'Consultant Contributor',
      pastDaysIso(100 + (i - 51) * 6),
      1
    );
  }

  // Zoom: 65 active, 15 idle - TC4
  for (let i = 1; i <= 65; i++) {
    insertUser.run(
      `zoom_u_${i.toString().padStart(3, '0')}`,
      'zoom',
      `emp_zoom_${i}@acmecorp.com`,
      'Sales / Solutions Executive',
      pastDaysIso((i % 10) + 1),
      0
    );
  }
  for (let i = 66; i <= 80; i++) {
    insertUser.run(
      `zoom_u_${i.toString().padStart(3, '0')}`,
      'zoom',
      `alumni_sales_${i}@acmecorp.com`,
      'Account Executive (Departed)',
      pastDaysIso(110 + (i - 66) * 5),
      1
    );
  }

  // 3. Initial Audit Evidence
  const insertEvidence = db.prepare(`
    INSERT INTO audit_evidence (
      id, saas_tool_id, source_url, retrieval_timestamp, raw_payload_json
    ) VALUES (?, ?, ?, ?, ?)
  `);

  insertEvidence.run(
    'evid_figma_01',
    'figma',
    '/api/mock-admin/figma/billing',
    now.toISOString(),
    JSON.stringify({
      tool: 'Figma Enterprise',
      total_seats: 50,
      active_seats: 46,
      idle_seats: 4,
      days_to_renewal: 14,
      auto_renew: true,
      rate_monthly: 50.0
    })
  );

  insertEvidence.run(
    'evid_slack_01',
    'slack',
    '/api/mock-admin/slack/users',
    now.toISOString(),
    JSON.stringify({
      tool: 'Slack Workspace',
      total_seats: 120,
      active_users: 102,
      idle_users_90d: 18,
      annual_waste_usd: 10800.0
    })
  );

  insertEvidence.run(
    'evid_github_01',
    'github',
    '/api/mock-admin/github/billing',
    now.toISOString(),
    JSON.stringify({
      tool: 'GitHub Enterprise',
      total_seats: 60,
      idle_seats: 10,
      contract_cycle: 'ANNUAL',
      tenure_months: 4,
      renewal_days: 240,
      lock_status: 'ACTIVE_MID_TERM_LOCK'
    })
  );

  insertEvidence.run(
    'evid_zoom_01',
    'zoom',
    '/api/mock-admin/zoom/billing',
    now.toISOString(),
    JSON.stringify({
      tool: 'Zoom Large Enterprise',
      current_seats: 80,
      idle_seats: 15,
      target_seats: 65,
      monthly_savings: 300.0,
      annual_savings: 3600.0
    })
  );

  // 4. Action Proposals
  const insertProposal = db.prepare(`
    INSERT INTO action_proposals (
      id, saas_tool_id, current_seats, proposed_seats, idle_seats_count,
      estimated_savings, status, decision_reason, reviewed_at, reviewed_by, verification_receipt
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  // TC4: Zoom Large Enterprise pending proposal (80 -> 65 seats, saving $3,600/yr)
  insertProposal.run(
    'prop_zoom_large_01',
    'zoom',
    80,
    65,
    15,
    3600.0,
    'PENDING_APPROVAL',
    '15 dormant users detected (inactive >= 90 days). Downscaling from 80 to 65 seats.',
    null,
    null,
    null
  );

  // TC3: GitHub Enterprise (Deferred mid-term lock)
  insertProposal.run(
    'prop_github_deferred',
    'github',
    60,
    60,
    10,
    0.0,
    'REJECTED',
    'Contract locked in month 4 of 12-month prepaid annual plan. Downscale deferred to prevent contract violation penalty.',
    now.toISOString(),
    'SYSTEM_ENGINE',
    null
  );

  console.log('Seeded optimizer.db with Figma, Slack, GitHub, and Zoom enterprise datasets.');
}

if (process.argv[1]?.endsWith('seed.js')) {
  seedDatabase();
}
