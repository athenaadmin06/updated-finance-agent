# Java Health Check API with Token Authentication

A simple, lightweight Java HTTP API for service health checks authenticated via an auth token.

Built using standard Java SE libraries (`com.sun.net.httpserver` and `java.net.http`), requiring **zero external dependencies**. Compatible with Java 11+.

---

## Features

- **Endpoints**: `GET /health` and `GET /api/health`
- **Authentication**: Supports standard `Authorization: Bearer <token>` or `X-Auth-Token: <token>` headers
- **CORS Support**: Preflight `OPTIONS` and standard headers included
- **Zero Dependencies**: Uses standard JDK libraries — runs with plain `javac`/`java` or Maven
- **Client & Tests Included**: Comes with `HealthCheckClient.java` and `test-health.sh` for automated verification

---

## Directory Structure

```
java-test/
├── pom.xml                                              # Optional Maven build file
├── README.md                                            # Documentation & API reference
├── run.sh                                               # Compile & run script
├── test-health.sh                                       # Automated curl test script
└── src/
    └── main/
        └── java/
            └── com/
                └── example/
                    └── health/
                        ├── HealthCheckServer.java       # HTTP Server & health check handler
                        └── HealthCheckClient.java       # Client caller & automated test suite
```

---

## Configuration

| Setting | Default Value | Environment Variable | System Property (`-D`) |
|---------|---------------|----------------------|------------------------|
| Port | `8080` | `PORT` | `-Dport=8080` |
| Auth Token | `secret-health-token-12345` | `AUTH_TOKEN` | `-Dauth.token=...` |

---

## How to Run

### Option 1: Direct Java (no build tool needed)

```bash
# 1. Compile
mkdir -p out
javac -d out src/main/java/com/example/health/*.java

# 2. Run the server
java -cp out com.example.health.HealthCheckServer

# Or specify custom port and token via environment:
PORT=9090 AUTH_TOKEN=my-secure-token java -cp out com.example.health.HealthCheckServer
```

### Option 2: Using the `run.sh` script

```bash
./run.sh
```

### Option 3: Using Maven

```bash
mvn compile exec:java
```

---

## How to Test

### 1. Using `curl`

#### Success: Valid Token (HTTP 200 OK)
```bash
curl -i http://localhost:8080/health \
  -H "Authorization: Bearer secret-health-token-12345"
```
**Response:**
```json
HTTP/1.1 200 OK
Content-Type: application/json; charset=UTF-8

{
  "status": "UP",
  "service": "health-check-api",
  "timestamp": "2026-11-02T12:20:00.000Z",
  "uptimeSeconds": 15,
  "authenticated": true
}
```

#### Failure: Missing Token (HTTP 401 Unauthorized)
```bash
curl -i http://localhost:8080/health
```
**Response:**
```json
HTTP/1.1 401 Unauthorized
Content-Type: application/json; charset=UTF-8

{
  "status": "DOWN",
  "error": "Unauthorized",
  "message": "Missing or invalid authorization token"
}
```

#### Failure: Invalid Token (HTTP 401 Unauthorized)
```bash
curl -i http://localhost:8080/health \
  -H "Authorization: Bearer wrong-token"
```

---

### 2. Using Automated Test Script (`test-health.sh`)

While the server is running (or via background):
```bash
./test-health.sh
```

---

### 3. Using the Java Verification Client (`HealthCheckClient.java`)

`HealthCheckClient` runs automated tests (missing token, invalid token, valid token). If the server is not already running, it automatically spins up an in-process instance, tests it, and tears it down:

```bash
# If compiled into out:
java -cp out com.example.health.HealthCheckClient
```

