FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
        | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list \
        -o /etc/apt/sources.list.d/microsoft-prod.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
        msodbcsql18 \
        unixodbc \
    && curl -fsSL https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem \
        -o /tmp/aws-rds-global-bundle.pem \
    && awk '/-----BEGIN CERTIFICATE-----/ { archivo=sprintf("/usr/local/share/ca-certificates/aws-rds-%d.crt", ++contador) } archivo { print > archivo }' \
        /tmp/aws-rds-global-bundle.pem \
    && update-ca-certificates \
    && rm -f /tmp/aws-rds-global-bundle.pem \
    && rm -rf /var/lib/apt/lists/* \
    && adduser \
    --disabled-password \
    --gecos "" \
    --no-create-home \
    --uid 10001 \
    appuser

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
