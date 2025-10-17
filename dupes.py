from sqlite3 import connect
from sqlite3 import Error


conn = connect(r"/Users/markschaver/GitHub/Anonymous/anon.db")
curs = conn.cursor()

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

SQL_statements = [
    "DELETE FROM anon WHERE link LIKE '%https://apnews.com/author/%';",
    "DELETE FROM anon WHERE link LIKE '%https://finance.yahoo.com/sectors/%';",
    "DELETE FROM anon WHERE link LIKE '%https://finance.yahoo.com/q/h%';",
    "DELETE FROM anon WHERE link LIKE '%https://finance.yahoo.com/q?%';",
    "DELETE FROM anon WHERE link LIKE '%https://finance.yahoo.com/quote/%';",
    "DELETE FROM anon WHERE link LIKE '%https://finance.yahoo.com/quotes/%';",
    "DELETE FROM anon WHERE link LIKE '%https://finance.yahoo.com/topic/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.axios.com/authors/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.cbsnews.com/detroit/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.cbsnews.com/feature/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.cnn.com/videos/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.newsweek.com/topic/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.nytimes.com/by/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.nytimes.com/search%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.nytimes.com/spotlight/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.nytimes.com/topic/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.politico.com/morningeducation/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.politico.com/morningtax/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.politico.com/morningtech/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.politico.com/newsletters/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.politico.com/playbook%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.politico.com/states/new-york/newsletters/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.reuters.com/authors/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.reuters.com/company/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.reuters.com/entity?%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.reuters.com/finance/deals%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.reuters.com/finance/stocks/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.reuters.com/journalists%';",
    "DELETE FROM anon WHERE link = 'https://www.reuters.com/legal/';",
    "DELETE FROM anon WHERE link LIKE '%https://www.reuters.com/news/archive%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.washingtonpost.com/people/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.wsj.com/livecoverage/%';",
    "DELETE FROM anon WHERE link = 'https://abcnews.go.com/Politics';",
    "DELETE FROM anon WHERE link LIKE '%https://abcnews.go.com/alerts/%';",
    "DELETE FROM anon WHERE link = 'https://www.axios.com/politics-policy';",
    "DELETE FROM anon WHERE link LIKE '%https://www.cbsnews.com/chicago/tag/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.chicagotribune.com/author/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.nytimes.com/international/section/education%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.nytimes.com/international/section/politics%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.nytimes.com/section/education%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.nytimes.com/the-daily%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.reuters.com/business/energy/pipelines-transport/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.reuters.com/business/energy/refining/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.reuters.com/sustainability/human-rights/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.reuters.com/sustainability/regulatory-oversight/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.reuters.com/technology/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.reuters.com/world/germany/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.reuters.com/world/immigration/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.reuters.com/world/us/california/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.sfchronicle.com/author/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.startribune.com/sports/%';",
    "DELETE FROM anon WHERE link LIKE '%https://www.startribune.com/author/%';",
    "DELETE FROM anon WHERE link = 'https://www.latimes.com/oe-howtosubmitoped-story.html';",
    "DELETE FROM anon WHERE link = 'https://www.latimes.com/espanol/politica';",
    "DELETE FROM anon WHERE link = 'https://www.propublica.org/';",
    "DELETE FROM anon WHERE link = 'https://www.sfchronicle.com/us-world/us/';",
    "DELETE FROM anon WHERE link LIKE '%https://www.washingtonpost.com/local/dc/%';",
    "DELETE FROM anon WHERE link = 'https://www.washingtontimes.com/topics/hamas/';",
]

for statement in SQL_statements:
    curs.execute(statement)
    conn.commit()
    print("Executed!")

conn.close()
