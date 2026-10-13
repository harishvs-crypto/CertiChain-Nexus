# CertiChain Nexus
<<<<<<< HEAD

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
=======
### Blockchain-Based Certificate Verification System

**Tagline:** Trust Every Credential. Verify Every Claim.

## 📌 About the Project

CertiChain Nexus is a blockchain-based digital certificate verification platform designed to improve the authenticity, security, and reliability of academic and professional credentials.

The system allows authorized institutions to issue digital certificates and enables employers, universities, and other verifiers to authenticate certificates using a unique certificate ID or QR code.

It uses SHA-256 cryptographic hashing and a hash-linked blockchain ledger to detect unauthorized changes to certificate records. Additional features include certificate revocation, issuer trust management, privacy-aware credential sharing, audit logging, and rule-based fraud monitoring.

## 🎯 Objectives

- Develop a secure digital certificate issuance and verification platform.
- Detect certificate tampering using cryptographic hashing.
- Maintain certificate integrity proofs using a blockchain-based ledger.
- Enable quick verification through QR codes and unique certificate IDs.
- Support certificate revocation and corrected credential versions.
- Protect sensitive student information by keeping it off-chain.
- Monitor suspicious verification attempts through a Fraud Radar dashboard.
- Provide transparent and explainable verification results.

## ✨ Key Features

### 1. Secure Certificate Issuance
Authorized institutions can issue digital certificates with unique identifiers and cryptographic fingerprints.

### 2. Blockchain-Based Integrity
Certificate proofs are recorded in a hash-linked ledger. Changes to historical blocks can be detected through chain validation.

### 3. QR Code Verification
Users can scan a certificate's QR code or enter its certificate ID to access the verification page.

### 4. Explainable Trust Engine
The system provides meaningful verification statuses, including:

- VERIFIED
- TAMPERED
- UNRECOGNIZED
- REVOKED
- SUPERSEDED
- ISSUER_UNTRUSTED
- LEDGER_ERROR

### 5. Certificate Revocation
Authorized issuers can revoke compromised, incorrect, or invalid credentials. The verification page reflects the current status.

### 6. Privacy-Aware Sharing
Students can share selected certificate information through restricted links with configurable expiration and revocation.

### 7. Fraud Radar
The dashboard monitors repeated failed verification attempts, fingerprint mismatches, and suspicious activity using configurable rules.

### 8. Blockchain Explorer
Authorized users can inspect block records, previous hashes, current hashes, and ledger integrity results.

### 9. Audit Logging
Important events, including issuance, verification, revocation, and administrative actions, are recorded for authorized review.

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Frontend | HTML5, CSS3, JavaScript, Bootstrap |
| Backend | Python, Flask |
| Database | SQLite |
| Cryptographic Hashing | SHA-256 |
| Blockchain | Python hash-linked ledger |
| QR Code Generation | Python qrcode library |
| Charts | Chart.js |
| Testing | pytest |

## 🏗️ System Architecture

The application consists of the following layers:

1. **Presentation Layer:** Web pages for administrators, issuers, students, and verifiers.
2. **Application Layer:** Flask routes, authentication, certificate management, and verification services.
3. **Trust Engine:** Hash comparison, issuer checks, revocation checks, and verification explanations.
4. **Database Layer:** Stores certificate metadata, users, issuers, and audit records.
5. **Blockchain Layer:** Records certificate proofs and credential events in a hash-linked ledger.

## 🔄 System Workflow

1. An educational institution registers and receives approval.
2. An authorized issuer enters certificate details.
3. The system generates a unique certificate ID.
4. A SHA-256 fingerprint is calculated from canonical certificate data.
5. Certificate metadata is stored in the database.
6. The integrity proof is recorded in the blockchain ledger.
7. A QR code is generated for the certificate.
8. A verifier scans the QR code or enters the certificate ID.
9. The system checks the fingerprint, ledger integrity, issuer status, and revocation status.
10. The verification page displays the result and its explanation.

## 📂 Project Structure

