# CertiChain Nexus

> **Blockchain-Based Certificate Verification System with Explainable Trust Analysis and Fraud Detection**
> *Trust Every Credential. Verify Every Claim.*

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests: 20 Passed](https://img.shields.io/badge/tests-20%20passed-brightgreen.svg)]()

---

## 1. Project Overview & Vision
**CertiChain Nexus** is a demo-ready, full-stack digital certificate verification and fraud detection platform. It eliminates credential fraud and administrative tampering by combining cryptographic commitments (SHA-256), Ed25519 digital signatures, an append-only hash-linked blockchain ledger, periodic Merkle tree checkpointing, and an Explainable Trust Engine.

### Problems Solved
1. **Unverifiable Paper/PDF Certificates:** Trivial to forge via desktop image editing.
2. **Database Vulnerability (The Insider Attack):** A database administrator or privileged hacker can alter grades or issue fake degrees undetected in a standard SQL database.
3. **Invisible Revocations:** Paper credentials and static PDF copies never show when a degree is revoked due to academic misconduct.
4. **Opaque "Valid/Invalid" Checks:** Traditional checkers provide no explanation of which check failed or why.

---

## 2. Core Innovations

### A. Explainable Trust Engine
Rather than returning a binary `True/False`, the engine validates credentials against a documented **Status Precedence Hierarchy**:
$$\text{LEDGER\_ERROR} \succ \text{TAMPERED} \succ \text{INVALID\_PROOF} \succ \text{ISSUER\_UNTRUSTED} \succ \text{REVOKED} \succ \text{SUPERSEDED} \succ \text{VERIFIED}$$
Every evaluation provides plain-language explanations, a 5-point inspection matrix, and a real-time Trust Timeline.

### B. Dynamic QR-Based Verification
Each certificate generates a high-resolution QR code containing the authoritative verification URL. The QR code itself is never trusted as standalone proof: scanning forces real-time server-side cryptographic re-validation against the live ledger.

### C. Append-Only Revocation & Supersession
Historical issuance records are never overwritten. Revocations and version updates are appended as new ledger events (`CERTIFICATE_REVOKED`, `CERTIFICATE_SUPERSEDED`), linking to replacements via `supersedes_certificate_id`.

### D. Privacy-Aware Credential Sharing
Students can create restricted share links with selective disclosure:
- Choose exactly which fields to disclose (e.g., share Course Name while concealing Grade).
- Raw tokens are generated via `secrets.token_urlsafe(32)` and stored exclusively as SHA-256 hashes at rest.
- Time-bounded expiry and instant one-click student revocation.

### E. Certificate Fraud Radar
Transparent, real-time heuristic anomaly detection over genuine audit logs (with zero fake AI/ML claims). Rules monitor rate-limit failures, repeated fingerprint mismatches, and probing against revoked or suspended entities.

### F. Blockchain Ledger Explorer
Allows auditors to inspect all block headers, hashes, action types, and previous-hash links. Includes a **Controlled Tamper Simulation** that safely clones the ledger in-memory to prove that modifying a past block breaks cryptographic chain continuity.

### G. Standalone Proof Capsules & Merkle Checkpoints
- **Ed25519 Signatures:** Issuers sign the content hash with an Ed25519 private key (stored encrypted at rest via Fernet).
- **Salted Commitments:** 64-hex salts eliminate dictionary guessing attacks on student attributes.
- **Merkle Checkpointing:** Compresses block history into cryptographic Merkle roots signed by platform keys.
- **Offline Verifier (`tools/verify_capsule.py`):** Enables offline validation without a server connection.

---

## 3. Threat Model & Security Defenses

| Threat Vector | System Defense | Limitation / Honest Disclosure |
|---|---|---|
| **Altered Degree Details (e.g. Photoshop)** | Canonical SHA-256 fingerprint mismatch returns `TAMPERED`. | Relies on verifiers using the digital verification portal. |
| **Tampered Historical Database Row** | Hash recalculation fails against blockchain ledger (`TAMPERED` or `LEDGER_ERROR`). | Privileged root attacker could rewrite both SQLite DB and block records unless external checkpoint was saved. |
| **Forged Issuance by Unauthorized Party** | Issuer Ed25519 digital signature verification fails (`INVALID_PROOF`). | If issuer's private key is compromised, forged certificates can be signed. |
| **Revoked Certificate Re-Use** | Real-time authoritative ledger check flags `REVOKED`. | Offline proof capsules generated prior to revocation require checking online revocation lists. |
| **Dictionary Guessing on Hashes** | 64-hex per-certificate cryptographic random salt. | Salts must remain confidential between student and issuer. |
| **Brute-Force Verification Probing** | Salted client identity hashing and Fraud Radar heuristic alert. | Rate-limiting uses IP/identity heuristics. |

---

## 4. Technology Stack
- **Backend:** Python 3.10+, Flask 3.1, Flask-SQLAlchemy, Flask-WTF, Werkzeug
- **Cryptography:** `cryptography` (Ed25519 & Fernet), `hashlib` (SHA-256), `hmac`
- **QR & Imaging:** `qrcode[pil]`, `Pillow`
- **Database:** SQLite (SQLAlchemy models portable to PostgreSQL)
- **Frontend:** Vanilla HTML5, Modern CSS3 Design System, JavaScript, Chart.js
- **Testing:** Pytest 8.0+ (20 automated tests)

---

## 5. Installation & Quickstart

### Prerequisites
- Python 3.10 or higher
- Git

### 1. Clone Repository & Setup Virtual Environment
```bash
# Clone repository
git clone https://github.com/certichain-nexus/certichain-nexus.git
cd certichain-nexus

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 4. Initialize Database & Seed Demo Data
```bash
flask seed-db
```
This idempotently seeds:
- Super Admin account
- 2 accredited institutions (`OIT`, `MIT`) with Ed25519 keypairs
- Issuer and Student user accounts
- Sample active, revoked, and superseded certificates
- Genesis block and Merkle checkpoint

### 5. Run the Application
```bash
python app.py
```
Open your browser at: `http://127.0.0.1:5000`

---

## 6. Pre-Configured Demo Credentials

| Role | Email Address | Password | Description |
|---|---|---|---|
| **Super Admin** | `admin@certichain.nexus` | `AdminPass123!` | System stats, approvals, checkpoints |
| **Institution Issuer** | `issuer@oit.edu` | `IssuerPass123!` | Issues and revokes certificates for OIT |
| **Student** | `student@oit.edu` | `StudentPass123!` | Views vault, generates share links, downloads capsules |
| **Public Verifier** | *No login needed* | *No login needed* | Verifies IDs, scans QR codes, reports fraud |

---

## 7. Running the Automated Test Suite
Execute the 20 automated tests covering canonical hashing, Ed25519 signatures, Merkle trees, ledger integrity, status precedence, and the offline CLI verifier:
```bash
pytest
```
*Expected output: `20 passed in ~14s`*

---

## 8. Offline Proof Capsule Verifier Tool
To verify any downloaded `.json` Proof Capsule offline without internet connectivity:
```bash
python tools/verify_capsule.py path/to/proof_capsule.json
```
