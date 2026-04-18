from sqlite3 import connect, Error


DB_PATH = "/Users/markschaver/GitHub/Anonymous/anon.db"

# For each column, keep the lowest ROWID in each (source, <column>) group.
DEDUP_COLUMNS = ['content', 'title', 'link']

# URL fragments; a row is deleted if its link contains any of these anywhere.
BLOCKLIST_LIKE = [
    'https://apnews.com/author/',
    'https://finance.yahoo.com/sectors/',
    'https://finance.yahoo.com/q/h',
    'https://finance.yahoo.com/q?',
    'https://finance.yahoo.com/quote/',
    'https://finance.yahoo.com/quotes/',
    'https://finance.yahoo.com/topic/',
    'https://www.axios.com/authors/',
    'https://www.cbsnews.com/detroit/',
    'https://www.cbsnews.com/feature/',
    'https://www.cnn.com/videos/',
    'https://www.newsweek.com/topic/',
    'https://www.nytimes.com/by/',
    'https://www.nytimes.com/search',
    'https://www.nytimes.com/spotlight/',
    'https://www.nytimes.com/topic/',
    'https://www.politico.com/morningeducation/',
    'https://www.politico.com/morningtax/',
    'https://www.politico.com/morningtech/',
    'https://www.politico.com/newsletters/',
    'https://www.politico.com/playbook',
    'https://www.politico.com/states/new-york/newsletters/',
    'https://www.reuters.com/authors/',
    'https://www.reuters.com/company/',
    'https://www.reuters.com/entity?',
    'https://www.reuters.com/finance/deals',
    'https://www.reuters.com/finance/stocks/',
    'https://www.reuters.com/journalists',
    'https://www.reuters.com/news/archive',
    'https://www.washingtonpost.com/people/',
    'https://www.wsj.com/livecoverage/',
    'https://abcnews.go.com/alerts/',
    'https://www.cbsnews.com/chicago/tag/',
    'https://www.chicagotribune.com/author/',
    'https://www.nytimes.com/international/section/education',
    'https://www.nytimes.com/international/section/politics',
    'https://www.nytimes.com/section/education',
    'https://www.nytimes.com/the-daily',
    'https://www.reuters.com/business/energy/pipelines-transport/',
    'https://www.reuters.com/business/energy/refining/',
    'https://www.reuters.com/sustainability/human-rights/',
    'https://www.reuters.com/sustainability/regulatory-oversight/',
    'https://www.reuters.com/technology/',
    'https://www.reuters.com/world/germany/',
    'https://www.reuters.com/world/immigration/',
    'https://www.reuters.com/world/us/california/',
    'https://www.sfchronicle.com/author/',
    'https://www.startribune.com/sports/',
    'https://www.startribune.com/author/',
    'https://www.washingtonpost.com/local/dc/',
]

# Full-URL exact matches.
BLOCKLIST_EXACT = [
    'https://www.reuters.com/legal/',
    'https://abcnews.go.com/Politics',
    'https://www.axios.com/politics-policy',
    'https://www.latimes.com/oe-howtosubmitoped-story.html',
    'https://www.latimes.com/espanol/politica',
    'https://www.propublica.org/',
    'https://www.sfchronicle.com/us-world/us/',
    'https://www.washingtontimes.com/topics/hamas/',
]


def delete_duplicates(conn, column):
    try:
        conn.execute(
            f"DELETE FROM anon WHERE ROWID NOT IN "
            f"(SELECT min(ROWID) FROM anon GROUP BY source, {column})"
        )
        conn.commit()
        print(f"Deduped by {column}.")
    except Error as e:
        print(f"Oops, duplicate {column} deletion didn't work: ", e.args[0])


def delete_blocklisted(conn):
    for fragment in BLOCKLIST_LIKE:
        conn.execute("DELETE FROM anon WHERE link LIKE ?", (f"%{fragment}%",))
    for url in BLOCKLIST_EXACT:
        conn.execute("DELETE FROM anon WHERE link = ?", (url,))
    conn.commit()
    print(f"Deleted blocklisted URLs ({len(BLOCKLIST_LIKE) + len(BLOCKLIST_EXACT)} patterns).")


def main(db_path=DB_PATH):
    conn = connect(db_path)
    try:
        for column in DEDUP_COLUMNS:
            delete_duplicates(conn, column)
        delete_blocklisted(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
