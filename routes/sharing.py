from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from services.sharing_service import (
    create_restricted_share_link,
    get_shared_certificate_data,
    revoke_share_token
)
from routes.auth import login_required, role_required, get_current_user
from models.schema import db, Certificate

sharing_bp = Blueprint('sharing', __name__)

@sharing_bp.route('/api/certificates/<cert_id>/share', methods=['POST'])
@login_required
@role_required('STUDENT', 'ADMIN', 'ISSUER')
def api_create_share(cert_id):
    user = get_current_user()
    data = request.get_json() or {}
    permitted_fields = data.get('permitted_fields', ['course_name', 'issue_date', 'student_ref'])
    expires_in_hours = int(data.get('expires_in_hours', 72))
    
    cert = db.session.get(Certificate, cert_id)
    if not cert:
        return jsonify({"error": "Certificate not found"}), 404
        
    try:
        raw_token, share_obj = create_restricted_share_link(cert.id, permitted_fields, expires_in_hours)
        share_url = request.url_root.rstrip('/') + url_for('sharing.view_shared', token=raw_token)
        return jsonify({
            "success": True,
            "raw_token": raw_token,
            "share_url": share_url,
            "expires_at": share_obj.expires_at.isoformat() + "Z",
            "permitted_fields": permitted_fields
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@sharing_bp.route('/share/<token>')
def view_shared(token):
    result = get_shared_certificate_data(token)
    return render_template('shared_certificate.html', result=result, token=token)

@sharing_bp.route('/api/share/<int:token_id>/revoke', methods=['POST'])
@login_required
def api_revoke_share(token_id):
    success = revoke_share_token(token_id)
    if success:
        return jsonify({"success": True, "message": "Share link revoked successfully."})
    return jsonify({"error": "Token not found"}), 404
