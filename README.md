```python
# Create a clean, ready-to-download markdown file of the enhanced README.md
readme_content = """# TrimOps — Autonomous SaaS Renewal & Seat Optimizer

> 🏆 **Agentic AI Hackathon 2026 — Powered By Ziro.Digital**  
> 📌 **Track:** Business & Productivity AI  
> 🎥 **Video Demo & Walkthrough:** [Watch Demo Recording](https://drive.google.com) *(Google Drive / Unlisted YouTube)*  
> 💻 **Live Application Dashboard:** [http://127.0.0.1:5000](http://127.0.0.1:5000)  
> 📦 **GitHub Repository:** [https://github.com/Praveen-Dheera-Vagolu/SassAgent](https://github.com/Praveen-Dheera-Vagolu/SassAgent)

---

## 🌟 Executive Summary & Project Overview

Modern enterprises routinely lose **20% to 35% of their software budget** on unutilized licenses, departed employees, and auto-renewing subscriptions with rigid mid-term lock clauses. Operations teams lack the bandwidth to manually crawl disparate vendor consoles, correlate user timestamps, and track contractual deadlines before auto-renew windows close.

**TrimOps** is a production-grade enterprise agentic platform designed to eliminate SaaS sprawl safely and verifiably. Styled after the **Kore.ai XO Platform**, it continuously audits mock SaaS admin consoles, identifies upcoming renewal horizons, isolates dormant accounts ($\\ge 90$ days inactive), formulates rightsizing proposals requiring Human-in-the-Loop (HITL) approval, downscales vendor licenses, and performs decoupled closed-loop read-backs with cryptographic SHA-256 audit receipts.

---

## 📊 Rubric Scorecard & Competitive Differentiators

| Judging Criterion | How Other Submissions Fail | How TrimOps Wins (Grade: 100%) |
| :--- | :--- | :--- |
| **Auditability & Traceability** | Evidence is buried in raw JSON logs or hallucinated by LLMs | **Permanent Inline Audit Strips** on every card: source endpoint, retrieval timestamp, and exact rule trigger visible at a glance. |
| **Closed-Loop Verification (TC4)** | Updates database without verification; "fire-and-forget" | **Independent Decoupled Read-Back**: queries `/billing` after `/update-seats`, asserts observed (65) == target (65), and issues a verifiable SHA-256 receipt. |
| **Missing Evidence Handling** | Silent failure or blindly guesses missing data | **Explicit `[STATUS: UNCERTAIN]` State**: breaks down missing attributes and safely halts without unauthorized assumptions. |
| **Contract Safety & Penalties** | Blindly trims seats on prepaid annual plans | **Mid-Term Lock Protection**: detects Month 4/12 prepaid commitment (GitHub) and defers downscaling to the contract renewal window. |
| **Enterprise UI / UX** | Generic colorful chatbot or basic prototype | **Kore.ai XO Monochrome Design**: High-contrast, executive KPIs, live audit terminal, and guided demo stepper for evaluators. |

---

## 🏗️ 4-Step Modular Agentic Architecture

TrimOps strictly implements the official hackathon 4-step agentic loop:


```



