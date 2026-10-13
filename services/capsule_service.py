import json
from models.schema import db, Certificate, Issuer, Block, Checkpoint
from blockchain.hashing import compute_content_hash, verify_content_hash
from blockchain.merkle import MerkleTree, verify_merkle_proof
from services.signing_service import verify_signature

def export_proof_capsule(certificate_id: str) -> dict:
    """
    Generate Proof Capsule dictionary for offline or client-side verification.
    Contains payload, salt, cryptographic proof, signature, block details, and Merkle proof.
    """
    cert = db.session.get(Certificate, certificate_id)
    if not cert:
        raise ValueError("Certificate not found.")
        
    issuer = db.session.get(Issuer, cert.issuer_id)
    if not issuer:
        raise ValueError("Issuer not found.")
        
    # Get associated block
    block = Block.query.filter_by(certificate_ref=cert.id, action_type="CERTIFICATE_ISSUED").first()
    block_index = block.index if block else 0
    block_hash = block.block_hash if block else ""
    
    # Get all blocks up to current to construct Merkle inclusion proof
    all_blocks = Block.query.order_by(Block.index.asc()).all()
    block_hashes = [b.block_hash for b in all_blocks]
    tree = MerkleTree(block_hashes)
    merkle_root = tree.get_root()
    merkle_proof = tree.get_proof(block_hash) if block_hash else []
    
    latest_cp = Checkpoint.query.order_by(Checkpoint.id.desc()).first()
    checkpoint_root = latest_cp.merkle_root if latest_cp else merkle_root

    return {
        "spec_version": "1.0",
        "certificate": {
            "certificate_id": cert.id,
            "issuer_id": str(cert.issuer_id),
            "student_ref": cert.student_ref,
            "certificate_type": cert.certificate_type,
            "course_name": cert.course_name,
            "issue_date": cert.issue_date,
            "grade": cert.grade or "",
            "salt": cert.salt
        },
        "content_hash": cert.content_hash,
        "signature": {
            "key_id": cert.signature_key_id,
            "issuer_public_key_pem": issuer.public_key_pem,
            "signature_b64": cert.issuer_signature
        },
        "ledger_proof": {
            "block_index": block_index,
            "block_hash": block_hash,
            "merkle_root": merkle_root,
            "merkle_proof": merkle_proof,
            "checkpoint_root": checkpoint_root
        }
    }

def verify_proof_capsule_data(capsule: dict) -> tuple[bool, str]:
    """
    Validate Proof Capsule data structure:
      1. Canonical content hash matches declared content_hash
      2. Ed25519 signature verifies against issuer public key PEM
      3. Merkle inclusion proof verifies block_hash against merkle_root
    Returns tuple: (is_valid: bool, reason: str)
    """
    try:
        cert_data = capsule.get("certificate", {})
        declared_hash = capsule.get("content_hash", "")
        sig_info = capsule.get("signature", {})
        ledger_info = capsule.get("ledger_proof", {})
        
        if not cert_data or not declared_hash or not sig_info:
            return False, "Malformed Proof Capsule structure."
            
        # 1. Content Hash Verification
        calc_hash = compute_content_hash(cert_data)
        if calc_hash.lower() != declared_hash.lower():
            return False, f"Content hash mismatch! Calculated={calc_hash[:16]}..., Declared={declared_hash[:16]}..."
            
        # 2. Signature Verification
        pub_pem = sig_info.get("issuer_public_key_pem", "")
        sig_b64 = sig_info.get("signature_b64", "")
        if not pub_pem or not sig_b64:
            return False, "Missing issuer public key or signature in capsule."
            
        if not verify_signature(pub_pem, declared_hash, sig_b64):
            return False, "Ed25519 digital signature verification failed!"
            
        # 3. Merkle Proof Verification (if provided)
        block_hash = ledger_info.get("block_hash", "")
        merkle_root = ledger_info.get("merkle_root", "")
        merkle_proof = ledger_info.get("merkle_proof", [])
        
        if block_hash and merkle_root and merkle_proof:
            if not verify_merkle_proof(block_hash, merkle_proof, merkle_root):
                return False, "Merkle inclusion proof failed to verify block_hash against merkle_root."

        return True, "Proof Capsule validated successfully! All cryptographic integrity checks passed."
    except Exception as e:
        return False, f"Capsule verification exception: {str(e)}"
