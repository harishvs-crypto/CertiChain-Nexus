import hashlib
import json
from datetime import datetime
from models.schema import db, Certificate, Issuer, Block, AuditLog
from services.certificate_service import issue_certificate
from blockchain.ledger import LedgerBlock

def revoke_certificate(certificate_id: str, actor_user_id: int, reason: str) -> Certificate:
    """Revoke an active certificate, append audit log, and record ledger event."""
    cert = db.session.get(Certificate, certificate_id)
    if not cert:
        raise ValueError("Certificate not found.")
    
    if cert.status == 'REVOKED':
        return cert
    
    cert.status = 'REVOKED'
    cert.revocation_reason = reason
    cert.revoked_at = datetime.utcnow()
    cert.revoked_by_id = actor_user_id
    
    # Append Ledger Block
    latest_block = Block.query.order_by(Block.index.desc()).first()
    new_index = latest_block.index + 1 if latest_block else 1
    prev_hash = latest_block.block_hash if latest_block else "0"*64
    timestamp_iso = datetime.utcnow().isoformat() + "Z"
    
    payload = {
        "action": "REVOCATION",
        "certificate_id": cert.id,
        "reason": reason,
        "revoked_at": timestamp_iso
    }
    payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode('utf-8')).hexdigest()
    
    lb = LedgerBlock(
        index=new_index,
        timestamp_iso=timestamp_iso,
        action_type="CERTIFICATE_REVOKED",
        certificate_ref=cert.id,
        payload_hash=payload_hash,
        prev_hash=prev_hash
    )
    
    block = Block(
        index=lb.index,
        timestamp=datetime.utcnow(),
        timestamp_iso=lb.timestamp_iso,
        action_type=lb.action_type,
        certificate_ref=lb.certificate_ref,
        payload_hash=lb.payload_hash,
        prev_hash=lb.prev_hash,
        block_hash=lb.block_hash
    )
    
    audit = AuditLog(
        actor_user_id=actor_user_id,
        event_type="CERTIFICATE_REVOKED",
        certificate_ref=cert.id,
        outcome="REVOKED",
        risk_flag=False,
        review_status="OBSERVED"
    )
    
    db.session.add(block)
    db.session.add(audit)
    db.session.commit()
    return cert

def supersede_certificate(
    old_cert_id: str,
    actor_user_id: int,
    reason: str,
    new_student_ref: str = None,
    new_certificate_type: str = None,
    new_course_name: str = None,
    new_issue_date: str = None,
    new_grade: str = None,
    base_url: str = "http://127.0.0.1:5000"
) -> tuple[Certificate, Certificate]:
    """
    Supersede an active/existing certificate with a updated replacement certificate.
    Increments version number, links superseded_by_id, and records CERTIFICATE_SUPERSEDED on ledger.
    Returns tuple: (old_certificate, new_certificate)
    """
    old_cert = db.session.get(Certificate, old_cert_id)
    if not old_cert:
        raise ValueError("Original certificate not found.")
    
    if old_cert.status in ['REVOKED', 'SUPERSEDED']:
        raise ValueError(f"Cannot supersede a certificate that is already {old_cert.status}.")
    
    # Issue replacement certificate
    new_cert, new_block, _ = issue_certificate(
        issuer_id=old_cert.issuer_id,
        student_ref=new_student_ref or old_cert.student_ref,
        certificate_type=new_certificate_type or old_cert.certificate_type,
        course_name=new_course_name or old_cert.course_name,
        issue_date=new_issue_date or datetime.utcnow().strftime("%Y-%m-%d"),
        grade=new_grade if new_grade is not None else old_cert.grade,
        student_user_id=old_cert.student_user_id,
        base_url=base_url
    )
    
    new_cert.version = old_cert.version + 1
    
    # Update old certificate status
    old_cert.status = 'SUPERSEDED'
    old_cert.superseded_by_id = new_cert.id
    old_cert.revocation_reason = f"Superseded by {new_cert.id}: {reason}"
    old_cert.revoked_at = datetime.utcnow()
    old_cert.revoked_by_id = actor_user_id
    
    # Record Supersession Ledger Block
    latest_block = Block.query.order_by(Block.index.desc()).first()
    new_index = latest_block.index + 1
    prev_hash = latest_block.block_hash
    timestamp_iso = datetime.utcnow().isoformat() + "Z"
    
    payload = {
        "action": "SUPERSEDED",
        "old_certificate_id": old_cert.id,
        "new_certificate_id": new_cert.id,
        "reason": reason
    }
    payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode('utf-8')).hexdigest()
    
    lb = LedgerBlock(
        index=new_index,
        timestamp_iso=timestamp_iso,
        action_type="CERTIFICATE_SUPERSEDED",
        certificate_ref=old_cert.id,
        payload_hash=payload_hash,
        prev_hash=prev_hash
    )
    
    block = Block(
        index=lb.index,
        timestamp=datetime.utcnow(),
        timestamp_iso=lb.timestamp_iso,
        action_type=lb.action_type,
        certificate_ref=lb.certificate_ref,
        payload_hash=lb.payload_hash,
        prev_hash=lb.prev_hash,
        block_hash=lb.block_hash
    )
    
    audit = AuditLog(
        actor_user_id=actor_user_id,
        event_type="CERTIFICATE_SUPERSEDED",
        certificate_ref=old_cert.id,
        outcome="SUPERSEDED",
        risk_flag=False,
        review_status="OBSERVED"
    )
    
    db.session.add(block)
    db.session.add(audit)
    db.session.commit()
    
    return old_cert, new_cert
