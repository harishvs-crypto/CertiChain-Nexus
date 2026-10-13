import pytest
from models.schema import Issuer, Certificate, User
from services.certificate_service import issue_certificate
from services.revocation_service import revoke_certificate, supersede_certificate
from services.verification_service import evaluate_certificate_verification

def test_revocation_flow(app):
    with app.app_context():
        issuer = Issuer.query.filter_by(code="OIT").first()
        admin = User.query.filter_by(role="ADMIN").first()
        
        cert, block, _ = issue_certificate(
            issuer_id=issuer.id,
            student_ref="STU-REV-001",
            certificate_type="Degree",
            course_name="Software Engineering",
            issue_date="2026-01-10"
        )
        
        revoked_cert = revoke_certificate(cert.id, admin.id, "Academic Misconduct")
        assert revoked_cert.status == "REVOKED"
        
        # Verify result must return REVOKED
        res = evaluate_certificate_verification(cert.id)
        assert res.status == "REVOKED"
        assert res.checks["credential_status"] is False
        assert "misconduct" in res.explanation.lower()

def test_supersession_flow(app):
    with app.app_context():
        issuer = Issuer.query.filter_by(code="OIT").first()
        admin = User.query.filter_by(role="ADMIN").first()
        
        old_cert, _, _ = issue_certificate(
            issuer_id=issuer.id,
            student_ref="STU-SUPER-001",
            certificate_type="Bachelor of Engineering",
            course_name="Computer Science",
            issue_date="2026-01-10",
            grade="Pass"
        )
        
        old_cert_updated, new_cert = supersede_certificate(
            old_cert_id=old_cert.id,
            actor_user_id=admin.id,
            reason="Grade Correction after re-evaluation",
            new_grade="First Class"
        )
        
        assert old_cert_updated.status == "SUPERSEDED"
        assert old_cert_updated.superseded_by_id == new_cert.id
        assert new_cert.version == 2
        assert new_cert.status == "ACTIVE"
        
        # Verification on old returns SUPERSEDED with pointer to replacement
        res_old = evaluate_certificate_verification(old_cert.id)
        assert res_old.status == "SUPERSEDED"
        assert res_old.superseded_by_id == new_cert.id
        
        # Verification on new returns VERIFIED
        res_new = evaluate_certificate_verification(new_cert.id)
        assert res_new.status == "VERIFIED"
