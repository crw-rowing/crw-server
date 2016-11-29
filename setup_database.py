from ergon import DATABASE
from ergon import DATABASE_USER
import database

if __name__ == '__main__':
    # Setup the user database (the users table in the database)
    user_database = database.UserDatabase(DATABASE, DATABASE_USER)
    user_database.init_database()
    user_database.close()
