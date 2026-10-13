# CertiChain Nexus - 5-Minute Live Demonstration Script

This document details the exact sequence of actions for presenting the platform to evaluators, auditors, or academic reviewers.

---

## Pre-requisites & Setup
Ensure the local virtual environment and Flask server are running:
```bash
# Terminal 1: Launch Web Application
python app.py
```
App is live at: `http://127.0.0.1:5000`

---

## Step 1: Issue a New Digital Certificate as an Accredited Issuer (1 min)
1. Navigate to `http://127.0.0.1:5000/login`.
2. Enter Issuer credentials:
   - Email: `issuer@oit.edu`
   - Password: `IssuerPass123!`
3. Click **"+ Issue New Certificate"**.
4. Enter Student & Course Details:
   - Student Ref / ID: `STU-2026-CS-888`
   - Award Type: `Bachelor of Science`
   - Course Name: `Computer Science & Cryptography`
   - Issue Date: `2026-10-10`
   - Grade: `First Class Honours`
5. Click **"Issue & Sign Certificate"**.
6. **Key Observation:** The certificate preview screen opens, showcasing:
   - Unique Certificate ID (e.g., `CERT-2026-XXXXX`)
   - 64-hex SHA-256 Content Hash
   - Issuer Ed25519 Key ID and signature proof
   - Authoritative Verification QR Code

---

## Step 2: Public Verification by ID and Mobile Viewport (1 min)
1. Open an Incognito/Private window (or log out) and go to `http://127.0.0.1:5000`.
2. Paste the newly issued Certificate ID into the search box and click **"Verify Credential"**.
3. **Key Observation:** The Explainable Trust Engine returns:
   - Large Green Status Chip: **STATUS: VERIFIED**
   - 5-Point Cryptographic Matrix:
     - 1. Payload Content Fingerprint (SHA-256): **MATCH**
     - 2. Blockchain Ledger Integrity: **VALID**
     - 3. Ed25519 Digital Signature: **AUTHENTIC**
     - 4. Institution Trust Status: **TRUSTED**
     - 5. Credential Lifecycle Status: **ACTIVE**
   - Interactive Trust Timeline showing issuance block timestamp and verification audit trail.
4. Press `F12` and switch to a mobile device view (e.g., iPhone 12/14, 375x812) to demonstrate responsive UI layout.

---

## Step 3: Controlled Ledger Tamper Simulation (1 min)
1. Navigate to `http://127.0.0.1:5000/ledger`.
2. Point out that all blocks are sequentially linked with previous hashes.
3. Click **"🛡️ Validate Whole Chain"** -> Alerts confirmation that the whole chain is 100% valid.
4. Under **"Controlled Tamper Simulation"**, select `Block #0` or `Block #1` and click **"Simulate Block Tampering"**.
5. **Key Observation:**
   - In-memory chain becomes **NO (FAILED AS EXPECTED)**.
   - Shows exact corrupted block index and discrepancy reason.
   - Highlights to reviewers that authoritative database and ledger remained untouched.

---

## Step 4: Revocation & Status Precedence Check (45 sec)
1. Sign back in as `issuer@oit.edu`.
2. Open a previously issued certificate preview, scroll down to **"Revoke Credential"**.
3. Enter reason: `Academic Integrity Board Decision` and confirm revocation.
4. Open the public verification URL for that certificate ID.
5. **Key Observation:** The verification status immediately switches to **REVOKED** with the exact revocation timestamp and reason displayed.

---

## Step 5: Standalone Proof Capsule & Offline CLI Verification (45 sec)
1. In the Student Vault (`http://127.0.0.1:5000/student/portal`), click **"📦 Proof Capsule"** to download `proof_capsule_<id>.json`.
2. Open terminal and run the offline verifier:
```bash
python tools/verify_capsule.py path/to/proof_capsule.json
```
3. Observe terminal output passing all checks offline without server connection.
4. Open the JSON file in an editor, alter 1 character in the student name, and re-run:
```bash
python tools/verify_capsule.py path/to/tampered_capsule.json
```
5. Observe terminal output rejecting the capsule with `[INVALID_PROOF]`.

---

## Step 6: Certificate Fraud Radar (30 sec)
1. Navigate to `http://127.0.0.1:5000/fraud-radar`.
2. Show live count of attempts, successes, and failed verifications generated during the demo.
3. Point out active anomaly heuristics (e.g. `RULE_REVOKED_CERT_PROBE` triggered by step 4).
