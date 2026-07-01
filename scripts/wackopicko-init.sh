#!/bin/bash
# Wait for MySQL, fix DB host config, import schema, start Apache

set -e

echo "Waiting for MySQL..."
for i in $(seq 1 30); do
    if mysqladmin ping -h wackopicko-db -u wackopicko -p'webvuln' --silent 2>/dev/null; then
        echo "MySQL is up!"
        break
    fi
    echo "  retry $i/30..."
    sleep 2
done

# Fix DB host: change "localhost" to "wackopicko-db" and password to "webvuln"
if [ -f /var/www/html/include/ourdb.php ]; then
    echo "Fixing DB host config..."
    sed -i 's/"localhost"/"wackopicko-db"/' /var/www/html/include/ourdb.php
    sed -i 's/webvuln!@#/webvuln/' /var/www/html/include/ourdb.php
fi

# Import the database schema if current.sql exists
# Strip CREATE USER/GRANT/SET PASSWORD lines that fail without root privileges
if [ -f /var/www/html/current.sql ]; then
    echo "Importing WackoPicko database..."
    grep -v "CREATE USER\|GRANT\|SET PASSWORD" /var/www/html/current.sql | \
        mysql -h wackopicko-db -u root -proot wackopicko 2>/dev/null || true
    echo "Database imported."
else
    echo "WARNING: current.sql not found, skipping DB import."
fi

# Start Apache in foreground
echo "Starting Apache..."
apache2-foreground