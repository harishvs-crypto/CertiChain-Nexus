import pytest
from services.signing_service import (
    generate_issuer_keypair,
    sign_content_hash,
    verify_signature
)

def test_ed25519_key_generation_sign_and_verify():
    pub_pem, enc_priv, key_id = generate_issuer_keypair()
    assert "BEGIN PUBLIC KEY" in pub_pem
    assert len(enc_priv) > 0
    assert len(key_id) == 16
    
    content_hash = "a" * 64
    sig_b64 = sign_content_hash(enc_priv, content_hash)
    assert len(sig_b64) > 0
    
    # Valid signature verify
    assert verify_signature(pub_pem, content_hash, sig_b64) is True
    
    # Invalid signature verify (modified content hash)
    assert verify_signature(pub_pem, "b" * 64, sig_b64) is False
    
    # Invalid signature verify (modified signature)
    bad_sig = sig_b64[:-4] + "AAAA"
    assert verify_signature(pub_pem, content_hash, bad_sig) is False
