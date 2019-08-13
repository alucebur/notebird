"""Login window to access the application."""
import logging

from PySide2 import QtWidgets, QtCore

from db import helpers, dbhelper
from windows import crud, signup
from utils import consts, exceptions
from utils.pyside_dynamic import load_ui
from utils.custom_widgets import ClickableLineEdit


class LoginWindow(QtWidgets.QMainWindow):
    """Starting window where user can log in or open sign up window."""

    def __init__(self, parent: QtWidgets.QMainWindow = None,
                 database: dbhelper.DBHelper = None,
                 pos: QtCore.QPoint = None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.database = database

        # Load UI
        custom_widgets = {"ClickableLineEdit": ClickableLineEdit}
        load_ui(str(consts.UI_PATH / "login.ui"), self, custom_widgets,
                str(consts.UI_PATH))

        # Set fixed size and disable arrows to resize
        self.setFixedSize(670, 370)
        self.setWindowFlags(
            QtCore.Qt.Window | QtCore.Qt.MSWindowsFixedSizeDialogHint)

        # Buttons
        self.line_edit_username.clicked.connect(self.label_message.clear)
        self.line_edit_password.clicked.connect(self.label_message.clear)

        self.pushButton_login.clicked.connect(self.check_login)
        self.pushButton_signup.clicked.connect(
            lambda: self.to_window(signup.SignUpWindow))

        # Move to the same position as the previous window
        if pos:
            self.move(pos)

    def check_login(self):
        """Identify the user against the database."""

        user = self.line_edit_username.text()
        password = self.line_edit_password.text()

        try:
            user_id = self.database.login(user, password)

        except exceptions.DatabaseError as e:
            self.label_message.setText("Internal error.")
            logging.warning(e.message)

        except exceptions.LoginError as e:
            # Wrong user/password
            self.label_message.setText(e.message)
            logging.warning(f"`{e.username}` - {e.message}")

        else:
            # Correct login
            self.label_message.setText(f"Logged in as {user}.")
            logging.info(f"`{user}` logged in the database.")
            self.database.current_user = {"id": user_id}

            # Close window and show crud
            self.to_window(crud.CrudWindow)

    def to_window(self, new_window: QtWidgets.QMainWindow):
        """Close current window and show new one."""

        window = new_window(None, database=self.database, pos=self.pos())

        self.close()
        window.show()
