"""Sign up window, where users can create an account."""
import logging

from PySide2 import QtWidgets, QtCore

from db import dbhelper
from windows import login
from utils import consts, exceptions
from utils.pyside_dynamic import load_ui
from utils.custom_widgets import ClickableLineEdit
from utils.validations import validate_username, validate_pwd, validate_name


class SignUpWindow(QtWidgets.QMainWindow):
    """Window for creating accounts in the application."""

    def __init__(self, parent: QtWidgets.QMainWindow = None,
                 database: dbhelper.DBHelper = None,
                 pos: QtCore.QPoint = None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.database = database

        # Load UI
        custom_widgets = {"ClickableLineEdit": ClickableLineEdit}
        load_ui(str(consts.UI_PATH / "signup.ui"), self, custom_widgets,
                str(consts.UI_PATH))

        # Set fixed size and disable arrows to resize
        self.setFixedSize(670, 370)
        self.setWindowFlags(
            QtCore.Qt.Window | QtCore.Qt.MSWindowsFixedSizeDialogHint)

        # Buttons
        self.line_edit_username.clicked.connect(self.label_message.clear)
        self.line_edit_name.clicked.connect(self.label_message.clear)
        self.line_edit_password.clicked.connect(self.label_message.clear)

        self.pushButton_signup.clicked.connect(self.insert_user)
        self.pushButton_login.clicked.connect(self.to_login)

        # Move to the same position as the previous window
        if pos:
            self.move(pos)

    def insert_user(self):
        """Create new user in the database."""

        user = self.line_edit_username.text()
        password = self.line_edit_password.text()
        name = self.line_edit_name.text()

        validations = {
            "username": validate_username(user),
            "password": validate_pwd(password),
            "name": validate_name(name)}

        if all(validations.values()):
            try:
                self.database.create_user(user, password, name)
            except exceptions.DatabaseError as e:
                self.label_message.setText("Internal error.")
                logging.warning(e.message)

            except exceptions.ValidationError as e:
                self.label_message.setText(
                    f"Invalid field {', '.join(e.columns)}")
                logging.debug(f"`{e.columns}` - {e.message}")

            except exceptions.UsernameExistsError as e:
                self.label_message.setText(f"User {user} already exists.")
                logging.debug(e.message)

            else:
                self.label_message.setText("User created. You can login now.")
                logging.info(f"`{user}`'s info inserted in the database.")
                self.line_edit_username.clear()
                self.line_edit_password.clear()
                self.line_edit_name.clear()

        elif not validations['username']:
            self.label_message.setText("Invalid username (min. 5 characters).")
            logging.debug("The username entered is too short.")

        elif not validations['password']:
            self.label_message.setText("Weak password (min. 8 characters).")
            logging.debug("The password entered is too weak.")

        elif not validations['name']:
            self.label_message.setText(
                "Please enter full name (min. 2 words).")
            logging.debug("The name entered is too short.")

    def to_login(self):
        """Close current window and show new one."""

        window = login.LoginWindow(
            None, database=self.database, pos=self.pos())

        self.close()
        window.show()
