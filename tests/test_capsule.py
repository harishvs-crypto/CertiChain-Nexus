import pytest
from models.schema import Issuer
from services.certificate_service import issue_certificate
from services.capsule_service import export_proof_capsule, verify_proof_capsule_data

def test_proof_capsule_generation_and_offline_verification(app):
    with app.app_context():
        issuer = Issuer.query.filter_by(code="OIT").first()
        cert, block, _ = issue_certificate(
            issuer_id=issuer.id,
            student_ref="STU-CAP-001",
            certificate_type="Master of Engineering",
            course_name="Cyber Security",
            issue_date="2026-04-12",
            grade="Distinction"
        )
        
        capsule = export_proof_capsule(cert.id)
        assert capsule["certificate"]["certificate_id"] == cert.id
        assert "signature_b64" in capsule["signature"]
        assert "merkle_root" in capsule["ledger_proof"]
        
        # Verify valid capsule
        is_valid, reason = verify_proof_capsule_data(capsule)
        assert is_valid is True
        assert "validated successfully" in reason.lower()
        
        # Verify tampered payload capsule
        bad_capsule = dict(capsule)
        bad_capsule["certificate"] = dict(capsule["certificate"])
        bad_capsule["certificate"]["grade"] = "Pass"
        
        bad_valid, bad_reason = verify_proof_capsule_data(bad_capsule)
        assert bad_valid is False
        assert "mismatch" in bad_reason.lower()
