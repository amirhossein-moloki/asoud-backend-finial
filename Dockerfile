FROM docker.arvancloud.ir/library/python:3.12-slim

# Skip rust installation and other related dependencies
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CRYPTOGRAPHY_DONT_BUILD_RUST=1

WORKDIR /asoud

# Install runtime and build dependencies
RUN set -ex \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       g++ \
       libffi-dev \
       libxml2-dev \
       libxslt1-dev \
       libjpeg-dev \
       zlib1g-dev \
       gettext \
       netcat-openbsd \
       libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# copy requirements aGQoLJDZHx
COPY ./requirements.txt /asoud/requirements.txt

# Create python's env and install Django's dependencies
RUN set -ex \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /asoud/requirements.txt \
    && pip install --no-cache-dir psutil

# TODO: Add a non-root user for better security
# RUN addgroup -S appgroup && adduser -S appuser -G appgroup
# USER appuser

COPY . /asoud

ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

# Ensure the entrypoint is executable
RUN chmod +x /asoud/entrypoint.sh

# Ensure the logs directory exists and is writable
RUN mkdir -p /asoud/logs && chmod -R 755 /asoud/logs

# run entrypoint.sh
ENTRYPOINT ["/asoud/entrypoint.sh"]
