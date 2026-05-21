#!/usr/bin/env python3
"""
Generate SSL certificate for Betfair API authentication
Uses Python cryptography library (no OpenSSL required)
"""
import sys
import os
from datetime import datetime, timedelta

try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend
except ImportError:
    print("❌ cryptography library not installed")
    print("Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])
    print("[OK] Installed. Please run this script again.")
    sys.exit(0)

def generate_certificate():
    """Generate self-signed SSL certificate for Betfair"""
    print("="*60)
    print("Generate Betfair SSL Certificate")
    print("="*60)
    print()
    
    # Get certificate details
    print("Certificate Information:")
    print("(Press Enter to use defaults)")
    print()
    
    country = input("Country Code [IE]: ").strip() or "IE"
    state = input("State/Province [Dublin]: ").strip() or "Dublin"
    city = input("City [Dublin]: ").strip() or "Dublin"
    org = input("Organization [Betting Bot]: ").strip() or "Betting Bot"
    common_name = input("Common Name [Betfair Client]: ").strip() or "Betfair Client"
    email = input("Email [your@email.com]: ").strip() or "your@email.com"
    
    print()
    print("Generating certificate...")
    
    # Generate private key
    print("  1. Generating private key (2048-bit RSA)...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Build certificate subject
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, country),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state),
        x509.NameAttribute(NameOID.LOCALITY_NAME, city),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, org),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        x509.NameAttribute(NameOID.EMAIL_ADDRESS, email),
    ])
    
    # Generate certificate
    print("  2. Generating self-signed certificate (3 years validity)...")
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
        datetime.utcnow() + timedelta(days=1095)  # 3 years
    ).sign(private_key, hashes.SHA256(), default_backend())
    
    # Write private key
    key_file = "betfair-client.key"
    with open(key_file, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    print(f"  [OK] Private key saved: {key_file}")
    
    # Write certificate
    cert_file = "betfair-client.crt"
    with open(cert_file, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    print(f"  [OK] Certificate saved: {cert_file}")
    
    print()
    print("="*60)
    print("[OK] Certificate Generation Complete!")
    print("="*60)
    print()
    
    print("Files created:")
    print(f"  • {key_file} (Private Key - Keep Secure!)")
    print(f"  • {cert_file} (Self-Signed Certificate)")
    print()
    
    print("NEXT STEPS:")
    print()
    print("1. Upload Certificate to Betfair:")
    print("   a. Go to: https://developer.betfair.com/")
    print("   b. Login with your account")
    print("   c. Navigate to: My Account -> Bot Access")
    print("   d. Click 'Upload Certificate'")
    print(f"   e. Select file: {cert_file}")
    print("   f. Click 'Upload'")
    print()
    
    print("2. Update Configuration:")
    print("   The certificate paths will be added to betfair-creds.json")
    print()
    
    # Update betfair-creds.json
    if os.path.exists("betfair-creds.json"):
        import json
        
        with open("betfair-creds.json", "r") as f:
            creds = json.load(f)
        
        creds["cert_file"] = f"./{cert_file}"
        creds["key_file"] = f"./{key_file}"
        
        with open("betfair-creds.json", "w") as f:
            json.dump(creds, f, indent=2)
        
        print("[OK] Updated betfair-creds.json with certificate paths")
        print()
    
    print("⚠  IMPORTANT: Keep betfair-client.key secure and private!")
    print()
    print("3. Test Authentication:")
    print("   python refresh_token_cert.py")
    print()
    
    return cert_file, key_file

if __name__ == "__main__":
    try:
        cert_file, key_file = generate_certificate()
        
        # Ask to open browser
        answer = input("Open Betfair developer portal now? (y/n): ").strip().lower()
        if answer == 'y':
            import webbrowser
            webbrowser.open("https://developer.betfair.com/")
            print()
            print("✓ Opening Betfair developer portal...")
            print(f"  Upload the certificate file: {cert_file}")
        
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
