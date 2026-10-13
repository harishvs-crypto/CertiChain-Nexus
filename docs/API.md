# CertiChain Nexus - REST API Documentation

This document describes all implemented HTTP API endpoints across authentication, institution administration, certificate lifecycle, verification, privacy sharing, Merkle checkpoints, and blockchain ledgers.

---

## 1. Authentication & Session

### `POST /login` (Web Form) / Session Auth
- **Description:** Authenticate user and initialize secure session cookies (`HttpOnly`, `SameSite=Lax`).
- **Body parameters:** `email` (string), `password` (string).
- **Responses:**
  - `302 Found`: Redirects to role-specific portal upon valid credentials.
  - `200 OK`: Renders error flash on invalid credentials.

### `GET /logout`
- **Description:** Terminate user session.
- **Responses:** `302 Found` (redirect to `/`).

---

## 2. Public Verification Engine

### `GET /api/verify/<certificate_id>`
- **Description:** Pure REST endpoint executing the explainable status-precedence verification algorithm.
- **Parameters:** `certificate_id` (string URL parameter, e.g. `CERT-2026-9592CD2D`).
- **Response `200 OK` (JSON):**
```json
{
  "status": "VERIFIED",
  "explanation": "All cryptographic fingerprints, ledger records, digital signatures, issuer trust, and credential statuses have been successfully authenticated.",
  "checks": {
    "fingerprint": true,
    "ledger": true,
    "signature": true,
    "issuer": true,
    "credential_status": true,
    "checkpoint": true
  },
  "certificate": {
    "id": "CERT-2026-9592CD2D",
    "certificate_type": "Bachelor of Science",
    "course_name": "Cybersecurity & Distributed Systems",
    "grade": "Distinction",
    "issue_date": "2026-10-10",
    "student_ref": "STU-2026-TEST-101",
    "status": "ACTIVE",
    "version": 1,
    "content_hash": "b2c9d8e7...",
    "signature_key_id": "a1b2c3d4e5f67890"
  },
  "issuer": {
    "id": 1,
    "name": "Oxford Institute of Technology",
    "code": "OIT",
    "status": "TRUSTED",
    "key_id": "a1b2c3d4e5f67890"
  },
  "verification_ref": "VR-9E3A71",
  "superseded_by_id": null,
  "timestamp": "2026-10-10T12:35:10.000Z"
}
```

---

## 3. Standalone Proof Capsule Verification

### `POST /api/verify/capsule`
- **Description:** Client-side / offline verifier upload endpoint accepting multipart/form-data (`capsule_file`) or application/json.
- **Payload:** JSON Proof Capsule payload containing certificate payload, salt, issuer public key, Ed25519 signature, and Merkle proof.
- **Response `200 OK` (JSON):**
```json
{
  "status": "VERIFIED",
  "valid": true,
  "reason": "Proof Capsule validated successfully! All cryptographic integrity checks passed.",
  "certificate_id": "CERT-2026-9592CD2D"
}
```

---

## 4. Privacy-Aware Restricted Sharing

### `POST /api/certificates/<certificate_id>/share`
- **Requires:** Authenticated Student, Issuer, or Admin.
- **Body parameters:**
  - `permitted_fields`: Array of strings (`["course_name", "issue_date"]`).
  - `expires_in_hours`: Integer (e.g. 72).
- **Response `200 OK` (JSON):**
```json
{
  "success": true,
  "raw_token": "aBC123xyz...",
  "share_url": "http://127.0.0.1:5000/share/aBC123xyz...",
  "expires_at": "2026-10-13T12:00:00Z",
  "permitted_fields": ["course_name", "issue_date"]
}
```

### `GET /share/<raw_token>`
- **Description:** Public view resolving token hash against stored hash commitment, revealing only authorized fields.

### `POST /api/share/<token_id>/revoke`
- **Requires:** Authenticated user.
- **Response `200 OK` (JSON):** `{"success": true, "message": "Share link revoked successfully."}`

---

## 5. Blockchain Ledger & Merkle Checkpoints

### `GET /api/ledger/validate`
- **Description:** Validates all block hashes and sequential previous-hash links from Genesis #0 to head.
- **Response `200 OK` (JSON):**
```json
{
  "is_valid": true,
  "failing_index": null,
  "reason": "Ledger integrity verified successfully",
  "total_blocks": 12
}
```

### `POST /api/ledger/tamper-demo`
- **Description:** Performs in-memory deep-copy tamper simulation on specified block index without modifying persistent DB records.
- **Body:** `{"block_index": 0}`
- **Response `200 OK` (JSON):**
```json
{
  "tampered_block_index": 0,
  "original_block_hash": "0a1b2c...",
  "calculated_block_hash": "f9e8d7...",
  "is_valid": false,
  "failing_block_index": 0,
  "reason": "Block contents altered at block #0"
}
```

---

## 6. Security & Fraud Radar

### `GET /api/fraud-radar`
- **Description:** Returns JSON metrics for total, authentic, and rejected verifications along with active heuristic alerts.

### `POST /api/reports`
- **Description:** Allows verifiers to flag suspicious certificates.
- **Body parameters:** `certificate_ref` (string), `reporter_contact` (string), `reason` (string).
- **Response `200 OK` (JSON):** `{"success": true, "message": "Report submitted successfully."}`