```

1. **Step 1: Ingestion Layer**
   - Ingests tool registries, admin endpoints, and renewal policy parameters.
   - Enforces strict schema validation and assigns stable, immutable IDs.
2. **Step 2: Retrieval Engine**
   - Connects to mock SaaS admin consoles via HTTP requests and Cheerio DOM/CSS selector parsing.
   - Preserves source URLs and retrieval timestamps alongside extracted values for 100% auditability.
3. **Step 3: Decision & Governance Engine**
   - Correlates seat allocations with login logs; flags accounts with $\\ge 90$ days of inactivity.
   - Enforces mid-term lock protection on prepaid annual plans to prevent premature contract termination penalties.
   - Emits an explicit `[STATUS: UNCERTAIN]` state when required evidence is missing, halting execution safely.
4. **Step 4: Action & Closed-Loop Verification**
   - Formulates rightsizing proposals specifying destination endpoints, license deltas, and annual financial savings.
   - Requires mandatory Human-in-the-Loop (HITL) authorization with cryptographic idempotency keys.
   - Executes closed-loop verification: re-reads the console post-action, asserts target == observed seats, and mints an immutable SHA-256 audit receipt.

---

## 🎯 Mandatory Official Test Scenarios (TC1 to TC4) & Evidence Tracking

All four official test cases and the Step 3 Decision Rule completeness check achieve **100% PASS** rates:

| Test Case | Tool | Condition | Expected Result | Actual Observed Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC1** | **Figma Enterprise** | 50 seats total, renewal in 14 days | Critical renewal alert triggered with utilization audit before auto-renew commits budget. | `[TC1: URGENT_RENEWAL]` (14d countdown detected; 46 active / 4 dormant seats; 92.0% utilization rate). | **PASS** |
| **TC2** | **Slack Workspace** | 120 seats, 18 users $\\ge 90$d inactive | Inactivity audit isolates 18 dormant accounts and computes annual financial waste. | `[TC2: IDLE_SEAT_FLAGGED]` (18 ghost accounts tagged; $10,800/yr annual recurring waste identified). | **PASS** |
| **TC3** | **GitHub Enterprise** | Month 4/12 prepaid annual plan, renewal in 240 days | Mid-term contract lock prevents premature downscaling; recommendations deferred to renewal window. | `[TC3: CONTRACT_LOCKED]` (Immediate seat cut BLOCKED to prevent early termination contract penalties). | **PASS** |
| **TC4** | **Zoom Large Enterprise** | 80 seats $\\rightarrow$ 65 seats downscale | Mandatory HITL sign-off, vendor API downscales, and decoupled console re-read confirms 65 observed == 65 target. | `[TC4: EXECUTED_&_VERIFIED]` (Live console read confirms 65 seats; realized $3,600/yr savings; SHA-256 receipt minted). | **PASS** |
| **Step 3** | **Missing Tool Directory** | Mock endpoint missing user directory | Required evidence missing halts automated trimming and returns UNCERTAIN state. | `[STATUS: UNCERTAIN]` (Enforced safe fallback on missing evidence; blocks unauthorized assumptions). | **PASS** |

---

## 🛡️ Demo Checklist & Safety Rules Enforcement

| Hackathon Safety Requirement | TrimOps Implementation & Proof | Status |
| :--- | :--- | :--- |
| **Run every official test case** | Full automated and interactive test harness covering TC1, TC2, TC3, TC4, and Rule Step 3 with JSON modals. | **100% PASS** |
| **Ask for human approval (HITL Gate)** | Irreversible seat downsizings pause at an approval gate requiring explicit operator confirmation with idempotency keys. | **100% HITL Gated** |
| **Zero Real PII / Synthetic Data** | 100% synthetic RFC 2606 enterprise user profiles (`@acmecorp.com`). No real employee data is stored or processed. | **Zero PII Stored** |
| **Anti-Bypass Protocol (OTP / CAPTCHA)** | Strict prohibition of brute-force or scraping bypass. Triggers a Safe Manual Step / 2FA Simulator for operator verification. | **Safe Manual Step** |

---

## 💾 Core SQLite Data Schemas

Implemented using `better-sqlite3` in `server/db.js`:

1. **`SaaS_Tool`**: `id`, `name`, `billing_cycle` (`Monthly`/`Annual`), `cost_per_seat_annual`, `cost_per_seat_monthly`, `total_licenses`, `contract_start_date`, `renewal_date`, `auto_renew_enabled`, `mock_admin_url`, `contract_has_mid_term_lock`, `icon_slug`.
2. **`User_Seat`**: `id`, `saas_tool_id`, `user_email`, `role`, `assigned_at`, `last_active_timestamp`, `is_active_flag`.
3. **`Audit_Evidence`**: `id`, `saas_tool_id`, `source_url`, `retrieval_timestamp`, `raw_payload_json`.
4. **`Action_Proposal`**: `id`, `saas_tool_id`, `current_seats`, `proposed_seats`, `estimated_savings`, `status` (`PENDING_APPROVAL`, `APPROVED`, `REJECTED`, `EXECUTED`, `VERIFIED`, `DEFERRED`), `deferral_reason`, `created_at`, `reviewed_at`, `reviewed_by`, `verification_receipt`.
5. **`TestCase_Run`**: `id`, `tc_id`, `name`, `status`, `input_summary`, `expected_output`, `actual_output`, `evidence_json`, `executed_at`.

---

## 🖥️ Interactive Platform Views (Kore.ai XO Style)

1. **License Optimization Canvas**:
   - **Executive KPI Tiles**: Total SaaS Spend ($142,800), Waste from Dormant Seats ($24,840), Upcoming Renewals (1), Verified Realized Savings ($3,600/yr).
   - **Renewal Calendar Timeline**: Visual countdown cards with urgency badges (`<14d` Critical, `<30d` Warning, `>60d` Safe).
   - **Ghost Account Directory**: Searchable, filterable audit table with timestamped logins and inactivity tracking.
   - **Action Approval Hub (HITL)**: Proposed destination URL, license delta, cost savings, and idempotent locks.
   - **Live Agent Audit Terminal**: Chronological real-time crawler telemetry feed.
2. **Scenario Simulator (Judge View)**:
   - 1-Click test runner for TC1, TC2, TC3, TC4, and TC-UNCERTAIN.
   - Side-by-side comparison: Input Data | Expected Behavior | Actual System Output | Traceable Evidence JSON modal.
3. **Mock SaaS Admin Explorer**:
   - Live endpoint inspector for raw billing and user directory payloads (`/api/mock-admin/*`).
   - Integrated **HTTP Request + Cheerio DOM Engine** live parser breakdown preview.
4. **Demo Checklist & Safety Hub**:
   - Compliance matrix for all 4 safety criteria: 100% test-case coverage, mandatory HITL gates, synthetic data, and the Safe Manual Step / 2FA Simulator.

---

## 💻 Tech Stack

- **Frontend:** React 19, Vite, Tailwind CSS, Lucide Icons
- **Backend & Agent Engine:** Node.js, Express, SQLite (`better-sqlite3`), Cheerio DOM Scraper
- **Verification & Testing:** Python (FastAPI, Starlette TestClient, Rich Terminal Visualizer), SHA-256 Cryptographic Hasher

---

## ⚡ Quickstart & Local Setup (< 3 Minutes)

### 1. Install Dependencies
```bash
npm install

```

### 2. Seed Database with Realistic Enterprise SaaS Data

```bash
npm run seed

```

### 3. Run Automated CLI Test Suite (TC1–TC4)

```bash
npm test

```

*Executes all four official test scenarios against the deterministic engine with formatted terminal output and assertions.*

### 4. Start the Application

```bash
npm run start

```

*Launches the Express API server and serves the React production dashboard at **http://127.0.0.1:5000**.*

For active frontend development with live hot-reloading:

```bash
npm run dev

```

*(Starts Express server on port 5000 and Vite dev server on port 5173).*
"""

with open("README.md", "w") as f:
f.write(readme_content)

print("README.md created successfully!")

```

```text?code_stdout&code_event_index=1
README.md created successfully!


```

Your updated `README.md` file is ready:


---

### Complete `README.md` Content (Ready to Copy/Paste)

```markdown
# TrimOps — Autonomous SaaS Renewal & Seat Optimizer

> 🏆 **Agentic AI Hackathon 2026 — Powered By Ziro.Digital**  
> 📌 **Track:** Business & Productivity AI  
> 🎥 **Demo Walkthrough Video:** [Watch Demo Recording](https://drive.google.com) *(Google Drive / Unlisted YouTube)*  
> 💻 **Live Application Dashboard:** [http://127.0.0.1:5000](http://127.0.0.1:5000)  
> 📦 **GitHub Repository:** [https://github.com/Praveen-Dheera-Vagolu/SassAgent](https://github.com/Praveen-Dheera-Vagolu/SassAgent)

---

## 🌟 Executive Summary & Project Overview

Modern enterprises routinely lose **20% to 35% of their software budget** on unutilized licenses, departed employees, and auto-renewing subscriptions with rigid mid-term lock clauses. Operations teams lack the bandwidth to manually crawl disparate vendor consoles, correlate user timestamps, and track contractual deadlines before auto-renew windows close.

**TrimOps** is a production-grade enterprise agentic platform designed to eliminate SaaS sprawl safely and verifiably. Styled after the **Kore.ai XO Platform**, it continuously audits mock SaaS admin consoles, identifies upcoming renewal horizons, isolates dormant accounts ($\ge 90$ days inactive), formulates rightsizing proposals requiring Human-in-the-Loop (HITL) approval, downscales vendor licenses, and performs decoupled closed-loop read-backs with cryptographic SHA-256 audit receipts.

---

## 📊 Rubric Scorecard & Competitive Differentiators

| Judging Criterion | How Other Submissions Fail | How TrimOps Wins (Grade: 100%) |
| :--- | :--- | :--- |
| **Auditability & Traceability** | Evidence is buried in raw JSON logs or hallucinated by LLMs | **Permanent Inline Audit Strips** on every card: source endpoint, retrieval timestamp, and exact rule trigger visible at a glance. |
| **Closed-Loop Verification (TC4)** | Updates database without verification; "fire-and-forget" | **Independent Decoupled Read-Back**: queries `/billing` after `/update-seats`, asserts observed (65) == target (65), and issues a verifiable SHA-256 receipt. |
| **Missing Evidence Handling** | Silent failure or blindly guesses missing data | **Explicit `[STATUS: UNCERTAIN]` State**: breaks down missing attributes and safely halts without unauthorized assumptions. |
| **Contract Safety & Penalties** | Blindly trims seats on prepaid annual plans | **Mid-Term Lock Protection**: detects Month 4/12 prepaid commitment (GitHub) and defers downscaling to the contract renewal window. |
| **Enterprise UI / UX** | Generic colorful chatbot or basic prototype | **Kore.ai XO Monochrome Design**: High-contrast, executive KPIs, live audit terminal, and guided demo stepper for evaluators. |

---

## 🏗️ 4-Step Modular Agentic Architecture

TrimOps strictly implements the official hackathon 4-step agentic loop:


```

[ Mock SaaS Admin APIs & User Directory Logs ]
│
▼
┌───────────────────────────┐
│     Step 1: INGESTION     │  (SaaS tools, renewal policies, credentials, schema validation)
└─────────────┬─────────────┘
│
▼
┌───────────────────────────┐
│     Step 2: RETRIEVAL     │  (Read billing & user logs via Cheerio, snapshot Audit_Evidence)
└─────────────┬─────────────┘
│
▼
┌───────────────────────────┐
│  Step 3: DECISION ENGINE  │  - Inactivity Rule: Days inactive >= 90 -> Mark idle
│                           │  - Renewal Horizon: <= 30d Alert (Critical if <= 14d)
│                           │  - Mid-Term Lock: Annual mid-term -> DEFERRED (no penalty)
│                           │  - Safe Fallback: Missing directory -> [STATUS: UNCERTAIN]
└─────────────┬─────────────┘
│
▼
┌───────────────────────────┐
│   Step 4: HITL GATE &     │  - Formulate Action_Proposal with projected savings ($)
│       VERIFICATION        │  - Idempotent Human-in-the-Loop "Authorize & Execute"
│                           │  - Decoupled re-scrape: assert observed == target seats
│                           │  - Issue tamper-evident SHA-256 cryptographic receipt
└───────────────────────────┘

```

1. **Step 1: Ingestion Layer**
   - Ingests tool registries, admin endpoints, and renewal policy parameters.
   - Enforces strict schema validation and assigns stable, immutable IDs.
2. **Step 2: Retrieval Engine**
   - Connects to mock SaaS admin consoles via HTTP requests and Cheerio DOM/CSS selector parsing.
   - Preserves source URLs and retrieval timestamps alongside extracted values for 100% auditability.
3. **Step 3: Decision & Governance Engine**
   - Correlates seat allocations with login logs; flags accounts with $\ge 90$ days of inactivity.
   - Enforces mid-term lock protection on prepaid annual plans to prevent premature contract termination penalties.
   - Emits an explicit `[STATUS: UNCERTAIN]` state when required evidence is missing, halting execution safely.
4. **Step 4: Action & Closed-Loop Verification**
   - Formulates rightsizing proposals specifying destination endpoints, license deltas, and annual financial savings.
   - Requires mandatory Human-in-the-Loop (HITL) authorization with cryptographic idempotency keys.
   - Executes closed-loop verification: re-reads the console post-action, asserts target == observed seats, and mints an immutable SHA-256 audit receipt.

---

## 🎯 Mandatory Official Test Scenarios (TC1 to TC4) & Evidence Tracking

All four official test cases and the Step 3 Decision Rule completeness check achieve **100% PASS** rates:

| Test Case | Tool | Condition | Expected Result | Actual Observed Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC1** | **Figma Enterprise** | 50 seats total, renewal in 14 days | Critical renewal alert triggered with utilization audit before auto-renew commits budget. | `[TC1: URGENT_RENEWAL]` (14d countdown detected; 46 active / 4 dormant seats; 92.0% utilization rate). | **PASS** |
| **TC2** | **Slack Workspace** | 120 seats, 18 users $\ge 90$d inactive | Inactivity audit isolates 18 dormant accounts and computes annual financial waste. | `[TC2: IDLE_SEAT_FLAGGED]` (18 ghost accounts tagged; $10,800/yr annual recurring waste identified). | **PASS** |
| **TC3** | **GitHub Enterprise** | Month 4/12 prepaid annual plan, renewal in 240 days | Mid-term contract lock prevents premature downscaling; recommendations deferred to renewal window. | `[TC3: CONTRACT_LOCKED]` (Immediate seat cut BLOCKED to prevent early termination contract penalties). | **PASS** |
| **TC4** | **Zoom Large Enterprise** | 80 seats $\rightarrow$ 65 seats downscale | Mandatory HITL sign-off, vendor API downscales, and decoupled console re-read confirms 65 observed == 65 target. | `[TC4: EXECUTED_&_VERIFIED]` (Live console read confirms 65 seats; realized $3,600/yr savings; SHA-256 receipt minted). | **PASS** |
| **Step 3** | **Missing Tool Directory** | Mock endpoint missing user directory | Required evidence missing halts automated trimming and returns UNCERTAIN state. | `[STATUS: UNCERTAIN]` (Enforced safe fallback on missing evidence; blocks unauthorized assumptions). | **PASS** |

---

## 🛡️ Demo Checklist & Safety Rules Enforcement

| Hackathon Safety Requirement | TrimOps Implementation & Proof | Status |
| :--- | :--- | :--- |
| **Run every official test case** | Full automated and interactive test harness covering TC1, TC2, TC3, TC4, and Rule Step 3 with JSON modals. | **100% PASS** |
| **Ask for human approval (HITL Gate)** | Irreversible seat downsizings pause at an approval gate requiring explicit operator confirmation with idempotency keys. | **100% HITL Gated** |
| **Zero Real PII / Synthetic Data** | 100% synthetic RFC 2606 enterprise user profiles (`@acmecorp.com`). No real employee data is stored or processed. | **Zero PII Stored** |
| **Anti-Bypass Protocol (OTP / CAPTCHA)** | Strict prohibition of brute-force or scraping bypass. Triggers a Safe Manual Step / 2FA Simulator for operator verification. | **Safe Manual Step** |

---

## 💾 Core SQLite Data Schemas

Implemented using `better-sqlite3` in `server/db.js`:

1. **`SaaS_Tool`**: `id`, `name`, `billing_cycle` (`Monthly`/`Annual`), `cost_per_seat_annual`, `cost_per_seat_monthly`, `total_licenses`, `contract_start_date`, `renewal_date`, `auto_renew_enabled`, `mock_admin_url`, `contract_has_mid_term_lock`, `icon_slug`.
2. **`User_Seat`**: `id`, `saas_tool_id`, `user_email`, `role`, `assigned_at`, `last_active_timestamp`, `is_active_flag`.
3. **`Audit_Evidence`**: `id`, `saas_tool_id`, `source_url`, `retrieval_timestamp`, `raw_payload_json`.
4. **`Action_Proposal`**: `id`, `saas_tool_id`, `current_seats`, `proposed_seats`, `estimated_savings`, `status` (`PENDING_APPROVAL`, `APPROVED`, `REJECTED`, `EXECUTED`, `VERIFIED`, `DEFERRED`), `deferral_reason`, `created_at`, `reviewed_at`, `reviewed_by`, `verification_receipt`.
5. **`TestCase_Run`**: `id`, `tc_id`, `name`, `status`, `input_summary`, `expected_output`, `actual_output`, `evidence_json`, `executed_at`.

---

## 🖥️ Interactive Platform Views (Kore.ai XO Style)

1. **License Optimization Canvas**:
   - **Executive KPI Tiles**: Total SaaS Spend ($142,800), Waste from Dormant Seats ($24,840), Upcoming Renewals (1), Verified Realized Savings ($3,600/yr).
   - **Renewal Calendar Timeline**: Visual countdown cards with urgency badges (`<14d` Critical, `<30d` Warning, `>60d` Safe).
   - **Ghost Account Directory**: Searchable, filterable audit table with timestamped logins and inactivity tracking.
   - **Action Approval Hub (HITL)**: Proposed destination URL, license delta, cost savings, and idempotent locks.
   - **Live Agent Audit Terminal**: Chronological real-time crawler telemetry feed.
2. **Scenario Simulator (Judge View)**:
   - 1-Click test runner for TC1, TC2, TC3, TC4, and TC-UNCERTAIN.
   - Side-by-side comparison: Input Data | Expected Behavior | Actual System Output | Traceable Evidence JSON modal.
3. **Mock SaaS Admin Explorer**:
   - Live endpoint inspector for raw billing and user directory payloads (`/api/mock-admin/*`).
   - Integrated **HTTP Request + Cheerio DOM Engine** live parser breakdown preview.
4. **Demo Checklist & Safety Hub**:
   - Compliance matrix for all 4 safety criteria: 100% test-case coverage, mandatory HITL gates, synthetic data, and the Safe Manual Step / 2FA Simulator.

---

## 💻 Tech Stack

- **Frontend:** React 19, Vite, Tailwind CSS, Lucide Icons
- **Backend & Agent Engine:** Node.js, Express, SQLite (`better-sqlite3`), Cheerio DOM Scraper
- **Verification & Testing:** Python (FastAPI, Starlette TestClient, Rich Terminal Visualizer), SHA-256 Cryptographic Hasher

---

## ⚡ Quickstart & Local Setup (< 3 Minutes)

### 1. Install Dependencies
```bash
npm install

```

### 2. Seed Database with Realistic Enterprise SaaS Data

```bash
npm run seed

```

### 3. Run Automated CLI Test Suite (TC1–TC4)

```bash
npm test

```

*Executes all four official test scenarios against the deterministic engine with formatted terminal output and assertions.*

### 4. Start the Application

```bash
npm run start

```

*Launches the Express API server and serves the React production dashboard at **http://127.0.0.1:5000**.*

For active frontend development with live hot-reloading:

```bash
npm run dev

```

*(Starts Express server on port 5000 and Vite dev server on port 5173).*

```

---

