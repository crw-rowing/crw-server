import psycopg2
from passlib.context import CryptContext
import random
import string
import datetime

# Global password context
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"]
    )


class Database:
    def __init__(self, database_name, database_user):
        self.database_connection = psycopg2.connect(database=database_name,
                                                    user=database_user)
        self.cursor = self.database_connection.cursor()

    def init_database(self):
        """Creates the table structure in the database.  This is to be used
        once for every database, not on every restart of the program."""
        self.cursor.execute(
            """CREATE TABLE teams
            (id INTEGER PRIMARY KEY,
            name TEXT NOT NULL)""")
        self.cursor.execute(
            """CREATE TABLE users
            (id INTEGER PRIMARY KEY,
            email TEXT UNIQUE,
            password TEXT,
            team_id INTEGER REFERENCES teams(id),
            coach BOOLEAN);""")
        self.cursor.execute(
            """CREATE TABLE sessions
            (key TEXT PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) NOT NULL,
            exp_date TIMESTAMP NOT NULL);
            """)
        self.database_connection.commit()

    def drop_all_tables(self):
        """Drops all tables from the database"""
        self.cursor.execute(
            """DROP TABLE sessions;""")
        self.cursor.execute(
            """DROP TABLE users;""")
        self.cursor.execute(
            """DROP TABLE teams;""")
        self.database_connection.commit()

    def close_database_connection(self):
        """Closes the database_connection and the cursor"""
        self.cursor.close()
        self.database_connection.close()


class UserDoesNotExistError(ValueError):
    def __init__(self, reference_type, value):
        super(UserDoesNotExistError, self).__init__(
            'No user with {}={} exists.'.format(reference_type, value))


class ActionNotPermittedError(ValueError):
    def __init__(self, who, what):
        super(ActionNotPermittedError, self).__init__(
            '{} is not permitted to {}'.format(who, what))


class UserDatabase:
    def __init__(self, database):
        self.d = database

    def add_user(self, email, password):
        """Adds an user to the database, using the given email as
        email, the given password as password and a new id, one higher
        than the highest id in the database."""

        # Check if there isn't already an user with this email address
        self.d.cursor.execute(
            """SELECT email FROM users
            WHERE email = %s;""", (email,))
        if self.d.cursor.fetchone() is not None:
            raise UserDoesNotExistError('email', email)

        # Find the current max_id to generate a new id that is one
        # higher
        self.d.cursor.execute(
            """SELECT MAX(id) FROM users;""")
        (max_id,) = self.d.cursor.fetchone()
        if max_id is None:
            max_id = 0

        # Hash and salt the password using passlib
        password_hash = pwd_context.hash(password)

        self.d.cursor.execute(
            """INSERT INTO users (id, email, password) VALUES
            (%s, %s, %s);""", (max_id + 1, email, password_hash))
        self.d.database_connection.commit()

    def verify_user(self, email, password):
        """Returns whether the given password is the same as the
        password associated with this email address. """
        self.d.cursor.execute(
            """SELECT password FROM users
            WHERE email = %s;""", (email,))

        saved_password_tuple = self.d.cursor.fetchone()
        if saved_password_tuple is None:
            raise UserDoesNotExistError('email', email)
        saved_password_hash = saved_password_tuple[0]

        return pwd_context.verify(password, saved_password_hash)

    def get_user_id(self, email):
        """Returns the user_id associated with this email address"""
        self.d.cursor.execute(
            """SELECT id FROM users
            WHERE email = %s;""", (email,))

        saved_id_tuple = self.d.cursor.fetchone()
        if saved_id_tuple is None:
            raise UserDoesNotExistError('email', email)

        return saved_id_tuple[0]

    def does_user_exist(self, user_id):
        """Checks if an user exists with the given user_id."""
        self.d.cursor.execute(
            """SELECT id FROM users
            WHERE id = %s;""", (user_id,))

        return (self.d.cursor.fetchone() is not None)

    def get_user_team_status(self, user_id):
        """Returns (team_id, coach) of the user with the id user_id,
        be aware that both may be None when the user doesn't have a
        team yet."""
        if not self.does_user_exist(user_id):
            raise UserDoesNotExistError('id', user_id)

        self.d.cursor.execute(
            """SELECT team_id, coach FROM users
            WHERE id = %s;""", (user_id,))
        return self.d.cursor.fetchone()


