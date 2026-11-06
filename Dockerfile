# The base digest is resolved and recorded in docs/toolchain.json.
FROM python:3.13-slim-bookworm@sha256:a5a7017efc5969e00ae2b91c8eb0631049a569652aa4ffc4501769049ae45c72 AS healthy
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app
COPY requirements.txt ./
RUN pip install --no-cache-dir --require-hashes -r requirements.txt
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
