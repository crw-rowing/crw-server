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
        self.tdb = d.TeamDatabase(self.db)
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
        with self.assertRaises(d.UserDoesNotExistError) as a:
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
        with self.assertRaises(d.UserDoesNotExistError) as a:
            self.udb.get_user_id('nietbestaand@email.com')

    def test_does_existing_user_exist(self):
        self.assertTrue(self.udb.does_user_exist(1),
                        """Test that does_user_exist returns true with
                        an existing user_id""")

    def test_does_not_existing_user_exist(self):
        self.assertFalse(self.udb.does_user_exist(len(self.USERS) + 2),
                         """Test that does_user_exist returns false for
                         an non-existing user_id""")

    def test_get_user_team_status_no_team(self):
        (team_id, coach) = self.udb.get_user_team_status(1)
        self.assertEqual(team_id, None,
                         """Test that the team_id returned by
                         get_user_team_status is None if the user
                         isn't in a team.""")

    def test_get_user_team_status_coach(self):
        user_id = 1
        team_id = self.tdb.create_team(user_id, 'ERGON')
        (user_team_id, coach) = self.udb.get_user_team_status(user_id)
        self.assertEqual(team_id, user_team_id,
                         """Test that the correct team_id is saved for
                         the creator in the users table""")
        self.assertEqual(coach, True,
                         """Test that the creator of the team is set
                         as an coach in the users table""")


class TeamDatabaseTest(DatabaseTest):
    def create_team_for_user_1(self):
        user_id = 1
        team_name = 'Team ERGON'
        return self.tdb.create_team(user_id, team_name)

    def test_create_team_correct_team_id(self):
        self.assertEquals(self.create_team_for_user_1(),
                          1, """Test that create_team returns 1 as first
                          team_id""")

    def test_create_team_correct_team_name(self):
        team_id = self.create_team_for_user_1()
        team_name = 'Team ERGON'
        self.assertEquals(self.tdb.get_team_name(team_id),
                          team_name,
                          """Test that the team name is correctly
                          saved and retrieved.""")

    def test_add_coach_to_correct_team(self):
        self.create_team_for_user_1()
        adder_id = 1
        user_to_add_id = 2
        self.tdb.add_user_to_team(adder_id, user_to_add_id, True)
        (adder_team_id, _) = self.udb.get_user_team_status(adder_id)
        (user_team_id, user_coach) = self.udb.get_user_team_status(
            user_to_add_id)

        self.assertEquals(adder_team_id, user_team_id,
                          """Test that the user is added to the team
                          of the adder""")
        self.assertTrue(user_coach,
                        """Test that the user is correctly set as
                        coach""")

    def test_add_user_to_correct_team(self):
        self.create_team_for_user_1()
        adder_id = 1
        user_to_add_id = 2
        self.tdb.add_user_to_team(adder_id, user_to_add_id, False)
        (user_team_id, user_coach) = self.udb.get_user_team_status(
            user_to_add_id)

        self.assertFalse(user_coach, """Test that the priviliges of a
        normal user are set correctly.""")

    def test_add_user_to_team_without_team(self):
        with self.assertRaises(ValueError) as e:
            self.tdb.add_user_to_team(1, 2)

    def test_add_non_existing_user_to_team(self):
        """Test that adding a user that does not exist to a team
        raises a UserDoesNotExistError"""
        with self.assertRaises(d.UserDoesNotExistError) as e:
            self.tdb.add_user_to_team(-1, 2)


if __name__ == '__main__':
    suite1 = u.TestLoader()\
              .loadTestsFromTestCase(UserDatabaseTest)
    suite2 = u.TestLoader()\
              .loadTestsFromTestCase(TeamDatabaseTest)
    suite = u.TestSuite([suite1, suite2])
    u.TextTestRunner(verbosity=2).run(suite)
