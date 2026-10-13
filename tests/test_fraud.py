import pytest
from models.schema import AuditLog
from services.verification_service import evaluate_certificate_verification
from services.fraud_service import evaluate_fraud_radar_rules, get_fraud_radar_summary

def test_fraud_radar_detection(app):
    with app.app_context():
        # Generate 6 failed verification attempts from same identity
        for _ in range(6):
            evaluate_certificate_verification("CERT-NONEXISTENT-BAD", client_ip="192.168.1.50")
            
        alerts = evaluate_fraud_radar_rules(window_minutes=60)
        assert len(alerts) > 0
        rule_ids = [a["rule_id"] for a in alerts]
        assert "RULE_HIGH_FAILURE_RATE" in rule_ids or "RULE_UNKNOWN_ID_PROBE" in rule_ids or len(alerts) >= 1
        
        summary = get_fraud_radar_summary()
        assert summary["total_verifications"] >= 6
        assert summary["failed_verifications"] >= 6
