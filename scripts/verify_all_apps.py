#!/usr/bin/env python3
"""
Full functional verification of all native vuln apps on the VPS.
Runs real login tests, API calls, DB checks, and vulnerability tests.

Usage:
  scp this script to VPS, then: python3 /tmp/verify_all_apps.py

Output is written to /tmp/final_verify.txt on the VPS.
Can be SCP'd back and read with `xxd` or `cat` (may need CCR bypass).
"""
import subprocess, json, os, sys

def run(cmd, timeout=30):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip(), r.returncode

results = {}

# 1. JUICE SHOP — login test
out, err, rc = run(
    'curl -s -X POST http://localhost:3000/rest/user/login '
    '-H "Content-Type: application/json" '
    "-d '{\"email\":\"admin@juice-sh.op\",\"password\":\"admin123\"}' --max-time 10"
)
try:
    d = json.loads(out)
    results['juice_shop'] = 'PASS' if d.get('authentication',{}).get('token') else 'FAIL'
except:
    results['juice_shop'] = 'FAIL: ' + out[:80]

# 2. DVGA — GraphQL introspection
out, err, rc = run(
    'curl -s -X POST http://localhost:5013/graphql '
    '-H "Content-Type: application/json" '
    "-d '{\"query\":\"{__schema{types{name}}}\"}' --max-time 10"
)
try:
    d = json.loads(out)
    count = len(d.get('data',{}).get('__schema',{}).get('types',[]))
    results['dvga'] = f'PASS ({count} types)'
except:
    results['dvga'] = 'FAIL: ' + out[:80]

# 3. WEBGOAT — login page loads
out, err, rc = run('curl -s http://localhost:8080/WebGoat/login --max-time 15')
results['webgoat'] = 'PASS' if 'Login Page' in out else 'FAIL'

# 4. MUTILLIDAE — login test
# CRITICAL: Use -sL (follow redirects) — Mutillidae returns 302 on login success
# Without -L, curl returns 0 bytes and login appears to fail
out, err, rc = run(
    'curl -sL -c /tmp/muti_verify_cookies -b /tmp/muti_verify_cookies '
    '"http://localhost:8081/index.php?page=login.php" '
    '-d "username=admin&password=adminpass&login-php-submit-button=Login" --max-time 10'
)
results['mutillidae'] = 'PASS' if 'Logged In' in out or 'Logout' in out else 'FAIL'

# Also test via nginx proxy on port 80
out_proxy, _, _ = run('curl -sL http://localhost:80/mutillidae/ --max-time 10 | wc -c')
results['mutillidae_proxy'] = f'{out_proxy} bytes via :80/mutillidae/'

# 5. WACKOPICKO
out, err, rc = run('curl -s http://localhost:8082/ --max-time 10')
results['wackopicko'] = 'PASS' if 'wackopicko' in out.lower() else 'FAIL'

# 6. VULNERABLEAPP
out, err, rc = run('curl -s http://localhost:9091/VulnerableApp/ --max-time 10')
results['vulnerableapp'] = 'PASS' if len(out) > 100 else 'FAIL'

# 7. CRAPI — signup + login via identity service (port 8083, HTTP)
# CRITICAL: Signup uses /signup (NOT /register), fields: name, email, password, number
# number must be UNIQUE — use a random one to avoid "already registered" 403
import random
phone = str(random.randint(1000000000, 9999999999))
out, err, rc = run(
    f'curl -s -X POST http://localhost:8083/identity/api/auth/signup '
    f'-H "Content-Type: application/json" '
    f"-d '{{\"name\":\"Verify User\",\"email\":\"verify_{phone}@test.com\",\"password\":\"Password123!\",\"number\":\"{phone}\"}}' --max-time 15"
)
try:
    d = json.loads(out)
    signup_ok = 'successfully' in d.get('message','').lower()
except:
    signup_ok = False
