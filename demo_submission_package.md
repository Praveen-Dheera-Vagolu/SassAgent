# TrimOps — Official Hackathon Demo & Submission Package
**Agentic AI Hackathon 2026 — Powered by Ziro.Digital**  
**Track:** Business & Productivity AI  
**Problem Statement:** SaaS Renewal & Seat Optimizer  

---

## 🎥 Recorded Demo Video

A full recorded video walkthrough of the TrimOps agent running through all test cases is available in your workspace root:

📁 **Workspace File:** [demo_video.webp](file:///c:/Users/prave/OneDrive/Desktop/sassagent/demo_video.webp)  
📁 **Artifact Recording:** `C:\Users\prave\.gemini\antigravity-ide\brain\fc299021-2f2f-482a-80b9-a244992c69f9\demo_run_1792777561649.webp`

![TrimOps Full Live Demo Walkthrough](C:/Users/prave/.gemini/antigravity-ide/brain/fc299021-2f2f-482a-80b9-a244992c69f9/demo_run_1792777561649.webp)

---

## 📸 Key Verification Visual Proofs

````carousel
![1. License Optimization Canvas & Executive KPIs](C:/Users/prave/.gemini/antigravity-ide/brain/fc299021-2f2f-482a-80b9-a244992c69f9/license_optimization_canvas_1792777150068.png)
<!-- slide -->
![2. Closed-Loop Verification (TC4): 65 Observed == 65 Target + SHA-256 Receipt](C:/Users/prave/.gemini/antigravity-ide/brain/fc299021-2f2f-482a-80b9-a244992c69f9/closed_loop_verified_1792777291844.png)
<!-- slide -->
![3. Scenario Simulator: All 5 Test Cases Verified with Traceable Evidence](C:/Users/prave/.gemini/antigravity-ide/brain/fc299021-2f2f-482a-80b9-a244992c69f9/trimops_scenario_simulator_1792777502994.png)
````

---

## 🏆 Test Case Compliance Matrix

| Test Case | Scenario Description | Expected Outcome | System Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TC1** | **Renewal in 14 days** (Figma Enterprise, 50 seats) | Alert with seat usage & horizon countdown | Flags `[TC1: URGENT_RENEWAL]`, 14d horizon detected, 92.0% utilization rate (46 active / 4 idle). | **PASS** |
| **TC2** | **User inactive 90 days** (Slack Workspace, 120 seats) | Flagged as idle seat & financial waste | Isolates 18 dormant accounts ($\ge 90$d inactive) and quantifies $\$10,800$/yr waste. | **PASS** |
| **TC3** | **Annual plan, mid-term** (GitHub Enterprise) | No reduction suggested before renewal | Recognizes month 4/12 prepaid commitment; defers downscaling to renewal window. | **PASS** |
| **TC4** | **Seat reduced & verified** (Zoom Large Enterprise) | Human approval required, console updated, new count verified | Pauses at HITL gate, downscales 80 &rarr; 65 seats, independently re-scrapes console ($65 == 65$), and mints SHA-256 receipt. | **PASS** |
| **Step 3 Rule** | **Missing user directory evidence** (Unconnected tool) | Halts safely with UNCERTAIN state | Flags `[STATUS: UNCERTAIN]`, aborts execution safely without fabricating assumptions. | **PASS** |

---

## 🛡️ Safety Rules Checklist Compliance

1. **Every official test case executed with input, result, and evidence**: Verified via automated runner and visible in Tab 2.
2. **Human approval required before non-reversible actions**: 100% of license downsizes require operator sign-off with idempotent execution locks.
3. **100% synthetic / mock data**: All users use sanitized RFC 2606 domains (`@acmecorp.com`).
4. **Anti-bypass authentication**: In the event of 2FA/CAPTCHA challenges, automated bypass is prohibited; an interactive safe manual step is triggered.
