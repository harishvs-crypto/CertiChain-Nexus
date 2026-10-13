import hashlib

def hash_pair(left_hash: str, right_hash: str) -> str:
    """Compute SHA-256 digest of concatenated pair hashes."""
    combined = (left_hash + right_hash).encode('utf-8')
    return hashlib.sha256(combined).hexdigest()

class MerkleTree:
    """SHA-256 Binary Merkle Tree implementation."""
    
    def __init__(self, leaves: list[str]):
        """
        Initialize Merkle tree with list of leaf hashes (hex strings).
        If leaves is empty, root is empty string.
        """
        self.leaves = [l.lower() for l in leaves]
        self.tree_levels = []
        if self.leaves:
            self._build_tree()

    def _build_tree(self):
        current_level = self.leaves[:]
        self.tree_levels.append(current_level)
        
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                if i + 1 < len(current_level):
                    right = current_level[i + 1]
                else:
                    right = left  # Duplicate last element if odd
                parent_hash = hash_pair(left, right)
                next_level.append(parent_hash)
            current_level = next_level
            self.tree_levels.append(current_level)

    def get_root(self) -> str:
        if not self.tree_levels:
            return ""
        return self.tree_levels[-1][0]

    def get_proof(self, leaf_hash: str) -> list[dict]:
        """
        Generate inclusion proof for a given leaf hash.
        Returns list of dicts: [{"direction": "right"/"left", "hash": "..."}]
        """
        target = leaf_hash.lower()
        if not self.leaves or target not in self.leaves:
            return []
        
        index = self.leaves.index(target)
        proof = []
        
        for level in self.tree_levels[:-1]: # Exclude root level
            is_right = (index % 2 == 1)
            sibling_index = index - 1 if is_right else index + 1
            
            if sibling_index < len(level):
                sibling_hash = level[sibling_index]
            else:
                sibling_hash = level[index] # Duplicated last node
            
            proof.append({
                "direction": "left" if is_right else "right",
                "hash": sibling_hash
            })
            
            index = index // 2 # Move to parent index
            
        return proof

def verify_merkle_proof(leaf_hash: str, proof: list[dict], root_hash: str) -> bool:
    """
    Verify Merkle inclusion proof for a given leaf hash against target root_hash.
    """
    current = leaf_hash.lower()
    for step in proof:
        sibling = step["hash"].lower()
        direction = step["direction"]
        if direction == "right":
            current = hash_pair(current, sibling)
        else:
            current = hash_pair(sibling, current)
            
    return current.lower() == root_hash.lower()
