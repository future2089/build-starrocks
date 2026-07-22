#!/bin/bash
set -e

# Install Java 8
dnf install -y java-1.8.0-openjdk-headless java-1.8.0-openjdk-devel 2>&1 | tail -5
echo "JAVA_INSTALLED"

# Verify java
java -version 2>&1
echo "JAVA_VERIFIED"

# Copy KDC config
cp /etc/krb5.conf /data/package/krb5.conf 2>/dev/null || echo "KRB5_COPY_FAILED"
echo "SETUP_DONE"
