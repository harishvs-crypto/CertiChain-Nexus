from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.certificate import certificate_bp
from routes.verify import verify_bp
from routes.capsule_routes import capsule_bp
from routes.sharing import sharing_bp
from routes.ledger import ledger_bp
from routes.analytics import analytics_bp

__all__ = [
    'auth_bp',
    'admin_bp',
    'certificate_bp',
    'verify_bp',
    'capsule_bp',
    'sharing_bp',
    'ledger_bp',
    'analytics_bp'
]
