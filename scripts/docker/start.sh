#!/bin/sh

set -eu

nginx_pid=""
uvicorn_pid=""

cleanup() {
    if [ -n "${nginx_pid}" ] && kill -0 "${nginx_pid}" 2>/dev/null; then
        kill "${nginx_pid}" 2>/dev/null || true
    fi

    if [ -n "${uvicorn_pid}" ] && kill -0 "${uvicorn_pid}" 2>/dev/null; then
        kill "${uvicorn_pid}" 2>/dev/null || true
    fi
}

trap cleanup INT TERM

python backend/main.py &
uvicorn_pid="$!"

nginx -g 'daemon off;' &
nginx_pid="$!"

while true; do
    if ! kill -0 "${uvicorn_pid}" 2>/dev/null; then
        break
    fi

    if ! kill -0 "${nginx_pid}" 2>/dev/null; then
        break
    fi

    sleep 1
done

cleanup
exit 1
