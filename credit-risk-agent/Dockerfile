# Use Python 3.10
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install OpenTelemetry packages
RUN pip install --no-cache-dir \
    opentelemetry-distro \
    opentelemetry-exporter-otlp \
    opentelemetry-instrumentation-logging \
    opentelemetry-instrumentation-requests \
    opentelemetry-instrumentation

# Install vistora instrumentation
COPY vistora_instrumentation /tmp/vistora-instrumentation/vistora_instrumentation
RUN printf "%s\n" \
  "[build-system]" \
  "requires = [\"setuptools>=68\", \"wheel\"]" \
  "build-backend = \"setuptools.build_meta\"" \
  "" \
  "[project]" \
  "name = \"vistora-instrumentation\"" \
  "version = \"0.1.0\"" \
  "requires-python = \">=3.10\"" \
  "" \
  "[tool.setuptools]" \
  "packages = [\"vistora_instrumentation\"]" \
  > /tmp/vistora-instrumentation/pyproject.toml

RUN pip install --no-cache-dir /tmp/vistora-instrumentation

# Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

EXPOSE 8101

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8101"]