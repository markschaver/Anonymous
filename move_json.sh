#!/usr/bin/env bash
set -euo pipefail

SRC="/Users/markschaver/GitHub/Anonymous/json"
DST="/Users/markschaver/GitHub/Archive/Anonymous/json"

# 1. Ensure the destination exists
mkdir -p "$DST"                          # creates DST if missing  [oai_citation:0‡linuxize.com](https://linuxize.com/post/how-to-create-directories-in-linux-with-the-mkdir-command/?utm_source=chatgpt.com)

# 2. Move all .json files
mv "$SRC"/*.json "$DST"/