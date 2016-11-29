import unittest as u
import database as d

# Before testing, make an empty database named userdatabasetest and
# create an file named test_database.properties with one line in the
# same folder as this file, the name of the account you created the
# database under..
with open('test_database.properties') as propFile:
    user = propFile.readline()
DATABASE = 'userdatabasetest'
print 'Testing with database ' + DATABASE + ' with the user ' + user


class UserDatabaseTest(u.TestCase):
    def setUp(self):
        self.db = d.UserDatabase('userdatabasetest', 'mhr')
        self.USERS = [('kees@kmail.com', 'hunter4'),
                      ('a', 'b'),
                      ('', 'b'),
                      ('ab', ''),
                      ('a\';DROP TABLE users; -- ',
                       'a\';DROP TABLE users; -- '),
                      ('henk@email.com', 'phenk'),
                      ('kees@email.com', 'pkees'),
                      ('jan@email.com', 'pjan'),
                      ('Jan@email.com', 'pjan')]
        self.db.init_database()
        self.populate_database()

    def tearDown(self):
        self.db.drop_user_table()
        self.db.close_database_connection()

    def populate_database(self):
        """Populates the database with the users saved in the USERS
        array, by calling self.db.add_user for each."""
        for user in self.USERS:
            self.db.add_user(user[0], user[1])

    def test_verify_correct_user(self):
        self.assertTrue(self.db.verify_user
                        ('henk@email.com', 'phenk'),
                        """Test that attempting to verify an user with
                        the correct email password combination returns
                        true""")

    def test_add_normal_user(self):
        self.db.add_user('nieuw@user.nl', 'hunter')
        self.assertTrue(
            self.db.verify_user('nieuw@user.nl', 'hunter'),
            """Unable to add a normal, non duplicate user to the database""")

    def test_verify_user_wrong_password(self):
        self.assertFalse(
            self.db.verify_user('henk@email.com', 'wrong'),
            """Test that verifying a user with an incorrect password
            returns false""")

    def test_verify_non_existing_user(self):
        with self.assertRaises(ValueError) as a:
            self.db.verify_user('nietbestaand@email.com', 'blabla')

    def test_add_duplicate_user(self):
        """Test that adding a duplicate user raises a ValueError"""
        with self.assertRaises(ValueError) as a:
            self.db.add_user('kees@kmail.com', 'hunter5')

    def test_get_correct_user_id(self):
        self.assertNotEqual(
            self.db.get_user_id(self.USERS[0][0]), None,
            """Test that the database returns a user id for
            an correct, existing email address""")

    def test_get_non_existing_user_id(self):
        with self.assertRaises(ValueError) as a:
            self.db.get_user_id('nietbestaand@email.com')


if __name__ == '__main__':
    suite = u.TestLoader()\
                    .loadTestsFromTestCase(UserDatabaseTest)
    u.TextTestRunner(verbosity=2).run(suite)
