FROM debian:stable-slim

ARG USER=factorio
ARG GROUP=factorio
ARG PUID=845
ARG PGID=845

ENV PORT=34197 \
    RCON_PORT=27015 \
    SAVES=/factorio/saves \
    CONFIG=/factorio/config \
    MODS=/factorio/mods \
    SCENARIOS=/factorio/scenarios \
    SCRIPTOUTPUT=/factorio/script-output \
    PUID="$PUID" \
    PGID="$PGID"

SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

RUN set -ox pipefail \
    && mkdir -p /opt /factorio \
    && apt-get -q update \
    && apt-get --no-install-recommends -qy install binutils curl file gettext jq pwgen xz-utils python3 python3-dateutil python3-requests \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system --gid "$PGID" "$GROUP" \
    && adduser --system --uid "$PUID" --gid "$PGID" --no-create-home --disabled-password --shell /bin/sh "$USER"

COPY files/root /

VOLUME /factorio
EXPOSE $PORT/udp $RCON_PORT/tcp
ENTRYPOINT ["/docker-entrypoint.sh"]

# version checksum of the archive to download
ARG VERSION
ARG SHA256

LABEL factorio.version=${VERSION} \
      factorio.sha256=${SHA256}

ENV VERSION=${VERSION} \
    SHA256=${SHA256}

RUN set -ox pipefail \
    && if [[ "${VERSION}" == "" ]]; then \
        echo "build-arg VERSION is required" \
        && exit 1; \
    fi \
    && if [[ "${SHA256}" == "" ]]; then \
        echo "build-arg SHA256 is required" \
        && exit 1; \
    fi \
    && archive="/tmp/factorio_headless_x64_$VERSION.tar.xz" \
    && curl -sSL "https://www.factorio.com/get-download/$VERSION/headless/linux64" -o "$archive" \
    && echo "$SHA256  $archive" | sha256sum -c \
    || (sha256sum "$archive" && file "$archive" && exit 1) \
    && tar xf "$archive" --directory /opt \
    && chmod ugo=rwx /opt/factorio \
    && rm "$archive" \
    && ln -s "$SCENARIOS" /opt/factorio/scenarios \
    && ln -s "$SAVES" /opt/factorio/saves \
    && mkdir -p /opt/factorio/config/ \
    && chown -R "$USER":"$GROUP" /opt/factorio /factorio

COPY files/config.ini /opt/factorio/config/config.ini

ARG GITREV=unknown
LABEL factorio-docker.revision=${GITREV}
