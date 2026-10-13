import hashlib
import hmac
from datetime import datetime
from models.schema import db, Certificate, Issuer, Block, AuditLog
from blockchain.hashing import verify_content_hash, build_canonical_payload
from blockchain.ledger import validate_chain_integrity, LedgerBlock
from services.signing_service import verify_signature

class VerificationResult:
    def __init__(
        self,
        status: str,
        explanation: str,
        checks: dict,
        certificate: dict = None,
        issuer: dict = None,
        verification_ref: str = None,
        superseded_by_id: str = None
    ):
        self.status = status # VERIFIED, TAMPERED, UNRECOGNIZED, REVOKED, SUPERSEDED, ISSUER_UNTRUSTED, LEDGER_ERROR, INVALID_PROOF
        self.explanation = explanation
        self.checks = checks # fingerprint, ledger, issuer, credential_status, signature, checkpoint
        self.certificate = certificate
        self.issuer = issuer
        self.verification_ref = verification_ref or f"VR-{secrets_ref()}"
        self.superseded_by_id = superseded_by_id
        self.timestamp = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "explanation": self.explanation,
            "checks": self.checks,
            "certificate": self.certificate,
            "issuer": self.issuer,
            "verification_ref": self.verification_ref,
            "superseded_by_id": self.superseded_by_id,
            "timestamp": self.timestamp
        }

def secrets_ref() -> str:
    import secrets
    return secrets.token_hex(6).upper()

def hash_client_identity(client_ip: str, user_agent: str = "") -> str:
    """Compute salted, truncated hash of client identity for privacy-preserving audit logging."""
    salt = "certichain-privacy-audit-salt-2026"
    combined = f"{salt}:{client_ip}:{user_agent}"
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:32]

