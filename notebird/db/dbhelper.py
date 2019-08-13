"""SQLite database management."""
# |===============|       |==============|
# | users         |       | library      |
# |===============|       |==============|
# | user_id (PK)  |--\    | note_id (PK) |
# | username      |   \--<| user_id (FK) |
# | password      |       | content      |
# | name          |       | creation     |
# | avatar_id     |       | last_update  |
# |===============|       |==============|
import time
import sqlite3
from typing import Optional, Tuple, List, NewType

from utils import exceptions
from utils.security import encrypt_password, check_encrypted_password
from utils.validations import validate_username, validate_pwd, validate_name

Timestamp = NewType("Timestamp", float)
UserInfo = NewType("UserInfo",
                   Tuple[str, str, int, int, str, Timestamp, Timestamp])


class DBHelper:
    """Connect to the given SQLite database."""

    def __init__(self, name: str):
        self.name = name
        self.current_user = None

        try:
            self.conn = sqlite3.connect(name)

        except sqlite3.OperationalError:
            error_message = f"Cannot connect to {name}."
            raise exceptions.DatabaseError(error_message)

        else:
            # Function creation routine (name, num_params, function)
            self.conn.create_function("hash", 1, encrypt_password)

    # =====  Database methods  ============================================
    def setup(self):
        """Create structure of the database for the first time."""

        stmt_table = """
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT    NOT NULL    UNIQUE,
                password    TEXT    NOT NULL,
                name        TEXT    NOT NULL,
                avatar_id   INTEGER NOT NULL
            )"""
        try:
            self.conn.execute(stmt_table)
        except sqlite3.OperationalError:
            error_message = "Cannot create table `users`."
            raise exceptions.DatabaseError(error_message)

        # Store dates as floats (UNIX Epoch time)
        stmt_table = """
            CREATE TABLE IF NOT EXISTS library (
                note_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER,
                content     TEXT    NOT NULL,
                creation    REAL    NOT NULL,
                last_update REAL    NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
                                      ON UPDATE CASCADE
                                      ON DELETE SET NULL
            )"""
        try:
            self.conn.execute(stmt_table)
        except sqlite3.OperationalError:
            error_message = "Cannot create table `library`."
            raise exceptions.DatabaseError(error_message)

        stmt_index = """CREATE INDEX IF NOT EXISTS owner_index
                               ON library (user_id ASC)"""
        try:
            self.conn.execute(stmt_index)
        except sqlite3.OperationalError:
            error_message = "Cannot create index for table `library`."
            raise exceptions.DatabaseError(error_message)

    # =====  `User` table methods  ========================================
    def create_user(self, user: str, password: str, name: str):
        """Insert info about the user into the database."""

        validations = {
            "username": validate_username(user),
            "password": validate_pwd(password),
            "name": validate_name(name)}

        if all(validations.values()):
            # user_id autoincremented, password hashed, avatar_id by default
            stmt = """INSERT INTO users
                             VALUES (NULL, ?, hash(?), ?, 0)"""
            params = (user, password, name)
            cur = self.conn.cursor()

            try:
                cur.execute(stmt, params)
            except sqlite3.IntegrityError:
                error_message = "User already exists in the database."
                raise exceptions.UsernameExistsError(user, error_message)

            except sqlite3.OperationalError:
                error_message = "An operational error prevented the insertion."
                raise exceptions.DatabaseError(error_message)

            else:
                self.conn.commit()

        # Server-side validation failed
        else:
            error_message = "Fields validation failed, insertion aborted."
            columns = tuple(col for col in validations if not validations[col])
            raise exceptions.ValidationError(columns, error_message)

    def check_password(self, user_id: int, password: str) -> bool:
        """Return `True` if `password` matches the password of
        the user with the given id."""

        stmt = """SELECT password FROM users
                                  WHERE user_id=?"""
        params = (user_id,)
        cur = self.conn.cursor()

        try:
            cur.execute(stmt, params)
        except sqlite3.OperationalError:
            error_message = "Cannot retrieve data from table `users`."
            raise exceptions.DatabaseError(error_message)

        else:
            if check_encrypted_password(password, cur.fetchone()[0]):
                return True

        # Passwords do not match
        return False

    def login(self, user: str, password: str) -> int:
        """Return `user_id` of the given user if passwords match."""

        stmt = """SELECT user_id, password FROM users
                                           WHERE username=?"""
        params = (user,)
        cur = self.conn.cursor()

        try:
            cur.execute(stmt, params)
        except sqlite3.OperationalError:
            error_message = "Cannot retrieve data from table `users`."
            raise exceptions.DatabaseError(error_message)

        else:
            # Check password if user found
            user_pass_combo = cur.fetchone()
            if user_pass_combo:
                if check_encrypted_password(password, user_pass_combo[1]):
                    return user_pass_combo[0]

        # User was not found or passwords do not match
        error_message = "Invalid user and/or password."
        raise exceptions.LoginError(user, error_message)

    def get_user_info(self, user_id: int) -> List[UserInfo]:
        """Return info and notes of the user with the given id."""

        stmt = """SELECT username, name, avatar_id,
                         note_id, content, creation, last_update
                  FROM users LEFT JOIN library
                       ON users.user_id = library.user_id
                  WHERE users.user_id=?"""
        params = (user_id,)
        cur = self.conn.cursor()
        try:
            cur.execute(stmt, params)
        except sqlite3.OperationalError:
            error_message = ("Cannot retrieve data from tables "
                             "`users` & `library`.")
            raise exceptions.DatabaseError(error_message)
        else:
            return cur.fetchall()

    def delete_user(self, user_id: int):
        """Delete the user with the given id from the database.

        `user_id` of their notes, if any, will be set to NULL."""

        stmt = """DELETE FROM users
                         WHERE user_id=?"""
        params = (user_id,)
        cur = self.conn.cursor()

        try:
            cur.execute(stmt, params)
        except sqlite3.OperationalError:
            error_message = "An operational error prevented the deletion."
            raise exceptions.DatabaseError(error_message)
        else:
            self.conn.commit()

    def update_user(self, user_id: int, user: str, name: str,
                    password: Optional[str]=None):
        """Edit info about the user with the given id."""

        validations = {
            "username": validate_username(user),
            "password": validate_pwd(password) if password else True,
            "name": validate_name(name)}

        if all(validations.values()):
            if password:
                stmt = """UPDATE users SET username=?,
                                           password=hash(?),
                                           name=?
                                    WHERE user_id=?"""
                params = (user, password, name, user_id)
            else:
                stmt = """UPDATE users SET username=?,
                                           name=?
                                    WHERE user_id=?"""
                params = (user, name, user_id)
            cur = self.conn.cursor()
            try:
                cur.execute(stmt, params)

            except sqlite3.IntegrityError:
                error_message = "User already exists in the database."
                raise exceptions.UsernameExistsError(user, error_message)

            except sqlite3.OperationalError:
                error_message = "An operational error prevented the edition."
                raise exceptions.DatabaseError(error_message)
            else:
                self.conn.commit()

        # Server-side validation failed
        else:
            error_message = "Fields validation failed, edition aborted."
            columns = tuple(col for col in validations if not validations[col])
            raise exceptions.ValidationError(columns, error_message)

    def set_avatar(self, user_id: int, avatar_id: int):
        """Add avatar for the given user."""

        stmt = """UPDATE users SET avatar_id=?
                               WHERE user_id=?"""
        params = (avatar_id, user_id)
        cur = self.conn.cursor()
        try:
            cur.execute(stmt, params)
        except sqlite3.OperationalError:
            error_message = "An operational error prevented the insertion."
            raise exceptions.DatabaseError(error_message)
        else:
            self.conn.commit()

    # =====  `Library` table methods  =====================================
    def add_item(self, user_id: int, item_text: str):
        """Add a note to the database."""

        stmt = """INSERT INTO library
                         VALUES (NULL, ?, ?, ?, ?)"""
        epoch_time = time.time()
        params = (user_id, item_text, epoch_time, epoch_time)
        cur = self.conn.cursor()

        try:
            cur.execute(stmt, params)
        except sqlite3.OperationalError:
            error_message = "An operational error prevented the insertion."
            raise exceptions.DatabaseError(error_message)
        else:
            self.conn.commit()

    def update_item(self, user_id: int, item_id: int, item_text: str):
        """Update the given note with a new text."""

        stmt = """ UPDATE library SET content=?,
                                      last_update=?
                                  WHERE user_id=? AND note_id=?"""
        epoch_time = time.time()
        params = (item_text, epoch_time, user_id, item_id)
        cur = self.conn.cursor()

        try:
            cur.execute(stmt, params)
        except sqlite3.OperationalError:
            error_message = "An operational error prevented the edition."
            raise exceptions.DatabaseError(error_message)
        else:
            self.conn.commit()

    def delete_item(self, user_id: int, item_id: int):
        """Delete the given note from the database."""

        stmt = """DELETE FROM library
                         WHERE user_id=? AND note_id=?"""
        params = (user_id, item_id)
        cur = self.conn.cursor()

        try:
            cur.execute(stmt, params)
        except sqlite3.OperationalError:
            error_message = "An operational error prevented the deletion."
            raise exceptions.DatabaseError(error_message)
        else:
            self.conn.commit()
