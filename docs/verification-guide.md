# Functional Verification Guide (Native Deployment)

## Why Content Checks Matter

HTTP status codes are NOT sufficient to verify a vulnerable app is
working. During real deployment testing, we found multiple cases where
apps returned HTTP 200 or 302 but were actually broken:

- WebGoat returned 302 → redirected to a 404 page (absolute path issue)
- Mutillidae returned 302 → redirected to `database-offline.php`
- WackoPicko returned 200 → but page was a PHP Fatal Error
- Mutillidae returned 200 on GET but 0 bytes on POST login → was 302 redirect
  that curl didn't follow (fix: use `curl -sL`)
- crAPI login returned "Key argument cannot be null" → JWKS missing private key

Only by checking the actual response body content can you confirm
the app is truly functional.

## Verification Script

A comprehensive verification script is available at `scripts/verify_all_apps.py`.
Upload it to the VPS and run it:

```bash
scp -i ~/.ssh/vulnapps_vps scripts/verify_all_apps.py hermes-agent@<VPS-IP>:/tmp/
ssh -i ~/.ssh/vulnapps_vps hermes-agent@<VPS-IP> 'python3 /tmp/verify_all_apps.py'
# Results saved to /tmp/final_verify.txt on VPS — SCP back to read
```

The script uses random phone numbers for crAPI signup to avoid "already
registered" 403 errors on re-runs.

## Per-App Verification Commands

All apps are proxied through nginx on port 80. Direct ports are listed
for reference. See native-deployment-log.md for the full architecture.

### 1. Dashboard (port 80)
```bash
curl -s http://localhost:80/ | grep -o "Vulnerable Apps Lab"
# Check all 7 app names present and links are relative (no HOSTNAME):
curl -s http://localhost:80/ | grep -oE "Juice Shop|WebGoat|Mutillidae|DVGA|WackoPicko|VulnerableApp|crAPI"
curl -s http://localhost:80/ | grep -c "HOSTNAME"  # Should be 0
```

### 2. Juice Shop (port 3000, proxied at /juice-shop/)
```bash
# Login test:
curl -s -X POST http://localhost:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","password":"admin123"}' | grep -o "token"
# Proxy test:
curl -s -o /dev/null -w "%{http_code}" http://localhost:80/juice-shop/
```

### 3. WebGoat (port 8080, proxied at /WebGoat/)
```bash
curl -s http://localhost:8080/WebGoat/login | grep -o "Login Page"
curl -s -o /dev/null -w "%{http_code}" http://localhost:80/WebGoat/login
```

### 4. Mutillidae II (port 8081, proxied at /mutillidae/)
```bash
# CRITICAL: Use -sL (follow redirects) — login POST returns 302
curl -sL -c /tmp/cookies -b /tmp/cookies \
  "http://localhost:8081/index.php?page=login.php" \
  -d "username=admin&password=adminpass&login-php-submit-button=Login" | grep -o "Logged In"
# DB check:
mysql -u mutillidae -pmutillidae -e "USE mutillidae; SHOW TABLES" 2>/dev/null | wc -l
# Should be 13 (header + 12 tables)
```

### 5. DVGA (port 5013, proxied at /dvga/)
```bash
curl -s -X POST http://localhost:5013/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{__schema{types{name}}}"}' | python3 -c "import sys,json; print(len(json.load(sys.stdin)['data']['__schema']['types']))"
```

### 6. VulnerableApp (port 9091, proxied at /VulnerableApp/)
```bash
curl -s http://localhost:9091/VulnerableApp/ | wc -c  # Should be > 100
```

### 7. WackoPicko (port 8082, proxied at /wackopicko/)
```bash
curl -s http://localhost:8082/ | grep -io "wackopicko"
# DB check:
mysql -u wackopicko -p'webvuln!@#' wackopicko -e "SHOW TABLES" 2>/dev/null | wc -l
```

### 8. crAPI (identity :8083, gateway :8888 HTTPS, proxied at /crapi/)
```bash
# Health check:
curl -s http://localhost:8083/identity/health_check
# Signup (NOT /register, fields: name/email/password/number, number must be unique):
curl -s -X POST http://localhost:8083/identity/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@test.com","password":"Password123!","number":"5551112222"}'
# Login:
curl -s -X POST http://localhost:8083/identity/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Password123!"}'
# Should return JWT token (not "Key argument cannot be null")
# Gateway (HTTPS — must use -k):
curl -sk https://localhost:8888/ | grep -o "crAPI Gateway"
# Proxy test:
curl -s -o /dev/null -w "%{http_code}" http://localhost:80/crapi/
```

## Database Verification (Native — no Docker)

### Mutillidae (MySQL, user: mutillidae)
```bash
mysql -u mutillidae -pmutillidae -e "USE mutillidae; SHOW TABLES" 2>/dev/null
# Should show: accounts, blogs_table, captured_data, credit_cards,
# help_texts, hitlog, page_help, page_hints, pen_test_tools, etc.
# Note: MySQL root uses auth_socket — must use `sudo mysql -u root` or
# the dedicated mutillidae user.
```

### WackoPicko (MySQL, user: wackopicko)
```bash
mysql -u wackopicko -p'webvuln!@#' wackopicko -e "SHOW TABLES" 2>/dev/null
# Should show 14 tables
```

### crAPI (PostgreSQL, user: crapi)
```bash
PGPASSWORD=crapi psql -U crapi -h 127.0.0.1 -d crapi -t -c \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"
# Should show ~27 tables
```

### crAPI (MongoDB)
```bash
mongosh --quiet --eval "db.getSiblingDB('crapi').getCollectionNames().length"
```

## Service Health Check (systemd)
```bash
for svc in juice-shop dvga webgoat vulnerableapp crapi-identity crapi-community \
  crapi-workshop crapi-chatbot crapi-gateway crapi-web nginx php8.1-fpm \
  php5.6-fpm mysql postgresql mongod; do
  echo "$svc: $(systemctl is-active $svc)"
done
# All should be "active" (crapi-chatbot may show "activating" briefly on boot)
```

## All Nginx Proxy Paths
```bash
for path in /juice-shop/ /WebGoat/ /mutillidae/ /dvga/ /wackopicko/ /VulnerableApp/ /crapi/; do
  echo "$path: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:80$path)"
done
# All should return 200
```