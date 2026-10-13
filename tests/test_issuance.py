import pytest
from models.schema import Issuer, Certificate, Block
from services.certificate_service import issue_certificate

def test_issue_certificate_success(app):
    with app.app_context():
        issuer = Issuer.query.filter_by(code="OIT").first()
        assert issuer is not None
        assert issuer.status == "TRUSTED"
        
        cert, block, qr_b64 = issue_certificate(
            issuer_id=issuer.id,
            student_ref="STU-2026-101",
            certificate_type="Bachelor of Science",
            course_name="Computer Science & Cryptography",
            issue_date="2026-06-01",
            grade="First Class Honours"
        )
        
        assert cert.id.startswith("CERT-2026-")
        assert cert.status == "ACTIVE"
        assert len(cert.content_hash) == 64
        assert len(cert.issuer_signature) > 0
        assert block.certificate_ref == cert.id
        assert block.action_type == "CERTIFICATE_ISSUED"
        assert len(qr_b64) > 0

def test_suspended_issuer_cannot_issue(app):
    with app.app_context():
        issuer = Issuer.query.filter_by(code="OIT").first()
        issuer.status = "SUSPENDED"
        
        with pytest.raises(PermissionError):
            issue_certificate(
                issuer_id=issuer.id,
                student_ref="STU-2026-102",
                certificate_type="Diploma",
                course_name="Cybersecurity",
                issue_date="2026-06-01"
            )
