"""Notebird, a desktop app to manage users' notes."""
import logging

from PySide2 import QtWidgets

from db import helpers
from utils import consts
from windows import login


def main():
    # Initialize logging
    format = "%(asctime)-15s %(levelname)s: %(message)s"
    logging.basicConfig(format=format, level=logging.DEBUG)

    # Initialize database
    db = helpers.connect_to_database(consts.DB_NAME)
    helpers.setup_database(db)

    # Initialize GUI and show
    app = QtWidgets.QApplication([])
    window = login.LoginWindow(database=db)
    window.show()
    app.exec_()

    # Close database connection
    helpers.close_database_connection(db)

if __name__ == "__main__":
    main()
