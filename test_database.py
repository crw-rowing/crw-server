import unittest as u
import database as d

# Before testing, make an empty database named userdatabasetest and
# create an file named test_database.properties with one line in the
# same folder as this file, the name of the account you created the
# database under..
with open('test_database.properties') as propFile:
    user = propFile.read().splitlines()[0]
DATABASE = 'userdatabasetest'
print 'Testing with database ' + DATABASE + ' with the user ' + user


class DatabaseTest(u.TestCase):
    def setUp(self):
        self.db = d.Database(DATABASE, user)
        self.udb = d.UserDatabase(self.db)
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
        self.db.drop_all_tables()
        self.db.close_database_connection()

    def populate_database(self):
        """Populates the database with the users saved in the USERS
        array, by calling self.db.add_user for each."""
        for user in self.USERS:
            self.udb.add_user(user[0], user[1])


class UserDatabaseTest(DatabaseTest):
    def test_verify_correct_user(self):
        self.assertTrue(self.udb.verify_user
                        ('henk@email.com', 'phenk'),
                        """Test that attempting to verify an user with
                        the correct email password combination returns
                        true""")

    def test_add_normal_user(self):
        self.udb.add_user('nieuw@user.nl', 'hunter')
        self.assertTrue(
            self.udb.verify_user('nieuw@user.nl', 'hunter'),
            """Unable to add a normal, non duplicate user to the database""")

    def test_verify_user_wrong_password(self):
        self.assertFalse(
            self.udb.verify_user('henk@email.com', 'wrong'),
            """Test that verifying a user with an incorrect password
            returns false""")

    def test_verify_non_existing_user(self):
        with self.assertRaises(ValueError) as a:
            self.udb.verify_user('nietbestaand@email.com', 'blabla')

    def test_add_duplicate_user(self):
        """Test that adding a duplicate user raises a ValueError"""
        with self.assertRaises(ValueError) as a:
            self.udb.add_user('kees@kmail.com', 'hunter5')

    def test_get_correct_user_id(self):
        self.assertNotEqual(
            self.udb.get_user_id(self.USERS[0][0]), None,
            """Test that the database returns a user id for
            an correct, existing email address""")

    def test_get_non_existing_user_id(self):
        with self.assertRaises(ValueError) as a:
            self.udb.get_user_id('nietbestaand@email.com')

    def test_does_existing_user_exist(self):
        self.assertTrue(self.udb.does_user_exist(1),
                        """Test that does_user_exist returns true with
                        an existing user_id""")

    def test_does_not_existing_user_exist(self):
        self.assertFalse(self.udb.does_user_exist(len(self.USERS) + 2),
                         """Test that does_user_exist returns false for
                         an non-existing user_id""")


class TeamDatabaseTest(DatabaseTest):
    def setUp(self):
        super(TeamDatabaseTest, self).setUp()
        self.tdb = d.TeamDatabase(self.db)

    def tearDown(self):
        super(TeamDatabaseTest, self).tearDown()

    def test_create_team_correct_team_id(self):
        user_id = 1
        team_name = 'Team ERGON'
        self.assertEquals(self.tdb.create_team(user_id, team_name),
                          1, """Test that create_team returns 1 as first
                          team_id""")

    def test_create_team_correct_team_name(self):
        user_id = 1
        team_name = 'Team ERGON'
        team_id = self.tdb.create_team(user_id, team_name)
        self.assertEquals(self.tdb.get_team_name(team_id),
                          team_name,
                          """Test that the team name is correctly
                          saved and retrieved.""")


if __name__ == '__main__':
    suite1 = u.TestLoader()\
              .loadTestsFromTestCase(UserDatabaseTest)
    suite2 = u.TestLoader()\
              .loadTestsFromTestCase(TeamDatabaseTest)
    suite = u.TestSuite([suite1, suite2])
    u.TextTestRunner(verbosity=2).run(suite)
