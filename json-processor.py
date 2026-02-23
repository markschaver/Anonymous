import json
import os
import html
import configparser
from datetime import date, datetime
import re
from sqlite3 import connect
from sqlite3 import Error

config = configparser.ConfigParser()
config.read("/Users/markschaver/.config/anonymous/config.ini")
YOUR_ID = config.get("Configuration", "id")
YOUR_KEY = config.get("Configuration", "key")

conn = connect(r"anon.db")
curs = conn.cursor()
today = date.today()
input_dir = "json/"
invalid_log_path = "invalid-dates.log"


bold_tag = re.compile(r"<b>", re.MULTILINE)
pub_date = re.compile(r".*(\d\d\d\d)/(\d\d)/(\d\d).*", re.MULTILINE)


def update_database(results_json):
    item_source = results_json[0]
    item_phrase = results_json[1]
    item_title = results_json[2]
    item_link = results_json[3]
    item_snippet = results_json[4]
    publish_date = results_json[5]
    insert_values = [item_source,
                     item_phrase,
                     item_title,
                     item_link,
                     item_snippet,
                     today,
                     publish_date]
    # Skip entries with invalid date values for today or publish_date.
    if not (is_valid_date(today) and is_valid_date(publish_date)):
        log_invalid_date(item_link, today, publish_date)
        print("Skipping. Invalid date for today or publish_date.")
        return
    match = re.search(
        bold_tag,
        item_snippet)  # Skip entries with no phrase in summary
    if match:
        try:
            curs.execute("INSERT INTO anon VALUES (?, ?, ?, ?, ?, ?, ?)",
                         insert_values)
            conn.commit()
            print("New entry inserted in the database.")
        except Error as e:
            print("Oops: ", e.args[0])
    else:
        print("Skipping. No anonymous phrase in the entry.")


def is_valid_date(value):
    if isinstance(value, date):
        return True
    if not value:
        return False
    # Accept Unix epoch timestamps (seconds) as valid date values.
    if isinstance(value, (int, float)):
        try:
            datetime.utcfromtimestamp(float(value))
            return True
        except (OverflowError, OSError, ValueError):
            return False
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return False
        if re.fullmatch(r"-?\d+(?:\.\d+)?", stripped):
            try:
                datetime.utcfromtimestamp(float(stripped))
                return True
            except (OverflowError, OSError, ValueError):
                return False
        try:
            datetime.strptime(stripped, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    return False


def log_invalid_date(item_link, today_value, publish_date_value):
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = (
        f"{timestamp}\turl={item_link}\t"
        f"today={today_value}\tpublish_date={publish_date_value}\n"
    )
    with open(invalid_log_path, "a", encoding="utf-8") as log_file:
        log_file.write(entry)


def process_search_results(results_json):
    try:
        item_count = results_json["queries"]["request"][0]["count"]
        for i in range(item_count):
            try:
                item_source = results_json["items"][i]["displayLink"]
                if item_source == 'apnews.com':
                    item_source = re.sub('apnews.com', 'www.apnews.com', item_source)
                item_phrase = results_json["queries"]["request"][0]["searchTerms"]
                item_title = results_json["items"][i]["title"]
                item_link = results_json["items"][i]["link"]
                item_snippet = html.unescape(results_json["items"][i]["htmlSnippet"])
                try:
                    item_published = results_json['items'][i]['pagemap']['newsarticle'][0]['datepublished']
                except KeyError:
                    pass
                try:
                    item_published = results_json['items'][i]['pagemap']['metatags'][0]['article:published']
                except KeyError:
                    pass
                try:
                    item_published = results_json['items'][i]['pagemap']['article'][0]['datepublished']
                except KeyError:
                    pass
                try:
                    item_published = results_json['items'][i]['pagemap']['metatags'][0]['date']
                except KeyError:
                    pass
                try:
                    item_published = results_json['items'][i]['pagemap']['metatags'][0]['iso-8601-publish-date']
                except KeyError:
                    pass
                try:
                    item_published = results_json['items'][i]['pagemap']['metatags'][0]['analyticsattributes.articledate']
                except KeyError:
                    pass
                try:
                    item_published = results_json['items'][i]['pagemap']['metatags'][0]['sailthru.date']
                except KeyError:
                    pass
                try:
                    item_published = results_json['items'][i]['pagemap']['metatags'][0]['article:published_time']
                except KeyError:
                    pass
                try:
                    item_published = results_json['items'][i]['pagemap']['metatags'][0]['dc.date']
                except KeyError:
                    pass
                if 'washingtonpost' in item_link:
                    pub_match = re.search(
                        pub_date,
                        item_link)
                    if pub_match:
                        item_published = pub_match[1] + '-' + pub_match[2] + '-' + pub_match[3]
                    else:
                        pass
                if 'usatoday' in item_link:
                    pub_match = re.search(
                        pub_date,
                        item_link)
                    if pub_match:
                        item_published = pub_match[1] + '-' + pub_match[2] + '-' + pub_match[3]
                    else:
                        pass
                publish_date_parsed = re.sub(r'(\d\d\d\d-\d\d-\d\d).*', r'\1', item_published)
                db_fields = [item_source, item_phrase, item_title, item_link, item_snippet, publish_date_parsed]
                update_database(db_fields)
            except KeyError:
                continue
    except Exception:
        print("There were no matches in this query.")


dir_files = os.listdir(input_dir)
for file in dir_files:
    try:
        # Try UTF-8 first
        with open(input_dir + file, encoding="utf-8") as f:
            json_string = json.load(f)
    except UnicodeDecodeError:
        try:
            # If UTF-8 fails, try Latin-1
            with open(input_dir + file, encoding="latin-1") as f:
                json_string = json.load(f)
        except Exception as e:
            print(f"Error processing file {file}: {str(e)}")
            continue
    process_search_results(json_string)

conn.close()
