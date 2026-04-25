import json
import os
import html
from datetime import date, datetime, timezone
import re
from sqlite3 import connect, Error

INPUT_DIR = "json/"
INVALID_LOG_PATH = "invalid-dates.log"
DB_PATH = "anon.db"

bold_tag = re.compile(r"<b>", re.MULTILINE)
pub_date_re = re.compile(r".*(\d\d\d\d)/(\d\d)/(\d\d).*", re.MULTILINE)

# Substring of displayLink -> canonical source stored in the DB.
# Checked in order; last match wins (same as the original stacked ifs).
SOURCE_OVERRIDES = {
    'nytimes.com': 'www.nytimes.com',
    'washingtonpost.com': 'www.washingtonpost.com',
    'abcnews.go.com': 'abcnews.go.com',
    'nbcnews.com': 'www.nbcnews.com',
    'foxnews.com': 'www.foxnews.com',
    'apnews.com': 'www.apnews.com',
    'bloomberg.com': 'www.bloomberg.com',
    'usatoday.com': 'www.usatoday.com',
    'wsj.com': 'www.wsj.com',
    'politico.com': 'www.politico.com',
    'cnn.com': 'www.cnn.com',
    'cbsnews.com': 'www.cbsnews.com',
    'cnbc.com': 'www.cnbc.com',
    'mcclatchydc.com': 'www.mcclatchydc.com',
    'reuters.com': 'www.reuters.com',
    'msnbc.com': 'www.msnbc.com',
    'theguardian.com': 'www.theguardian.com',
    'time.com': 'time.com',
    'newsweek.com': 'www.newsweek.com',
    'msn.com': 'www.msn.com',
    'bbc.com': 'www.bbc.com',
    'nypost.com': 'nypost.com',
    'latimes.com': 'www.latimes.com',
    'axios.com': 'www.axios.com',
    'yahoo.com': 'www.yahoo.com',
    'startribune.com': 'www.startribune.com',
    'ft.com': 'www.ft.com',
    'sfchronicle.com': 'www.sfchronicle.com',
    'propublica.org': 'www.propublica.org',
    'chicagotribune.com': 'www.chicagotribune.com',
    'vox.com': 'www.vox.com',
    'washingtonexaminer.com': 'www.washingtonexaminer.com',
    'washingtontimes.com': 'www.washingtontimes.com',
    'theglobeandmail.com': 'www.theglobeandmail.com',
    'theaustralian.com.au': 'www.theaustralian.com.au',
    'thehill.com': 'thehill.com',
    'npr.org': 'www.npr.org',
    'newsday.com': 'www.newsday.com',
}

# Paths into item['pagemap'] where a publish date might live.
# Checked in order; LAST successful lookup wins (matches original stacked try/except/pass).
PUB_DATE_PATHS = [
    ('newsarticle', 0, 'datepublished'),
    ('metatags', 0, 'article:published'),
    ('article', 0, 'datepublished'),
    ('metatags', 0, 'date'),
    ('metatags', 0, 'iso-8601-publish-date'),
    ('metatags', 0, 'analyticsattributes.articledate'),
    ('metatags', 0, 'sailthru.date'),
    ('metatags', 0, 'article:published_time'),
    ('metatags', 0, 'dc.date'),
]


def normalize_source(item_source):
    for needle, replacement in SOURCE_OVERRIDES.items():
        if needle in item_source:
            item_source = replacement
    return item_source


def extract_publish_date(item):
    pagemap = item.get('pagemap', {})
    item_published = None
    for path in PUB_DATE_PATHS:
        try:
            value = pagemap
            for key in path:
                value = value[key]
            item_published = value
        except (KeyError, IndexError, TypeError):
            continue
    return item_published


def is_valid_date(value):
    if isinstance(value, date):
        return True
    if not value:
        return False
    if isinstance(value, (int, float)):
        try:
            datetime.fromtimestamp(float(value), tz=timezone.utc)
            return True
        except (OverflowError, OSError, ValueError):
            return False
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return False
        if re.fullmatch(r"-?\d+(?:\.\d+)?", stripped):
            try:
                datetime.fromtimestamp(float(stripped), tz=timezone.utc)
                return True
            except (OverflowError, OSError, ValueError):
                return False
        try:
            datetime.strptime(stripped, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    return False


def log_invalid_date(item_link, today_value, publish_date_value, log_path=INVALID_LOG_PATH):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = (
        f"{timestamp}\turl={item_link}\t"
        f"today={today_value}\tpublish_date={publish_date_value}\n"
    )
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(entry)


def update_database(conn, today, fields):
    item_source, item_phrase, item_title, item_link, item_snippet, publish_date = fields
    if not (is_valid_date(today) and is_valid_date(publish_date)):
        log_invalid_date(item_link, today, publish_date)
        print("Skipping. Invalid date for today or publish_date.")
        return
    if not bold_tag.search(item_snippet):
        print("Skipping. No anonymous phrase in the entry.")
        return
    today_str = today.isoformat() if isinstance(today, date) else today
    try:
        conn.execute(
            "INSERT INTO anon VALUES (?, ?, ?, ?, ?, ?, ?)",
            [item_source, item_phrase, item_title, item_link, item_snippet, today_str, publish_date],
        )
        conn.commit()
        print("New entry inserted in the database.")
    except Error as e:
        print("Oops: ", e.args[0])


def process_search_results(conn, today, results_json):
    try:
        item_count = results_json["queries"]["request"][0]["count"]
        item_phrase = results_json["queries"]["request"][0]["searchTerms"]
    except (KeyError, IndexError):
        print("There were no matches in this query.")
        return

    for i in range(item_count):
        try:
            item = results_json["items"][i]
            item_source = normalize_source(item["displayLink"])
            item_title = item["title"]
            item_link = item["link"]
            item_snippet = html.unescape(item["htmlSnippet"])
        except (KeyError, IndexError):
            continue

        item_published = extract_publish_date(item)
        if 'washingtonpost' in item_link or 'usatoday' in item_link:
            match = pub_date_re.search(item_link)
            if match:
                item_published = f"{match[1]}-{match[2]}-{match[3]}"

        if item_published is None:
            continue

        publish_date_parsed = re.sub(r'(\d\d\d\d-\d\d-\d\d).*', r'\1', item_published)
        update_database(
            conn,
            today,
            [item_source, item_phrase, item_title, item_link, item_snippet, publish_date_parsed],
        )


def load_json_file(filepath):
    try:
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    except UnicodeDecodeError:
        with open(filepath, encoding="latin-1") as f:
            return json.load(f)


def main(input_dir=INPUT_DIR, db_path=DB_PATH):
    conn = connect(db_path)
    today = date.today()
    try:
        for filename in os.listdir(input_dir):
            filepath = os.path.join(input_dir, filename)
            try:
                data = load_json_file(filepath)
            except Exception as e:
                print(f"Error processing file {filename}: {e}")
                continue
            process_search_results(conn, today, data)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