class TeamDatabase:
    def __init__(self, database):
        self.d = database

    def create_team(self, user_id, team_name):
        """Creates a new team with one member, the user referenced by
        the user_id, this user will automatically be marked as a
        coach.
        Returns the team_id."""
        if not UserDatabase(self.d).does_user_exist(user_id):
            raise UserDoesNotExistError('id', user_id)

        # Find the max team id, so we can choose one that is one
        # higher
        self.d.cursor.execute(
            """SELECT MAX(id) FROM teams;""")
        (max_team_id,) = self.d.cursor.fetchone()
        if max_team_id is None:
            max_team_id = 0
        team_id = max_team_id + 1

        # Create the team
        self.d.cursor.execute(
            """INSERT INTO teams (id, name) VALUES (%s, %s);""",
            (team_id, team_name))

        self.d.cursor.execute(
            """UPDATE users
            SET team_id = %s, coach = %s
            WHERE id = %s;""", (team_id, True, user_id))

        self.d.database_connection.commit()

        return team_id

    def get_team_name(self, team_id):
        """Returns the team name associated with the team_id"""
        self.d.cursor.execute(
            """SELECT name FROM teams
            WHERE id = %s;""", (team_id,))
        team_name_tuple = self.d.cursor.fetchone()
        if team_name_tuple is None:
            raise ValueError(
                """No team found for this team_id""")

        return team_name_tuple[0]

    def add_user_to_team(
            self, adder_id, user_to_add_id, coach=False):
        """Adds an user to the team of the adder (the user who is
        adding another user) with as coach attribute `coach`"""
        udb = UserDatabase(self.d)
        if not udb.does_user_exist(adder_id):
            raise UserDoesNotExistError('id', adder_id)
        if not udb.does_user_exist(user_to_add_id):
            raise UserDoesNotExistError('id', user_to_add_id)

        (team_id, adder_coach) = udb.get_user_team_status(adder_id)
        (user_team_id, _) = udb.get_user_team_status(user_to_add_id)
        if team_id is None:
            raise ValueError('The adder is not in any team')
        if (not adder_coach) or (user_team_id is not None):
            raise ActionNotPermittedError(
                'The user with id={}'.format(adder_id),
                'add the user with id={}'.format(user_to_add_id))

        self.d.cursor.execute(
            """UPDATE users
            SET team_id = %s, coach = %s
            WHERE id = %s;""", (team_id, coach, user_to_add_id))

        self.d.database_connection.commit()

    def remove_user_from_team(
            self, requesting_user_id, user_to_remove_id):
        """Removes a user from the team it is in. Either the
        requesting_user has to be the same as the user_to_remove,
        or the requesting_user has to be a coach in the team of
        the user_to_remove."""
        udb = UserDatabase(self.d)
        if not udb.does_user_exist(requesting_user_id):
            raise UserDoesNotExistError('id', requesting_user_id)
        if not udb.does_user_exist(user_to_remove_id):
            raise UserDoesNotExistError('id', user_to_remove_id)

        (requesting_user_team, requesting_user_coach)\
            = udb.get_user_team_status(requesting_user_id)
        (user_to_remove_team, _) = udb.get_user_team_status(
            user_to_remove_id)

        allowed = (requesting_user_id == user_to_remove_id) or\
                  (requesting_user_team == user_to_remove_team and
                   requesting_user_coach)
        if not allowed:
            raise ActionNotPermittedError(
                'The user with id={}'.format(requesting_user_id),
                'remove this user from this team')

        self.d.cursor.execute(
            """UPDATE users
            SET team_id = %s, coach = %s
            WHERE id = %s""", (None, None, user_to_remove_id))


class SessionDatabase:
    def __init__(self, database):
        self.d = database

    def generate_session_key(self, user_id,
                             livespan=datetime.timedelta(weeks=1)):
        """Generates and returns a new session key for the user, the user
        should already be verified for this. The session key will be
        saved in the sessions table and will be valid for one week.

        This will (as a side effect) remove all session keys that are
        outdated from this user from the session key database."""
        udb = UserDatabase(self.d)
        if not udb.does_user_exist(user_id):
            raise UserDoesNotExistError('id', user_id)

        self.remove_expired_keys(user_id)

        # Generate a random, cryptographically secure string of
        # printable characters, that will be used as session key.
        # Based on http://stackoverflow.com/a/23728630
        session_key_length = 32
        session_key = ''.join(random.SystemRandom()
                              .choice(string.ascii_letters +
                                      string.digits)
                              for _ in range(session_key_length))

        # Set the expiration date of the session key
        expiration_date\
            = datetime.datetime.now() + livespan

        # Inserting the key in the sessions table
        self.d.cursor.execute(
            """INSERT INTO sessions (key, user_id, exp_date)
            VALUES (%s, %s, %s);""", (session_key, user_id,
                                      expiration_date))
        self.d.database_connection.commit()

        return session_key

    def remove_expired_keys(self, user_id):
        """Removes all expired session keys for this user from the
        sessions database."""
        self.d.cursor.execute(
            """DELETE FROM sessions
            WHERE user_id = %s
            AND exp_date < %s;""", (user_id,
                                    datetime.datetime.now()))

        self.d.database_connection.commit()
