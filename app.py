from flask import Flask, render_template, g, current_app, request, abort
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
config.read("config.ini")
FREEZER_DESTINATION = config.get("Configuration", "destination")
PER_PAGE = config.get("Configuration", "per_page")
PER_PAGE = int(PER_PAGE)


app = Flask(__name__)
app.config['FREEZER_DESTINATION'] = FREEZER_DESTINATION
app.config.from_object(__name__)
app.config['FREEZER_RELATIVE_URLS'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
freezer = Freezer(app)
extra_bold = re.compile(r"</b>.*?<b>", re.MULTILINE)


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


def get_outlet_names():
    g.db = connect_db()
    names = query_db("SELECT DISTINCT name FROM outlets ORDER BY name")
    g.db.close()
    return names


def get_total_anon_pages():
    g.db = connect_db()
    results = query_db("SELECT count(*) FROM anon", '', one=True)
    total = int(next(iter(results.values())))
    num_pages = total / PER_PAGE
    num_pages = math.ceil(num_pages)
    g.db.close()
    return num_pages


def get_total_outlet_pages(outlet_url):
    g.db = connect_db()
    results = query_db("SELECT count(*) FROM anon WHERE source = ?", (outlet_url,), one=True)
    total = int(next(iter(results.values())))
    num_pages = total / PER_PAGE
    num_pages = math.ceil(num_pages)
    g.db.close()
    return num_pages


def get_articles():
    g.db = connect_db()
    results = query_db("SELECT source, date_published, title FROM anon")
    g.db.close()
    return results


# --------------------------------------------------------------------
# TEMPLATE FILTERS
# --------------------------------------------------------------------
@app.template_filter('datetimeformat')
def datetimeformat(value, date_format='%B %e, %Y'):
    if(value):
        d = datetime.strptime(value, '%Y-%m-%d')
        return d.strftime(date_format)
    else:
        return abort(404)


@app.template_filter('clean_content')
def clean_content(content):
    if(content):
        content = content.strip()
        content = content.replace('\n', ' ').replace('\r', '')
        content = content.replace('<b>...</b>', '...')
        content = content.replace('<br>', '')
        content = content.replace(chr(0x01), '')
        content = re.sub(extra_bold, "\1 ", content)
        return content
    else:
        return abort(404)


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


def get_page_items():
    page = int(request.args.get('page', 1))
    per_page = request.args.get('per_page')
    if not per_page:
        per_page = PER_PAGE
    else:
        per_page = int(per_page)
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
    pages = get_total_anon_pages()
    for page in range(1, int(pages) + 1):
        yield 'index_pages', {'page': str(page)}


@freezer.register_generator
def outlet_pages():
    outlet_urls = get_outlet_urls()
    for outlet_url in outlet_urls:
        pages = get_total_outlet_pages(outlet_url['url'])
        outlet_name = get_outlet_name(outlet_url['url'])
        # TODO: Fix spurious pages-not-frozen error
        for page in range(1, int(pages) + 1):
            page_url = '/outlet/' + outlet_name + '/page/' + str(page) + '/'
            yield page_url

# --------------------------------------------------------------------
# ROUTES
# --------------------------------------------------------------------
@app.route('/')
def index():
    total = query_db('SELECT count(*) FROM anon', '', one=True)
    page, per_page, offset = get_page_items()
    results = query_db('SELECT anon.source, '
                       'outlets.name, '
                       'anon.phrase, '
                       'anon.title, '
                       'anon.link, '
                       'anon.content, '
                       'anon.date_published '
                       'FROM '
                       'anon '
                       'LEFT OUTER JOIN '
                       'outlets '
                       'ON '
                       'anon.source = outlets.url '
                       'ORDER BY '
                       'date_published DESC '
                       'LIMIT ?, ?', (offset, per_page))
    outlets = query_db("SELECT DISTINCT "
                       "outlets.name, "
                       "outlets.url "
                       "FROM outlets "
                       "JOIN anon "
                       "ON outlets.url = anon.source "
                       "ORDER BY outlets.name")
    pagination = get_pagination(page=page,
                                per_page=per_page,
                                total=next(iter(total.values())),
                                format_total=True,
                                format_number=True,
                                display_msg='',
                                href='/anonymous/page/{0}/'
                                )
    return render_template('index.html',
                           entries=results,
                           page=page,
                           per_page=per_page,
                           outlets=outlets,
                           pagination=pagination)


@app.route('/page/<int:page>/')
def index_pages(page):
    per_page = request.args.get('per_page')
    if not per_page:
        per_page = PER_PAGE
    else:
        per_page = int(per_page)
    offset = (page - 1) * per_page
    total = query_db('SELECT count(*) FROM anon', '', one=True)
    results = query_db('SELECT anon.source, '
                       'outlets.name, '
                       'anon.phrase, '
                       'anon.title, '
                       'anon.link, '
                       'anon.content, '
                       'anon.date_published '
                       'FROM '
                       'anon '
                       'LEFT OUTER JOIN '
                       'outlets '
                       'ON '
                       'anon.source = outlets.url '
                       'ORDER BY '
                       'date_published DESC '
                       'LIMIT ?, ?', (offset, per_page))
    outlets = query_db("SELECT DISTINCT "
                       "outlets.name, "
                       "outlets.url "
                       "FROM outlets "
                       "JOIN anon "
                       "ON outlets.url = anon.source "
                       "ORDER BY outlets.name")
    pagination = get_pagination(page=page,
                                per_page=per_page,
                                total=next(iter(total.values())),
                                format_total=True,
                                format_number=True,
                                display_msg='',
                                href='/anonymous/page/{0}/'
                                )
    return render_template('index.html',
                           entries=results,
                           page=page,
                           per_page=per_page,
                           outlets=outlets,
                           pagination=pagination)

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


@app.route('/outlet/<outlet_name>/')
def outlet(outlet_name):
    masthead = parse.unquote_plus(outlet_name)
    outlet_url = get_outlet_url(outlet_name)
    total = query_db(
        'SELECT count(*) '
        'FROM anon '
        'LEFT OUTER JOIN outlets ON anon.source = outlets.url '
        'WHERE anon.source = ?',
        (outlet_url,), one=True)
    page, per_page, offset = get_page_items()
    results = query_db("SELECT "
                       "anon.link, "
                       "outlets.name, "
                       "anon.source, "
                       "anon.phrase, "
                       "anon.title, "
                       "anon.content, "
                       "anon.date_published "
                       "FROM "
                       "anon "
                       "LEFT OUTER JOIN outlets "
                       "ON anon.source = outlets.url "
                       "WHERE anon.source = ? "
                       "ORDER BY anon.date_published DESC "
                       "LIMIT ?, ?", (outlet_url, offset, per_page))
    outlets = query_db("SELECT DISTINCT "
                       "outlets.name, "
                       "outlets.url "
                       "FROM outlets "
                       "JOIN anon "
                       "ON outlets.url = anon.source "
                       "ORDER BY outlets.name")
    pagination = get_pagination(page=page,
                                per_page=per_page,
                                total=next(iter(total.values())),
                                format_total=True,
                                format_number=True,
                                display_msg='',
                                href="/anonymous/outlet/" + outlet_name + "/page/{0}/"
                                )
    return render_template('outlet.html',
                           entries=results,
                           page=page,
                           per_page=per_page,
                           masthead=masthead,
                           outlets=outlets,
                           pagination=pagination)


@app.route('/outlet/<outlet_name>/page/<int:page>/')
def outlet_pages(outlet_name, page):
    masthead = parse.unquote_plus(outlet_name)
    outlet_url = get_outlet_url(outlet_name)
    total = query_db(
        'SELECT count(*) '
        'FROM anon '
        'LEFT OUTER JOIN outlets ON anon.source = outlets.url '
        'WHERE anon.source = ?',
        (outlet_url,), one=True)
    per_page = request.args.get('per_page')
    if not per_page:
        per_page = PER_PAGE
    else:
        per_page = int(per_page)
    offset = (page - 1) * per_page
    results = query_db("SELECT "
                       "anon.link, "
                       "outlets.name, "
                       "anon.source, "
                       "anon.phrase, "
                       "anon.title, "
                       "anon.content, "
                       "anon.date_published "
                       "FROM "
                       "anon "
                       "LEFT OUTER JOIN outlets "
                       "ON anon.source = outlets.url "
                       "WHERE anon.source = ? "
                       "ORDER BY anon.date_published DESC "
                       "LIMIT ?, ?", (outlet_url, offset, per_page))
    outlets = query_db("SELECT DISTINCT "
                       "outlets.name, "
                       "outlets.url "
                       "FROM outlets "
                       "JOIN anon "
                       "ON outlets.url = anon.source "
                       "ORDER BY outlets.name")
    pagination = get_pagination(page=page,
                                per_page=per_page,
                                total=next(iter(total.values())),
                                format_total=True,
                                format_number=True,
                                display_msg='',
                                href="/anonymous/outlet/" + outlet_name + "/page/{0}/"
                                )
    return render_template('outlet.html',
                           entries=results,
                           page=page,
                           per_page=per_page,
                           masthead=masthead,
                           outlets=outlets,
                           pagination=pagination)


@app.route('/mentions/')
def mentions():
    return render_template('mentions.html')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        freezer.freeze()
    else:
        app.run(host='0.0.0.0', debug=True)

