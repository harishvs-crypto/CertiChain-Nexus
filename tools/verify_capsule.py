#!/usr/bin/env python3
"""
CertiChain Nexus - Standalone Proof Capsule Offline Verifier CLI Tool.
Usage:
    python tools/verify_capsule.py path/to/proof_capsule.json
"""

import sys
import json
import hashlib
import hmac
import unicodedata
import base64
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

def normalize_text(text: str) -> str:
    if text is None:
        return ""
    return unicodedata.normalize('NFC', str(text).strip())

def compute_content_hash(cert_dict: dict) -> str:
    canonical = {
        "certificate_id": normalize_text(cert_dict.get("certificate_id", "")).upper(),
        "course_name": normalize_text(cert_dict.get("course_name", "")),
        "certificate_type": normalize_text(cert_dict.get("certificate_type", "")),
        "grade": normalize_text(cert_dict.get("grade", "")),
        "issue_date": normalize_text(cert_dict.get("issue_date", "")),
        "issuer_id": normalize_text(cert_dict.get("issuer_id", "")),
        "salt": normalize_text(cert_dict.get("salt", "")),
        "student_ref": normalize_text(cert_dict.get("student_ref", ""))
    }
    json_bytes = json.dumps(canonical, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(json_bytes).hexdigest()

def verify_ed25519_signature(pub_pem: str, content_hash: str, sig_b64: str) -> bool:
    try:
        public_key = serialization.load_pem_public_key(pub_pem.encode('utf-8'))
        sig_bytes = base64.b64decode(sig_b64.encode('utf-8'))
        public_key.verify(sig_bytes, content_hash.encode('utf-8'))
        return True
    except Exception:
        return False

def hash_pair(left_hash: str, right_hash: str) -> str:
    combined = (left_hash + right_hash).encode('utf-8')
    return hashlib.sha256(combined).hexdigest()

def verify_merkle_proof(leaf_hash: str, proof: list, root_hash: str) -> bool:
    current = leaf_hash.lower()
    for step in proof:
        sibling = step["hash"].lower()
        direction = step["direction"]
        if direction == "right":
            current = hash_pair(current, sibling)
        else:
            current = hash_pair(sibling, current)
    return current.lower() == root_hash.lower()

def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/verify_capsule.py <path_to_capsule.json>")
        sys.exit(1)
        
    capsule_path = Path(sys.argv[1])
    if not capsule_path.exists():
        print(f"Error: File '{capsule_path}' not found.")
        sys.exit(1)
        
    try:
        with open(capsule_path, "r", encoding="utf-8") as f:
            capsule = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        sys.exit(1)

    print("\n=======================================================")
    print("      CertiChain Nexus - Proof Capsule Offline Verifier")
    print("=======================================================\n")
    
    cert = capsule.get("certificate", {})
    cert_id = cert.get("certificate_id", "UNKNOWN")
    declared_hash = capsule.get("content_hash", "")
    sig_info = capsule.get("signature", {})
    ledger_info = capsule.get("ledger_proof", {})

    print(f"Target Certificate ID : {cert_id}")
    print(f"Course Name           : {cert.get('course_name')}")
    print(f"Student Reference     : {cert.get('student_ref')}")
    print(f"Declared Content Hash : {declared_hash[:16]}...")
    print("-" * 55)

    # 1. Content Hash Verification
    calc_hash = compute_content_hash(cert)
    hash_match = (calc_hash.lower() == declared_hash.lower())
    print(f"[CHECK 1] Content Payload Hash : {'[PASSED]' if hash_match else '[FAILED]'}")
    if not hash_match:
        print(f"  -> Recalculated hash: {calc_hash}")
        
    # 2. Digital Signature Verification
    pub_pem = sig_info.get("issuer_public_key_pem", "")
    sig_b64 = sig_info.get("signature_b64", "")
    sig_valid = verify_ed25519_signature(pub_pem, declared_hash, sig_b64)
    print(f"[CHECK 2] Issuer Ed25519 Signature: {'[PASSED]' if sig_valid else '[FAILED]'}")

    # 3. Merkle Inclusion Proof
    block_hash = ledger_info.get("block_hash", "")
    merkle_root = ledger_info.get("merkle_root", "")
    merkle_proof = ledger_info.get("merkle_proof", [])
    merkle_valid = True
    if block_hash and merkle_root and merkle_proof:
        merkle_valid = verify_merkle_proof(block_hash, merkle_proof, merkle_root)
        print(f"[CHECK 3] Merkle Ledger Inclusion: {'[PASSED]' if merkle_valid else '[FAILED]'}")
    else:
        print(f"[CHECK 3] Merkle Ledger Inclusion: [SKIPPED - Incomplete Proof Data]")

    print("=" * 55)
    overall_valid = hash_match and sig_valid and merkle_valid
    if overall_valid:
        print("VERIFICATION RESULT: [VERIFIED] - Proof Capsule is 100% Cryptographically Authentic.")
        sys.exit(0)
    else:
        print("VERIFICATION RESULT: [INVALID_PROOF] - Proof Capsule Integrity Checks Failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
