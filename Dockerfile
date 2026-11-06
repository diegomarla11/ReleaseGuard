# The base digest is resolved and recorded in docs/toolchain.json.
FROM python:3.13-alpine@sha256:1e1f6334529d1fb26a2ef619d7cffb30a7c7d7cc1cc7338ebee283a58d1aeaca AS healthy
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
RUN addgroup -g 10001 app && adduser -D -H -u 10001 -G app app
COPY requirements.txt ./
# Remove install-only tooling (including bundled ensurepip wheels) from runtime.
RUN pip install --no-cache-dir --require-hashes -r requirements.txt \
    && pip uninstall --yes pip \
    && rm -rf /usr/local/lib/python3.13/ensurepip
COPY --chown=10001:10001 api ./api
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=2s --timeout=2s --start-period=3s --retries=3 \
  CMD python -c "import urllib.request; r=urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=1); assert r.status == 200"
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Intentionally broken targets: isolated laboratory use only.
FROM healthy AS broken-health
COPY --chown=10001:10001 laboratory/broken_health.py /app/broken_health.py
CMD ["python", "-m", "uvicorn", "broken_health:app", "--host", "0.0.0.0", "--port", "8000"]

FROM healthy AS root-user
USER 0:0

# Default build is ALWAYS the healthy, unprivileged application.
FROM healthy AS runtime
