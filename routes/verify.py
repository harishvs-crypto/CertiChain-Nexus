from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from models.schema import db, Certificate, Issuer, Block, AuditLog
from services.verification_service import evaluate_certificate_verification
from routes.auth import get_current_user

verify_bp = Blueprint('verify', __name__)

@verify_bp.route('/')
def landing():
    user = get_current_user()
    recent_stats = {
        "verified_count": AuditLog.query.filter_by(outcome='VERIFIED').count(),
        "total_certs": Certificate.query.count(),
        "total_issuers": Issuer.query.filter_by(status='TRUSTED').count()
    }
    return render_template('landing.html', user=user, stats=recent_stats)

@verify_bp.route('/verify', methods=['GET'])
def search_page():
    cert_id = request.args.get('id', '').strip()
    if cert_id:
        return redirect(url_for('verify.verify_certificate_page', certificate_id=cert_id))
    return render_template('verify.html')

@verify_bp.route('/verify/<certificate_id>')
def verify_certificate_page(certificate_id):
    client_ip = request.remote_addr or "127.0.0.1"
    user_agent = request.headers.get("User-Agent", "")
    user = get_current_user()
    actor_id = user.id if user else None
    
    result = evaluate_certificate_verification(
        certificate_id=certificate_id,
        client_ip=client_ip,
        user_agent=user_agent,
        actor_user_id=actor_id
    )
    
    # Load Trust Timeline events
    blocks = Block.query.filter_by(certificate_ref=certificate_id).order_by(Block.index.asc()).all()
    audits = AuditLog.query.filter_by(certificate_ref=certificate_id).order_by(AuditLog.timestamp.asc()).all()
    
    timeline = []
    for b in blocks:
        timeline.append({
            "type": "LEDGER_BLOCK",
            "title": f"Ledger Event: {b.action_type}",
            "detail": f"Block #{b.index} | Payload Hash: {b.payload_hash[:16]}...",
            "timestamp": b.timestamp_iso
        })
    for a in audits:
        timeline.append({
            "type": "AUDIT_LOG",
            "title": f"Verification Check: {a.outcome}",
            "detail": f"Status: {a.outcome} | Identity Hash: {a.identity_hash[:12] if a.identity_hash else 'Anonymous'}",
            "timestamp": a.timestamp.isoformat() + "Z"
        })
        
    return render_template(
        'verification_result.html',
        result=result.to_dict(),
        cert_id=certificate_id,
        timeline=timeline
    )

@verify_bp.route('/api/verify/<certificate_id>', methods=['GET'])
def api_verify(certificate_id):
    client_ip = request.remote_addr or "127.0.0.1"
    user_agent = request.headers.get("User-Agent", "")
    user = get_current_user()
    actor_id = user.id if user else None
    
    result = evaluate_certificate_verification(
        certificate_id=certificate_id,
        client_ip=client_ip,
        user_agent=user_agent,
        actor_user_id=actor_id
    )
    return jsonify(result.to_dict()), 200
