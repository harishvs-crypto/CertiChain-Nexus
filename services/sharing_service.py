import secrets
import hashlib
import json
from datetime import datetime, timedelta
from models.schema import db, Certificate, ShareToken, Issuer

def create_restricted_share_link(
    certificate_id: str,
    permitted_fields: list[str],
    expires_in_hours: int = 72
) -> tuple[str, ShareToken]:
    """
    Create a privacy-aware restricted share link for a student certificate.
    Returns tuple: (raw_token, ShareToken_model_instance)
    """
    cert = db.session.get(Certificate, certificate_id)
    if not cert:
        raise ValueError("Certificate not found.")
    
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
    expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
    
    share_token = ShareToken(
        certificate_id=cert.id,
        token_hash=token_hash,
        permitted_fields=json.dumps(permitted_fields),
        expires_at=expires_at,
        revoked=False
    )
    
    db.session.add(share_token)
    db.session.commit()
    return raw_token, share_token

def get_shared_certificate_data(raw_token: str) -> dict:
    """
    Access shared certificate data via raw token.
    Validates token hash, expiry, and revocation, returning ONLY permitted fields.
    """
    if not raw_token:
        return {"error": "Token is required", "valid": False}
    
    token_hash = hashlib.sha256(raw_token.strip().encode('utf-8')).hexdigest()
    st = ShareToken.query.filter_by(token_hash=token_hash).first()
    
    if not st:
        return {"error": "Invalid or unrecognized share token", "valid": False}
        
    if st.revoked:
        return {"error": "This share link has been revoked by the student", "valid": False}
        
    if datetime.utcnow() > st.expires_at:
        return {"error": "This share link has expired", "valid": False}
        
    cert = db.session.get(Certificate, st.certificate_id)
    if not cert or cert.status != 'ACTIVE':
        return {"error": f"Credential is no longer active (Status: {cert.status if cert else 'NOT_FOUND'})", "valid": False}
        
    issuer = db.session.get(Issuer, cert.issuer_id)
    permitted_fields = json.loads(st.permitted_fields)
    
    # Filter permitted fields
    full_data = {
        "certificate_id": cert.id,
        "student_ref": cert.student_ref,
        "certificate_type": cert.certificate_type,
        "course_name": cert.course_name,
        "issue_date": cert.issue_date,
        "grade": cert.grade,
        "issuer_name": issuer.name if issuer else "Unknown",
        "issuer_code": issuer.code if issuer else "UNKNOWN",
        "status": cert.status,
        "version": cert.version
    }
    
    filtered_data = {k: v for k, v in full_data.items() if k in permitted_fields or k in ["certificate_id", "issuer_name", "status"]}
    
    return {
        "valid": True,
        "shared_fields": filtered_data,
        "permitted_field_names": permitted_fields,
        "expires_at": st.expires_at.isoformat() + "Z"
    }

def revoke_share_token(share_token_id: int) -> bool:
    """Revoke a share token by ID."""
    st = db.session.get(ShareToken, share_token_id)
    if st:
        st.revoked = True
        db.session.commit()
        return True
    return False
