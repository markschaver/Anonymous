#!/usr/bin
import json
import time
import datetime
from datetime import date
import configparser
from random import randint
from time import sleep
from urllib import parse
import os
import html
import re
from sqlite3 import connect
from sqlite3 import Error
import requests

config = configparser.ConfigParser()
config.read("config.ini")
YOUR_ID = config.get("Configuration", "id")
YOUR_KEY = config.get("Configuration", "key")

conn = connect(r"/var/www/html/anonymous/anon.db")
curs = conn.cursor()
today = date.today()

input_dir = '/var/www/html/anonymous/json/'
output_dir = '/var/www/html/anonymous/json/'
phrases = open("/var/www/html/anonymous/phrases.txt")


def encode_phrase(unencoded_phrase):
    unencoded_phrase = unencoded_phrase.strip()
    encoded_phrase = parse.quote_plus(unencoded_phrase)
    print("Encoded phrase: " + encoded_phrase)
    return encoded_phrase


def get_url(query):
    base = 'https://www.googleapis.com/customsearch/v1?q='
    google_id = YOUR_ID
    restrict = "&dateRestrict=d5"
    exact = "&" + query
    language = "&hl=en"
    google_key = YOUR_KEY
    alt = "&alt=json"
    request_url = (base +
                   query +
                   google_id +
                   restrict +
                   exact +
                   language +
                   google_key +
                   alt)
    print("Request url: " + request_url)
    return request_url


def get_json(search_url):
    filename = output_dir + time.strftime("%Y%m%d-%H%M%S") + ".json"
    r = requests.get(search_url)
    f = open(filename, "w")
    json_str = json.dumps(r.json())
    f.write(json_str)
    f.close()


def pause_search():
    # Delay queries randomly to avoid being blocked
    print("Sleeping...")
    sleep(randint(10, 20))


for phrase in phrases:
    phrase = encode_phrase(phrase)
    url = get_url(phrase)
    pause_search()
    get_json(url)


bold_tag = re.compile(r"<b>", re.MULTILINE)
pub_date = re.compile(r".*(\d\d\d\d)/(\d\d)/(\d\d).*", re.MULTILINE)


def validate(date_text):
    try:
        datetime.datetime.strptime(date_text, '%Y-%m-%d')
        return True
    except ValueError:
        pass
        # raise ValueError("Incorrect data format, should be YYYY-MM-DD")


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
    match = re.search(
        bold_tag,
        item_snippet)  # Skip entries with no phrase in summary
    if match:
        if validate(publish_date):
            try:
                curs.execute("INSERT INTO anon VALUES (?, ?, ?, ?, ?, ?, ?)",
                             insert_values)
                conn.commit()
                print("New entry inserted in the database.")
            except Error as e:
                print("Oops: ", e.args[0])
        else:
            pass
    else:
        print("Skipping. No anonymous phrase in the entry.")


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
    with open(input_dir + file, encoding="utf8") as f:
        json_string = json.load(f)
    process_search_results(json_string)


try:
    curs.execute('DELETE '
                 'FROM anon '
                 'WHERE ROWID '
                 'NOT IN '
                 '(SELECT min(ROWID) '
                 'FROM anon '
                 'GROUP BY source, content)')
    conn.commit()
    print("Cursor executed!")
except Error as e:
    print("Oops, duplicate content deletion didn't work: ", e.args[0])

try:
    curs.execute('DELETE '
                 'FROM anon '
                 'WHERE ROWID '
                 'NOT IN '
                 '(SELECT min(ROWID) '
                 'FROM anon '
                 'GROUP BY source, title)')
    conn.commit()
    print("Cursor executed!")
except Error as e:
    print("Oops, duplicate title deletion didn't work: ", e.args[0])

try:
    curs.execute('DELETE '
                 'FROM anon '
                 'WHERE ROWID '
                 'NOT IN '
                 '(SELECT min(ROWID) '
                 'FROM anon '
                 'GROUP BY source, link)')
    conn.commit()
    print("Cursor executed!")
except Error as e:
    print("Oops, duplicate link deletion didn't work: ", e.args[0])

SQL_statements = ["DELETE FROM anon WHERE link LIKE '%http://www.nytimes.com/by%';",
                  "DELETE FROM anon WHERE link LIKE '%https://apnews.com/RogerStone%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.axios.com/authors%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.cnn.com/videos/%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.nytimes.com/search%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.politico.com/morningeducation%';",
                  "DELETE FROM anon WHERE link LIKE '%https://abcnews.go.com/WN%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.reuters.com/journalists%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.politico.com/morningtax%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.politico.com/morningtech%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.politico.com/newsletters%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.politico.com/states/new-york/newsletters%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.cnbc.com/vladimir-putin%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.cnbc.com/mario-draghi%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.cnbc.com/private-equity-and-hedge-funds%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.cnbc.com/biotech-and-pharmaceuticals%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.cnbc.com/ipos%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.washingtonpost.com/people%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.wsj.com/livecoverage%';"]


for statement in SQL_statements:
    curs.execute(statement)
    conn.commit()
    print("Executed!")

conn.close()
