import os
from flask import Flask, render_template
from config import Config
from models.schema import db
from routes import (
    auth_bp,
    admin_bp,
    certificate_bp,
    verify_bp,
    capsule_bp,
    sharing_bp,
    ledger_bp,
    analytics_bp
)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure required instance and certificate directories exist
    os.makedirs(app.config.get('INSTANCE_PATH', 'instance'), exist_ok=True)
    os.makedirs(app.config.get('CERTIFICATES_DIR', 'certificates'), exist_ok=True)
    os.makedirs(app.config.get('KEYS_DIR', 'instance/keys'), exist_ok=True)

    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(certificate_bp)
    app.register_blueprint(verify_bp)
    app.register_blueprint(capsule_bp)
    app.register_blueprint(sharing_bp)
    app.register_blueprint(ledger_bp)
    app.register_blueprint(analytics_bp)

    # Security Headers Middleware
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    # Global Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error.html', error_code=404, message="The requested resource or page was not found."), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('error.html', error_code=500, message="An internal server error occurred."), 500

    # Register CLI seed command
    register_commands(app)

    return app

def register_commands(app):
    @app.cli.command("init-db")
    def init_db():
        """Initialize database tables and create Genesis block."""
        with app.app_context():
            db.create_all()
            from blockchain.ledger import create_genesis_block
            from models.schema import Block
            if not Block.query.filter_by(index=0).first():
                gen = create_genesis_block()
                gen_block = Block(
                    index=gen.index,
                    timestamp_iso=gen.timestamp_iso,
                    action_type=gen.action_type,
                    certificate_ref=gen.certificate_ref,
                    payload_hash=gen.payload_hash,
                    prev_hash=gen.prev_hash,
                    block_hash=gen.block_hash
                )
                db.session.add(gen_block)
                db.session.commit()
                print("Database initialized and Genesis Block #0 created.")
            else:
                print("Database already initialized.")

    @app.cli.command("seed-db")
    def seed_db():
        """Idempotent developer seed command."""
        from werkzeug.security import generate_password_hash
        from models.schema import User, Issuer, Certificate, Block, AuditLog, SuspiciousReport
        from services.issuer_service import register_institution, approve_institution
        from services.certificate_service import issue_certificate
        from services.revocation_service import revoke_certificate, supersede_certificate
        from services.checkpoint_service import create_merkle_checkpoint

        with app.app_context():
            db.create_all()

            # Ensure Genesis block
            if not Block.query.filter_by(index=0).first():
                from blockchain.ledger import create_genesis_block
                gen = create_genesis_block()
                db.session.add(Block(
                    index=gen.index,
                    timestamp_iso=gen.timestamp_iso,
                    action_type=gen.action_type,
                    certificate_ref=gen.certificate_ref,
                    payload_hash=gen.payload_hash,
                    prev_hash=gen.prev_hash,
                    block_hash=gen.block_hash
                ))
                db.session.commit()

            # 1. Super Admin
            admin = User.query.filter_by(email="admin@certichain.nexus").first()
            if not admin:
                admin = User(
                    email="admin@certichain.nexus",
                    password_hash=generate_password_hash("AdminPass123!"),
                    role="ADMIN",
                    full_name="Super Administrator"
                )
                db.session.add(admin)
                db.session.commit()

            # 2. Institutions
            oit = Issuer.query.filter_by(code="OIT").first()
            if not oit:
                oit = register_institution("Oxford Institute of Technology", "OIT")
                approve_institution(oit.id, admin.id)

            mit = Issuer.query.filter_by(code="MIT").first()
            if not mit:
                mit = register_institution("Metropolitan Institute of Technology", "MIT")
                approve_institution(mit.id, admin.id)

            # 3. Issuer User Accounts
            issuer_user = User.query.filter_by(email="issuer@oit.edu").first()
            if not issuer_user:
                issuer_user = User(
                    email="issuer@oit.edu",
                    password_hash=generate_password_hash("IssuerPass123!"),
                    role="ISSUER",
                    institution_id=oit.id,
                    full_name="Prof. David Turing"
                )
                db.session.add(issuer_user)
                db.session.commit()

            # 4. Student Accounts
            student_user = User.query.filter_by(email="student@oit.edu").first()
            if not student_user:
                student_user = User(
                    email="student@oit.edu",
                    password_hash=generate_password_hash("StudentPass123!"),
                    role="STUDENT",
                    institution_id=oit.id,
                    full_name="Alice Student"
                )
                db.session.add(student_user)
                db.session.commit()

            # 5. Certificates (Active, Revoked, Superseded)
            if Certificate.query.count() < 4:
                # Active Certificate 1
                c1, _, _ = issue_certificate(
                    issuer_id=oit.id,
                    student_ref="STU-2026-CS-001",
                    certificate_type="Bachelor of Science",
                    course_name="Computer Science & Cryptography",
                    issue_date="2026-05-20",
                    grade="First Class Honours",
                    student_user_id=student_user.id
                )
                
                # Active Certificate 2
                c2, _, _ = issue_certificate(
                    issuer_id=oit.id,
                    student_ref="STU-2026-AI-002",
                    certificate_type="Master of Science",
                    course_name="Artificial Intelligence & Blockchain",
                    issue_date="2026-06-15",
                    grade="Distinction",
                    student_user_id=student_user.id
                )

                # Revoked Certificate 3
                c3, _, _ = issue_certificate(
                    issuer_id=oit.id,
                    student_ref="STU-2026-DS-003",
                    certificate_type="Diploma in Data Analytics",
                    course_name="Data Science",
                    issue_date="2026-01-10",
                    grade="Pass"
                )
                revoke_certificate(c3.id, issuer_user.id, "Academic Plagiarism Confirmed by Disciplinary Board")

                # Superseded Certificate 4
                c4, _, _ = issue_certificate(
                    issuer_id=oit.id,
                    student_ref="STU-2026-SEC-004",
                    certificate_type="Bachelor of Engineering",
                    course_name="Cybersecurity Operations",
                    issue_date="2026-02-12",
                    grade="Second Class Lower"
                )
                supersede_certificate(
                    old_cert_id=c4.id,
                    actor_user_id=issuer_user.id,
                    reason="Grade re-evaluation correction following formal recheck",
                    new_grade="First Class"
                )

                # Create Merkle Checkpoint
                create_merkle_checkpoint()

            # 6. Sample Fraud Radar logs (labeled clearly as SAMPLE DATA)
            if AuditLog.query.filter_by(event_type="SAMPLE_EVENT").count() == 0:
                sample_log1 = AuditLog(
                    actor_user_id=None,
                    event_type="SAMPLE_EVENT",
                    certificate_ref="CERT-SAMPLE-TAMPERED-01",
                    outcome="TAMPERED",
                    identity_hash="demo_attacker_identity_hash_999",
                    risk_flag=True,
                    review_status="ALERT"
                )
                sample_log2 = AuditLog(
                    actor_user_id=None,
                    event_type="SAMPLE_EVENT",
                    certificate_ref="CERT-SAMPLE-PROBE-02",
                    outcome="UNRECOGNIZED",
                    identity_hash="demo_attacker_identity_hash_999",
                    risk_flag=True,
                    review_status="ALERT"
                )
                db.session.add(sample_log1)
                db.session.add(sample_log2)
                db.session.commit()

            print("Database seeded successfully with demo accounts, certificates, checkpoints, and sample data!")

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
