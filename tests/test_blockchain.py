import pytest
from datetime import datetime
from blockchain.ledger import (
    LedgerBlock,
    create_genesis_block,
    validate_chain_integrity,
    simulate_chain_tamper
)

def test_genesis_block():
    gen = create_genesis_block()
    assert gen.index == 0
    assert gen.action_type == "GENESIS"
    assert len(gen.block_hash) == 64

def test_chain_integrity():
    gen = create_genesis_block()
    b1 = LedgerBlock(
        index=1,
        timestamp_iso="2026-01-02T10:00:00Z",
        action_type="CERTIFICATE_ISSUED",
        certificate_ref="CERT-001",
        payload_hash="1" * 64,
        prev_hash=gen.block_hash
    )
    b2 = LedgerBlock(
        index=2,
        timestamp_iso="2026-01-03T10:00:00Z",
        action_type="CERTIFICATE_REVOKED",
        certificate_ref="CERT-001",
        payload_hash="2" * 64,
        prev_hash=b1.block_hash
    )
    
    chain = [gen, b1, b2]
    is_valid, failing_idx, reason = validate_chain_integrity(chain)
    assert is_valid is True
    assert failing_idx is None

def test_tamper_detection():
    gen = create_genesis_block()
    b1 = LedgerBlock(
        index=1,
        timestamp_iso="2026-01-02T10:00:00Z",
        action_type="CERTIFICATE_ISSUED",
        certificate_ref="CERT-001",
        payload_hash="1" * 64,
        prev_hash=gen.block_hash
    )
    chain = [gen, b1]
    
    tamper_result = simulate_chain_tamper(chain, block_index_to_tamper=1, new_payload_hash="f" * 64)
    assert tamper_result["is_valid"] is False
    assert tamper_result["failing_block_index"] == 1
    # Check that original chain remains untouched
    is_orig_valid, _, _ = validate_chain_integrity(chain)
    assert is_orig_valid is True
