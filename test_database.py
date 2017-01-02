import unittest as u
import database as d
import datetime

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
        self.sdb = d.SessionDatabase(self.db)
        self.hdb = d.HealthDatabase(self.db)
        self.USERS = [('kees@kmail.com', 'hunter4'),
                      ('a', 'b'),
                      ('', 'b'),
                      ('ab', 'dfd'),
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
        array, by calling self.db.add_user for each.
        Also adds health data for the first user."""
        for user in self.USERS:
            self.udb.add_user(user[0], user[1])

        self.test_health_user_id = 1
        self.test_health_date = datetime.date(2010, 1, 1)
        self.test_health_data = (80, 70, 'Feeling great today')
        self.hdb.add_health_data(self.test_health_user_id,
                                 self.test_health_date,
                                 self.test_health_data[0],
                                 self.test_health_data[1],
                                 self.test_health_data[2])

        # Add three additional entries in the past week, with two in
        # the past three days.
        self.test_health_last_week_amm = 3
        self.test_health_last_3_days_amm = 2

        # Today
        self.hdb.add_health_data(self.test_health_user_id,
                                 datetime.date.today(),
                                 0, 0, '')
        # Three days ago
        self.hdb.add_health_data(self.test_health_user_id,
                                 datetime.date.today() -
                                 datetime.timedelta(days=2),
                                 0, 0, '')
        # Seven days ago
        self.hdb.add_health_data(self.test_health_user_id,
                                 datetime.date.today() -
                                 datetime.timedelta(days=7),
                                 0, 0, '')


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

    def test_does_existing_user_email_exist(self):
        self.assertTrue(self.udb.does_user_email_exist(self.USERS[2][0]),
                        """Test that does_user_email_exist returns
                        true for an existing email address.""")

    def test_does_not_existing_user_email_exist(self):
        self.assertFalse(self.udb.does_user_email_exist(
            'doesnotexist@email.com'),
                         """Test that does_user_email_exist returns
                         false for an non-existing email address.""")

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

    def test_get_user_team_status_no_user(self):
        """Test that getting the status of a non existing user, raises
        a UserDoesNotExistError"""
        with self.assertRaises(d.UserDoesNotExistError) as e:
            self.udb.get_user_team_status(-1)


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

    def test_get_team_name_no_team(self):
        """Test that attempting to retrieve the name of a team that
        doesn't exist raises a ValueError"""
        with self.assertRaises(ValueError) as e:
            self.tdb.get_team_name(-1)

    def test_create_team_no_user(self):
        """Test that creating a team with an user_id that doesn't
        exist raises a UserDoesNotExistError."""
        with self.assertRaises(d.UserDoesNotExistError) as e:
            self.tdb.create_team(-1, 'leet')

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

    def test_add_to_team_of_non_existing_user(self):
        """Test that adding a user to a team, when the adder doesn't
        have a team raises a UserDoesNotExistError"""
        with self.assertRaises(d.UserDoesNotExistError) as e:
            self.tdb.add_user_to_team(-1, 2)

    def test_add_non_existing_user_to_team(self):
        """Test that adding a user that does not exist to a team
        raises a UserDoesNotExistError"""
        with self.assertRaises(d.UserDoesNotExistError) as e:
            self.tdb.add_user_to_team(1, -1)

    def test_add_user_to_team_no_coach(self):
        """Test that a team member that isn't a coach can't add users
        to his team"""
        team_id = self.create_team_for_user_1()
        self.tdb.add_user_to_team(1, 2, False)

        with self.assertRaises(d.ActionNotPermittedError) as e:
            self.tdb.add_user_to_team(2, 3)

    def test_add_user_to_team_already_in_team(self):
        """Test that adding a user to a team, that already is in a
        team raises an ActionNotPermittedError"""
        team_id = self.create_team_for_user_1()
        self.tdb.create_team(2, 'naam')

        with self.assertRaises(d.ActionNotPermittedError) as e:
            self.tdb.add_user_to_team(1, 2)

    def test_remove_member_from_team_correct(self):
        team_id = self.create_team_for_user_1()
        user_to_add = 2
        self.tdb.add_user_to_team(1, user_to_add, False)
        self.tdb.remove_user_from_team(1, user_to_add)
        (u_team_id, _) = self.udb.get_user_team_status(user_to_add)

        self.assertIsNone(u_team_id, """Test that the team_id of the
        removed user is None, after being removed""")

    def test_remove_coach_from_team_correct(self):
        team_id = self.create_team_for_user_1()
        user_to_add = 2
        self.tdb.add_user_to_team(1, user_to_add, True)
        self.tdb.remove_user_from_team(1, user_to_add)
        (u_team_id, _) = self.udb.get_user_team_status(user_to_add)

        self.assertIsNone(u_team_id, """Test that the team_id of the
        removed user is None, after being removed""")

    def test_remove_user_from_team_no_member(self):
        """Test that an user that isn't a member that team, can't
        add someone to that team"""
        team_id = self.create_team_for_user_1()
        self.tdb.add_user_to_team(1, 2)
        self.tdb.create_team(3, 'team')
        with self.assertRaises(d.ActionNotPermittedError) as e:
            self.tdb.remove_user_from_team(3, 2)

    def test_remove_user_from_team_no_adder(self):
        """Test that if the user that is removing the user doesn't
        exist, it raises a UserDoesNotExistError"""
        team_id = self.create_team_for_user_1()
        self.tdb.add_user_to_team(1, 2)
        with self.assertRaises(d.UserDoesNotExistError) as e:
            self.tdb.remove_user_from_team(-1, 2)

    def test_remove_user_from_team_no_user(self):
        """Test that if the user that is attempting to be removed
        doesn't exist, an UserDoesNotExistError is raised"""
        team_id = self.create_team_for_user_1()
        with self.assertRaises(d.UserDoesNotExistError) as e:
            self.tdb.remove_user_from_team(1, -1)

    def test_get_team_members_no_team(self):
        """Test that attempting to retrieve the members of a team that
        doesn't exist raises a ValueError"""
        with self.assertRaises(ValueError) as e:
            self.tdb.get_team_members(-1)


class SessionDatabaseTest(DatabaseTest):
    def test_generate_correct_session_key(self):
        user_id = 2
        session_key = self.sdb.generate_session_key(user_id)
        self.assertTrue(self.sdb.verify_session_key
                        (user_id, session_key),
                        """Test that SessionDatabase generates a
                        correct session key that can later be verified
                        correctly.""")

    def test_generate_session_key_no_user(self):
        user_id = -1
        with self.assertRaises(d.UserDoesNotExistError) as e:
            self.sdb.generate_session_key(user_id)

    def test_verify_wrong_session_key(self):
        session_key_1 = self.sdb.generate_session_key(1)
        session_key_2 = self.sdb.generate_session_key(2)

        self.assertFalse(self.sdb.verify_session_key
                         (1, session_key_2),
                         """Test that verifying an user with another
                         users session key fails""")

    def test_verify_empty_session_key(self):
        session_key_1 = self.sdb.generate_session_key(1)
        session_key_2 = self.sdb.generate_session_key(2)

        self.assertFalse(self.sdb.verify_session_key(1, ""),
                         """Test that verifying an user with an empty
                         string as session key fails, but doesn't
                         raise an error""")

    def test_verify_expired_session_key(self):
        expired_key = self.sdb.generate_session_key(1, datetime.
                                                    timedelta(hours=-1))

        self.assertFalse(self.sdb.verify_session_key(1, expired_key),
                         """Test that verifying an user with an
                         expired session key fails""")

    def test_renew_session_key(self):
        expired_key = self.sdb.generate_session_key(1, datetime.
                                                    timedelta(hours=-1))
        # Renew the key and test that it can be used again
        self.sdb.renew_session_key(1, expired_key)

        self.assertTrue(self.sdb.verify_session_key(1, expired_key),
                        """Test that renewing an expired key makes it
                        valid again.""")

    def test_remove_outdated_keys(self):
        expired_key = self.sdb.generate_session_key(1, datetime.
                                                    timedelta(hours=-1))
        self.sdb.remove_expired_keys(1)
        # If the outdated key is correctly removed, the renewal won't
        # help, since it doesn't exist anymore.
        self.sdb.renew_session_key(1, expired_key)

        self.assertFalse(self.sdb.verify_session_key(1, expired_key),
                         """Test that remove_expired_keys removes
                         expired keys""")


class HealthDatabaseTest(DatabaseTest):
    def test_add_new_health_data(self):
        user_id = 2
        date = datetime.date(2016, 12, 31)
        heart_rate = 900
        weight = 80
        comment = 'My heart rate is way too high!'
        self.hdb.add_health_data(user_id, date, heart_rate, weight,
                                 comment)
        self.assertEquals(self.hdb.get_health_data(user_id, date),
                          (heart_rate, weight, comment),
                          """Test that the correct data is saved when
                          adding a new entry.""")

    def test_add_updating_health_data(self):
        heart_rate = 900
        weight = 80
        comment = 'My heart rate is way too high!'
        self.hdb.add_health_data(self.test_health_user_id,
                                 self.test_health_date,
                                 heart_rate, weight, comment)
        self.assertEquals(self.hdb.get_health_data(
            self.test_health_user_id, self.test_health_date),
                          (heart_rate, weight, comment),
                          """Test that the entry is correctly
                          retreived after updating.""")

        # Test that there is actually only one entry and not just the
        # correct one is retreived.
        self.hdb.d.cursor.execute(
            """SELECT * FROM health_data
            WHERE user_id = %s AND date = %s;""",
            (self.test_health_user_id, self.test_health_date))
        self.assertEquals(len(self.hdb.d.cursor.fetchall()), 1,
                          """Test that there is only one entry
                          matching the date and user after
                          updating.""")

    def test_add_health_data_no_user(self):
        with self.assertRaises(d.UserDoesNotExistError) as e:
            self.hdb.add_health_data(-1, datetime.date(1999, 12, 31),
                                     10, 10, '')

    def test_get_health_data(self):
        self.assertEquals(self.hdb.get_health_data(
            self.test_health_user_id, self.test_health_date),
                          self.test_health_data,
                          """Test that the correct data is retreived
                          from the health database.""")

    def test_get_past_health_data_standard_period(self):
        self.assertEquals(
            len(self.hdb.get_past_health_data(self.test_health_user_id)),
            self.test_health_last_week_amm,
            """Test that the correct ammount of entries is retreived
            for the past week""")

    def test_get_past_health_data_short_period(self):
        self.assertEquals(
            len(self.hdb.get_past_health_data(self.test_health_user_id,
                                              datetime.timedelta(days=3))),
            self.test_health_last_3_days_amm,
            """Test that the correct ammount of entries is retreived
            for the past three days""")

    def test_get_past_health_data_no_data(self):
        self.assertEquals(
            len(self.hdb.get_past_health_data(4)), 0,
            """Test that no entries are retreived if the user doesn't
            have any.""")

    def test_get_past_health_data_no_user(self):
        self.assertEquals(
            len(self.hdb.get_past_health_data(-1)), 0,
            """Test that no entries are retreived if the user doesn't
            exist.""")

if __name__ == '__main__':
    suite1 = u.TestLoader()\
              .loadTestsFromTestCase(UserDatabaseTest)
    suite2 = u.TestLoader()\
              .loadTestsFromTestCase(TeamDatabaseTest)
    suite3 = u.TestLoader()\
              .loadTestsFromTestCase(SessionDatabaseTest)
    suite4 = u.TestLoader()\
              .loadTestsFromTestCase(HealthDatabaseTest)
    suite = u.TestSuite([suite1, suite2, suite3, suite4])
    u.TextTestRunner(verbosity=2).run(suite)
