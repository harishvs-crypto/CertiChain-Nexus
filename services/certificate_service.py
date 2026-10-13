import os
import secrets
import qrcode
import io
import base64
from datetime import datetime
from pathlib import Path
from flask import current_app, url_for
from models.schema import db, Certificate, Issuer, User, Block
from blockchain.hashing import compute_content_hash, build_canonical_payload
from blockchain.ledger import LedgerBlock, create_genesis_block
from services.signing_service import sign_content_hash

def generate_certificate_id() -> str:
    """Generate unique Certificate ID format CERT-YYYY-XXXXX."""
    year = datetime.utcnow().strftime("%Y")
    random_hex = secrets.token_hex(4).upper()
    return f"CERT-{year}-{random_hex}"

def generate_qr_code(verification_url: str) -> tuple[bytes, str]:
    """Generate PNG QR code bytes and base64 string for direct rendering."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(verification_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_bytes = buffer.getvalue()
    qr_b64 = base64.b64encode(qr_bytes).decode('utf-8')
    return qr_bytes, qr_b64

def issue_certificate(
    issuer_id: int,
    student_ref: str,
    certificate_type: str,
    course_name: str,
    issue_date: str,
    grade: str = None,
    student_user_id: int = None,
    base_url: str = "http://127.0.0.1:5000"
) -> tuple[Certificate, Block, str]:
    """
    Issue a new certificate.
    Atomically commits Certificate record + Blockchain Ledger block in a single DB transaction.
    Returns tuple: (certificate, block, qr_b64)
    """
    issuer = db.session.get(Issuer, issuer_id)
    if not issuer:
        raise ValueError("Issuer institution not found.")
    
    if issuer.status != 'TRUSTED':
        raise PermissionError(f"Issuer '{issuer.name}' is currently in {issuer.status} status and cannot issue certificates.")
    
    if not issuer.encrypted_private_key or not issuer.public_key_pem:
        raise ValueError("Issuer institution has not been provisioned with Ed25519 signing keypair.")
    
    cert_id = generate_certificate_id()
    salt = secrets.token_hex(32)
    
    cert_payload = {
        "certificate_id": cert_id,
        "issuer_id": str(issuer.id),
        "student_ref": student_ref,
        "certificate_type": certificate_type,
        "course_name": course_name,
        "issue_date": issue_date,
        "grade": grade or "",
        "salt": salt
    }
    
    content_hash = compute_content_hash(cert_payload)
    signature_b64 = sign_content_hash(issuer.encrypted_private_key, content_hash)
    
    # Check if student_user_id exists
    if student_user_id:
        student_user = db.session.get(User, student_user_id)
        if not student_user:
            student_user_id = None

    certificate = Certificate(
        id=cert_id,
        issuer_id=issuer.id,
        student_ref=student_ref,
        student_user_id=student_user_id,
        certificate_type=certificate_type,
        course_name=course_name,
        issue_date=issue_date,
        grade=grade,
        salt=salt,
        content_hash=content_hash,
        issuer_signature=signature_b64,
        signature_key_id=issuer.key_id,
        status='ACTIVE',
        version=1
    )
    
    # Atomic transaction start
    try:
        db.session.add(certificate)
        
        # Ensure Genesis block exists
        latest_block = Block.query.order_by(Block.index.desc()).first()
        if not latest_block:
            gen = create_genesis_block()
            latest_block = Block(
                index=gen.index,
                timestamp=datetime.utcnow(),
                timestamp_iso=gen.timestamp_iso,
                action_type=gen.action_type,
                certificate_ref=gen.certificate_ref,
                payload_hash=gen.payload_hash,
                prev_hash=gen.prev_hash,
                block_hash=gen.block_hash
            )
            db.session.add(latest_block)
            db.session.flush()

        new_index = latest_block.index + 1
        timestamp_iso = datetime.utcnow().isoformat() + "Z"
        
        lb = LedgerBlock(
            index=new_index,
            timestamp_iso=timestamp_iso,
            action_type="CERTIFICATE_ISSUED",
            certificate_ref=cert_id,
            payload_hash=content_hash,
            prev_hash=latest_block.block_hash
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
        
        db.session.add(block)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise RuntimeError(f"Certificate issuance failed during atomic DB/Ledger transaction: {str(e)}")
    
    # Generate QR Code
    verify_url = f"{base_url.rstrip('/')}/verify/{cert_id}"
    qr_bytes, qr_b64 = generate_qr_code(verify_url)
    
    # Save QR code to certificates directory
    cert_dir = current_app.config.get('CERTIFICATES_DIR', Path('certificates'))
    os.makedirs(cert_dir, exist_ok=True)
    qr_file_path = Path(cert_dir) / f"qr_{cert_id}.png"
    with open(qr_file_path, "wb") as f:
        f.write(qr_bytes)
        
    return certificate, block, qr_b64
