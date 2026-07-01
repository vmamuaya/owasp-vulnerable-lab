#!/bin/bash
# Native vulnerable apps setup script for Ubuntu 22.04 VPS
# Downloads and installs all apps natively (no Docker)
# Usage: bash native-setup.sh [APPDIR]
# Requires: sudo access, apt, internet access

set -o errexit  # Don't use set -e with functions that may fail individually

APPDIR="${1:-$HOME/vulnapps}"
mkdir -p "$APPDIR"
cd "$APPDIR"

STATUS_FILE="/tmp/setup_status.json"
echo "{" > $STATUS_FILE
FIRST=1
add_status() {
    if [ $FIRST -eq 0 ]; then echo "," >> $STATUS_FILE; fi
    echo "\"$1\": \"$2\"" >> $STATUS_FILE
    FIRST=0
}

# === Install Node.js via nvm ===
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm install 22  # Juice Shop 20.x requires Node v22+
nvm alias default 22

# === Install Java 23 via Adoptium ===
wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public | sudo tee /etc/apt/keyrings/adoptium.asc > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/adoptium.asc] https://packages.adoptium.net/artifactory/deb jammy main" | sudo tee /etc/apt/sources.list.d/adoptium.list
sudo apt-get update -qq
sudo apt-get install -y temurin-23-jdk
sudo update-alternatives --set java /usr/lib/jvm/temurin-23-jdk-amd64/bin/java

# === Install other runtimes ===
sudo apt-get install -y openjdk-17-jdk php php-cli php-mysql php-fpm php-gd php-mbstring php-xml \
  mysql-server postgresql nginx git maven python3-pip python3-venv curl wget

# === Start databases ===
sudo systemctl enable mysql postgresql php8.1-fpm nginx
sudo systemctl start mysql postgresql php8.1-fpm

# === 1. Juice Shop ===
git clone --depth 1 https://github.com/juice-shop/juice-shop.git
cd juice-shop && npm install && npm run build && cd "$APPDIR"
add_status "juice_shop" "READY"

# === 2. DVGA ===
git clone --depth 1 https://github.com/dolevf/damn-vulnerable-graphql-application.git dvga
cd dvga && python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt && python3 setup.py && deactivate && cd "$APPDIR"
add_status "dvga" "READY"

# === 3. WackoPicko ===
git clone --depth 1 https://github.com/adamdoupe/WackoPicko.git wackopicko
# Copy mysql_compat shim (see templates/mysql_compat_shim.php)
# Set up MySQL (strip CREATE USER/GRANT lines from schema)
sudo mysql -e "CREATE DATABASE wackopicko; CREATE USER 'wackopicko'@'localhost' IDENTIFIED BY 'webvuln!@#'; GRANT ALL ON wackopicko.* TO 'wackopicko'@'localhost'; FLUSH PRIVILEGES;"
grep -v "CREATE USER\|GRANT\|SET PASSWORD" wackopicko/current.sql | sudo mysql wackopicko
add_status "wackopicko" "READY"

# === 4. Mutillidae ===
git clone --depth 1 https://github.com/webpwnized/mutillidae.git
sudo mysql -e "CREATE DATABASE mutillidae;"
add_status "mutillidae" "READY"

# === 5. WebGoat ===
mkdir -p webgoat && cd webgoat
curl -L -o webgoat.jar "https://github.com/WebGoat/WebGoat/releases/download/v2025.3/webgoat-2025.3.jar"
chmod +x webgoat.jar && cd "$APPDIR"
add_status "webgoat" "READY"

# === 6. VulnerableApp ===
git clone --depth 1 https://github.com/SasanLabs/VulnerableApp.git vulnerableapp
cd vulnerableapp
# Build with Java 17 (Gradle doesn't support Java 23)
JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 ./gradlew bootJar -x test
cd "$APPDIR"
add_status "vulnerableapp" "READY"

# === 7. crAPI ===
git clone --depth 1 https://github.com/OWASP/crAPI.git crapi
add_status "crapi" "CLONED_ONLY"

# === Fix permissions for nginx ===
chmod o+x "$HOME"
find "$APPDIR" -type d -exec chmod o+x {} \;
find "$APPDIR/dashboard" "$APPDIR/mutillidae/src" "$APPDIR/wackopicko/website" -exec chmod -R o+r {} \;

echo "}" >> $STATUS_FILE
echo "SETUP COMPLETE — see $STATUS_FILE for results"