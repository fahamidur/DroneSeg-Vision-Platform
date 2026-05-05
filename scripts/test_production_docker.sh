#!/usr/bin/env bash
set -euo pipefail

docker build -t droneseg-hf .
docker run --rm -p 7860:7860 droneseg-hf
