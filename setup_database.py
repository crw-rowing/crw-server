from crw import \
    DATABASE_HOST, DATABASE_PORT, DATABASE_NAME, DATABASE_USER, DATABASE_PASS
import database

if __name__ == '__main__':
    # Setup the user database (the users table in the database)
    db = database.Database(
        DATABASE_HOST, DATABASE_PORT, DATABASE_NAME,
        DATABASE_USER, DATABASE_PASS)
    db.init_database()
    db.close_database_connection()
