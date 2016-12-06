from crw import DATABASE
from crw import DATABASE_USER
import database

if __name__ == '__main__':
    # Setup the user database (the users table in the database)
    db = database.Database(DATABASE, DATABASE_USER)
    db.init_database()
    db.close_database_connection()
