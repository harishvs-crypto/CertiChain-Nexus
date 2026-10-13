from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file, current_app
from models.schema import db, Certificate, Issuer, User, Block, AuditLog, ShareToken
from routes.auth import login_required, role_required, get_current_user
from services.certificate_service import issue_certificate, generate_qr_code
from services.revocation_service import revoke_certificate, supersede_certificate
from services.capsule_service import export_proof_capsule

certificate_bp = Blueprint('certificate', __name__)

@certificate_bp.route('/issuer/dashboard')
@login_required
@role_required('ISSUER')
def issuer_dashboard():
    user = get_current_user()
    if not user.institution_id:
        flash("No institution associated with this issuer account.", "danger")
        return redirect(url_for('auth.login'))
        
    issuer = db.session.get(Issuer, user.institution_id)
    certificates = Certificate.query.filter_by(issuer_id=issuer.id).order_by(Certificate.created_at.desc()).all()
    
    total_issued = len(certificates)
    active_count = sum(1 for c in certificates if c.status == 'ACTIVE')
    revoked_count = sum(1 for c in certificates if c.status == 'REVOKED')
    superseded_count = sum(1 for c in certificates if c.status == 'SUPERSEDED')
    
    return render_template(
        'issuer_dashboard.html',
        user=user,
        issuer=issuer,
        certificates=certificates,
        stats={
            "total": total_issued,
            "active": active_count,
            "revoked": revoked_count,
            "superseded": superseded_count
        }
    )

@certificate_bp.route('/issuer/issue', methods=['GET', 'POST'])
@login_required
@role_required('ISSUER')
def issue():
    user = get_current_user()
    issuer = db.session.get(Issuer, user.institution_id) if user.institution_id else None
    
    if not issuer or issuer.status != 'TRUSTED':
        flash("Your institution is not approved or is suspended. Certificate issuance is disabled.", "danger")
        return redirect(url_for('certificate.issuer_dashboard'))
        
    if request.method == 'POST':
        student_ref = request.form.get('student_ref', '').strip()
        student_email = request.form.get('student_email', '').strip()
        cert_type = request.form.get('certificate_type', '').strip()
        course_name = request.form.get('course_name', '').strip()
        issue_date = request.form.get('issue_date', '').strip()
        grade = request.form.get('grade', '').strip()
        
        if not student_ref or not cert_type or not course_name or not issue_date:
            flash("Please fill in all required fields.", "danger")
            return render_template('issue_certificate.html', issuer=issuer)
            
        student_user = User.query.filter_by(email=student_email).first() if student_email else None
        student_user_id = student_user.id if student_user else None
        
        try:
            base_url = request.url_root
            cert, block, qr_b64 = issue_certificate(
                issuer_id=issuer.id,
                student_ref=student_ref,
                certificate_type=cert_type,
                course_name=course_name,
                issue_date=issue_date,
                grade=grade,
                student_user_id=student_user_id,
                base_url=base_url
            )
            flash(f"Certificate {cert.id} issued successfully and recorded on Ledger Block #{block.index}!", "success")
            return redirect(url_for('certificate.preview', cert_id=cert.id))
        except Exception as e:
            flash(f"Issuance failed: {str(e)}", "danger")
            
    return render_template('issue_certificate.html', issuer=issuer)

@certificate_bp.route('/student/portal')
@login_required
@role_required('STUDENT')
def student_portal():
    user = get_current_user()
    certificates = Certificate.query.filter(
        (Certificate.student_user_id == user.id) | (Certificate.student_ref == user.email)
    ).order_by(Certificate.created_at.desc()).all()
    
    return render_template('student_portal.html', user=user, certificates=certificates)

@certificate_bp.route('/certificate/<cert_id>/preview')
def preview(cert_id):
    cert = db.session.get(Certificate, cert_id)
    if not cert:
        flash("Certificate not found.", "danger")
        return redirect(url_for('verify.landing'))
        
    issuer = db.session.get(Issuer, cert.issuer_id)
    verify_url = request.url_root.rstrip('/') + url_for('verify.verify_certificate_page', certificate_id=cert.id)
    qr_bytes, qr_b64 = generate_qr_code(verify_url)
    
    blocks = Block.query.filter_by(certificate_ref=cert.id).all()
    audits = AuditLog.query.filter_by(certificate_ref=cert.id).order_by(AuditLog.timestamp.asc()).all()
    
    return render_template(
        'certificate_preview.html',
        cert=cert,
        issuer=issuer,
        qr_b64=qr_b64,
        verify_url=verify_url,
        blocks=blocks,
        audits=audits
    )

@certificate_bp.route('/certificate/<cert_id>/revoke', methods=['POST'])
@login_required
@role_required('ISSUER', 'ADMIN')
def revoke(cert_id):
    user = get_current_user()
    reason = request.form.get('reason', 'Administrative Revocation').strip()
    
    cert = db.session.get(Certificate, cert_id)
    if not cert:
        flash("Certificate not found.", "danger")
        return redirect(url_for('certificate.issuer_dashboard'))
        
    if user.role == 'ISSUER' and cert.issuer_id != user.institution_id:
        flash("Permission denied. You can only revoke certificates for your institution.", "danger")
        return redirect(url_for('certificate.issuer_dashboard'))
        
    try:
        revoke_certificate(cert.id, user.id, reason)
        flash(f"Certificate {cert.id} has been REVOKED.", "warning")
    except Exception as e:
        flash(f"Revocation failed: {str(e)}", "danger")
        
    return redirect(url_for('certificate.preview', cert_id=cert.id))

@certificate_bp.route('/certificate/<cert_id>/supersede', methods=['POST'])
@login_required
@role_required('ISSUER', 'ADMIN')
def supersede(cert_id):
    user = get_current_user()
    reason = request.form.get('reason', 'Version Correction').strip()
    new_grade = request.form.get('grade', '').strip()
    new_course = request.form.get('course_name', '').strip()
    
    cert = db.session.get(Certificate, cert_id)
    if not cert:
        flash("Certificate not found.", "danger")
        return redirect(url_for('certificate.issuer_dashboard'))
        
    if user.role == 'ISSUER' and cert.issuer_id != user.institution_id:
        flash("Permission denied.", "danger")
        return redirect(url_for('certificate.issuer_dashboard'))
        
    try:
        base_url = request.url_root
        old_cert, new_cert = supersede_certificate(
            old_cert_id=cert.id,
            actor_user_id=user.id,
            reason=reason,
            new_course_name=new_course or None,
            new_grade=new_grade or None,
            base_url=base_url
        )
        flash(f"Certificate {cert.id} superseded by new version {new_cert.id}!", "success")
        return redirect(url_for('certificate.preview', cert_id=new_cert.id))
    except Exception as e:
        flash(f"Supersession failed: {str(e)}", "danger")
        return redirect(url_for('certificate.preview', cert_id=cert.id))
