FROM alpine:3.21

ARG TARGETARCH
RUN apk add --no-cache ca-certificates curl

WORKDIR /mediamtx

RUN case "$TARGETARCH" in \
      amd64) MTX_ARCH="amd64" ;; \
      arm64) MTX_ARCH="arm64v8" ;; \
      *) echo "Unsupported architecture: $TARGETARCH" && exit 1 ;; \
    esac \
    && curl -L -o mediamtx.tar.gz "https://github.com/bluenviron/mediamtx/releases/download/v1.9.1/mediamtx_v1.9.1_linux_${MTX_ARCH}.tar.gz" \
    && tar -xzf mediamtx.tar.gz mediamtx \
    && rm mediamtx.tar.gz \
    && chmod +x mediamtx

COPY mediamtx.yml /mediamtx/mediamtx.yml

RUN addgroup -S lowuser && adduser -S lowuser -G lowuser
USER lowuser

EXPOSE 8554 8889 9997
CMD ["/mediamtx/mediamtx"]