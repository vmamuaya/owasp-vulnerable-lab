#!/usr/bin/env python3
"""
Generate a JWKS (JSON Web Key Set) with RSA private key for crAPI identity service.

The crAPI identity service needs a JWKS containing BOTH public and private key
parameters for JWT signing. A JWKS with only public keys (n, e) will cause
"Key argument cannot be null" on login because rsaKey.toKeyPair() returns null.

Usage:
    python3 generate_jwks.py

Output:
    Prints base64-encoded JWKS JSON to stdout.
    Update the crapi-identity systemd service:
    Environment=JWKS=<base64-string-here>

Requires: Python cryptography library (pip install cryptography)
"""
import json, base64
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

def int_to_b64url(n):
    """Convert integer to base64url-encoded bytes (no padding)."""
    byte_len = (n.bit_length() + 7) // 8
    data = n.to_bytes(byte_len, 'big')
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

def generate_jwks():
    """Generate RSA 2048 key pair as base64-encoded JWKS with private key."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    pn = private_key.private_numbers()
    pub = pn.public_numbers

    jwk = {
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "kid": "crapi-key-1",
        "n": int_to_b64url(pub.n),
        "e": int_to_b64url(pub.e),
        "d": int_to_b64url(pn.d),
        "p": int_to_b64url(pn.p),
        "q": int_to_b64url(pn.q),
        "dp": int_to_b64url(pn.dmp1),
        "dq": int_to_b64url(pn.dmq1),
        "qi": int_to_b64url(pn.iqmp),
    }

    jwks = {"keys": [jwk]}
    jwks_json = json.dumps(jwks)
    jwks_b64 = base64.b64encode(jwks_json.encode()).decode()

    return jwks_b64

if __name__ == "__main__":
    jwks_b64 = generate_jwks()
    print(jwks_b64)
    print(f"\n# Length: {len(jwks_b64)} chars")
    print("# Update crapi-identity.service:")
    print(f"#   Environment=JWKS={jwks_b64}")
    print("# Then: sudo systemctl daemon-reload && sudo systemctl restart crapi-identity")