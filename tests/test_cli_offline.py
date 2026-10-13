import os
import sys
import json
import subprocess
import pytest
from app import create_app
from services.capsule_service import export_proof_capsule
from models.schema import Certificate

def test_offline_cli_verifier(app, tmp_path):
    with app.app_context():
        from services.certificate_service import issue_certificate
        from models.schema import Issuer
        
        issuer = Issuer.query.filter_by(code="OIT").first()
        cert, block, _ = issue_certificate(
            issuer_id=issuer.id,
            student_ref="STU-CLI-001",
            certificate_type="Master of Science",
            course_name="Distributed Ledger Systems",
            issue_date="2026-07-01",
            grade="Distinction"
        )
        
        capsule_data = export_proof_capsule(cert.id)
        capsule_file = tmp_path / "valid_capsule.json"
        capsule_file.write_text(json.dumps(capsule_data, indent=2), encoding="utf-8")
        
        # 1. Run tools/verify_capsule.py on valid capsule
        res = subprocess.run(
            [sys.executable, "tools/verify_capsule.py", str(capsule_file)],
            capture_output=True,
            text=True
        )
        assert res.returncode == 0
        assert "VERIFIED" in res.stdout
        assert "Cryptographically Authentic" in res.stdout
        
        # 2. Run tools/verify_capsule.py on tampered capsule
        tampered_capsule = dict(capsule_data)
        tampered_capsule["certificate"] = dict(tampered_capsule["certificate"])
        tampered_capsule["certificate"]["course_name"] = "Falsified Degree Title"
        
        tampered_file = tmp_path / "tampered_capsule.json"
        tampered_file.write_text(json.dumps(tampered_capsule, indent=2), encoding="utf-8")
        
        bad_res = subprocess.run(
            [sys.executable, "tools/verify_capsule.py", str(tampered_file)],
            capture_output=True,
            text=True
        )
        assert bad_res.returncode == 1
        assert "INVALID_PROOF" in bad_res.stdout
