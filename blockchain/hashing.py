import json
import hashlib
import hmac
import unicodedata

def normalize_text(text: str) -> str:
    """Normalize text string using Unicode NFC and strip whitespace."""
    if text is None:
        return ""
    text = str(text).strip()
    return unicodedata.normalize('NFC', text)

def build_canonical_payload(cert_dict: dict) -> dict:
    """
    Construct canonical dictionary from protected certificate fields.
    Fields included:
      - certificate_id: str (normalized, upper)
      - issuer_id: str/int (normalized string)
      - student_ref: str (normalized)
      - certificate_type: str (normalized)
      - course_name: str (normalized)
      - issue_date: str (YYYY-MM-DD)
      - grade: str (normalized)
      - salt: str (64 hex characters)
    """
    return {
        "certificate_id": normalize_text(cert_dict.get("certificate_id", "")).upper(),
        "course_name": normalize_text(cert_dict.get("course_name", "")),
        "certificate_type": normalize_text(cert_dict.get("certificate_type", "")),
        "grade": normalize_text(cert_dict.get("grade", "")),
        "issue_date": normalize_text(cert_dict.get("issue_date", "")),
        "issuer_id": normalize_text(cert_dict.get("issuer_id", "")),
        "salt": normalize_text(cert_dict.get("salt", "")),
        "student_ref": normalize_text(cert_dict.get("student_ref", ""))
    }

def serialize_canonical_payload(canonical_dict: dict) -> bytes:
    """Serialize canonical payload dictionary to UTF-8 encoded sorted JSON with no extra whitespace."""
    json_str = json.dumps(canonical_dict, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return json_str.encode('utf-8')

def compute_content_hash(cert_dict: dict) -> str:
    """Compute 64-character hex SHA-256 digest over canonical payload."""
    canonical = build_canonical_payload(cert_dict)
    payload_bytes = serialize_canonical_payload(canonical)
    return hashlib.sha256(payload_bytes).hexdigest()

def verify_content_hash(cert_dict: dict, expected_hash: str) -> bool:
    """Constant-time verification of content hash."""
    calculated_hash = compute_content_hash(cert_dict)
    return hmac.compare_digest(calculated_hash.lower(), expected_hash.lower())
