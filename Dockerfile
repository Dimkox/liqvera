# syntax=docker/dockerfile:1@sha256:87999aa3d42bdc6bea60565083ee17e86d1f3339802f543c0d03998580f9cb89

FROM golang:1.26.5-alpine3.23@sha256:622e56dbc11a8cfe87cafa2331e9a201877271cbff918af53d3be315f3da88cc AS verify
WORKDIR /src

COPY go.mod ./
RUN --mount=type=cache,target=/go/pkg/mod go mod download

COPY . .
RUN files="$(gofmt -l .)" && test -z "$files" && \
    go vet ./... && \
    go test -cover ./...

FROM verify AS build
ARG VERSION=dev
ARG COMMIT=unknown
RUN --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=linux go build -trimpath \
    -ldflags="-s -w -X main.version=${VERSION} -X main.commit=${COMMIT}" \
    -o /out/engine ./cmd/engine

FROM alpine:3.23.3@sha256:25109184c71bdad752c8312a8623239686a9a2071e8825f20acb8f2198c3f659 AS production
WORKDIR /app

RUN addgroup -S -g 10001 engine && \
    adduser -S -D -H -u 10001 -G engine engine

COPY --from=build --chown=10001:10001 /out/engine /usr/local/bin/engine

ENV ENGINE_MODE=shadow \
    HTTP_ADDR=:8080

USER 10001:10001
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["wget", "--no-verbose", "--tries=1", "--spider", "http://127.0.0.1:8080/healthz"]

ENTRYPOINT ["/usr/local/bin/engine"]
