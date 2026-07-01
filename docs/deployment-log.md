# Native Deployment Log — 2026-07-01 (Updated)

## VPS Specs
- Ubuntu 22.04.5 LTS, x86_64, 16GB RAM, 62GB disk, 4 cores
- IP: <VPS-IP>, user: hermes-agent, SSH key: ~/.ssh/vulnapps_vps
- sudo access: passwordless

## Phase 1: Docker Teardown
- Stopped all 18 containers, removed containers/images/volumes
- `sudo docker system prune -af --volumes`
- Freed ~15GB (26G used → 11G used)

## Phase 2: Runtime Installation

### What was installed via apt:
- openjdk-17-jdk (Java 17) — insufficient for WebGoat 2025.3
- php 8.1.2 + php-fpm + php-mysql + php-gd + php-mbstring + php-xml
- php5.6 + php5.6-fpm (for WackoPicko compat)
- mysql-server 8.0.46
- postgresql 14.23
- nginx 1.18.0
- git, maven, python3-pip, python3-venv

### What needed manual install (apt versions too old):
- **Node.js**: Ubuntu 22.04 apt has Node 12 only. Installed via nvm:
  - Juice Shop 20.1.1 requires Node v22+ (not v18 or v20!)
  - `nvm install 22` → v22.23.1
  - `nvm alias default 22`
- **Java 23**: WebGoat 2025.3 requires class file version 67 = Java 23.
  - Ubuntu 22.04 repos max out at JDK 17
  - Added Adoptium/Temurin repo:
    ```
    wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public | sudo tee /etc/apt/keyrings/adoptium.asc
    echo "deb [signed-by=/etc/apt/keyrings/adoptium.asc] https://packages.adoptium.net/artifactory/deb jammy main" | sudo tee /etc/apt/sources.list.d/adoptium.list
    sudo apt-get update && sudo apt-get install -y temurin-23-jdk
    sudo update-alternatives --set java /usr/lib/jvm/temurin-23-jdk-amd64/bin/java
    ```

## Phase 3: App Installation

### 1. OWASP Juice Shop — WORKING (port 3000)
- Runtime: Node.js v22.23.1 via nvm
- Pitfall: `npm install --production` does NOT build the app. Must run `npm run build` separately.
- Pitfall: Juice Shop 20.1.1 requires Node v22-26. Node 18 and 20 are too old.
- Systemd service uses nvm node path: `/home/hermes-agent/.nvm/versions/node/v22.23.1/bin/npm start`
- Must set `Environment=PATH=...nvm.../bin:...` in systemd service or npm fails silently
- Build steps: `git clone → npm install → npm run build → npm start`

### 2. DVGA — WORKING (port 5013)
- Runtime: Python3 venv
- Repository moved: github.com/dolevf/DVGA → github.com/dolevf/damn-vulnerable-graphql-application
- Pitfall: Database must be initialized BEFORE first start: `source venv/bin/activate && python3 setup.py`
- Without setup.py, get `sqlalchemy.exc.OperationalError: no such table: servermode`
- Systemd service: `ExecStart=.../venv/bin/python app.py`

### 3. OWASP Mutillidae II — WORKING (port 8081, proxied at :80/mutillidae/)
- Runtime: PHP 8.1 + PHP-FPM + MySQL
- Pitfall: index.php is in `src/` subdirectory, not project root
- nginx root must be: `/home/hermes-agent/vulnapps/mutillidae/src`
- Served directly by nginx+PHP-FPM (no systemd service needed)
- **CRITICAL: MySQL root uses auth_socket on Ubuntu 22.04** — `sudo mysql -u root` works but
  `mysql -u root -pmutillidae` does NOT. Must create dedicated MySQL user:
  `CREATE USER 'mutillidae'@'localhost' IDENTIFIED BY 'mutillidae'`
- **CRITICAL: Must use php8.1-fpm.sock** (not php5.6) — Mutillidae uses `protected const`
  (PHP 7.1+ feature). PHP 5.6 throws parse error.
- **No .sql schema files** — tables created by `set-up-database.php` (curl it after DB user fix)
- **Login test**: Must use `curl -sL` (follow redirects) — login POST returns 302, curl without
  -L gives 0-byte response even when login succeeds
- Default creds: admin / adminpass