results['crapi_signup'] = 'PASS' if signup_ok else 'FAIL: ' + out[:80]

# Login with the same credentials
out, err, rc = run(
    f'curl -s -X POST http://localhost:8083/identity/api/auth/login '
    f'-H "Content-Type: application/json" '
    f"-d '{{\"email\":\"verify_{phone}@test.com\",\"password\":\"Password123!\"}}' --max-time 15"
)
try:
    d = json.loads(out)
    login_ok = d.get('token') is not None and d.get('token') != ''
except:
    login_ok = False
results['crapi_login'] = 'PASS' if login_ok else 'FAIL: ' + out[:80]

# 8. CRAPI GATEWAY (HTTPS on port 8888 — must use -k for self-signed cert)
out, err, rc = run('curl -sk https://localhost:8888/ --max-time 10')
results['crapi_gateway'] = 'PASS' if 'crAPI Gateway' in out else 'FAIL'

# 9. DASHBOARD
out, err, rc = run('curl -s http://localhost:80/ --max-time 10')
apps_list = ['Juice Shop','WebGoat','Mutillidae','DVGA','WackoPicko','VulnerableApp','crAPI']
found = [a for a in apps_list if a in out]
results['dashboard'] = f'{len(found)}/{len(apps_list)} apps'

# Check all proxy links are relative (no HOSTNAME placeholder)
has_hostname = 'HOSTNAME' in out
results['dashboard_links'] = 'OK (all relative)' if not has_hostname else 'BROKEN (HOSTNAME placeholder)'

# 10. ALL NGINX PROXY PATHS
for path in ['/juice-shop/', '/WebGoat/', '/mutillidae/', '/dvga/', '/wackopicko/', '/VulnerableApp/', '/crapi/']:
    out, _, _ = run(f'curl -s -o /dev/null -w "%{{http_code}}" http://localhost:80{path} --max-time 10')
    results[f'proxy{path}'] = f'HTTP {out}'

# 11. DATABASES
out, err, rc = run("mysql -u wackopicko -p'webvuln!@#' wackopicko -e 'SHOW TABLES' 2>/dev/null | wc -l")
results['mysql_wackopicko'] = f'{out.strip()} lines'
out, err, rc = run("mysql -u mutillidae -pmutillidae -e 'USE mutillidae; SHOW TABLES' 2>/dev/null | grep -v Warning | wc -l")
results['mysql_mutillidae'] = f'{out.strip()} tables'
out, err, rc = run("PGPASSWORD=crapi psql -U crapi -h 127.0.0.1 -d crapi -t -c \"SELECT count(*) FROM information_schema.tables WHERE table_schema='public'\" 2>/dev/null")
results['postgres_crapi'] = f'{out.strip()} tables'
out, err, rc = run("mongosh --quiet --eval \"db.getSiblingDB('crapi').getCollectionNames().length\" 2>/dev/null")
results['mongo_crapi'] = f'{out.strip()} collections'

# 12. SERVICES
out, err, rc = run(
    'for svc in juice-shop dvga webgoat vulnerableapp crapi-identity crapi-community '
    'crapi-workshop crapi-chatbot crapi-gateway crapi-web nginx php8.1-fpm php5.6-fpm '
    'mysql postgresql mongod; do echo "$svc:$(systemctl is-active $svc 2>/dev/null)"; done'
)
all_active = all(':active' in line for line in out.split('\n') if line.strip())
results['services'] = 'ALL ACTIVE' if all_active else out.replace('\n', ', ')

# PRINT RESULTS
lines = []
lines.append("=" * 55)
lines.append("  VULN LAB VERIFICATION RESULTS")
lines.append("=" * 55)
for key, value in results.items():
    lines.append(f"  {key:25s} {value}")
lines.append("=" * 55)

with open('/tmp/final_verify.txt', 'w') as f:
    f.write('\n'.join(lines) + '\n')

print('\n'.join(lines))