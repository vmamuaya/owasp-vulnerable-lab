# OWASP Vulnerable Lab

7 deliberately vulnerable web applications deployed **natively** (no Docker) on a single Linux VPS, fronted by an nginx reverse proxy with a unified dashboard.

## Applications

| App | Port | Proxy Path | Tech Stack | Default Login |
|-----|------|-----------|------------|---------------|
| Juice Shop | 3000 | `/juice-shop/` | Node.js/Angular | admin@juice-sh.op / admin123 |
| WebGoat | 8080 | `/WebGoat/` | Java/Spring Boot | Register new account |
| Mutillidae II | 8081 | `/mutillidae/` | PHP/MySQL (PHP 8.1) | admin / adminpass |
| DVGA | 5013 | `/dvga/` | Python/Flask/GraphQL | N/A |
| WackoPicko | 8082 | `/wackopicko/` | PHP/MySQL (PHP 5.6) | Register new account |
| VulnerableApp | 9091 | `/VulnerableApp/` | Java | N/A |
| crAPI | 8888 | `/crapi/` | Java/Spring Boot + Go gateway | Register via API |

All apps are proxied through nginx on port 80. A dashboard at `/` provides launch links to all 7 apps.

## Architecture

```
                    ┌─────────────┐
                    │   nginx:80  │  ← Dashboard + reverse proxy
                    └──────┬──────┘
        ┌──────┬──────┬─────┼──────┬──────┬──────┬──────┐
        ▼      ▼      ▼     ▼      ▼      ▼      ▼      ▼
   :3000   :8080  :8081  :5013  :8082  :9091  :8888  :8083
   Juice   Web    Mutill  DVGA   Wacko  Vuln   crAPI  crAPI
   Shop    Goat    idae          Picko  App    GW     Identity
                                                    :8087 Community
                                                    :8088 Web
```

## Repository Structure

```
├── README.md                    # This file
├── docs/
│   ├── deployment-guide.md      # Full step-by-step deployment instructions
│   ├── troubleshooting.md       # Known issues and fixes (JWKS, PHP versions, MySQL auth, etc.)
│   ├── verification-guide.md    # Per-app verification commands
│   ├── deployment-log.md        # Deployment log with all fixes applied
│   └── app-catalog.md           # App details, ports, credentials
├── scripts/
│   ├── verify_all_apps.py       # Automated verification: login tests, DB checks, all 8 apps
│   ├── generate_jwks.py         # Generate JWKS with RSA private key for crAPI JWT auth
│   ├── native-setup.sh          # Bulk setup script (installs deps, creates DBs, etc.)
│   └── wackopicko-init.sh       # WackoPicko database initialization
├── templates/
│   ├── nginx-native.conf        # Ready-to-use nginx config (replace USER placeholder)
│   ├── dashboard.html           # Dashboard HTML with all 7 app links
│   ├── systemd-service.template # Template for systemd unit files
│   └── mysql_compat_shim.php    # PHP 5.6 compatibility shim for WackoPicko
```

## Quick Start

### Prerequisites
- Ubuntu 22.04+ VPS (tested on <VPS-IP>)
- sudo access
- Java 17, Node.js 18+, Python 3, PHP 5.6 + 8.1, MySQL 8, PostgreSQL 14, MongoDB 6

### 1. Clone and Prepare
```bash
git clone https://github.com/vmamuaya/owasp-vulnerable-lab.git
cd owasp-vulnerable-lab
```

### 2. Install Dependencies
See `docs/deployment-guide.md` for the full package list.

### 3. Deploy Each App
Follow `docs/deployment-guide.md` for step-by-step instructions for each app.

### 4. Configure Nginx
```bash
# Replace USER with your VPS username
sed 's/USER/your-username/g' templates/nginx-native.conf | sudo tee /etc/nginx/sites-available/vulnapps
sudo ln -sf /etc/nginx/sites-available/vulnapps /etc/nginx/sites-enabled/vulnapps
sudo nginx -t && sudo systemctl reload nginx
```

### 5. Deploy Dashboard
```bash
mkdir -p ~/vulnapps/dashboard
cp templates/dashboard.html ~/vulnapps/dashboard/index.html
```

### 6. Generate crAPI JWKS
```bash
# The crAPI identity service needs a JWKS WITH private key for JWT signing.
# Without this, login returns "Key argument cannot be null".
python3 scripts/generate_jwks.py
# Copy the base64 output to the crapi-identity.service Environment=JWKS= line
```

### 7. Verify Everything Works
```bash
scp scripts/verify_all_apps.py your-vps:/tmp/
ssh your-vps 'python3 /tmp/verify_all_apps.py'
# Check results for all PASS
```

## Critical Fixes (Read Before Deploying)

These issues were discovered and fixed during deployment. See `docs/troubleshooting.md` for full details.

### Mutillidae: MySQL auth_socket
MySQL root on Ubuntu uses `auth_socket` — PHP can't connect as root with a password.
**Fix:** Create a dedicated MySQL user:
```sql
CREATE USER 'mutillidae'@'localhost' IDENTIFIED BY 'mutillidae';
CREATE DATABASE mutillidae;
GRANT ALL PRIVILEGES ON mutillidae.* TO 'mutillidae'@'localhost';
FLUSH PRIVILEGES;
```
Then update `includes/database-config.inc`: `DB_USERNAME` → `mutillidae`.

### Mutillidae: PHP Version
Mutillidae uses `protected const` (PHP 7.1+). Must use `php8.1-fpm.sock`, NOT php5.6.

### crAPI: JWKS Private Key
The JWKS must include the RSA private key (`d` parameter). A public-only JWKS causes
`rsaKey.toKeyPair()` to return null → "Key argument cannot be null" on login.
**Fix:** Run `python3 scripts/generate_jwks.py` and use the output.

### crAPI: Gateway is HTTPS
The crAPI gateway (port 8888) uses `ListenAndServeTLS` with self-signed certs.
nginx proxy must use `proxy_pass https://127.0.0.1:8888/` with `proxy_ssl_verify off`.

### crAPI: Signup API
Endpoint is `/identity/api/auth/signup` (NOT `/register`). Fields: `name`, `email`,
`password`, `number` (NOT `firstName`/`lastName`).

### WackoPicko: PHP Version
WackoPicko is a PHP 5.x app. Must use `php5.6-fpm.sock`, NOT php8.1.

### Dashboard: Links
All dashboard links must use relative proxy paths (`/mutillidae/`, `/wackopicko/`),
not `http://HOSTNAME:8081/` placeholders.

## Verification

Run the automated verification script to confirm all apps work:

```bash
# On the VPS:
python3 scripts/verify_all_apps.py
```

Expected output:
```
=======================================================
  juice_shop                PASS
  dvga                      PASS (29 types)
  webgoat                   PASS
  mutillidae                PASS
  wackopicko                PASS
  vulnerableapp             PASS
  crapi_signup              PASS
  crapi_login               PASS
  crapi_gateway             PASS
  dashboard                 7/7 apps
  services                  ALL ACTIVE
=======================================================
```

## License

MIT — The vulnerable applications themselves have their own licenses (see each project).
This repo contains only deployment configurations, scripts, and documentation.

## Warning

These are deliberately vulnerable applications. NEVER expose them to the public internet.
Use a firewall, VPN, or SSH tunnel to restrict access.