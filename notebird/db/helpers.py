"""Helper functions to start and close database connections."""
import time
import logging

from db import dbhelper
from utils import exceptions


def connect_to_database(database: str) -> dbhelper.DBHelper:
    """Connect to the given database."""
    while True:
        try:
            db = dbhelper.DBHelper(database)
        except exceptions.DatabaseError as e:
            logging.critical(e.message)

            # Try to reconnect after 2 seconds
            time.sleep(2)
            continue
        break
    logging.info(f"Connected to `{database}`.")
    return db


def setup_database(db: dbhelper.DBHelper):
    """Create tables and indexes if they don't exist."""
    try:
        db.setup()
    except exceptions.DatabaseError as e:
        logging.critical(e.message)


def close_database_connection(db: dbhelper.DBHelper):
    """Close connection with the database."""
    while True:
        try:
            db.conn.close()
        except exceptions.DatabaseError as e:
            logging.critical(e.message)

            # Try to disconnect again after 2 seconds
            time.sleep(2)
            continue
        break
    logging.info(f"Disconnected from `{db.name}`.")
