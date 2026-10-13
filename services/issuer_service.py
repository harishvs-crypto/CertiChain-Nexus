import json
import hashlib
from datetime import datetime
from models.schema import db, Issuer, User, Block
from services.signing_service import generate_issuer_keypair
from blockchain.ledger import LedgerBlock, create_genesis_block

def register_institution(name: str, code: str) -> Issuer:
    """Register a new institution in PENDING status."""
    existing = Issuer.query.filter((Issuer.code == code) | (Issuer.name == name)).first()
    if existing:
        raise ValueError(f"Institution with code '{code}' or name '{name}' already exists.")
    
    issuer = Issuer(
        name=name,
        code=code.upper(),
        status='PENDING'
    )
    db.session.add(issuer)
    db.session.commit()
    return issuer

def approve_institution(issuer_id: int, admin_user_id: int) -> Issuer:
    """Approve institution, generate Ed25519 keypair, and log ledger block."""
    issuer = db.session.get(Issuer, issuer_id)
    if not issuer:
        raise ValueError("Institution not found.")
    
    if issuer.status == 'TRUSTED':
        return issuer

    # Generate keypair
    pub_pem, enc_priv, key_id = generate_issuer_keypair()
    issuer.public_key_pem = pub_pem
    issuer.encrypted_private_key = enc_priv
    issuer.key_id = key_id
    issuer.status = 'TRUSTED'

    # Get latest block to link
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
    payload = {
        "action": "ISSUER_APPROVED",
        "issuer_id": issuer.id,
        "issuer_code": issuer.code,
        "key_id": key_id
    }
    payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode('utf-8')).hexdigest()
    
    lb = LedgerBlock(
        index=new_index,
        timestamp_iso=timestamp_iso,
        action_type="ISSUER_STATUS_CHANGED",
        certificate_ref=f"ISSUER-{issuer.id}",
        payload_hash=payload_hash,
        prev_hash=latest_block.block_hash
    )
    
    new_block = Block(
        index=lb.index,
        timestamp=datetime.utcnow(),
        timestamp_iso=lb.timestamp_iso,
        action_type=lb.action_type,
        certificate_ref=lb.certificate_ref,
        payload_hash=lb.payload_hash,
        prev_hash=lb.prev_hash,
        block_hash=lb.block_hash
    )
    db.session.add(new_block)
    db.session.commit()
    return issuer

def suspend_institution(issuer_id: int, admin_user_id: int) -> Issuer:
    """Suspend institution."""
    issuer = db.session.get(Issuer, issuer_id)
    if not issuer:
        raise ValueError("Institution not found.")
    
    issuer.status = 'SUSPENDED'
    
    latest_block = Block.query.order_by(Block.index.desc()).first()
    new_index = latest_block.index + 1 if latest_block else 1
    prev_hash = latest_block.block_hash if latest_block else "0"*64
    timestamp_iso = datetime.utcnow().isoformat() + "Z"
    
    payload = {"action": "ISSUER_SUSPENDED", "issuer_id": issuer.id, "issuer_code": issuer.code}
    payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode('utf-8')).hexdigest()
    
    lb = LedgerBlock(
        index=new_index,
        timestamp_iso=timestamp_iso,
        action_type="ISSUER_STATUS_CHANGED",
        certificate_ref=f"ISSUER-{issuer.id}",
        payload_hash=payload_hash,
        prev_hash=prev_hash
    )
    
    new_block = Block(
        index=lb.index,
        timestamp=datetime.utcnow(),
        timestamp_iso=lb.timestamp_iso,
        action_type=lb.action_type,
        certificate_ref=lb.certificate_ref,
        payload_hash=lb.payload_hash,
        prev_hash=lb.prev_hash,
        block_hash=lb.block_hash
    )
    db.session.add(new_block)
    db.session.commit()
    return issuer

def reinstate_institution(issuer_id: int, admin_user_id: int) -> Issuer:
    """Reinstate suspended institution."""
    issuer = db.session.get(Issuer, issuer_id)
    if not issuer:
        raise ValueError("Institution not found.")
    
    issuer.status = 'TRUSTED'
    
    latest_block = Block.query.order_by(Block.index.desc()).first()
    new_index = latest_block.index + 1 if latest_block else 1
    prev_hash = latest_block.block_hash if latest_block else "0"*64
    timestamp_iso = datetime.utcnow().isoformat() + "Z"
    
    payload = {"action": "ISSUER_REINSTATED", "issuer_id": issuer.id, "issuer_code": issuer.code}
    payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode('utf-8')).hexdigest()
    
    lb = LedgerBlock(
        index=new_index,
        timestamp_iso=timestamp_iso,
        action_type="ISSUER_STATUS_CHANGED",
        certificate_ref=f"ISSUER-{issuer.id}",
        payload_hash=payload_hash,
        prev_hash=prev_hash
    )
    
    new_block = Block(
        index=lb.index,
        timestamp=datetime.utcnow(),
        timestamp_iso=lb.timestamp_iso,
        action_type=lb.action_type,
        certificate_ref=lb.certificate_ref,
        payload_hash=lb.payload_hash,
        prev_hash=lb.prev_hash,
        block_hash=lb.block_hash
    )
    db.session.add(new_block)
    db.session.commit()
    return issuer
