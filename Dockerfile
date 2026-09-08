# syntax=docker/dockerfile:1
# Registry digests verified 2026-09-08. BuildKit selects the platform manifest.
FROM ghcr.io/astral-sh/uv:0.12.5@sha256:e85be844203885286c60ffad8a858d48afb6c5a5c237ca0e67f12e74b8f174b1 AS uv
FROM python:3.12.14-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254 AS python-base

# Git supplies repository provenance and explicit benchmark preparation.
# libgomp supplies the OpenMP runtime used by optional CPU numerical packages.
RUN apt-get update \
    && apt-get install --no-install-recommends -y ca-certificates git libgomp1 \
    && rm -rf /var/lib/apt/lists/*

FROM python-base AS build-common
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=0 \
    UV_LINK_MODE=copy
WORKDIR /build
COPY pyproject.toml uv.lock README.md ./

FROM build-common AS build-base
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project
COPY src/ ./src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

FROM build-common AS build-dense
# The dense extra resolves Torch from the CPU index already recorded in uv.lock.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --extra dense --no-install-project
COPY src/ ./src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --extra dense --no-editable

FROM python-base AS runtime
RUN groupadd --gid 10001 sacr \
    && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin sacr \
    && mkdir -p /app/artifacts/cache \
    && chown -R 10001:10001 /app/artifacts
ENV PATH="/opt/venv/bin:$PATH" \
    HOME=/home/sacr \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    XDG_CACHE_HOME=/app/artifacts/cache \
    HF_HOME=/app/artifacts/cache/huggingface \
    TOKENIZERS_PARALLELISM=false
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY configs/ ./configs/
COPY benchmarks/ ./benchmarks/
COPY scripts/ ./scripts/
COPY tests/fixtures/sample_repo/ ./tests/fixtures/sample_repo/
USER 10001:10001
ENTRYPOINT ["sacr"]
CMD ["--help"]

# Opt in explicitly: docker build --target dense -t sacr:dense .
FROM runtime AS dense
COPY --from=build-dense /opt/venv /opt/venv

# Keep the last stage lean so an ordinary docker build never installs Torch.
FROM runtime AS base
COPY --from=build-base /opt/venv /opt/venv