```text
certichain-nexus/
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── blockchain/
│   ├── ledger.py
│   ├── hashing.py
│   └── validator.py
├── services/
│   ├── certificate_service.py
│   ├── verification_service.py
│   ├── issuer_service.py
│   ├── revocation_service.py
│   ├── fraud_service.py
│   └── sharing_service.py
├── models/
│   ├── database.py
│   └── schema.py
├── routes/
│   ├── auth_routes.py
│   ├── admin_routes.py
│   ├── certificate_routes.py
│   ├── verify_routes.py
│   └── analytics_routes.py
├── templates/
├── static/
├── instance/
└── tests/
```

The final directory structure may include additional templates, routes, and test files as implementation progresses.

## 💻 Installation and Setup

### Prerequisites

- Python 3.10 or a compatible supported version.
- pip package manager.
- A modern web browser.
- Git, optionally.

### Step 1: Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
cd certichain-nexus
```

Replace `YOUR_REPOSITORY_URL` with your actual repository URL. If you have not created a repository, create the project folder locally instead.

### Step 2: Create a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Linux or macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install dependencies

>>>>>>> b10b01e724ac61f9fea1c45ef9dc15f5933baaf2
```bash
pip install -r requirements.txt
```

<<<<<<< HEAD
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
=======
### Step 4: Configure the application

Create a `.env` file using `.env.example` as a reference.

Set a secure development secret key and the required database configuration. Never commit real secrets to source control.

### Step 5: Initialize the database

Run the database initialization command documented by the implementation.

If a development seeding command is provided, use it to create fictional institutions, sample certificates, and development accounts.

### Step 6: Start the application

```bash
python app.py
```

Open the local URL displayed by Flask in your browser, typically:

`http://127.0.0.1:5000`

Follow the final implementation's README instructions if its startup command differs.

## 🧪 Testing

Run the test suite with:

```bash
pytest
```

Important test scenarios include:

- Successful verification of a genuine certificate.
- Detection of modified certificate details.
- Rejection of unknown certificate IDs.
- Correct handling of revoked certificates.
- Detection of blockchain integrity failures.
- Prevention of unauthorized certificate issuance.
- Enforcement of student and issuer access restrictions.
- Expiration and revocation of sharing links.
- Detection of repeated failed verification attempts.

## 🔐 Security and Privacy

- Passwords are stored using secure password hashing.
- Protected operations require authentication and authorization.
- Certificate fingerprints are calculated using deterministic serialization.
- Sensitive personal information is kept off-chain.
- Verification endpoints apply input validation and appropriate rate limiting.
- Share links use secure tokens with expiration and revocation.
- Audit records are designed to avoid unnecessary exposure of personal information.

## ⚠️ Implementation Limitations

The initial version uses a locally maintained Python hash-linked ledger. This demonstrates blockchain-style hash linking and tamper detection but is not a decentralized public blockchain.

A privileged administrator who controls all ledger storage may be able to rewrite the entire ledger. Stronger guarantees require independently maintained replicas, trusted external anchoring, or an appropriately designed distributed blockchain.

A matching hash proves consistency with the recorded data; it does not independently prove that the original certificate was legitimately issued. Issuer authentication and trust management are therefore essential.

## 🚀 Future Enhancements

- Solidity smart-contract integration.
- Deployment to an Ethereum-compatible test network.
- Multi-institution blockchain governance.
- Standards-based verifiable credentials.
- Decentralized identifiers.
- Advanced selective-disclosure proofs.
- Zero-knowledge proof integration.
- PostgreSQL support.
- Production-grade institutional signing-key management.
- Mobile application integration.

## 🎓 Project Applications

- Academic certificate verification.
- Professional training certificates.
- Online course completion credentials.
- Internship and workshop certificates.
- Skill and achievement verification.

## 👥 Intended Users

- Educational institutions.
- Students and graduates.
- Employers and recruiters.
- Universities and verification agencies.
- Authorized system administrators.

## 📄 License

Choose and add an appropriate license before distributing the project publicly.

## 👨‍💻 Conclusion

CertiChain Nexus demonstrates how cryptographic hashing, blockchain-style integrity proofs, QR-based verification, access control, and audit monitoring can be combined to improve digital certificate verification.

The project aims to reduce manual verification effort, make unauthorized changes detectable, improve transparency, and provide a foundation for future decentralized credential systems.
>>>>>>> b10b01e724ac61f9fea1c45ef9dc15f5933baaf2
