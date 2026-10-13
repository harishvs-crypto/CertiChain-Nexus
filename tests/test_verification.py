import pytest
from models.schema import Issuer, Certificate, Block
from services.certificate_service import issue_certificate
from services.verification_service import evaluate_certificate_verification

def test_verification_valid_certificate(app):
    with app.app_context():
        issuer = Issuer.query.filter_by(code="OIT").first()
        cert, block, _ = issue_certificate(
            issuer_id=issuer.id,
            student_ref="STU-VERIFY-001",
            certificate_type="Master of Science",
            course_name="Blockchain Engineering",
            issue_date="2026-06-15",
            grade="Distinction"
        )
        
        result = evaluate_certificate_verification(cert.id)
        assert result.status == "VERIFIED"
        assert result.checks["fingerprint"] is True
        assert result.checks["ledger"] is True
        assert result.checks["issuer"] is True
        assert result.checks["signature"] is True
        assert result.checks["credential_status"] is True

def test_verification_unrecognized_id(app):
    with app.app_context():
        result = evaluate_certificate_verification("CERT-NONEXISTENT-999")
        assert result.status == "UNRECOGNIZED"
        assert "not recognized" in result.explanation.lower()

def test_verification_tampered_payload(app):
    with app.app_context():
        issuer = Issuer.query.filter_by(code="OIT").first()
        cert, block, _ = issue_certificate(
            issuer_id=issuer.id,
            student_ref="STU-TAMPER-001",
            certificate_type="Master of Science",
            course_name="Data Science",
            issue_date="2026-06-15",
            grade="Pass"
        )
        
        # Tamper certificate grade in DB
        cert.grade = "Distinction"
        
        result = evaluate_certificate_verification(cert.id)
        assert result.status == "TAMPERED"
        assert result.checks["fingerprint"] is False
        assert "mismatch" in result.explanation.lower()

def test_verification_untrusted_issuer(app):
    with app.app_context():
        issuer = Issuer.query.filter_by(code="OIT").first()
        cert, block, _ = issue_certificate(
            issuer_id=issuer.id,
            student_ref="STU-SUSPEND-001",
            certificate_type="Certificate",
            course_name="Security",
            issue_date="2026-06-15"
        )
        
        # Suspend issuer after issuance
        issuer.status = "SUSPENDED"
        
        result = evaluate_certificate_verification(cert.id)
        assert result.status == "ISSUER_UNTRUSTED"
        assert result.checks["issuer"] is False
