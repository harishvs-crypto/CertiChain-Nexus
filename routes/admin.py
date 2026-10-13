from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.schema import db, User, Issuer, Certificate, Block, Checkpoint, AuditLog
from routes.auth import login_required, role_required, get_current_user
from services.issuer_service import register_institution, approve_institution, suspend_institution, reinstate_institution
from services.checkpoint_service import create_merkle_checkpoint, export_checkpoint_json

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@role_required('ADMIN')
def dashboard():
    user = get_current_user()
    
    total_issuers = Issuer.query.count()
    trusted_issuers = Issuer.query.filter_by(status='TRUSTED').count()
    pending_issuers = Issuer.query.filter_by(status='PENDING').count()
    
    total_certificates = Certificate.query.count()
    active_certificates = Certificate.query.filter_by(status='ACTIVE').count()
    revoked_certificates = Certificate.query.filter_by(status='REVOKED').count()
    superseded_certificates = Certificate.query.filter_by(status='SUPERSEDED').count()
    
    total_blocks = Block.query.count()
    total_checkpoints = Checkpoint.query.count()
    
    recent_issuers = Issuer.query.order_by(Issuer.created_at.desc()).limit(5).all()
    recent_certs = Certificate.query.order_by(Certificate.created_at.desc()).limit(5).all()
    recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(8).all()
    
    return render_template(
        'admin_dashboard.html',
        user=user,
        stats={
            "total_issuers": total_issuers,
            "trusted_issuers": trusted_issuers,
            "pending_issuers": pending_issuers,
            "total_certificates": total_certificates,
            "active_certificates": active_certificates,
            "revoked_certificates": revoked_certificates,
            "superseded_certificates": superseded_certificates,
            "total_blocks": total_blocks,
            "total_checkpoints": total_checkpoints
        },
        recent_issuers=recent_issuers,
        recent_certs=recent_certs,
        recent_logs=recent_logs
    )

@admin_bp.route('/issuers/register', methods=['POST'])
@login_required
@role_required('ADMIN')
def register_issuer():
    name = request.form.get('name', '').strip()
    code = request.form.get('code', '').strip().upper()
    
    if not name or not code:
        flash("Institution name and code are required.", "danger")
        return redirect(url_for('admin.dashboard'))
        
    try:
        issuer = register_institution(name, code)
        flash(f"Institution '{name}' ({code}) registered successfully in PENDING status.", "success")
    except ValueError as e:
        flash(str(e), "danger")
        
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/issuers/<int:issuer_id>/approve', methods=['POST'])
@login_required
@role_required('ADMIN')
def approve_issuer(issuer_id):
    user = get_current_user()
    try:
        issuer = approve_institution(issuer_id, user.id)
        flash(f"Institution '{issuer.name}' approved! Ed25519 keypair generated (Key ID: {issuer.key_id}).", "success")
    except Exception as e:
        flash(f"Approval failed: {str(e)}", "danger")
        
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/issuers/<int:issuer_id>/suspend', methods=['POST'])
@login_required
@role_required('ADMIN')
def suspend_issuer(issuer_id):
    user = get_current_user()
    try:
        issuer = suspend_institution(issuer_id, user.id)
        flash(f"Institution '{issuer.name}' has been SUSPENDED.", "warning")
    except Exception as e:
        flash(f"Suspension failed: {str(e)}", "danger")
        
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/issuers/<int:issuer_id>/reinstate', methods=['POST'])
@login_required
@role_required('ADMIN')
def reinstate_issuer(issuer_id):
    user = get_current_user()
    try:
        issuer = reinstate_institution(issuer_id, user.id)
        flash(f"Institution '{issuer.name}' has been REINSTATED.", "success")
    except Exception as e:
        flash(f"Reinstatement failed: {str(e)}", "danger")
        
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/checkpoints', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN')
def checkpoints():
    if request.method == 'POST':
        try:
            cp, block = create_merkle_checkpoint()
            flash(f"Merkle Checkpoint #{cp.id} created! Merkle Root: {cp.merkle_root[:16]}...", "success")
        except Exception as e:
            flash(f"Checkpoint creation failed: {str(e)}", "danger")
        return redirect(url_for('admin.checkpoints'))
        
    all_checkpoints = Checkpoint.query.order_by(Checkpoint.created_at.desc()).all()
    return render_template('checkpoints.html', checkpoints=all_checkpoints)
