from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='STUDENT') # ADMIN, ISSUER, STUDENT
    institution_id = db.Column(db.Integer, db.ForeignKey('issuers.id'), nullable=True)
    full_name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    institution = db.relationship('Issuer', backref=db.backref('users', lazy=True))
    certificates = db.relationship('Certificate', foreign_keys='Certificate.student_user_id', backref='student_user', lazy=True)

class Issuer(db.Model):
    __tablename__ = 'issuers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='PENDING') # PENDING, TRUSTED, SUSPENDED
    public_key_pem = db.Column(db.Text, nullable=True)
    key_id = db.Column(db.String(64), nullable=True)
    encrypted_private_key = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    certificates = db.relationship('Certificate', foreign_keys='Certificate.issuer_id', backref='issuer', lazy=True)

class Certificate(db.Model):
    __tablename__ = 'certificates'
    
    id = db.Column(db.String(64), primary_key=True)
    issuer_id = db.Column(db.Integer, db.ForeignKey('issuers.id'), nullable=False)
    student_ref = db.Column(db.String(120), nullable=False)
    student_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    certificate_type = db.Column(db.String(100), nullable=False)
    course_name = db.Column(db.String(150), nullable=False)
    issue_date = db.Column(db.String(10), nullable=False) # YYYY-MM-DD
    grade = db.Column(db.String(50), nullable=True)
    salt = db.Column(db.String(64), nullable=False)
    content_hash = db.Column(db.String(64), nullable=False)
    issuer_signature = db.Column(db.Text, nullable=False)
    signature_key_id = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='ACTIVE') # ACTIVE, REVOKED, SUPERSEDED
    revocation_reason = db.Column(db.Text, nullable=True)
    revoked_at = db.Column(db.DateTime, nullable=True)
    revoked_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    superseded_by_id = db.Column(db.String(64), db.ForeignKey('certificates.id'), nullable=True)
    version = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    share_tokens = db.relationship('ShareToken', backref='certificate', lazy=True, cascade="all, delete-orphan")

class Block(db.Model):
    __tablename__ = 'blocks'
    
    index = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    timestamp_iso = db.Column(db.String(50), nullable=False, default="2026-01-01T00:00:00Z")
    action_type = db.Column(db.String(50), nullable=False)
    certificate_ref = db.Column(db.String(64), nullable=True)
    payload_hash = db.Column(db.String(64), nullable=False)
    prev_hash = db.Column(db.String(64), nullable=False)
    block_hash = db.Column(db.String(64), nullable=False)
    nonce = db.Column(db.Integer, default=0)

class Checkpoint(db.Model):
    __tablename__ = 'checkpoints'
    
    id = db.Column(db.Integer, primary_key=True)
    merkle_root = db.Column(db.String(64), nullable=False)
    from_block = db.Column(db.Integer, nullable=False)
    to_block = db.Column(db.Integer, nullable=False)
    block_count = db.Column(db.Integer, nullable=False)
    signature = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ShareToken(db.Model):
    __tablename__ = 'share_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    certificate_id = db.Column(db.String(64), db.ForeignKey('certificates.id'), nullable=False)
    token_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    permitted_fields = db.Column(db.Text, nullable=False) # JSON array of field names
    expires_at = db.Column(db.DateTime, nullable=False)
    revoked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    event_type = db.Column(db.String(50), nullable=False)
    certificate_ref = db.Column(db.String(64), nullable=True)
    outcome = db.Column(db.String(50), nullable=False)
    identity_hash = db.Column(db.String(64), nullable=True)
    risk_flag = db.Column(db.Boolean, default=False)
    review_status = db.Column(db.String(20), default='OBSERVED') # OBSERVED, ALERT, REVIEWED
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class SuspiciousReport(db.Model):
    __tablename__ = 'suspicious_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    certificate_ref = db.Column(db.String(64), nullable=False)
    reporter_contact = db.Column(db.String(120), nullable=True)
    reason = db.Column(db.Text, nullable=False)
    review_status = db.Column(db.String(20), default='PENDING') # PENDING, DISMISSED, CONFIRMED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
