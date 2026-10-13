# CertiChain Nexus
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

```bash
pip install -r requirements.txt
```

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
