FROM postgis/postgis:15-3.4-alpine

ARG PGVECTOR_VERSION=v0.8.0

RUN apk add --no-cache --virtual .pgvector-build-dependencies \
        git \
        build-base \
        postgresql15-dev \
    && git clone \
        --depth 1 \
        --branch ${PGVECTOR_VERSION} \
        https://github.com/pgvector/pgvector.git \
        /tmp/pgvector \
    && make -C /tmp/pgvector with_llvm=no \
    && make -C /tmp/pgvector with_llvm=no install \
    && rm -rf /tmp/pgvector \
    && apk del .pgvector-build-dependencies