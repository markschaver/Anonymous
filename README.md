# Anonymous Source Tracker

Tracks examples of anonymous-source phrasing ("a source familiar with...",
"a person briefed on the matter", etc.) across major English-language
news outlets. Runs daily Google Custom Search queries, stores hits in a
local SQLite database, and renders a static site from the results.

## Pipeline

```
json-downloader.py   # query Google Custom Search, save raw JSON
json-processor.py    # parse JSON, insert rows into anon.db
dupes.py             # dedupe and apply URL blocklist
convert_epoch.py     # normalize epoch timestamps to ISO dates
clean_snippet.py     # strip "X hours ago" preambles from snippets
app.py build         # freeze the Flask app to a static site
```

## Setup

1. Install dependencies:

   ```sh
   uv sync
   ```

2. Create a config file at `~/.config/anonymous/config.ini` (or set
   `ANON_CONFIG=/path/to/config.ini`):

   ```ini
   [Configuration]
   id = &cx=YOUR_GOOGLE_CSE_ID
   key = &key=YOUR_GOOGLE_API_KEY
   destination = /absolute/path/to/freeze/output
   per_page = 25
   ga_id =                ; optional Google Analytics measurement ID
   ```

   Note the `id` and `key` values include the leading query-string
   fragments (`&cx=`, `&key=`) — they are concatenated raw into the
   request URL.

3. Initialize the database from `anonymous.sql` (the `CREATE TABLE`
   statement near the bottom).

## Running

```sh
uv run python json-downloader.py    # fetch today's results
uv run python json-processor.py     # ingest into anon.db
uv run python dupes.py
uv run python clean_snippet.py
uv run python app.py build          # freeze static site to FREEZER_DESTINATION
```

For local development of the Flask app:

```sh
ANON_DEBUG=1 uv run python app.py
# defaults to 127.0.0.1:8080; override with ANON_HOST / ANON_PORT
```

## Environment variables

| Variable        | Purpose                                            |
| --------------- | -------------------------------------------------- |
| `ANON_CONFIG`   | Path to `config.ini` (default `~/.config/...`)     |
| `ANON_DB`       | Path to `anon.db` (default: alongside the scripts) |
| `ANON_HOST`     | Flask bind host (default `127.0.0.1`)              |
| `ANON_PORT`     | Flask port (default `8080`)                        |
| `ANON_DEBUG`    | Set to `1` to enable Werkzeug debugger             |
| `ANON_GA_ID`    | Google Analytics measurement ID (overrides config) |
| `ANON_JSON_SRC` | Source dir for `move_json.sh`                      |
| `ANON_JSON_DST` | Destination dir for `move_json.sh`                 |

## Tests

```sh
uv run pytest -q
```

The route tests in `tests/test_routes.py` snapshot the rendered HTML.
Re-run with `UPDATE_SNAPSHOTS=1` after intentional template or data
changes.

## Security

The static site is the intended output. Don't serve `app.py` directly to
untrusted clients — `content` and `title` columns are rendered with
Jinja's `|safe` because they hold HTML snippets returned by Google.

## License

MIT — see [LICENSE](LICENSE).
