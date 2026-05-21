import re
with open('_bpapi_patched.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, l in enumerate(lines, start=1):
    if "'picks': future_picks" in l:
        print(f'Line {i}: {repr(l)}')
