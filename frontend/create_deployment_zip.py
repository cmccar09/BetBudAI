"""
Create a properly formatted Amplify deployment zip.
PowerShell's Compress-Archive uses backslashes which Amplify doesn't handle correctly.
"""
import zipfile
import os
from pathlib import Path

build_dir = Path('build')
output_zip = Path('amplify-deploy.zip')

print(f"Creating deployment zip from {build_dir}...")

with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(build_dir):
        for file in files:
            file_path = Path(root) / file
            # Create archive name relative to build dir, using forward slashes
            arcname = str(file_path.relative_to(build_dir)).replace('\\', '/')
            zipf.write(file_path, arcname)
            print(f"  Added: {arcname}")

print(f"\nCreated {output_zip} ({output_zip.stat().st_size // 1024} KB)")
print("Verifying zip contents...")

with zipfile.ZipFile(output_zip, 'r') as zipf:
    names = zipf.namelist()
    print(f"  Total files: {len(names)}")
    print(f"  Sample files:")
    for name in names[:5]:
        print(f"    - {name}")

    # Verify paths use forward slashes
    bad_paths = [n for n in names if '\\' in n]
    if bad_paths:
        print(f"\n  WARNING: Found {len(bad_paths)} paths with backslashes:")
        for p in bad_paths[:3]:
            print(f"    - {p}")
    else:
        print(f"  All paths use forward slashes (correct)")

print("\nReady to deploy!")
