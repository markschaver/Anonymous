import sqlite3
import re

DB_PATH = 'anon.db'

# Matches "1 days ago ... ...", … up to "24 days ago ... ...", plus everything after.
import re

pattern = re.compile(
    r'\b(?:'
      r'(?:[1-9]|1[0-9]|2[0-4])\s+(?:day|hour)s?'
      r'|'
      r'(?:[1-9]|[1-5][0-9])\s+minutes?'
    r')\s+ago\s*<b>\.\.\.<\/b>',
    flags=re.IGNORECASE
)

def clean_content(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute('SELECT rowid, content FROM anon')
    for row in cur.fetchall():
        original = row['content']
        cleaned = pattern.sub('', original).strip()
        if cleaned != original:
            cur.execute(
                'UPDATE anon SET content = ? WHERE rowid = ?',
                (cleaned, row['rowid'])
            )

    conn.commit()
    conn.close()

if __name__ == '__main__':
    clean_content(DB_PATH)
    print("Content cleaned.")