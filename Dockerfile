FROM python:3.12-alpine@sha256:c5ba3deef00c7758561a0f03c26f44f10589263d40e732b8748e0d1f38f6dd89
WORKDIR /srv/gateway
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ARG BUILD_REF=dev
ENV BUILD_REF=${BUILD_REF} HTTP_PORT=8080 SERVICE_STATE=maintenance
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY gateway.py ./
USER 12540:12540
EXPOSE 8080
CMD ["python", "gateway.py"]
