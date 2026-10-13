import json
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from models.schema import db, Block, Checkpoint
from blockchain.ledger import LedgerBlock, validate_chain_integrity, simulate_chain_tamper
from services.checkpoint_service import verify_external_checkpoint, export_checkpoint_json
from routes.auth import get_current_user

ledger_bp = Blueprint('ledger', __name__)

@ledger_bp.route('/ledger')
def explorer():
    user = get_current_user()
    blocks_db = Block.query.order_by(Block.index.asc()).all()
    checkpoints = Checkpoint.query.order_by(Checkpoint.created_at.desc()).all()
    
    # Reconstruct LedgerBlock objects for integrity check
    ledger_blocks = [
        LedgerBlock(
            index=b.index,
            timestamp_iso=b.timestamp_iso,
            action_type=b.action_type,
            certificate_ref=b.certificate_ref,
            payload_hash=b.payload_hash,
            prev_hash=b.prev_hash,
            block_hash=b.block_hash,
            nonce=b.nonce
        ) for b in blocks_db
    ]
    
    is_valid, failing_index, reason = validate_chain_integrity(ledger_blocks)
    
    return render_template(
        'ledger_explorer.html',
        user=user,
        blocks=blocks_db,
        checkpoints=checkpoints,
        chain_status={
            "is_valid": is_valid,
            "failing_index": failing_index,
            "reason": reason,
            "total_blocks": len(blocks_db)
        }
    )

@ledger_bp.route('/api/ledger/validate', methods=['GET', 'POST'])
def api_validate_ledger():
    blocks_db = Block.query.order_by(Block.index.asc()).all()
    ledger_blocks = [
        LedgerBlock(
            index=b.index,
            timestamp_iso=b.timestamp_iso,
            action_type=b.action_type,
            certificate_ref=b.certificate_ref,
            payload_hash=b.payload_hash,
            prev_hash=b.prev_hash,
            block_hash=b.block_hash,
            nonce=b.nonce
        ) for b in blocks_db
    ]
    is_valid, failing_index, reason = validate_chain_integrity(ledger_blocks)
    return jsonify({
        "is_valid": is_valid,
        "failing_index": failing_index,
        "reason": reason,
        "total_blocks": len(blocks_db)
    })

@ledger_bp.route('/api/ledger/tamper-demo', methods=['POST'])
def tamper_demo():
    """Execute tamper simulation on disposable in-memory copy of ledger."""
    data = request.get_json() or {}
    block_index = int(data.get('block_index', 1))
    
    blocks_db = Block.query.order_by(Block.index.asc()).all()
    ledger_blocks = [
        LedgerBlock(
            index=b.index,
            timestamp_iso=b.timestamp_iso,
            action_type=b.action_type,
            certificate_ref=b.certificate_ref,
            payload_hash=b.payload_hash,
            prev_hash=b.prev_hash,
            block_hash=b.block_hash,
            nonce=b.nonce
        ) for b in blocks_db
    ]
    
    if not ledger_blocks:
        return jsonify({"error": "Ledger is empty"}), 400
        
    result = simulate_chain_tamper(ledger_blocks, block_index)
    return jsonify(result)

@ledger_bp.route('/ledger/verify-checkpoint', methods=['POST'])
def verify_checkpoint():
    cp_json = None
    if request.is_json:
        cp_json = request.get_json()
    elif 'checkpoint_file' in request.files and request.files['checkpoint_file'].filename:
        try:
            cp_json = json.load(request.files['checkpoint_file'].stream)
        except Exception as e:
            flash(f"Invalid JSON file format: {str(e)}", "danger")
            return redirect(url_for('ledger.explorer'))
    elif 'checkpoint_text' in request.form and request.form['checkpoint_text'].strip():
        try:
            cp_json = json.loads(request.form['checkpoint_text'].strip())
        except Exception as e:
            flash(f"Invalid JSON text format: {str(e)}", "danger")
            return redirect(url_for('ledger.explorer'))

    if not cp_json:
        flash("Please provide checkpoint JSON file or text.", "warning")
        return redirect(url_for('ledger.explorer'))
        
    res = verify_external_checkpoint(cp_json)
    if res["valid"]:
        flash(f"Checkpoint Verified! {res['reason']}", "success")
    else:
        flash(f"Checkpoint Verification Failed! {res['reason']}", "danger")
        
    return redirect(url_for('ledger.explorer'))
