#!/usr/bin/env python3
import os,subprocess,csv,hmac,hashlib,shlex

# Read salt from .env
salt = ''
env_path = '/home/amachado/workspace/equivalence-engine-service/.env'
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.strip().startswith('API_KEY_SALT='):
                salt = line.strip().split('=',1)[1]
                break

if not salt:
    print('API_KEY_SALT not found in .env')

# Fetch api_keys from Postgres via docker compose
cmd = ['docker','compose','exec','-T','postgres','psql','-U','equivalence','-d','equivalence','-c','COPY (SELECT name,key_hash FROM api_keys ORDER BY name) TO STDOUT WITH CSV;']
try:
    p = subprocess.run(cmd, capture_output=True, text=True, check=True)
    out = p.stdout
except subprocess.CalledProcessError as e:
    print('psql failed:', e)
    print('stdout:', e.stdout)
    print('stderr:', e.stderr)
    raise

# write to temp file
tmp = '/tmp/api_keys.csv'
with open(tmp,'w') as f:
    f.write(out)

keys_to_try = ['dev-admin-123','dev-admin-abc123','dev-client-123','dev-auditor-123']
with open(tmp) as f:
    for row in csv.reader(f):
        if not row:
            continue
        name,key_hash = row
        print('db:',name,key_hash)
        matched = False
        for k in keys_to_try:
            h = hmac.new(salt.encode(), k.encode(), hashlib.sha256).hexdigest()
            if h == key_hash:
                print(' MATCH ->',k)
                matched = True
                break
        if not matched:
            print(' NO MATCH')
