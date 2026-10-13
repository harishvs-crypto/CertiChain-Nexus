import pytest
from models.schema import Issuer, Certificate
from services.certificate_service import issue_certificate
from services.checkpoint_service import (
    create_merkle_checkpoint,
    export_checkpoint_json,
    verify_external_checkpoint
)

def test_merkle_checkpoint_creation_and_external_verification(app):
    with app.app_context():
        issuer = Issuer.query.filter_by(code="OIT").first()
        issue_certificate(issuer.id, "STU-CP-01", "BSc", "Math", "2026-01-01")
        issue_certificate(issuer.id, "STU-CP-02", "BSc", "Physics", "2026-01-02")
        
        cp, block = create_merkle_checkpoint()
        assert cp.id is not None
        assert len(cp.merkle_root) == 64
        assert cp.block_count >= 3 # Genesis + 2 certs
        
        cp_json = export_checkpoint_json(cp.id)
        assert cp_json["merkle_root"] == cp.merkle_root
        
        # Verify valid checkpoint
        res = verify_external_checkpoint(cp_json)
        assert res["valid"] is True
        
        # Verify tampered checkpoint root
        bad_cp_json = dict(cp_json)
        bad_cp_json["merkle_root"] = "0" * 64
        bad_res = verify_external_checkpoint(bad_cp_json)
        assert bad_res["valid"] is False
