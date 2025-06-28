from sqlite3 import connect
import configparser
import csv

config = configparser.ConfigParser()
config.read("config.ini")


CSV_FILE = config.get("Configuration", "csv")


def writecsvfile():

    conn = connect(r"anon.db")
    curs = conn.cursor()

    f = open(CSV_FILE,
             'w',
             encoding='utf-8')

    def clean_content(content):
        content = content.strip()
        content = content.replace('\n', ' ').replace('\r', '')
        content = content.replace('\t', '')
        content = content.replace('<b>...</b>', '...')
        content = content.replace('<br>', '')
        return content

    w = csv.writer(f, lineterminator='\n')

    titles = ['LINK', 'SOURCE', 'PHRASE', 'TITLE', 'CONTENT', 'DATE_ENTERED']
    w.writerow(titles)
    curs.execute('SELECT * FROM anon')
    for row in curs.fetchall():
        new_row = [clean_content(row[0]),
                   clean_content(row[1]),
                   clean_content(row[2]),
                   clean_content(row[3]),
                   clean_content(row[4]),
                   clean_content(row[5])]
        w.writerow(new_row)

    f.close()
    conn.close()


writecsvfile()
