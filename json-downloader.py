import json
import os
import time
import configparser
from datetime import date
from random import randint
from time import sleep
from urllib import parse

import requests


DEFAULT_CONFIG_PATH = os.path.expanduser("~/.config/anonymous/config.ini")
CONFIG_PATH = os.environ.get("ANON_CONFIG", DEFAULT_CONFIG_PATH)
OUTPUT_DIR = "json/"
PHRASES_EVEN = "anonymous-phrases-even.txt"
PHRASES_ODD = "anonymous-phrases-odd.txt"
SLEEP_RANGE = (10, 30)


def load_config(path=CONFIG_PATH):
    config = configparser.ConfigParser()
    config.read(path)
    return (
        config.get("Configuration", "id"),
        config.get("Configuration", "key"),
    )


def get_phrase_file(today):
    if today.day % 2 == 0:
        print("It's an even day.")
        return PHRASES_EVEN
    print("It's an odd day.")
    return PHRASES_ODD


def encode_phrase(unencoded_phrase):
    encoded_phrase = parse.quote_plus(unencoded_phrase.strip())
    print("Encoded phrase: " + encoded_phrase)
    return encoded_phrase


def get_url(query, google_id, google_key):
    base = 'https://www.googleapis.com/customsearch/v1?q='
    restrict = "&dateRestrict=d2"
    exact = "&" + query
    language = "&hl=en"
    alt = "&alt=json"
    request_url = base + query + google_id + restrict + exact + language + google_key + alt
    print("Request url: " + request_url)
    return request_url


def get_json(search_url, output_dir=OUTPUT_DIR):
    filename = output_dir + time.strftime("%Y%m%d-%H%M%S") + ".json"
    response = requests.get(search_url)
    with open(filename, "w") as f:
        json.dump(response.json(), f)


def pause_search(sleep_range=SLEEP_RANGE):
    print("Sleeping...")
    sleep(randint(*sleep_range))


def main():
    google_id, google_key = load_config()
    today = date.today()
    phrase_path = get_phrase_file(today)
    with open(phrase_path) as phrases:
        for phrase in phrases:
            encoded = encode_phrase(phrase)
            url = get_url(encoded, google_id, google_key)
            pause_search()
            get_json(url)


if __name__ == "__main__":
    main()