### 4. OWASP WebGoat — WORKING (port 8080, WebWolf port 9090)
- Runtime: Java 23 (Temurin)
- The release JAR (webgoat-2025.3.jar) is a Spring Boot "fully executable" JAR — starts with `#!/bin/bash`
- Must run as executable: `ExecStart=/path/to/webgoat.jar --webgoat.port=8080 --webwolf.port=9090`
- NOT `java -jar webgoat.jar` (that gives UnsupportedClassVersionError with Java < 23)
- Download URL format: `https://github.com/WebGoat/WebGoat/releases/download/v2025.3/webgoat-2025.3.jar`

### 5. WackoPicko — WORKING (port 8082, proxied at :80/wackopicko/)
- Runtime: PHP 5.6 + PHP-FPM + MySQL 8
- **CRITICAL: Uses php5.6-fpm.sock** (not php8.1) — deprecated `mysql_*` functions
- Shim maps mysql_connect→mysqli_connect, etc.
- auto_prepend via nginx fastcgi_param
- MySQL password in ourdb.php is `webvuln!@#` (not `webvuln`)
- Schema import: strip CREATE USER/GRANT/SET PASSWORD lines from current.sql
- nginx root: `/home/hermes-agent/vulnapps/wackoPicko/website`

### 6. OWASP VulnerableApp — WORKING (port 9091)
- Runtime: Java 23 (run) + Java 17 (build)
- Repository: github.com/SasanLabs/VulnerableApp (capital V)
- Uses Gradle (NOT Maven) — `./gradlew bootJar -x test`
- Build with Java 17, run with Java 23
- Context path: /VulnerableApp/

### 7. OWASP crAPI — WORKING (identity :8083, gateway :8888 HTTPS, web :8088)
- **Microservices architecture**: identity (Java/Spring), community (Java), workshop (Java),
  chatbot (Java), gateway (Go), web (Python http.server)
- Identity service env vars (in systemd service):
  - DB_HOST=127.0.0.1, DB_PORT=5432, DB_NAME=crapi, DB_USER=crapi, DB_PASSWORD=crapi
  - SERVER_PORT=8083, TLS_ENABLED=false
  - JWKS=<base64-encoded JWKS JSON with PRIVATE key>
  - API_GATEWAY_URL=http://localhost:8888
  - SPRING_JPA_HIBERNATE_DDL_AUTO=update
- **CRITICAL: JWKS must include private key params (d, p, q, dp, dq, qi)** — not just
  public (n, e). Without private key, login throws "Key argument cannot be null"
  because rsaKey.toKeyPair() returns null. See native-troubleshooting.md for fix script.
- **Signup endpoint**: `/identity/api/auth/signup` (NOT /register)
  Fields: name, email, password, number (phone — must be unique)
- **Gateway is HTTPS only**: Go gateway uses ListenAndServeTLS. nginx proxy must use
  `proxy_pass https://127.0.0.1:8888/; proxy_ssl_verify off;`
- Build: Maven build for each Java service (`./mvnw package -DskipTests`)
- Gateway: Go binary, `go build` in services/gateway-service/

## Phase 4: nginx Configuration
- Single config file: `/etc/nginx/sites-available/vulnapps`
- Server block on port 80: dashboard + all proxy locations
- Server block on port 8081: Mutillidae (PHP 8.1)
- Server block on port 8082: WackoPicko (PHP 5.6)
- **Pitfall**: Use line-number-targeted sed when editing nginx config to avoid
  changing ALL fastcgi_pass lines. Mutillidae needs php8.1-fpm.sock, WackoPicko
  needs php5.6-fpm.sock.
- **Dashboard proxy locations** (all on port 80 server block):
  - `/juice-shop/` → http://127.0.0.1:3000/
  - `/WebGoat/` → http://127.0.0.1:8080/WebGoat/
  - `/mutillidae/` → http://127.0.0.1:8081/
  - `/dvga/` → http://127.0.0.1:5013/
  - `/wackopicko/` → http://127.0.0.1:8082/
  - `/VulnerableApp/` → http://127.0.0.1:9091/VulnerableApp/
  - `/crapi/` → https://127.0.0.1:8888/ (with proxy_ssl_verify off)

## Phase 5: Dashboard Link Fixes
- Dashboard HTML at `~/vulnapps/dashboard/index.html`
- All app links must use relative proxy paths (e.g. `/juice-shop/`)
- Common issues: literal "HOSTNAME" placeholder, broken href syntax
- Fix: `sed -i 's|http://HOSTNAME:8081/|/mutillidae/|' ~/vulnapps/dashboard/index.html`

