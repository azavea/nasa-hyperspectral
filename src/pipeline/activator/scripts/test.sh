#!/bin/bash

set -e

if [[ -n "${NASA_HSI_DEBUG}" ]]; then
    set -x
fi

function usage() {
    echo -n \
        "Usage: $(basename "$0")
Run tests for Python activators.
"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    if [[ "${1:-}" == "--help" ]]; then
        usage
    else
        python -m unittest discover tests/
    fi
fi
