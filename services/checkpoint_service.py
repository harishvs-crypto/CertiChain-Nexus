import json
import hashlib
import hmac
from datetime import datetime
from flask import current_app
from models.schema import db, Block, Checkpoint
from blockchain.merkle import MerkleTree, verify_merkle_proof
from blockchain.ledger import LedgerBlock

def _sign_merkle_root(merkle_root: str, from_block: int, to_block: int) -> str:
    """Sign Merkle root using platform master signing key."""
    platform_key = current_app.config.get("PLATFORM_SIGNING_KEY", "platform-master-key-dev-seed-2026")
    msg = f"CHECKPOINT:{merkle_root}:{from_block}:{to_block}"
    return hmac.new(platform_key.encode('utf-8'), msg.encode('utf-8'), hashlib.sha256).hexdigest()

def create_merkle_checkpoint() -> tuple[Checkpoint, Block]:
    """
    Build binary Merkle Tree over all blocks, construct root, sign with platform key,
    store Checkpoint model, and append CHECKPOINT block to ledger.
    """
    blocks = Block.query.order_by(Block.index.asc()).all()
    if not blocks:
        raise ValueError("Cannot create checkpoint on an empty ledger.")
    
    last_checkpoint = Checkpoint.query.order_by(Checkpoint.to_block.desc()).first()
    from_block = last_checkpoint.to_block + 1 if last_checkpoint else 0
    to_block = blocks[-1].index
    
    block_hashes = [b.block_hash for b in blocks]
    tree = MerkleTree(block_hashes)
    merkle_root = tree.get_root()
    
    signature = _sign_merkle_root(merkle_root, from_block, to_block)
    
    checkpoint = Checkpoint(
        merkle_root=merkle_root,
        from_block=from_block,
        to_block=to_block,
        block_count=len(block_hashes),
        signature=signature,
        created_at=datetime.utcnow()
    )
    db.session.add(checkpoint)
    db.session.flush()
    
    # Append CHECKPOINT block to ledger
    new_index = to_block + 1
    prev_hash = blocks[-1].block_hash
    timestamp_iso = datetime.utcnow().isoformat() + "Z"
    
    payload = {
        "action": "CHECKPOINT",
        "checkpoint_id": checkpoint.id,
        "merkle_root": merkle_root,
        "from_block": from_block,
        "to_block": to_block
    }
    payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode('utf-8')).hexdigest()
    
    lb = LedgerBlock(
        index=new_index,
        timestamp_iso=timestamp_iso,
        action_type="CHECKPOINT",
        certificate_ref=f"CHECKPOINT-{checkpoint.id}",
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
    
    db.session.add(block)
    db.session.commit()
    
    return checkpoint, block

def export_checkpoint_json(checkpoint_id: int) -> dict:
    """Export checkpoint data structure for external archiving."""
    cp = db.session.get(Checkpoint, checkpoint_id)
    if not cp:
        raise ValueError("Checkpoint not found.")
        
    return {
        "checkpoint_id": cp.id,
        "merkle_root": cp.merkle_root,
        "from_block": cp.from_block,
        "to_block": cp.to_block,
        "block_count": cp.block_count,
        "signature": cp.signature,
        "created_at": cp.created_at.isoformat() + "Z"
    }

def verify_external_checkpoint(checkpoint_data: dict) -> dict:
    """
    Verify external checkpoint JSON against current authoritative ledger state.
    Returns validation breakdown.
    """
    merkle_root = checkpoint_data.get("merkle_root")
    from_block = checkpoint_data.get("from_block")
    to_block = checkpoint_data.get("to_block")
    signature = checkpoint_data.get("signature")
    
    if not merkle_root or signature is None:
        return {"valid": False, "reason": "Malformed checkpoint data format"}
        
    # Check signature
    expected_sig = _sign_merkle_root(merkle_root, from_block, to_block)
    if not hmac.compare_digest(signature, expected_sig):
        return {"valid": False, "reason": "Platform checkpoint signature verification failed!"}
        
    # Re-calculate Merkle root over current ledger blocks up to to_block
    target_blocks = Block.query.filter(Block.index <= to_block).order_by(Block.index.asc()).all()
    if not target_blocks:
        return {"valid": False, "reason": "Ledger has fewer blocks than requested checkpoint target"}
        
    current_hashes = [b.block_hash for b in target_blocks]
    current_tree = MerkleTree(current_hashes)
    current_root = current_tree.get_root()
    
    if not hmac.compare_digest(merkle_root.lower(), current_root.lower()):
        return {
            "valid": False,
            "reason": f"External Merkle root mismatch! External root: {merkle_root[:16]}..., Current ledger root: {current_root[:16]}..."
        }
        
    return {
        "valid": True,
        "reason": "External checkpoint perfectly matches current ledger history!",
        "merkle_root": current_root,
        "verified_block_count": len(target_blocks)
    }
