"""Crud window, main one, where user interacts with their data."""
import time
import logging
from pathlib import Path

from PIL import Image
from PySide2 import QtWidgets, QtCore, QtGui

from db import dbhelper
from windows import login
from utils import consts, exceptions
from utils.pyside_dynamic import load_ui
from utils.custom_widgets import ClickableLineEdit, ClickablePlainTextEdit
from utils.validations import validate_username, validate_pwd, validate_name


def epoch_to_local_date(timestamp: float):
    """Epoch timestamp to `day/month/year - time` representation."""
    return time.strftime("%d/%b/%Y - %X", time.localtime(int(timestamp)))


class CrudWindow(QtWidgets.QMainWindow):
    """Window where logged user can manage their notes."""

    def __init__(self, parent: QtWidgets.QMainWindow = None,
                 database: dbhelper.DBHelper = None,
                 pos: QtCore.QPoint = None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.database = database

        # Load UI
        custom_widgets = {"ClickableLineEdit": ClickableLineEdit,
                          "ClickablePlainTextEdit": ClickablePlainTextEdit}
        load_ui(str(consts.UI_PATH / "crud.ui"), self, custom_widgets,
                str(consts.UI_PATH))

        # Set fixed size and disable arrows to resize
        self.setFixedSize(670, 370)
        self.setWindowFlags(
            QtCore.Qt.Window | QtCore.Qt.MSWindowsFixedSizeDialogHint)

        # Menu
        self.actionLogout.setShortcut("Ctrl+Q")
        self.actionLogout.setStatusTip("Log out of the application")
        self.actionLogout.triggered.connect(self.logout)

        self.actionNew.setShortcut("Ctrl+N")
        self.actionNew.setStatusTip("Create a new note")
        self.actionNew.triggered.connect(self.new_note)

        self.actionUpdate.setShortcut("Ctrl+E")
        self.actionUpdate.setStatusTip("Update account info")
        self.actionUpdate.triggered.connect(self.update_info)

        self.actionDelete.setShortcut("Ctrl+D")
        self.actionDelete.setStatusTip("Delete account")
        self.actionDelete.triggered.connect(self.delete_account)

        self.actionLicense.setShortcut("Ctrl+L")
        self.actionLicense.setStatusTip("Show license info")
        self.actionLicense.triggered.connect(self.license_info)

        self.actionAbout.setShortcut("Ctrl+A")
        self.actionAbout.setStatusTip("Show app info")
        self.actionAbout.triggered.connect(self.about_info)

        # Inputboxes
        self.username_line_edit.clicked.connect(self.label_message.clear)
        self.name_line_edit.clicked.connect(self.label_message.clear)
        self.pwd_line_edit.clicked.connect(self.label_message.clear)
        self.comment_block.clicked.connect(self.label_message2.clear)

        # Buttons
        self.btn_create.clicked.connect(self.new_note)
        self.btn_discard_note.clicked.connect(self.discard_note)
        self.btn_discard_changes.clicked.connect(self.discard_changes)
        self.btn_upload_avatar.clicked.connect(self.update_avatar)
        self.btn_del_avatar.clicked.connect(self.delete_avatar)
        self.btn_save_info.clicked.connect(self.save_info)
        self.btn_update.clicked.connect(self.save_note)
        self.btn_delete.clicked.connect(self.delete_note)

        # Spinboxes
        self.spinBox.valueChanged.connect(
            lambda x: self.change_displayed_note(x))
        self.spinBox_2.valueChanged.connect(
            lambda x: self.change_edited_note(x))

        # Checkbox
        self.pwd_checkbox.stateChanged.connect(
            lambda x: self.toggle_pwd_field(x))

        # Move to the same position as the previous window
        if pos:
            self.move(pos)

        # Fill window with user's info
        self.populate_user_info()

    def save_note(self):
        """Update an existing note or create a new one."""

        note_position = self.spinBox_2.value()
        user_id = self.database.current_user["id"]
        username = self.database.current_user["username"]
        text = self.comment_block.toPlainText()

        if note_position == 0:
            # New note
            try:
                self.database.add_item(user_id, text)

            except exceptions.DatabaseError as e:
                self.label_message.setText("Internal error.")
                logging.warning(e.message)

            else:
                # Refresh user's info
                self.populate_user_info()

                # Finish edition
                last_note = len(self.database.current_user["notes"])
                self.spinBox_2.setValue(last_note)

                logging.info(f"`{username}` created a new note.")
                self.label_message2.setText("New note created.")

        else:
            # Update note
            note_id = self.database.current_user["notes"][note_position-1][0]
            try:
                self.database.update_item(user_id, note_id, text)

            except exceptions.DatabaseError as e:
                self.label_message.setText("Internal error.")
                logging.warning(e.message)

            else:
                # Refresh user's info
                self.populate_user_info()

                # Finish edition
                self.spinBox_2.setValue(note_position)

                logging.info(f"`{username}` updated `note {note_id}`.")
                self.label_message2.setText(f"Note {note_position} updated.")

    def delete_note(self):
        """Delete a user's note."""

        note_position = self.spinBox_2.value()
        note_id = self.database.current_user["notes"][note_position-1][0]
        user_id = self.database.current_user["id"]
        username = self.database.current_user["username"]

        try:
            self.database.delete_item(user_id, note_id)

        except exceptions.DatabaseError as e:
            self.label_message.setText("Internal error.")
            logging.warning(e.message)

        else:
            # Refresh user's info
            self.populate_user_info()

            # Finish edition
            self.discard_note()

            logging.info(f"`{username}` deleted `note {note_id}`.")
            self.label_message2.setText(f"Note {note_position} deleted.")

    def save_info(self):
        """Update account info of the current user."""

        user_id = self.database.current_user["id"]
        user = self.username_line_edit.text()
        name = self.name_line_edit.text()
        update_pwd = self.pwd_checkbox.isChecked()
        password = self.pwd_line_edit.text() if update_pwd else None

        validations = {
            "username": validate_username(user),
            "password": validate_pwd(password) if password else True,
            "name": validate_name(name)}

        if all(validations.values()):
            # Require password
            response = QtWidgets.QInputDialog.getText(
                self, "Identify", "Enter current password:",
                QtWidgets.QLineEdit.EchoMode.Password)

            if response[1]:
                # Clicked ok
                try:
                    user_ok = self.database.check_password(user_id,
                                                           response[0])

                except exceptions.DatabaseError as e:
                    self.label_message.setText("Internal error.")
                    logging.warning(e.message)

                else:
                    if not user_ok:
                        self.label_message.setText("Wrong password.")
                    else:
                        # Correct password
                        try:
                            self.database.update_user(
                                user_id, user, name, password)

                        except exceptions.DatabaseError as e:
                            self.label_message.setText("Internal error.")
                            logging.warning(e.message)

                        except exceptions.ValidationError as e:
                            self.label_message.setText(
                                f"Invalid field {', '.join(e.columns)}")
                            logging.debug(f"`{e.columns}` - {e.message}")

                        except exceptions.UsernameExistsError as e:
                            self.label_message.setText(
                                f"User {user} already exists.")
                            logging.debug(e.message)

                        else:
                            # Everything ok
                            logging.info(
                                f"Info updated for `user {user_id}` "
                                f"- `{user}`.")

                            # Refresh user's info
                            self.populate_user_info()

                            # Finish edition
                            self.discard_changes()

                            # Feedback
                            self.label_message.setText("Info updated.")

        # Some validations failed
        elif not validations['username']:
            self.label_message.setText("Invalid username (min. 5 characters).")
            logging.debug("The username entered is too short.")

        elif not validations['name']:
            self.label_message.setText(
                "Please enter your full name (min. 2 words).")
            logging.debug("The name entered is too short.")

        elif not validations['password']:
            self.label_message.setText("Weak password (min. 8 characters).")
            logging.debug("The password entered is too weak.")

    def change_displayed_note(self, note: int):
        """Change the note displayed in tab0."""

        if note > 0:
            text = self.database.current_user["notes"][note-1][1]
            self.note_rendered_label.setText(text)
            self.creation_date_label.setText(
                epoch_to_local_date(
                    self.database.current_user["notes"][note-1][2]))
            self.last_update_label.setText(
                epoch_to_local_date(
                        self.database.current_user["notes"][note-1][3]))
            note_content = self.database.current_user["notes"][note-1][1]
            self.number_words_label.setText(str(len(note_content.split())))

    def change_edited_note(self, note: int):
        """Change the note displayed in tab1."""

        if note > 0:
            text = self.database.current_user["notes"][note-1][1]
            self.comment_block.setPlainText(text)
            self.btn_create.setEnabled(True)
            self.btn_delete.setEnabled(True)

        else:
            self.comment_block.clear()
            self.btn_create.setEnabled(False)
            self.btn_delete.setEnabled(False)

        self.btn_update.setEnabled(True)
        self.btn_discard_note.setEnabled(True)

        # Clean message label
        self.label_message2.clear()

    def populate_user_info(self):
        """Fill application with user's info."""

        try:
            user_info = self.database.get_user_info(
                self.database.current_user["id"])

        except exceptions.DatabaseError as e:
            logging.warning(e.message)

        else:
            self.database.current_user["username"] = user_info[0][0]
            self.database.current_user["name"] = user_info[0][1]
            self.database.current_user["avatar"] = user_info[0][2]
            self.database.current_user["notes"] = [
                note[3:] for note in user_info]

            self.populate_main_tab()
            self.populate_notes_tab()
            self.populate_account_tab()

    def populate_main_tab(self):
        """Fill tab 0 with data."""

        num_notes = len(self.database.current_user["notes"])
        if not self.database.current_user["notes"][0][0]:
            num_notes = 0

        self.author_label.setText(
            f"{self.database.current_user['name']} "
            f"({self.database.current_user['username']})")
        self.total_notes_label.setText(str(num_notes))

        # Add avatar
        img = QtGui.QPixmap(str(consts.AVATAR_PATH /
                                str(self.database.current_user["avatar"])) +
                            ".png")
        img2 = img.scaled(
            QtCore.QSize(75, 75), QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation)
        self.avatar_mini.setPixmap(img2)

        if num_notes > 0:
            self.note_rendered_label.setText(
                self.database.current_user["notes"][0][1])

            self.spinBox.setMinimum(1)
            self.spinBox.setMaximum(num_notes)
            self.spinBox.setValue(1)

            # Most recent update among all their notes
            last_update = max(note[3] for note in
                              self.database.current_user["notes"])
            self.date_label.setText(epoch_to_local_date(last_update))

            # Displayed note's metadata
            self.creation_date_label.setText(
                epoch_to_local_date(
                    self.database.current_user["notes"][0][2]))
            self.last_update_label.setText(
                epoch_to_local_date(
                    self.database.current_user["notes"][0][3]))
            self.number_words_label.setText(
                str(len(self.database.current_user["notes"][0][1].split())))

        else:
            self.note_rendered_label.clear()
            self.spinBox.setMinimum(0)
            self.spinBox.setMaximum(0)
            self.date_label.setText("-")
            self.creation_date_label.setText("-")
            self.last_update_label.setText("-")
            self.number_words_label.setText("0")

    def populate_notes_tab(self):
        """Fill tab 1 with data."""

        num_notes = len(self.database.current_user["notes"])
        # Check if note id is None (no notes retrieved)
        if not self.database.current_user["notes"][0][0]:
            num_notes = 0

        if num_notes > 0:
            self.spinBox_2.setMinimum(0)
            self.spinBox_2.setMaximum(num_notes)
            self.spinBox_2.setValue(0)

        else:
            self.spinBox_2.setMinimum(0)
            self.spinBox_2.setMaximum(0)

    def populate_account_tab(self):
        """Fill tab 2 with data."""

        self.username_line_edit.setText(
            self.database.current_user["username"])
        self.name_line_edit.setText(self.database.current_user["name"])

        # Add avatar
        img = QtGui.QPixmap(str(consts.AVATAR_PATH /
                                str(self.database.current_user["avatar"])) +
                            ".png")
        self.avatar.setPixmap(img)

    def update_avatar(self):
        """Upload a new image as avatar."""

        # Open file dialog filtering images
        dial = QtWidgets.QFileDialog()
        dial.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        dial.setNameFilters(["Image files (*.png *.jpg)"])

        if dial.exec_():
            filename = dial.selectedFiles()[0]

            # Read image
            new_avatar = Image.open(filename)

            # Resize image conserving aspect ratio
            max_width, max_height = (175, 175)
            ratio = min(max_width/new_avatar.width,
                        max_height/new_avatar.height)
            new_size = (int(ratio * new_avatar.width),
                        int(ratio * new_avatar.height))
            new_avatar = new_avatar.resize(new_size, Image.LANCZOS)

            # Save image as png
            filename = (str(consts.AVATAR_PATH /
                            str(self.database.current_user["id"])) + ".png")
            new_avatar.save(filename)

            if self.database.current_user["avatar"] == 0:
                # User didn't have a previous avatar
                user_id = self.database.current_user["id"]
                try:
                    self.database.set_avatar(user_id, user_id)
                except exceptions.DatabaseError as e:
                    logging.warning(e.message)

            logging.info(f"`{self.database.current_user['username']}` "
                         "uploaded new avatar.")

            # Refresh user's info
            self.populate_user_info()

            # Finish edition
            self.discard_changes()

    def delete_avatar(self):
        """Delete avatar and set the default one."""

        # Create Messagebox
        text = ("Are you sure you want to delete your avatar?\n"
                "This action cannot be undone.")
        dial = QtWidgets.QMessageBox(self)
        dial.setWindowTitle("Delete avatar")
        dial.setIcon(QtWidgets.QMessageBox.Warning)
        dial.setText(text)
        dial.addButton("Delete", QtWidgets.QMessageBox.AcceptRole)
        dial.addButton(QtWidgets.QMessageBox.Cancel)
        dial.setDefaultButton(QtWidgets.QMessageBox.Cancel)

        response = dial.exec_()
        if response == 0:
            # Delete avatar
            user_id = self.database.current_user["id"]
            if user_id:  # Never ever remove the default avatar (0.png)
                Path.unlink(consts.AVATAR_PATH / (str(user_id) + ".png"))
            try:
                self.database.set_avatar(user_id, 0)

            except exceptions.DatabaseError as e:
                logging.warning(e.message)

            logging.info(f"`{self.database.current_user['username']}` "
                         "deleted avatar.")

            # Refresh user's info
            self.populate_user_info()

            # Finish edition
            self.discard_changes()

    def toggle_pwd_field(self, state: int):
        """Enable/disable password field."""

        if state == 0:
            # Disabled
            self.pwd_line_edit.setEnabled(False)
            self.pwd_line_edit.clear()
            self.label_message.clear()
        else:
            self.pwd_line_edit.setEnabled(True)

    def new_note(self):
        """Adjust UI elements for writing a new note."""

        self.tabWidget.setCurrentIndex(1)
        # This triggers valueChanged signal and set buttons
        self.spinBox_2.setValue(0)

    def update_info(self):
        """Enable buttons to edit account info and move to account tab."""

        self.tabWidget.setCurrentIndex(2)
        self.username_line_edit.setEnabled(True)
        self.name_line_edit.setEnabled(True)
        self.pwd_checkbox.setEnabled(True)
        self.btn_save_info.setEnabled(True)
        self.btn_upload_avatar.setEnabled(True)

        # Don't allow to delete avatar if using the default one
        if self.database.current_user["avatar"] != 0:
            self.btn_del_avatar.setEnabled(True)
        else:
            self.btn_del_avatar.setEnabled(False)

        self.btn_discard_changes.setEnabled(True)

    def delete_account(self):
        """Delete user's account after a confirmation message."""

        # Create Messagebox
        text = ("Are you sure you want to delete your account?\n"
                "This action cannot be undone.")
        dial = QtWidgets.QMessageBox(self)
        dial.setWindowTitle("Delete account")
        dial.setIcon(QtWidgets.QMessageBox.Warning)
        dial.setText(text)
        dial.addButton("Delete", QtWidgets.QMessageBox.AcceptRole)
        dial.addButton(QtWidgets.QMessageBox.Cancel)
        dial.setDefaultButton(QtWidgets.QMessageBox.Cancel)

        response = dial.exec_()
        if response == 0:
            # Delete user
            user_id = self.database.current_user["id"]
            try:
                self.database.delete_user(user_id)

            except exceptions.DatabaseError as e:
                logging.warning(e.message)

            else:
                username = self.database.current_user['username']
                logging.info(f"Account `{username}` deleted.")

                # Delete avatar
                if self.database.current_user["avatar"] != 0:
                    Path.unlink(consts.AVATAR_PATH / (str(user_id) + ".png"))

                # Log user out of the application
                self.logout()

    def license_info(self):
        """Open messagebox with license info."""

        text = ("<span style='color:#7070a0;font-weight:600'>Notebird"
                "</span> is under the Unlicense, which means that it "
                "is free and unencumbered software released into the "
                "<span style='font-weight:600'>Public Domain</span>.")
        QtWidgets.QMessageBox.about(self, "License", text)

    def about_info(self):
        """Open messagebox with app info."""

        text = ("<span style='color:#7070a0;font-weight:600'>Notebird v0.1"
                "</span> was designed in QT Creator and coded using PySide2 "
                "module. It was built for learning purposes by Alucebur in "
                "2019.")
        QtWidgets.QMessageBox.about(self, "About", text)

    def discard_note(self):
        """Discard unsaved changes of current note."""

        self.change_edited_note(self.spinBox_2.value())

    def discard_changes(self):
        """Discard unsaved changes of account info."""

        self.username_line_edit.setEnabled(False)
        self.name_line_edit.setEnabled(False)
        self.pwd_line_edit.setEnabled(False)
        self.pwd_checkbox.setEnabled(False)
        self.btn_save_info.setEnabled(False)
        self.btn_upload_avatar.setEnabled(False)
        self.btn_del_avatar.setEnabled(False)
        self.btn_discard_changes.setEnabled(False)
        self.label_message.clear()

        if self.database.current_user:
            self.username_line_edit.setText(
                self.database.current_user["username"])
            self.name_line_edit.setText(self.database.current_user["name"])
        self.pwd_line_edit.clear()
        self.pwd_checkbox.setCheckState(QtCore.Qt.Unchecked)

    def logout(self):
        """Log user out of the application, showing login window again."""

        self.database.current_user = None
        logging.info(f"`{self.database.current_user['username']}` logged out.")

        window = login.LoginWindow(
            None, database=self.database, pos=self.pos())

        self.close()
        window.show()
