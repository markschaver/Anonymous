#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${ANON_JSON_SRC:-$SCRIPT_DIR/json}"
DST="${ANON_JSON_DST:-$SCRIPT_DIR/../Archive/Anonymous/json}"

# 1. Ensure the destination exists
mkdir -p "$DST"                          # creates DST if missing  [oai_citation:0‡linuxize.com](https://linuxize.com/post/how-to-create-directories-in-linux-with-the-mkdir-command/?utm_source=chatgpt.com)

# 2. Move all .json files
mv "$SRC"/*.json "$DST"/
