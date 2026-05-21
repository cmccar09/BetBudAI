#!/usr/bin/env python3
"""
Generate Betfair SSL Certificate using Python cryptography library
"""

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from datetime import datetime, timedelta
import os

# Generate private key
print("Generating RSA private key (2048 bits)...")
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

# Generate certificate
print("Generating self-signed certificate...")
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME, "cmccar02"),
])

cert = x509.CertificateBuilder().subject_name(
    subject
).issuer_name(
    issuer
).public_key(
    private_key.public_key()
).serial_number(
    x509.random_serial_number()
).not_valid_before(
    datetime.utcnow()
).not_valid_after(
    datetime.utcnow() + timedelta(days=365)
).sign(private_key, hashes.SHA256())

# Write private key to file
key_file = "betfair-client.key"
with open(key_file, "wb") as f:
    f.write(private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ))
print(f"✓ Private key saved to: {key_file}")

# Write certificate to file
cert_file = "betfair-client.crt"
with open(cert_file, "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))
print(f"✓ Certificate saved to: {cert_file}")

print("\n" + "=" * 70)
print("Certificate generated successfully!")
print("=" * 70)
print("\nNext steps:")
print("1. Upload betfair-client.crt to your Betfair account:")
print("   https://myaccount.betfair.com/accountdetails/mysecurity?showAPI=1")
print("\n2. Click 'Edit' next to 'API Certificates'")
print("3. Upload the betfair-client.crt file")
print("4. Save changes")
print("\n5. Wait a few minutes for Betfair to activate the certificate")
print("6. Run: .\\generate_todays_picks.ps1")
print("=" * 70)
