#!/bin/sh
# Source checkout launcher. Release downloads include their own runtime.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ -x "$root/.venv/bin/python" ]; then
    exec "$root/.venv/bin/python" -B "$root/service.py" "$@"
fi
exec python3 -B "$root/service.py" "$@"
