import json
import hashlib
from datetime import datetime
from copy import deepcopy

class LedgerBlock:
    def __init__(self, index: int, timestamp_iso: str, action_type: str, certificate_ref: str, payload_hash: str, prev_hash: str, block_hash: str = None, nonce: int = 0):
        self.index = index
        self.timestamp_iso = timestamp_iso
        self.action_type = action_type
        self.certificate_ref = certificate_ref or ""
        self.payload_hash = payload_hash
        self.prev_hash = prev_hash
        self.nonce = nonce
        self.block_hash = block_hash or self.calculate_hash()

    def to_canonical_dict(self) -> dict:
        return {
            "action_type": self.action_type,
            "certificate_ref": self.certificate_ref,
            "index": self.index,
            "nonce": self.nonce,
            "payload_hash": self.payload_hash,
            "prev_hash": self.prev_hash,
            "timestamp_iso": self.timestamp_iso
        }

    def calculate_hash(self) -> str:
        canonical_json = json.dumps(self.to_canonical_dict(), sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

def create_genesis_block() -> LedgerBlock:
    """Create the hardcoded Genesis block (Index 0)."""
    return LedgerBlock(
        index=0,
        timestamp_iso="2026-01-01T00:00:00Z",
        action_type="GENESIS",
        certificate_ref="SYSTEM_GENESIS",
        payload_hash=hashlib.sha256(b"CERTICHAIN_NEXUS_GENESIS_SEED_2026").hexdigest(),
        prev_hash="0" * 64,
        nonce=0
    )

def calculate_block_hash(index: int, timestamp_iso: str, action_type: str, certificate_ref: str, payload_hash: str, prev_hash: str, nonce: int = 0) -> str:
    block = LedgerBlock(index, timestamp_iso, action_type, certificate_ref, payload_hash, prev_hash, nonce=nonce)
    return block.calculate_hash()

def validate_chain_integrity(blocks_list: list) -> tuple[bool, int | None, str | None]:
    """
    Validate sequence of blocks.
    Returns: (is_valid: bool, failing_block_index: int | None, reason: str | None)
    """
    if not blocks_list:
        return True, None, "Empty chain"
    
    # Check Genesis block
    genesis = blocks_list[0]
    if genesis.index != 0:
        return False, 0, "Genesis block index is not 0"
    
    calculated_gen_hash = genesis.calculate_hash()
    if genesis.block_hash.lower() != calculated_gen_hash.lower():
        return False, 0, f"Genesis block hash invalid: stored={genesis.block_hash}, calculated={calculated_gen_hash}"
    
    # Check subsequent blocks
    for i in range(1, len(blocks_list)):
        prev_b = blocks_list[i - 1]
        curr_b = blocks_list[i]
        
        if curr_b.index != prev_b.index + 1:
            return False, curr_b.index, f"Block index discontinuity: expected {prev_b.index + 1}, got {curr_b.index}"
            
        if curr_b.prev_hash.lower() != prev_b.block_hash.lower():
            return False, curr_b.index, f"Previous hash mismatch at block #{curr_b.index}: expected {prev_b.block_hash}, got {curr_b.prev_hash}"
            
        calc_hash = curr_b.calculate_hash()
        if curr_b.block_hash.lower() != calc_hash.lower():
            return False, curr_b.index, f"Block contents altered at block #{curr_b.index}: stored={curr_b.block_hash}, calculated={calc_hash}"

    return True, None, "Ledger integrity verified successfully"

def simulate_chain_tamper(blocks_list: list, block_index_to_tamper: int, new_payload_hash: str = "tampered_payload_hash_1234567890abcdef") -> dict:
    """
    Perform tamper simulation on an isolated IN-MEMORY copy of blocks.
    Never alters authoritative ledger/database.
    Returns dictionary with initial validation state, tampered state, and error detail.
    """
    copied_blocks = deepcopy(blocks_list)
    if block_index_to_tamper < 0 or block_index_to_tamper >= len(copied_blocks):
        return {"error": "Invalid block index for tamper simulation"}
    
    target_block = copied_blocks[block_index_to_tamper]
    original_hash = target_block.block_hash
    original_payload = target_block.payload_hash
    
    # Modify payload_hash WITHOUT recalculating block_hash (simulating silent data alteration)
    target_block.payload_hash = new_payload_hash
    
    is_valid, fail_index, reason = validate_chain_integrity(copied_blocks)
    
    return {
        "tampered_block_index": block_index_to_tamper,
        "original_payload_hash": original_payload,
        "tampered_payload_hash": new_payload_hash,
        "original_block_hash": original_hash,
        "calculated_block_hash": target_block.calculate_hash(),
        "is_valid": is_valid,
        "failing_block_index": fail_index,
        "reason": reason
    }
