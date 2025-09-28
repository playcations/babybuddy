# syntax=docker/dockerfile:1

FROM ghcr.io/linuxserver/baseimage-alpine-nginx:3.20

# set version label
ARG BUILD_DATE
ARG VERSION
ARG BABYBUDDY_VERSION
LABEL build_version="Linuxserver.io version:- ${VERSION} Build-date:- ${BUILD_DATE}"
LABEL maintainer="Baby Buddy Community"

ENV S6_STAGE2_HOOK="/init-hook"

RUN \
  echo "**** install build packages ****" && \
  apk add --no-cache --virtual=build-dependencies \
    build-base \
    jpeg-dev \
    libffi-dev \
    libxml2-dev \
    libxslt-dev \
    mariadb-dev \
    postgresql-dev \
    python3-dev \
    pkgconf \
    gettext \
    zlib-dev \
    nodejs \
    npm && \
  echo "**** install runtime packages ****" && \
  apk add --no-cache \
    jpeg \
    libffi \
    libpq \
    libxml2 \
    libxslt \
    mariadb-connector-c \
    python3 && \
  echo "**** install babybuddy ****" && \
  mkdir -p /app/www/public

# copy our application files instead of downloading from GitHub
COPY . /app/www/public/

# Install Python requirements using LinuxServer approach
RUN \
  cd /app/www/public && \
  python3 -m venv /lsiopy && \
  /lsiopy/bin/pip install -U --no-cache-dir \
    pip \
    wheel && \
  /lsiopy/bin/pip install -U --no-cache-dir --find-links https://wheel-index.linuxserver.io/alpine-3.20/ \
    -r requirements.txt && \
  /lsiopy/bin/pip install -U --no-cache-dir --find-links https://wheel-index.linuxserver.io/alpine-3.20/ \
    mysqlclient && \
  npm install && \
  npx gulp build && \
  BABYBUDDY_USE_PIPENV=0 BABYBUDDY_PYTHON=/lsiopy/bin/python npx gulp compilemessages && \
  rm -rf node_modules && \
  printf "Baby Buddy Community version: ${VERSION}\nBuild-date: ${BUILD_DATE}" > /build_version && \
  echo "**** cleanup build deps ****" && \
  apk del --purge build-dependencies && \
  rm -rf \
    /tmp/* \
    $HOME/.cache \
    $HOME/.cargo

# Set up PATH to use virtual environment (LinuxServer approach)
ENV PATH="/lsiopy/bin:$PATH"

# copy local files
COPY root/ /

# ports and volumes
EXPOSE 8000
VOLUME /config
