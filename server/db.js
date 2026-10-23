import Database from 'better-sqlite3';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const dbPath = path.resolve(__dirname, '../optimizer.db');
export const db = new Database(dbPath);

// Enable foreign keys and WAL mode for enterprise concurrency
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');

export function initDatabase() {
  db.exec(`
    CREATE TABLE IF NOT EXISTS saas_tools (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      billing_cycle TEXT NOT NULL CHECK(billing_cycle IN ('MONTHLY', 'ANNUAL')),
      cost_per_seat_annual REAL NOT NULL,
      cost_per_seat_monthly REAL NOT NULL,
      total_licenses INTEGER NOT NULL,
      contract_start_date DATETIME NOT NULL,
      renewal_date DATETIME NOT NULL,
      auto_renew_enabled BOOLEAN NOT NULL DEFAULT 1,
      mock_admin_endpoint TEXT NOT NULL,
      contract_has_mid_term_lock BOOLEAN NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS user_seats (
      id TEXT PRIMARY KEY,
      saas_tool_id TEXT NOT NULL REFERENCES saas_tools(id) ON DELETE CASCADE,
      user_email TEXT NOT NULL,
      role TEXT NOT NULL,
      last_active_timestamp DATETIME NOT NULL,
      is_idle BOOLEAN DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS audit_evidence (
      id TEXT PRIMARY KEY,
      saas_tool_id TEXT NOT NULL REFERENCES saas_tools(id) ON DELETE CASCADE,
      source_url TEXT NOT NULL,
      retrieval_timestamp DATETIME NOT NULL,
      raw_payload_json TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS action_proposals (
      id TEXT PRIMARY KEY,
      saas_tool_id TEXT NOT NULL REFERENCES saas_tools(id) ON DELETE CASCADE,
      current_seats INTEGER NOT NULL,
      proposed_seats INTEGER NOT NULL,
      idle_seats_count INTEGER NOT NULL,
      estimated_savings REAL NOT NULL,
      status TEXT NOT NULL CHECK(status IN ('PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'EXECUTED', 'VERIFIED')),
      decision_reason TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      reviewed_at DATETIME NULL,
      reviewed_by TEXT NULL,
      verification_receipt TEXT NULL
    );

    CREATE TABLE IF NOT EXISTS test_case_runs (
      id TEXT PRIMARY KEY,
      tc_code TEXT NOT NULL,
      scenario_name TEXT NOT NULL,
      status TEXT NOT NULL,
      input_summary TEXT NOT NULL,
      expected_output TEXT NOT NULL,
      actual_output TEXT NOT NULL,
      evidence_snapshot TEXT NOT NULL,
      executed_at DATETIME NOT NULL
    );
  `);
}

initDatabase();
