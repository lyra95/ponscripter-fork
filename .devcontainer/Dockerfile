FROM ghcr.io/astral-sh/uv:0.13.8 AS uv

FROM registry.gitlab.steamos.cloud/steamrt/sniper/sdk@sha256:bb30053d3cd19d35c76ae69b2790dbaa1430448006f8240cb6d7e723f2d1940e

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install --yes --no-install-recommends autoconf automake libtool \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /uvx /usr/local/bin/

ENV CMAKE_GENERATOR=Ninja \
    SMPEG2_PATH=/opt/ponscripter-deps \
    STEAM_SDK_ROOT=/opt/steamworks-sdk \
    UV_PROJECT_ENVIRONMENT=/opt/venvs/ponscripter-yomigana \
    UV_CACHE_DIR=/opt/uv-cache
