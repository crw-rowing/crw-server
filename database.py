import psycopg2


class UserDatabase:
    def __init__(self, database_name, database_user):
        self.database_connection = psycopg2.connect(database=database_name,
                                                    user=database_user)
        self.cursor = self.database_connection.cursor()

    def init_database(self):
        """Creates the table structure of 'users' in the database.
        This is to be used once for every database, not on every
        restart of the program"""
        self.cursor.execute(
            """CREATE TABLE users
            (id INTEGER UNIQUE,
            email TEXT UNIQUE,
            password TEXT);""")
        self.database_connection.commit()

    def add_user(self, email, password):
        """Adds an user to the database, using the given email as
        email, the given password as password and a new id, one higher
        than the highest id in the database."""

        # Check if there isn't already an user with this email address
        self.cursor.execute(
            """SELECT email FROM users
            WHERE email = %s;""", (email,))
        if self.cursor.fetchone() is not None:
            raise ValueError('An user with this email already exists')

        # Find the current max_id to generate a new id that is one
        # higher
        self.cursor.execute(
            """SELECT MAX(id) FROM users;""")
        (max_id,) = self.cursor.fetchone()

        self.cursor.execute(
            """INSERT INTO users (id, email, password) VALUES
            (%s, %s, %s);""", (max_id + 1, email, password))
        self.database_connection.commit()

    def verify_user(self, email, password):
        """Returns whether the given password is the same as the
        password associated with this email address. """
        self.cursor.execute(
            """SELECT password FROM users
            WHERE email = %s;""", (email,))

        saved_password_tuple = self.cursor.fetchone()
        if saved_password_tuple is None:
            raise ValueError('There is no user associated with ' +
                             'this email address')

        return saved_password_tuple[0] == password

    def get_user_id(self, email):
        """Returns the user_id associated with this email address"""
        self.cursor.execute(
            """SELECT id FROM users
            WHERE email = %s;""", (email,))

        saved_id_tuple = self.cursor.fetchone()
        if saved_id_tuple is None:
            raise ValueError('There is no user associated with ' +
                             'this email address')

        return saved_id_tuple[0]
