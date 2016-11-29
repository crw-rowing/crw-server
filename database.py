import psycopg2
from passlib.context import CryptContext

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
        self.database_connection.commit()

    def drop_all_tables(self):
        """Drops all tables from the database"""
        self.cursor.execute(
            """DROP TABLE users;""")
        self.cursor.execute(
            """DROP TABLE teams""")
        self.database_connection.commit()

    def close_database_connection(self):
        """Closes the database_connection and the cursor"""
        self.cursor.close()
        self.database_connection.close()


class UserDoesNotExistError(ValueError):
    def __init__(self, reference_type, value):
        super(UserDoesNotExistError, self).__init__(
            'No user with ' + reference_type + '=' + str(value) + ' exists.')


class ActionNotPermittedError(ValueError):
    def __init__(self, who, what):
        super(ActionNotPermittedError, self).__init__(
            str(who) + ' is not permitted to ' + str(what))


class UserDatabase():
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


class TeamDatabase():
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
        if team_id is None:
            raise ValueError('The adder is not in any team')
        if not adder_coach:
            raise ActionNotPermittedError(
                'The user with id=' + str(adder_id),
                'add an user to a team, because he/she isn\'t a coach')

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
                'The user with id=' + str(requesting_user_id),
                'remove this user from his team')

        self.d.cursor.execute(
            """UPDATE users
            SET team_id = %s, coach = %s
            WHERE id = %s""", (None, None, user_to_remove_id))
