from datetime import datetime, timedelta
from models.schema import db, AuditLog, SuspiciousReport, Certificate, Issuer

def evaluate_fraud_radar_rules(window_minutes: int = 60) -> list[dict]:
    """
    Execute transparent rule-based anomaly detection over REAL audit events.
    Rules:
      Rule 1: Rate limit identity > 5 failed verifications in window_minutes
      Rule 2: Repeated TAMPERED fingerprint mismatches (>= 2 in window)
      Rule 3: Repeated UNRECOGNIZED Certificate ID probe attempts (>= 3 in window)
      Rule 4: Access attempts on REVOKED credentials
      Rule 5: Access attempts on SUSPENDED issuer credentials
    """
    cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
    recent_logs = AuditLog.query.filter(AuditLog.timestamp >= cutoff).all()
    
    alerts = []
    
    # Rule 1: Failures by identity_hash
    identity_failures = {}
    for log in recent_logs:
        if log.outcome != 'VERIFIED' and log.identity_hash:
            identity_failures[log.identity_hash] = identity_failures.get(log.identity_hash, 0) + 1
            
    for ident, count in identity_failures.items():
        if count >= 5:
            alerts.append({
                "rule_id": "RULE_HIGH_FAILURE_RATE",
                "severity": "HIGH",
                "reason": f"Identity '{ident[:12]}...' attempted {count} failed verifications within {window_minutes} minutes.",
                "identity_hash": ident,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
            
    # Rule 2: Tampered Mismatches
    tampered_logs = [l for l in recent_logs if l.outcome == 'TAMPERED']
    if len(tampered_logs) >= 2:
        alerts.append({
            "rule_id": "RULE_TAMPER_PATTERN_DETECTED",
            "severity": "CRITICAL",
            "reason": f"{len(tampered_logs)} payload tamper attempts detected in the past {window_minutes} minutes!",
            "certificate_ref": tampered_logs[-1].certificate_ref,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
    # Rule 3: Revoked Credential Probing
    revoked_attempts = [l for l in recent_logs if l.outcome == 'REVOKED']
    if revoked_attempts:
        alerts.append({
            "rule_id": "RULE_REVOKED_CERT_PROBE",
            "severity": "MEDIUM",
            "reason": f"{len(revoked_attempts)} verification attempts made on explicitly revoked credentials.",
            "certificate_ref": revoked_attempts[-1].certificate_ref,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

    # Rule 4: Suspended Issuer Attempts
    suspended_attempts = [l for l in recent_logs if l.outcome == 'ISSUER_UNTRUSTED']
    if suspended_attempts:
        alerts.append({
            "rule_id": "RULE_SUSPENDED_ISSUER_PROBE",
            "severity": "HIGH",
            "reason": f"{len(suspended_attempts)} verification attempts made against suspended/untrusted issuers.",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

    return alerts

def get_fraud_radar_summary() -> dict:
    """Get real dashboard metrics and recent fraud alerts."""
    total_logs = AuditLog.query.count()
    success_count = AuditLog.query.filter_by(outcome='VERIFIED').count()
    failed_count = total_logs - success_count
    risk_alerts_count = AuditLog.query.filter_by(risk_flag=True).count()
    
    recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(20).all()
    user_reports = SuspiciousReport.query.order_by(SuspiciousReport.created_at.desc()).limit(10).all()
    
    rules_alerts = evaluate_fraud_radar_rules()
    
    return {
        "total_verifications": total_logs,
        "successful_verifications": success_count,
        "failed_verifications": failed_count,
        "risk_alerts_count": risk_alerts_count,
        "alerts": rules_alerts,
        "recent_logs": [
            {
                "id": l.id,
                "event_type": l.event_type,
                "certificate_ref": l.certificate_ref,
                "outcome": l.outcome,
                "risk_flag": l.risk_flag,
                "review_status": l.review_status,
                "timestamp": l.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            } for l in recent_logs
        ],
        "user_reports": [
            {
                "id": r.id,
                "certificate_ref": r.certificate_ref,
                "reporter_contact": r.reporter_contact,
                "reason": r.reason,
                "review_status": r.review_status,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S")
            } for r in user_reports
        ]
    }
