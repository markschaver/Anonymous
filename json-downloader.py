import json
import os
import time
from datetime import date
import configparser
from random import randint
from time import sleep
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

config = configparser.ConfigParser()
config.read("/Users/markschaver/.config/anonymous/config.ini")
YOUR_ID = config.get("Configuration", "id")
YOUR_KEY = config.get("Configuration", "key")

output_dir = 'json/'
failure_log = output_dir + "failures.log"
os.makedirs(output_dir, exist_ok=True)

today = date.today()

# Divide phrases into two days to stay under Google's 100 free queries a day limit
if today.day % 2 == 0:
    # Even
    phrases = open("anonymous-phrases-even.txt")
    print("It's an even day.")
else:
    # Odd
    phrases = open("anonymous-phrases-odd.txt")
    print("It's an odd day.")

# phrases = open("phrases.txt")
# print("Opening phrases...")


def encode_phrase(unencoded_phrase):
    phrase = unencoded_phrase.strip()
    print("Phrase: " + phrase)
    return phrase


def build_request(query):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "cx": YOUR_ID,
        "key": YOUR_KEY,
        "dateRestrict": "d2",
        "hl": "en",
        "alt": "json",
    }
    return url, params


def build_session():
    session = requests.Session()
    retries = Retry(
        total=5,
        connect=5,
        read=3,
        status=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET"]),
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get_json(session, search_url, params):
    filename = output_dir + time.strftime("%Y%m%d-%H%M%S") + ".json"
    try:
        r = session.get(search_url, params=params, timeout=20)
        r.raise_for_status()
        with open(filename, "w") as f:
            json.dump(r.json(), f)
    except requests.exceptions.RequestException as e:
        query = params.get("q", "")
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        error_line = f"{timestamp}\tquery={query}\terror={e}\n"
        print(f"Request failed for query '{query}': {e}")
        with open(failure_log, "a") as log_file:
            log_file.write(error_line)


def pause_search():
    # Delay queries randomly to avoid being blocked
    print("Sleeping...")
    sleep(randint(10, 30))


session = build_session()

for phrase in phrases:
    phrase = encode_phrase(phrase)
    url, params = build_request(phrase)
    pause_search()
    get_json(session, url, params)
