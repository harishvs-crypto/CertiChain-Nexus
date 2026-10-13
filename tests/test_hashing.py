import pytest
from blockchain.hashing import (
    build_canonical_payload,
    compute_content_hash,
    verify_content_hash,
    normalize_text
)

def test_normalize_text():
    assert normalize_text("  hello world  ") == "hello world"
    assert normalize_text(None) == ""

def test_canonical_payload_and_hashing():
    cert_data = {
        "certificate_id": "cert-2026-001",
        "issuer_id": "INST-01",
        "student_ref": "STU-999",
        "certificate_type": "Bachelor of Science",
        "course_name": "Computer Science",
        "issue_date": "2026-05-15",
        "grade": "Distinction",
        "salt": "a" * 64
    }
    
    canonical = build_canonical_payload(cert_data)
    assert canonical["certificate_id"] == "CERT-2026-001"
    assert canonical["salt"] == "a" * 64
    
    hash1 = compute_content_hash(cert_data)
    assert len(hash1) == 64
    assert verify_content_hash(cert_data, hash1) is True
    
    # Tampered field
    tampered_data = dict(cert_data)
    tampered_data["grade"] = "Pass"
    assert verify_content_hash(tampered_data, hash1) is False
