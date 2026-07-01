# Native Deployment (Non-Docker) — Vulnerable Apps Lab

When the user wants vulnerable apps running natively on a VPS (no Docker), this reference
documents the approach, gotchas, and per-app requirements discovered during real deployment
on Ubuntu 22.04 (VPS: <VPS-IP>, 4 cores, 16GB RAM, 62GB disk).

## Why Native Instead of Docker?

- Full access to app internals for debugging and customization
- No container overhead (memory, disk)
- Can install custom tools (debuggers, proxies, MITM) alongside apps
- Better for training scenarios that require host-level access

## VPS Prerequisites

```bash
# Install all runtimes at once
sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
  openjdk-17-jdk nodejs npm \
  php php-cli php-mysql php-fpm php-gd php-mbstring php-xml \
  mysql-server postgresql \
  nginx git maven \
  python3-pip python3-venv curl wget unzip
```

### Node.js Version Issue (CRITICAL)

Ubuntu 22.04's `nodejs` package installs Node v12 which is too old for Juice Shop (needs 18+).
NodeSource setup may fail due to dpkg conflicts. The reliable fix is **nvm**:

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm install 18
```

**Pitfall:** System `npm` still points to the apt-installed Node v12. Any systemd service
or script that runs `npm` must source nvm first:
```bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 18
```

### MySQL Setup

```bash
sudo systemctl enable mysql
sudo systemctl start mysql
# Create databases per-app (see each app section below)
```

### PostgreSQL Setup

```bash
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

## Per-App Native Setup

### 1. OWASP Juice Shop (Node.js 18)

```bash
cd ~/vulnapps
git clone --depth 1 https://github.com/juice-shop/juice-shop.git
cd juice-shop
# MUST use nvm node 18, not system node 12
export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh" && nvm use 18
npm install --production
# Run: npm start (default port 3000)
```

**Pitfall:** `npm install` will silently use system Node v12 if nvm is not sourced first,
producing "npm error command failed" with no clear reason. Always verify `node --version`
shows v18 before running npm.

### 2. DVGA — Damn Vulnerable GraphQL Application (Python)

**Pitfall:** The GitHub repo URL changed. The old URL `https://github.com/dolevf/DVGA.git`
returns 404. The correct URL is:
```
https://github.com/dolevf/damn-vulnerable-graphql-application.git
```

```bash
cd ~/vulnapps
git clone --depth 1 https://github.com/dolevf/damn-vulnerable-graphql-application.git dvga
cd dvga
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Run: python3 app.py (default port 5013)
```

### 3. OWASP Mutillidae II (PHP + MySQL)

```bash
cd ~/vulnapps
git clone --depth 1 https://github.com/webpwnized/mutillidae.git
# Create MySQL database
mysql -u root -e "CREATE DATABASE IF NOT EXISTS mutillidae;"
# Import schema (find .sql files in the repo)
find mutillidae/ -name "*.sql" -exec mysql -u root mutillidae < {} \;
# Run with PHP built-in server or nginx+php-fpm
# Built-in: php -S 0.0.0.0:8081 -t mutillidae
```

**Note:** Mutillidae's PHP code is compatible with PHP 8.1 (uses mysqli, not deprecated mysql_connect).

### 4. WackoPicko (PHP + MySQL) — COMPATIBILITY ISSUE

**CRITICAL Pitfall:** WackoPicko uses `mysql_connect()`, `mysql_query()`, `mysql_fetch_*()`
functions that were **removed in PHP 7.0**. PHP 8.1 (Ubuntu 22.04 default) does not have
these functions at all. Two options:

**Option A — Install PHP 5.6 via PPA:**
```bash
sudo add-apt-repository ppa:ondrej/php
sudo apt-get update
sudo apt-get install php5.6 php5.6-mysql php5.6-cli
# Run with: php5.6 -S 0.0.0.0:8083 -t wackopicko
```

**Option B — Patch code to use mysqli:**
Replace `mysql_connect($host, $user, $pass)` with `mysqli_connect($host, $user, $pass, $db)`
and all other `mysql_*` calls with `mysqli_*` equivalents. This is a manual process as
the API is slightly different (mysqli requires the connection link as first argument).

```bash
# MySQL setup (works regardless of PHP version)
mysql -u root -e "CREATE DATABASE IF NOT EXISTS wackopicko; \
  CREATE USER IF NOT EXISTS 'wackopicko'@'localhost' IDENTIFIED BY 'webvuln'; \
  GRANT ALL ON wackopicko.* TO 'wackopicko'@'localhost'; FLUSH PRIVILEGES;"
mysql -u root wackopicko < wackopicko/sql/wackopicko.sql
# Also fix DB config: sed -i 's/localhost/wackopicko-db/' wackopicko/include/config.php
# And fix password: ensure password is 'webvuln' not 'webvuln!@#'
```

### 5. OWASP WebGoat (Java)

