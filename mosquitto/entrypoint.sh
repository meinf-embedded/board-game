#!/bin/ash

set -e

# Fix write permissions for mosquitto directories
chown --no-dereference --recursive mosquitto /mosquitto/log

mkdir -p /var/run/mosquitto \
  && chown --no-dereference --recursive mosquitto /var/run/mosquitto

# Create mosquitto password file
touch mosquitto.passwd
chmod 0700 mosquitto.passwd
chown mosquitto:mosquitto mosquitto.passwd

for file in /mosquitto/config/users/*; do
    echo "Adding user ${file##*/}"
    mosquitto_passwd -b mosquitto.passwd "${file##*/}" "$(cat $file)"
done

exec "$@"