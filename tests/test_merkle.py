import pytest
from blockchain.merkle import MerkleTree, verify_merkle_proof

def test_merkle_tree_and_proof():
    hashes = [
        "1" * 64,
        "2" * 64,
        "3" * 64,
        "4" * 64
    ]
    tree = MerkleTree(hashes)
    root = tree.get_root()
    assert len(root) == 64
    
    # Proof for element 2
    proof = tree.get_proof(hashes[1])
    assert len(proof) > 0
    
    # Valid proof check
    assert verify_merkle_proof(hashes[1], proof, root) is True
    
    # Invalid proof check (tampered hash)
    assert verify_merkle_proof("f" * 64, proof, root) is False