**Pitfall:** The release JAR naming convention changed. The file is named `webgoat-2025.3.jar`
(NOT `webgoat-server-v2025.3.jar`). Always check the GitHub releases API for exact asset names:

```bash
# Find the correct download URL
curl -s "https://api.github.com/repos/WebGoat/WebGoat/releases" | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print(d[0]['assets'][0]['browser_download_url'])"

# Download (example for v2025.3)
mkdir -p ~/vulnapps/webgoat
wget -q https://github.com/WebGoat/WebGoat/releases/download/v2025.3/webgoat-2025.3.jar \
  -O ~/vulnapps/webgoat/webgoat.jar
# Run: java -jar webgoat.jar (default port 8080, WebWolf on 9090)
```

**Pitfall:** The JAR is ~150MB+. wget may timeout on slow connections. Use `--timeout=120`.
Verify the file size is >1MB after download (failed downloads leave empty/truncated files).

### 6. OWASP VulnerableApp (Java + Maven)

**Pitfall:** The GitHub repo URL is case-sensitive. `owasp-vulnerableapp` (lowercase) returns
404. The correct URL is `SasanLabs/VulnerableApp` (capital V):

```bash
cd ~/vulnapps
git clone --depth 1 https://github.com/SasanLabs/VulnerableApp.git vulnerableapp
cd vulnerableapp
mvn clean package -DskipTests
# Run: java -jar target/vulnerableapp-*.jar (default port 9090)
```

### 7. OWASP crAPI (Java microservices + PostgreSQL)

Most complex to deploy natively. Requires Maven build + PostgreSQL + multiple services.

```bash
cd ~/vulnapps
git clone --depth 1 https://github.com/OWASP/crAPI.git crapi
# Build: cd crapi && mvn clean package -DskipTests
# Configure PostgreSQL: create crapi database and user
# Run each microservice separately (identity, community, workshop, chatbot)
```

crAPI is the hardest to run natively. Consider keeping it in Docker even when other apps
are native, or use the Spring Boot JARs from the build output.

## Systemd Services for Native Apps

Each app needs a systemd service. Example for Juice Shop:

```ini
# /etc/systemd/system/vuln-juice-shop.service
[Unit]
Description=OWASP Juice Shop (native)
After=network.target

[Service]
Type=simple
User=hermes-agent
WorkingDirectory=/home/hermes-agent/vulnapps/juice-shop
ExecStart=/home/hermes-agent/.nvm/versions/node/v18.20.8/bin/npm start
Restart=on-failure
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
```

**Pitfall:** systemd services do NOT source `.bashrc` or `.profile`. If using nvm, you must
use the full path to the nvm-installed node binary, not just `npm`. Find it with:
`which npm` after `nvm use 18`.

## Nginx Reverse Proxy for Native Apps

```nginx
# /etc/nginx/sites-available/vulnapps
upstream juice_shop { server 127.0.0.1:3000; }
upstream dvga { server 127.0.0.1:5013; }
upstream mutillidae { server 127.0.0.1:8081; }
upstream webgoat { server 127.0.0.1:8080; }
upstream wackopicko { server 127.0.0.1:8083; }
upstream vulnerableapp { server 127.0.0.1:9090; }

server {
    listen 80;
    server_name _;

    location /juice-shop/ { proxy_pass http://juice_shop/; }
    location /dvga/ { proxy_pass http://dvga/; }
    location /mutillidae/ { proxy_pass http://mutillidae/; }
    location /WebGoat/ { proxy_pass http://webgoat/WebGoat/; }
    location /wackopicko/ { proxy_pass http://wackopicko/; }
    location /VulnerableApp/ { proxy_pass http://vulnerableapp/VulnerableApp/; }
}
```

## Status Tracking Pattern

When running a multi-app setup script on a remote VPS, write status to a JSON file
on the VPS and poll it, rather than trying to parse script output over SSH:

```bash
# On the VPS, write to /tmp/setup_status.json
echo "{\"juice_shop\": \"READY\", \"dvga\": \"CLONE_FAILED\"}" > /tmp/setup_status.json
```

Then read it from the agent:
```python
result = subprocess.run(['ssh', '-i', key, user@host, 'cat /tmp/setup_status.json'], ...)
data = json.loads(result.stdout)
```

## Headroom CCR Workaround for SSH Output

When Headroom context compression proxy is active, SSH command output gets compressed
with CCR wrappers (`<<ccr:...>>`), making it unreadable through normal tool output. To
work around this:

1. Write output to a file on the VPS, then SCP it back and read with `read_file`
2. Or encode output as character codes: `[ord(c) for c in result.stdout]` and decode
   on the agent side. Print as comma-separated integers, then decode mentally:
   `"".join(chr(n) for n in [118,49,56,46,50,48,46,56])` = "v18.20.8"
3. Use JSON status files on the VPS (most reliable for multi-step setups)
4. For simple yes/no checks, just match known byte sequences (e.g., "52,48,52" = "404")