#!/usr/bin/env bash
set -e
uv run json-downloader.py
uv run json-processor.py
uv run dupes.py
uv run convert_epoch.py anon.db anon date_published
uv run clean_snippet.py
uv run app.py build
./move_json.sh
cd /Users/markschaver/Library/CloudStorage/OneDrive-Personal/markschaver.github.io/
./auto_commit.sh "Update" master
