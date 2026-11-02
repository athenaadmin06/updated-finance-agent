#!/usr/bin/env bash
# Compile and run Java Health Check API Server

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

mkdir -p out

if command -v javac >/dev/null 2>&1; then
    echo "Compiling Java files with javac..."
    javac -d out src/main/java/com/example/health/*.java
    echo "Starting HealthCheckServer..."
    java -cp out com.example.health.HealthCheckServer "$@"
elif command -v mvn >/dev/null 2>&1; then
    echo "Running via Maven..."
    mvn compile exec:java
else
    echo "Neither javac/java nor mvn command found in PATH."
    echo "Please install Java (JDK 11+) to run the server."
    exit 1
fi