def evaluate_certificate_verification(
    certificate_id: str,
    client_ip: str = "127.0.0.1",
    user_agent: str = "",
    actor_user_id: int = None
) -> VerificationResult:
    """
    Core Verification Engine implementing Status Precedence Policy:
    LEDGER_ERROR > TAMPERED > INVALID_PROOF > ISSUER_UNTRUSTED > REVOKED > SUPERSEDED > VERIFIED
    (or UNRECOGNIZED when certificate_id is missing).
    """
    identity_hash = hash_client_identity(client_ip, user_agent)
    
    checks = {
        "fingerprint": False,
        "ledger": False,
        "issuer": False,
        "credential_status": False,
        "signature": False,
        "checkpoint": True
    }
    
    if not certificate_id:
        _log_audit(actor_user_id, "VERIFY_ATTEMPT", None, "UNRECOGNIZED", identity_hash, risk_flag=False)
        return VerificationResult(
            status="UNRECOGNIZED",
            explanation="No Certificate ID was provided for verification.",
            checks=checks
        )
    
    cert_id_clean = str(certificate_id).strip().upper()
    cert = db.session.get(Certificate, cert_id_clean)
    
    if not cert:
        _log_audit(actor_user_id, "VERIFY_ATTEMPT", cert_id_clean, "UNRECOGNIZED", identity_hash, risk_flag=False)
        return VerificationResult(
            status="UNRECOGNIZED",
            explanation=f"Credential record with ID '{cert_id_clean}' was not recognized by the platform.",
            checks=checks
        )
    
    issuer = db.session.get(Issuer, cert.issuer_id)
    
    # 1. LEDGER INTEGRITY CHECK
    all_blocks = Block.query.order_by(Block.index.asc()).all()
    ledger_blocks = [
        LedgerBlock(
            index=b.index,
            timestamp_iso=getattr(b, 'timestamp_iso', None) or (b.timestamp.isoformat() + "Z"),
            action_type=b.action_type,
            certificate_ref=b.certificate_ref,
            payload_hash=b.payload_hash,
            prev_hash=b.prev_hash,
            block_hash=b.block_hash,
            nonce=b.nonce
        )
        for b in all_blocks
    ]
    
    is_ledger_valid, failing_idx, ledger_reason = validate_chain_integrity(ledger_blocks)
    if is_ledger_valid:
        checks["ledger"] = True
    else:
        _log_audit(actor_user_id, "VERIFY_ATTEMPT", cert_id_clean, "LEDGER_ERROR", identity_hash, risk_flag=True)
        return VerificationResult(
            status="LEDGER_ERROR",
            explanation=f"Ledger integrity check failed at block #{failing_idx}: {ledger_reason}",
            checks=checks,
            certificate=_cert_to_public_dict(cert, hide_private=True),
            issuer=_issuer_to_dict(issuer)
        )
        
    # 2. FINGERPRINT & TAMPER CHECK
    cert_payload = {
        "certificate_id": cert.id,
        "issuer_id": str(cert.issuer_id),
        "student_ref": cert.student_ref,
        "certificate_type": cert.certificate_type,
        "course_name": cert.course_name,
        "issue_date": cert.issue_date,
        "grade": cert.grade or "",
        "salt": cert.salt
    }
    
    if verify_content_hash(cert_payload, cert.content_hash):
        checks["fingerprint"] = True
    else:
        _log_audit(actor_user_id, "VERIFY_ATTEMPT", cert_id_clean, "TAMPERED", identity_hash, risk_flag=True)
        return VerificationResult(
            status="TAMPERED",
            explanation="Cryptographic fingerprint mismatch detected. The certificate payload details differ from the original recorded commitment.",
            checks=checks,
            certificate=_cert_to_public_dict(cert, hide_private=True),
            issuer=_issuer_to_dict(issuer)
        )
        
    # 3. DIGITAL SIGNATURE CHECK
    if issuer and issuer.public_key_pem:
        if verify_signature(issuer.public_key_pem, cert.content_hash, cert.issuer_signature):
            checks["signature"] = True
        else:
            _log_audit(actor_user_id, "VERIFY_ATTEMPT", cert_id_clean, "INVALID_PROOF", identity_hash, risk_flag=True)
            return VerificationResult(
                status="INVALID_PROOF",
                explanation="Issuer Ed25519 digital signature verification failed. The proof capsule or payload signature is invalid.",
                checks=checks,
                certificate=_cert_to_public_dict(cert, hide_private=True),
                issuer=_issuer_to_dict(issuer)
            )
    else:
        checks["signature"] = False

    # 4. ISSUER TRUST CHECK
    if issuer and issuer.status == 'TRUSTED':
        checks["issuer"] = True
    else:
        issuer_status_name = issuer.status if issuer else "UNREGISTERED"
        _log_audit(actor_user_id, "VERIFY_ATTEMPT", cert_id_clean, "ISSUER_UNTRUSTED", identity_hash, risk_flag=True)
        return VerificationResult(
            status="ISSUER_UNTRUSTED",
            explanation=f"Issuing institution '{issuer.name if issuer else 'Unknown'}' is currently in '{issuer_status_name}' status and not trusted.",
            checks=checks,
            certificate=_cert_to_public_dict(cert, hide_private=True),
            issuer=_issuer_to_dict(issuer)
        )

    # 5. CREDENTIAL STATUS CHECKS (REVOKED / SUPERSEDED / ACTIVE)
    if cert.status == 'REVOKED':
        checks["credential_status"] = False
        _log_audit(actor_user_id, "VERIFY_ATTEMPT", cert_id_clean, "REVOKED", identity_hash, risk_flag=False)
        return VerificationResult(
            status="REVOKED",
            explanation=f"This credential was explicitly REVOKED by the issuing institution on {cert.revoked_at}. Reason: {cert.revocation_reason or 'No reason specified'}.",
            checks=checks,
            certificate=_cert_to_public_dict(cert, hide_private=False),
            issuer=_issuer_to_dict(issuer)
        )
    elif cert.status == 'SUPERSEDED':
        checks["credential_status"] = False
        _log_audit(actor_user_id, "VERIFY_ATTEMPT", cert_id_clean, "SUPERSEDED", identity_hash, risk_flag=False)
        return VerificationResult(
            status="SUPERSEDED",
            explanation=f"This credential has been SUPERSEDED by an updated authorized version (Replacement ID: {cert.superseded_by_id or 'See institution'}).",
            checks=checks,
            certificate=_cert_to_public_dict(cert, hide_private=False),
            issuer=_issuer_to_dict(issuer),
            superseded_by_id=cert.superseded_by_id
        )
    elif cert.status == 'ACTIVE':
        checks["credential_status"] = True
        _log_audit(actor_user_id, "VERIFY_ATTEMPT", cert_id_clean, "VERIFIED", identity_hash, risk_flag=False)
        return VerificationResult(
            status="VERIFIED",
            explanation="All cryptographic fingerprints, ledger records, digital signatures, issuer trust, and credential statuses have been successfully authenticated.",
            checks=checks,
            certificate=_cert_to_public_dict(cert, hide_private=False),
            issuer=_issuer_to_dict(issuer)
        )

    _log_audit(actor_user_id, "VERIFY_ATTEMPT", cert_id_clean, "UNRECOGNIZED", identity_hash, risk_flag=False)
    return VerificationResult(
        status="UNRECOGNIZED",
        explanation="Unknown credential status.",
        checks=checks
    )

def _cert_to_public_dict(cert: Certificate, hide_private: bool = False) -> dict:
    return {
        "id": cert.id,
        "certificate_type": cert.certificate_type,
        "course_name": cert.course_name,
        "issue_date": cert.issue_date,
        "student_ref": cert.student_ref if not hide_private else "[PROTECTED]",
        "grade": cert.grade if not hide_private else "[PROTECTED]",
        "status": cert.status,
        "content_hash": cert.content_hash,
        "signature_key_id": cert.signature_key_id,
        "version": cert.version,
        "created_at": cert.created_at.isoformat() + "Z"
    }

def _issuer_to_dict(issuer: Issuer) -> dict:
    if not issuer:
        return {}
    return {
        "id": issuer.id,
        "name": issuer.name,
        "code": issuer.code,
        "status": issuer.status,
        "key_id": issuer.key_id,
        "public_key_pem": issuer.public_key_pem
    }

def _log_audit(user_id: int, event_type: str, cert_ref: str, outcome: str, identity_hash: str, risk_flag: bool = False):
    log = AuditLog(
        actor_user_id=user_id,
        event_type=event_type,
        certificate_ref=cert_ref,
        outcome=outcome,
        identity_hash=identity_hash,
        risk_flag=risk_flag,
        review_status='ALERT' if risk_flag else 'OBSERVED',
        timestamp=datetime.utcnow()
    )
    db.session.add(log)
    db.session.commit()
