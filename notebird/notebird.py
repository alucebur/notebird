"""Notebird, a desktop app for managing users' notes."""
import logging
import argparse

from PySide2 import QtWidgets

from db import helpers
from utils import consts
from windows import login


def main(argv):
    # Initialize logging
    format = "%(asctime)-15s %(levelname)s: %(message)s"
    logging.basicConfig(format=format, level=logging.DEBUG)

    # Initialize database
    db = helpers.connect_to_database(consts.DB_NAME)
    helpers.setup_database(db)

    # Initialize GUI
    app = QtWidgets.QApplication([])

    # Load and apply stylesheet
    if argv.dark:
        with open(consts.STYLESHEET) as f:
            style = f.read()
        app.setStyleSheet(style)

    # Show login  window
    window = login.LoginWindow(database=db)
    window.show()
    app.exec_()

    # Close database connection
    helpers.close_database_connection(db)

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Notebird, a desktop app for managing users' HTML notes.",
        allow_abbrev=False)
    parser.add_argument("-d", "--dark", action="store_true",
                        help="apply dark stylesheet")
    args = parser.parse_args()

    # Run the app
    main(args)
