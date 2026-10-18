FROM python:3.11-slim AS builder

WORKDIR /install
COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install --prefix=/install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app


WORKDIR /app
RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser


COPY --from=builder /install /usr/local

COPY server ./server
COPY data ./data
COPY scripts ./scripts

RUN mkdir -p /app/data \
    && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000



HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"


CMD ["uvicorn", "server.mcp_server:app", "--host", "0.0.0.0", "--port", "8000"]