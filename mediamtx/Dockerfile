FROM alpine:3.21

RUN apk add --no-cache ca-certificates

WORKDIR /mediamtx

COPY mediamtx /mediamtx/mediamtx
COPY mediamtx.yml /mediamtx/mediamtx.yml

RUN chmod +x /mediamtx/mediamtx \
    && addgroup -S lowuser && adduser -S lowuser -G lowuser

USER lowuser

EXPOSE 8554 8889 9997

CMD ["/mediamtx/mediamtx"]