from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from models.schema import db, AuditLog, SuspiciousReport
from services.fraud_service import get_fraud_radar_summary
from routes.auth import login_required, role_required, get_current_user

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/fraud-radar')
def fraud_radar():
    user = get_current_user()
    summary = get_fraud_radar_summary()
    return render_template('fraud_radar.html', user=user, summary=summary)

@analytics_bp.route('/api/fraud-radar', methods=['GET'])
def api_fraud_radar():
    summary = get_fraud_radar_summary()
    return jsonify(summary)

@analytics_bp.route('/audit-log')
@login_required
def audit_log():
    user = get_current_user()
    if user.role not in ['ADMIN', 'ISSUER']:
        flash("Permission denied.", "danger")
        return redirect(url_for('verify.landing'))
        
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()
    return render_template('audit_log.html', user=user, logs=logs)

@analytics_bp.route('/api/reports', methods=['POST'])
def report_suspicious():
    cert_ref = request.form.get('certificate_ref', '').strip()
    contact = request.form.get('reporter_contact', '').strip()
    reason = request.form.get('reason', '').strip()
    
    if not cert_ref or not reason:
        if request.is_json:
            return jsonify({"error": "Certificate ID and reason are required"}), 400
        flash("Certificate ID and reason are required.", "danger")
        return redirect(url_for('verify.landing'))
        
    report = SuspiciousReport(
        certificate_ref=cert_ref.upper(),
        reporter_contact=contact,
        reason=reason,
        review_status='PENDING'
    )
    db.session.add(report)
    db.session.commit()
    
    if request.is_json:
        return jsonify({"success": True, "message": "Report submitted successfully."})
    
    flash("Thank you. Your suspicious certificate report has been logged for security review.", "success")
    return redirect(url_for('verify.landing'))
