from flask import Flask, render_template, g, current_app, request
from flask_paginate import Pagination
from sqlite3 import connect
from datetime import datetime
import re
import urllib
from urllib import parse
from flask_frozen import Freezer
import sys
import configparser
import math


# --------------------------------------------------------------------
# CONFIGURATION
# --------------------------------------------------------------------
config = configparser.ConfigParser()
config.read("/Users/markschaver/.config/anonymous/config.ini")
FREEZER_DESTINATION = config.get("Configuration", "destination")
PER_PAGE = config.getint("Configuration", "per_page")


app = Flask(__name__)
app.config['FREEZER_DESTINATION'] = FREEZER_DESTINATION
app.config.from_object(__name__)
app.config['FREEZER_RELATIVE_URLS'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
freezer = Freezer(app)
extra_bold = re.compile(r"</b>.*?<b>", re.MULTILINE)


# --------------------------------------------------------------------
# SQL
# --------------------------------------------------------------------
ENTRIES_SELECT = (
    "SELECT anon.source, outlets.name, anon.phrase, anon.title, "
    "anon.link, anon.content, anon.date_published "
    "FROM anon LEFT OUTER JOIN outlets ON anon.source = outlets.url"
)
OUTLETS_IN_USE = (
    "SELECT DISTINCT outlets.name, outlets.url "
    "FROM outlets JOIN anon ON outlets.url = anon.source "
    "ORDER BY outlets.name"
)
COUNT_ANON = "SELECT count(*) AS n FROM anon"
COUNT_ANON_BY_SOURCE = "SELECT count(*) AS n FROM anon WHERE source = ?"


# --------------------------------------------------------------------
# DATABASE
# --------------------------------------------------------------------
def connect_db():
    return connect("anon.db")


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()


def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv


def get_outlet_url(outlet_name):
    outlet_name = parse.unquote_plus(outlet_name)
    outlet_url = query_db(
        "SELECT url FROM outlets WHERE name = ?",
        (outlet_name,),
        one=True)
    return outlet_url['url']


def get_outlet_name(outlet_url):
    outlet_url = parse.unquote_plus(outlet_url)
    g.db = connect_db()
    results = query_db(
        "SELECT name FROM outlets WHERE url= ?",
        (outlet_url,),
        one=True)
    name = results['name']
    name = plus_for_spaces(name)
    g.db.close()
    return name


def get_page_info(source, pub_date, title):
    results = query_db(
        "SELECT source, title, link, content, date_published FROM anon WHERE source = ? AND title = ? AND date_published = ?",
        (source, title, pub_date), one=True)
    return results


def get_outlet_urls():
    g.db = connect_db()
    urls = query_db("SELECT DISTINCT url FROM outlets ORDER BY url")
    g.db.close()
    return urls


def get_total_anon_pages():
    g.db = connect_db()
    results = query_db(COUNT_ANON, one=True)
    g.db.close()
    return math.ceil(results['n'] / PER_PAGE)


def get_total_outlet_pages(outlet_url):
    g.db = connect_db()
    results = query_db(COUNT_ANON_BY_SOURCE, (outlet_url,), one=True)
    g.db.close()
    return math.ceil(results['n'] / PER_PAGE)


# --------------------------------------------------------------------
# TEMPLATE FILTERS
# --------------------------------------------------------------------
@app.template_filter('datetimeformat')
def datetimeformat(value, date_format='%B %e, %Y'):
    if not value:
        return ''
    return datetime.strptime(value, '%Y-%m-%d').strftime(date_format)


@app.template_filter('clean_content')
def clean_content(content):
    if not content:
        return ''
    content = content.strip()
    content = content.replace('\n', ' ').replace('\r', '')
    content = content.replace('<b>...</b>', '...')
    content = content.replace('<br>', '')
    content = content.replace(chr(0x01), '')
    content = re.sub(extra_bold, " ", content)
    return content


@app.template_filter('plus_for_spaces')
def plus_for_spaces(content):
    content = urllib.parse.quote_plus(content)
    return content


# --------------------------------------------------------------------
# PAGINATOR FUNCTIONS
# --------------------------------------------------------------------
def get_css_framework():
    return current_app.config.get('CSS_FRAMEWORK', 'bootstrap3')


def get_link_size():
    return current_app.config.get('LINK_SIZE', 'sm')


def show_single_page_or_not():
    return current_app.config.get('SHOW_SINGLE_PAGE', False)


def get_page_items(page=None):
    if page is None:
        page = int(request.args.get('page', 1))
    per_page = request.args.get('per_page')
    per_page = int(per_page) if per_page else PER_PAGE
    offset = (page - 1) * per_page
    return page, per_page, offset


def get_pagination(**kwargs):
    kwargs.setdefault('record_name', 'records')
    return Pagination(css_framework=get_css_framework(),
                      link_size=get_link_size(),
                      show_single_page=show_single_page_or_not(),
                      **kwargs)


# --------------------------------------------------------------------
# URL GENERATORS
# --------------------------------------------------------------------
@freezer.register_generator
def index_pages():
    yield '/'
    for page in range(1, get_total_anon_pages() + 1):
        yield f'/page/{page}/'


@freezer.register_generator
def outlet_pages():
    for outlet_url in get_outlet_urls():
        pages = get_total_outlet_pages(outlet_url['url'])
        outlet_name = get_outlet_name(outlet_url['url'])
        yield f'/outlet/{outlet_name}/'
        # TODO: Fix spurious pages-not-frozen error
        for page in range(1, pages + 1):
            yield f'/outlet/{outlet_name}/page/{page}/'

# --------------------------------------------------------------------
# ROUTES
# --------------------------------------------------------------------
@app.route('/', defaults={'page': None})
@app.route('/page/<int:page>/')
def index(page):
    page, per_page, offset = get_page_items(page)
    total = query_db(COUNT_ANON, one=True)
    results = query_db(
        f"{ENTRIES_SELECT} ORDER BY date_published DESC LIMIT ?, ?",
        (offset, per_page),
    )
    outlets = query_db(OUTLETS_IN_USE)
    pagination = get_pagination(
        page=page,
        per_page=per_page,
        total=total['n'],
        format_total=True,
        format_number=True,
        display_msg='',
        href='/anonymous/page/{0}/',
    )
    return render_template(
        'index.html',
        entries=results,
        page=page,
        per_page=per_page,
        outlets=outlets,
        pagination=pagination,
    )

# TODO: Fix function so outlet name has to match
# TODO: Try doing search on parameters without article ID
@app.route('/article/<string:outlet>/<pub_date>/<title>/')
def article(outlet, pub_date, title):
    outlet_url = get_outlet_url(outlet)
    title = parse.unquote_plus(title)
    results = get_page_info(outlet_url, pub_date, title)
    masthead = parse.unquote_plus(outlet)
    return render_template('article.html',
                           masthead=masthead,
                           results=results)


@app.route('/outlet/<outlet_name>/', defaults={'page': None})
@app.route('/outlet/<outlet_name>/page/<int:page>/')
def outlet(outlet_name, page):
    masthead = parse.unquote_plus(outlet_name)
    outlet_url = get_outlet_url(outlet_name)
    page, per_page, offset = get_page_items(page)
    total = query_db(COUNT_ANON_BY_SOURCE, (outlet_url,), one=True)
    results = query_db(
        f"{ENTRIES_SELECT} WHERE anon.source = ? "
        "ORDER BY anon.date_published DESC LIMIT ?, ?",
        (outlet_url, offset, per_page),
    )
    outlets = query_db(OUTLETS_IN_USE)
    pagination = get_pagination(
        page=page,
        per_page=per_page,
        total=total['n'],
        format_total=True,
        format_number=True,
        display_msg='',
        href=f"/anonymous/outlet/{outlet_name}/page/{{0}}/",
    )
    return render_template(
        'outlet.html',
        entries=results,
        page=page,
        per_page=per_page,
        masthead=masthead,
        outlets=outlets,
        pagination=pagination,
    )


@app.route('/mentions/')
def mentions():
    return render_template('mentions.html')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        freezer.freeze()
    else:
        app.run(host='0.0.0.0', debug=True, port=8080)
