import json
import io
from flask import Blueprint, render_template, request, jsonify, send_file, flash
from services.capsule_service import export_proof_capsule, verify_proof_capsule_data

capsule_bp = Blueprint('capsule', __name__)

@capsule_bp.route('/certificate/<cert_id>/capsule/download')
def download_capsule(cert_id):
    try:
        capsule_data = export_proof_capsule(cert_id)
        json_str = json.dumps(capsule_data, indent=2)
        buffer = io.BytesIO(json_str.encode('utf-8'))
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"proof_capsule_{cert_id}.json",
            mimetype="application/json"
        )
    except Exception as e:
        flash(f"Failed to generate Proof Capsule: {str(e)}", "danger")
        return jsonify({"error": str(e)}), 400

@capsule_bp.route('/capsule/verify', methods=['GET'])
def capsule_verify_page():
    return render_template('capsule_verify.html')

@capsule_bp.route('/api/verify/capsule', methods=['POST'])
def api_verify_capsule():
    capsule_json = None
    if request.is_json:
        capsule_json = request.get_json()
    elif 'capsule_file' in request.files:
        file = request.files['capsule_file']
        if file.filename == '':
            return jsonify({"valid": False, "reason": "No file selected"}), 400
        try:
            capsule_json = json.load(file.stream)
        except Exception as e:
            return jsonify({"valid": False, "reason": f"Invalid JSON format: {str(e)}"}), 400
            
    if not capsule_json:
        return jsonify({"valid": False, "reason": "No capsule JSON provided"}), 400
        
    is_valid, reason = verify_proof_capsule_data(capsule_json)
    return jsonify({
        "status": "VERIFIED" if is_valid else "INVALID_PROOF",
        "valid": is_valid,
        "reason": reason,
        "certificate_id": capsule_json.get("certificate", {}).get("certificate_id")
    })