## Phase 6: Permissions
- CRITICAL: www-data (nginx) cannot read files in /home/hermes-agent/ by default
- Fix: `chmod o+x /home/hermes-agent` and `chmod -R o+r` on app directories
- Find directories and make them traversable: `find ~/vulnapps/... -type d -exec chmod o+x {} \;`

## Phase 7: Systemd Services
- All Java/Node apps have systemd services with Restart=on-failure
- PHP apps served by nginx+PHP-FPM (no individual services)
- nvm paths must be explicit in ExecStart and Environment=PATH
- Services: juice-shop, dvga, webgoat, vulnerableapp, crapi-identity,
  crapi-community, crapi-workshop, crapi-chatbot, crapi-gateway, crapi-web

## Verification Results (2026-07-01, all passing)
| App | Port | Proxy Path | Status |
|-----|------|-----------|--------|
| Dashboard | 80 | / | 200, 7/7 apps |
| Juice Shop | 3000 | /juice-shop/ | PASS (login) |
| DVGA | 5013 | /dvga/ | PASS (29 GraphQL types) |
| WebGoat | 8080 | /WebGoat/ | PASS (login page) |
| Mutillidae | 8081 | /mutillidae/ | PASS (login + 12 tables) |
| WackoPicko | 8082 | /wackopicko/ | PASS |
| VulnerableApp | 9091 | /VulnerableApp/ | PASS |
| crAPI signup | 8083 | /crapi/ | PASS |
| crAPI login | 8083 | /crapi/ | PASS (JWT token) |
| crAPI gateway | 8888 | /crapi/ | PASS (HTTPS) |

## Dashboard Link Fixes (2026-07-01)

### Problem
Dashboard had 3 broken app links and 1 broken nginx proxy:

1. **WebGoat**: `href:8080/WebGoat/"` (broken HTML syntax, missing `="`) -> fixed to `/WebGoat/`
2. **Mutillidae**: `http://HOSTNAME:8081/` (literal "HOSTNAME" placeholder) -> fixed to `/mutillidae/`
3. **WackoPicko**: `http://HOSTNAME:8082/` (literal "HOSTNAME" placeholder) -> fixed to `/wackopicko/`
4. **crAPI proxy**: nginx `proxy_pass http://127.0.0.1:8888/` -> gateway expects HTTPS -> fixed to `https://127.0.0.1:8888/` with `proxy_ssl_verify off`

### Fix Steps
1. Fix dashboard HTML:
   ```bash
   sed -i 's|href:8080/WebGoat/"|href="/WebGoat/"|' ~/vulnapps/dashboard/index.html
   sed -i 's|http://HOSTNAME:8081/|/mutillidae/|' ~/vulnapps/dashboard/index.html
   sed -i 's|http://HOSTNAME:8082/|/wackopicko/|' ~/vulnapps/dashboard/index.html
   ```

2. Add nginx proxy locations for mutillidae and wackopicko, fix crapi HTTPS:
   ```nginx
   location /crapi/ {
       proxy_pass https://127.0.0.1:8888/;
       proxy_ssl_verify off;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
   }
   location /mutillidae/ {
       proxy_pass http://127.0.0.1:8081/;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
   }
   location /wackopicko/ {
       proxy_pass http://127.0.0.1:8082/;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
   }
   ```

3. Test nginx and reload:
   ```bash
   sudo nginx -t && sudo systemctl reload nginx
   ```

4. Verify all proxy paths return 200:
   ```bash
   for path in /juice-shop/ /WebGoat/ /mutillidae/ /dvga/ /wackopicko/ /VulnerableApp/ /crapi/; do
     echo "$path: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:80$path)"
   done
   ```

### JWKS Private Key Fix (crAPI login)
The crAPI identity service JWKS must include the RSA private key (param `d`).
A JWKS with only public params (n, e) causes `rsaKey.toKeyPair()` to return null,
producing "Key argument cannot be null" on login.

Generate a proper JWKS:
```bash
python3 scripts/generate_jwks.py  # outputs base64 string
```

Update the service:
```bash
sudo sed -i "s|Environment=JWKS=.*|Environment=JWKS=<new-base64>|" /etc/systemd/system/crapi-identity.service
sudo systemctl daemon-reload && sudo systemctl restart crapi-identity
```

## Headroom CCR Compression Issue
- Headroom proxy compresses ALL tool output including SSH command output,
  file reads, and local command output via execute_code/terminal/read_file.
- See references/native-troubleshooting.md for bypass techniques.
- Most reliable: SCP file back + `xxd` to read hex dump (CCR can't pattern-match hex).