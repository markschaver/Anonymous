from sqlite3 import connect
from sqlite3 import Error


conn = connect(r"/Users/markschaver/Library/CloudStorage/OneDrive-Personal/Code/anonymous/anon.db")
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

SQL_statements = ["DELETE FROM anon WHERE link LIKE '%http://www.nytimes.com/by/%';",
                  "DELETE FROM anon WHERE link = 'https://apnews.com/RogerStone';",
                  "DELETE FROM anon WHERE link = 'https://finance.yahoo.com/news/';",
                  "DELETE FROM anon WHERE link LIKE '%https://finance.yahoo.com/q/h%';",
                  "DELETE FROM anon WHERE link LIKE '%https://finance.yahoo.com/quote/%';",
                  "DELETE FROM anon WHERE link LIKE '%https://finance.yahoo.com/q?%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.axios.com/authors/%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.cnn.com/videos/%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.nytimes.com/search%';",
                  "DELETE FROM anon WHERE link = 'https://www.politico.com/morningeducation/';",
                  "DELETE FROM anon WHERE link = 'https://www.politico.com/morningtax/';",
                  "DELETE FROM anon WHERE link = 'https://www.politico.com/morningtech/';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.politico.com/newsletters/%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.politico.com/states/new-york/newsletters/%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.reuters.com/entity?%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.reuters.com/finance/stocks/%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.reuters.com/journalists%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.reuters.com/news/archive%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.reuters.com/finance/deals%';",
                  "DELETE FROM anon WHERE link = '%https://www.washingtonpost.com/people/%';",
                  "DELETE FROM anon WHERE link LIKE '%https://www.wsj.com/livecoverage/%';"]

for statement in SQL_statements:
    curs.execute(statement)
    conn.commit()
    print("Executed!")

conn.close()
