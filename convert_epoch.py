#!/usr/bin/env python3

import re
import sqlite3
import datetime
import argparse


_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_identifier(name, kind):
    if not _IDENT_RE.fullmatch(name):
        raise ValueError(f"Invalid {kind} name: {name!r}")
    return name


def convert_epoch_to_iso_date(db_path, table, column):
    """
    Connect to the SQLite database at db_path, read each row’s epoch timestamp
    in `table`.`column`, convert to ISO 8601 date (YYYY-MM-DD), write it back.
    """
    table = _validate_identifier(table, "table")
    column = _validate_identifier(column, "column")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch each row’s internal rowid and the epoch value
    cursor.execute(f"SELECT rowid, {column} FROM {table}")
    for rowid, epoch in cursor.fetchall():
        try:
            epoch_int = int(epoch)
        except (ValueError, TypeError):
            # Skip values that aren’t valid integer timestamps
            continue

        # Convert to date-only ISO 8601 (YYYY-MM-DD)
        iso_date = datetime.datetime.utcfromtimestamp(epoch_int).date().isoformat()

        # Update the row
        cursor.execute(
            f"UPDATE {table} SET {column} = ? WHERE rowid = ?",
            (iso_date, rowid)
        )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert epoch timestamps to ISO 8601 date (YYYY-MM-DD) in a SQLite database."
    )
    parser.add_argument("db_path", help="Path to the SQLite .db file.")
    parser.add_argument("table",   help="Name of the table containing the timestamps.")
    parser.add_argument("column",  help="Name of the column with epoch timestamps.")
    args = parser.parse_args()

    convert_epoch_to_iso_date(args.db_path, args.table, args.column)
