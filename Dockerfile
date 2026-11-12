# syntax=docker/dockerfile:1

# One image for every host: Home Assistant on a Raspberry Pi (arm64), a NAS or a PC (amd64).
# GitHub builds it (.github/workflows/release.yml), so Docker is not needed on a
# development PC.

ARG PYTHON_IMAGE=python:3.13-slim
ARG UV_VERSION=0.13.7

# uv installs the Python packages. It is only borrowed while building and is not part of
# the final image. Two copies are needed: one for the processor of the build machine and
# one for the processor the image is built for.
FROM --platform=$BUILDPLATFORM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv-build
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv-target


# ---- Stage 1: build the styles and collect the static files --------------------------
# The result is the same for every processor, so this stage runs on the build machine's
# own processor even when the image is being built for a Raspberry Pi.
FROM --platform=$BUILDPLATFORM ${PYTHON_IMAGE} AS assets
WORKDIR /app
ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    BLABTODO_DATA_DIR=/tmp/blabtodo-build \
    BLABTODO_DEBUG=0
COPY pyproject.toml uv.lock .python-version ./
RUN --mount=from=uv-build,source=/uv,target=/bin/uv \
    uv sync --frozen --no-dev
COPY . .
RUN .venv/bin/python manage.py tailwind build \
 && .venv/bin/python manage.py collectstatic --noinput


# ---- Stage 2: the image that runs -----------------------------------------------------
FROM ${PYTHON_IMAGE} AS runtime
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    BLABTODO_DATA_DIR=/data \
    BLABTODO_DEBUG=0

COPY pyproject.toml uv.lock .python-version ./
RUN --mount=from=uv-target,source=/uv,target=/bin/uv \
    uv sync --frozen --no-dev

# Every Django app folder must be listed here. The checks on GitHub start the image and
# request a page, so a forgotten folder is caught before a release.
COPY manage.py ./
COPY config/ config/
COPY household/ household/
COPY people/ people/
COPY templates/ templates/
COPY locale/ locale/
COPY --from=assets /app/staticfiles/ staticfiles/

ARG BLABTODO_VERSION=dev
ENV BLABTODO_VERSION=${BLABTODO_VERSION}

# The database, photos and backups. The host keeps this folder; the image never does.
VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/', timeout=4)"]

# Bring the database up to date, then serve. One process with a few threads is plenty for
# a household and keeps memory use low.
CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 1 --threads 4 --access-logfile -"]
