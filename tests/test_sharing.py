import pytest
from models.schema import Issuer, Certificate
from services.certificate_service import issue_certificate
from services.sharing_service import (
    create_restricted_share_link,
    get_shared_certificate_data,
    revoke_share_token
)

def test_privacy_sharing_flow(app):
    with app.app_context():
        issuer = Issuer.query.filter_by(code="OIT").first()
        cert, _, _ = issue_certificate(
            issuer_id=issuer.id,
            student_ref="STU-SHARE-001",
            certificate_type="Degree",
            course_name="AI & Robotics",
            issue_date="2026-03-20",
            grade="Distinction"
        )
        
        # Student shares ONLY course_name and issue_date (grade & student_ref excluded)
        raw_token, token_obj = create_restricted_share_link(
            certificate_id=cert.id,
            permitted_fields=["course_name", "issue_date"],
            expires_in_hours=24
        )
        
        assert len(raw_token) > 0
        
        # Public access via raw token
        result = get_shared_certificate_data(raw_token)
        assert result["valid"] is True
        fields = result["shared_fields"]
        assert fields["course_name"] == "AI & Robotics"
        assert fields["issue_date"] == "2026-03-20"
        assert "grade" not in fields
        assert "student_ref" not in fields
        
        # Revoke share link
        revoke_share_token(token_obj.id)
        rev_result = get_shared_certificate_data(raw_token)
        assert rev_result["valid"] is False
        assert "revoked" in rev_result["error"].lower()
