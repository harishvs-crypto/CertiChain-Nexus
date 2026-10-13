import pytest
import os
import tempfile
from flask import Flask
from config import Config
from models.schema import db, User, Issuer
from services.issuer_service import register_institution, approve_institution
from services.signing_service import generate_issuer_keypair
from werkzeug.security import generate_password_hash

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key-32bytes-min-length-string!"
    PLATFORM_SIGNING_KEY = "test-platform-signing-key-secret"

@pytest.fixture
def app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(TestConfig)
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
        # Seed test admin & test issuer institution
        admin = User(
            email="admin@certichain.nexus",
            password_hash=generate_password_hash("AdminPass123!"),
            role="ADMIN",
            full_name="Super Admin"
        )
        db.session.add(admin)
        db.session.commit()
        
        inst = register_institution("Oxford Institute of Technology", "OIT")
        approve_institution(inst.id, admin.id)
        
        issuer_user = User(
            email="issuer@oit.edu",
            password_hash=generate_password_hash("IssuerPass123!"),
            role="ISSUER",
            institution_id=inst.id,
            full_name="Dr. Oxford Issuer"
        )
        student_user = User(
            email="student@oit.edu",
            password_hash=generate_password_hash("StudentPass123!"),
            role="STUDENT",
            institution_id=inst.id,
            full_name="Alice Student"
        )
        db.session.add(issuer_user)
        db.session.add(student_user)
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
