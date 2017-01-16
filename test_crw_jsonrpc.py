import unittest as u
import database as d
import crw_jsonrpc as e
import jsonrpc
import json
import string
import datetime
from crw import DATABASE_HOST, DATABASE_PORT, DATABASE_USER, DATABASE_PASS

# Before testing, make an empty database named userdatabasetest with the same
# username and password as stated in crw.cfg

DATABASE = 'userdatabasetest'
print 'Testing with database ' + DATABASE + ' with the user ' + DATABASE_USER


class CrwJsonRpcTest(u.TestCase):
    def setUp(self):
        self.db = d.Database(DATABASE_HOST, DATABASE_PORT, DATABASE,
                             DATABASE_USER, DATABASE_PASS)
        self.udb = d.UserDatabase(self.db)
        self.tdb = d.TeamDatabase(self.db)
        self.hdb = d.HealthDatabase(self.db)
        self.trdb = d.TrainingDatabase(self.db)
        self.idb = d.IntervalDatabase(self.db)
        self.USERS = [('kees@kmail.com', 'hunter4'),
                      ('adfd@bdfds.nl', 'b'),
                      ('b+a@b.b.b.nl', 'b'),
                      ('abldf@blldfds.dfdf', 'dfd'),
                      ('fds@fd.a\';DROP TABLE users; -- ',
                       'ds\';DROP TABLE users; -- '),
                      ('henk@email.com', 'phenk'),
                      ('kees@email.com', 'pkees'),
                      ('jan@email.com', 'pjan'),
                      ('Jan@email.com', 'pjan')]
        self.db.init_database()
        self.rpc = e.CrwJsonRpc(self.db)
        self.populate_database()

    def tearDown(self):
        self.db.drop_all_tables()
        self.db.close_database_connection()

    def set_user_and_authenticated(self, user_id, authenticated=True):
        """Sets the user as user_id and marks it authenticated for one
        RPC call."""
        self.rpc.current_user_id = user_id
        self.rpc.authenticated = authenticated

    def populate_database(self):
        """Populates the database with the users saved in the USERS
        array, by calling self.db.add_user for each."""
        for user in self.USERS:
            self.udb.add_user(user[0], user[1])

        self.test_team_name = "test"
        self.test_team_coach_id = 6
        self.set_user_and_authenticated(self.test_team_coach_id)
        self.test_team_id = self.rpc.create_team(self.test_team_name)
        self.set_user_and_authenticated(-1, False)

    def test_generate_correct_response(self):
        rpc_request = """{"jsonrpc": "2.0", "method": "echo",
                        "params": [true], "id": 1}"""
        rpc_response = self.rpc.rpc_invoke(rpc_request)
        response_obj = json.loads(rpc_response)

        self.assertTrue('jsonrpc' in response_obj,
                        """Test that a jsonrpc field is included in
                        the response.""")
        self.assertEquals(response_obj['jsonrpc'], self.rpc.version,
                          """Test that the jsonrpc field includes the
                          correct jsonrpc version""")

        self.assertTrue('id' in response_obj,
                        """Test that an id field is included in
                        the response""")
        self.assertEquals(response_obj['id'], 1,
                          """Test that an id corresponding to the
                          request id is included in the response""")

        self.assert_result_equals(rpc_response,  True,
                                  """Test that the response includes a
                                  result field""")

    def test_create_correct_account(self):
        rpc_request = """{"jsonrpc": "2.0", "method": "create_account",
                        "params": ["nieuw@email.com", "hunter4"],
                        "id": 2}"""
        rpc_response = self.rpc.rpc_invoke(rpc_request)
        response_obj = json.loads(rpc_response)

        self.assertTrue('result' in response_obj,
                        """Test that the response contains a
                        result""")
        self.assertEquals(response_obj['result'], True,
                          """Test that the response contains True as
                          result when a correct create_account request
                          has been invoked""")

        self.assertTrue(self.udb.verify_user('nieuw@email.com',
                                             'hunter4'),
                        """Test that the account has been saved
                        correctly in the database and the user
                        can be verified using the supplied
                        credentials.""")

    def test_create_duplicate_account(self):
        rpc_request = """{"jsonrpc": "2.0", "method": "create_account",
                        "params": ["henk@email.com", "password"],
                        "id": 2}"""
        rpc_response = self.rpc.rpc_invoke(rpc_request)

        self.assert_error_equals(rpc_response, 1,
                                 """Test that creating a duplicate
                                 account returns a
                                 error_account_already_exists.""")

    def test_create_account_invalid_email(self):
        with self.assertRaises(jsonrpc.RPCError) as err:
            self.rpc.create_account("geen email", "test")

        self.assertEquals(err.exception.code, 10,
                          """Test that the correct exception is raised
                          when an invalid email is given.""")

    def assert_result_equals(self, response, expected_result, message):
        """Asserts that a result exists in the response and that the
        result is equal to the expected_result."""
        response_obj = json.loads(response)
        self.assertTrue('result' in response_obj, """Assert that the
        response has a result""")
        self.assertEquals(response_obj['result'], expected_result,
                          message)

    def assert_error_equals(self, response, expected_error_code, message):
        """Asserts that an error exists in the response and that the
        error code is equal to the expected error code."""
        response_obj = json.loads(response)
        self.assertTrue('error' in response_obj,
                        """Assert that the response has an error""")
        self.assertEquals(response_obj['error']['code'],
                          expected_error_code, message)

    def assert_contains_only_characters(self, s, allowed_characters,
                                        message):
        # Check that the session keys only contains allowed
        # characters. See http://stackoverflow.com/a/1323374 for how
        # this works.
        self.assertTrue(set(session_key) <= set(allowed_characters),
                        message)

    def test_login_valid_user_valid_session_key(self):
        (email, password) = self.USERS[0]
        session_key = self.rpc.login(email, password)

        allowed_characters = string.ascii_letters + string.digits
        self.assert_contains_only_characters
        (session_key, allowed_characters,
         """Test that the generated session key
         contains only allowed characters.""")

    def test_login_invalid_password(self):
        """Test that attempting to login with an invalid password
        raises an invalid account credentials RPCError"""
        with self.assertRaises(jsonrpc.RPCError) as err:
            self.rpc.login(self.USERS[0][0], 'incorrectpassword')
        self.assertEquals(err.exception.code, 2)

    def test_login_invalid_email(self):
        """Test that attempting to login with an invalid email
        raises an invalid account credentials RPCError"""
        with self.assertRaises(jsonrpc.RPCError) as err:
            self.rpc.login('nonexistingemail', self.USERS[0][1])
        self.assertEquals(err.exception.code, 2)

    def generate_rpc_request(self, method, params,
                             session='', user_id=-1):
        """Creates an JSON RPC request. Method and params should be
        strings."""
        return '{"jsonrpc": "2.0", "method": "' + method + '",' +\
            '"params": ' + params + ', "id": 2, "session": "' +\
            session + '", "user_id": ' + str(user_id) + ' }'

    def test_login_valid_request(self):
        (email, password) = self.USERS[0]
        request = self.generate_rpc_request('login', '["{}","{}"]'.
                                            format(email, password))
        response = self.rpc.rpc_invoke(request)
        r_obj = json.loads(response)
        allowed_characters = string.ascii_letters + string.digits
        self.assert_contains_only_characters
        (r_obj['result'], allowed_characters,
         """Test that the generated session key
         contains only allowed characters.""")

    def test_create_team_correct_session(self):
        (email, password) = self.USERS[0]
        session_key = self.rpc.login(email, password)
        team_name = 'Team TEST'
        par = '["{}"]'.format(team_name)
        request = self.generate_rpc_request('create_team', par,
                                            session_key, 1)

        response = self.rpc.rpc_invoke(request)
        response_obj = json.loads(response)
        team_id = response_obj['result']

        self.assertEquals(self.tdb.get_team_name(team_id), team_name,
                          """Test that a team with the correct id and
                          name has been created""")
        self.assertEquals(self.udb.get_user_team_status(1),
                          (team_id, True),
                          """Test that the creating user is in the
                          correct team and is a coach""")

    def test_create_team_incorrect_session(self):
        session_key = 'incorrect key'
        team_name = 'Team TEST'
        par = '["{}"]'.format(team_name)
        request = self.generate_rpc_request('create_team', par,
                                            session_key, 1)

        response = self.rpc.rpc_invoke(request)
        self.assert_error_equals(
            response, 3,
            """Test that the correct exception is raised when an
            incorrect key is provided to pcreate_team RPC.""")

    def test_create_team_incorrect_user(self):
        (email, password) = self.USERS[0]
        session_key = self.rpc.login(email, password)
        team_name = "Team TEST"
        incorrect_user_id = -1
        par = '["{}"]'.format(team_name)
        request = self.generate_rpc_request('create_team', par,
                                            session_key,
                                            incorrect_user_id)

        response = self.rpc.rpc_invoke(request)
        self.assert_error_equals(
            response, 3,
            """Test that the correct error is raised
            when a non existing user id is provided to
            create_team.""")

    def test_add_correct_to_team(self):
        self.set_user_and_authenticated(self.test_team_coach_id)
        self.rpc.add_to_team(self.USERS[2][0])

        (team_id, coach) = self.udb.get_user_team_status(3)
        self.assertEquals(team_id, self.test_team_id,
                          """Test that a user is added to the correct
                          team with add_to_team RPC""")
        self.assertEquals(coach, False,
                          """Test that a user is set as __not__ a
                          coach when they are added with the
                          add_to_team RPC""")

    def test_add_to_team_not_authenticated(self):
        self.set_user_and_authenticated(3, False)
        with self.assertRaises(jsonrpc.RPCError) as err:
            self.rpc.add_to_team(self.USERS[2][0])

        self.assertEquals(err.exception.code, 3,
                          """Test that the correct exception is raised
                          when an incorrect key is provided to
                          create_team RPC.""")

    def test_add_to_team_not_coach(self):
        self.set_user_and_authenticated(self.test_team_coach_id)
        self.rpc.add_to_team(self.USERS[2][0])

        with self.assertRaises(jsonrpc.RPCError) as err:
            self.set_user_and_authenticated(3)
            self.rpc.add_to_team(self.USERS[3][0])

        self.assertEquals(err.exception.code, 5,
                          """Test that the correct exception is raised
                          when a user who isn't a coach attempts to
                          add someone to his team.""")

    def test_add_to_team_invalid_email(self):
        with self.assertRaises(jsonrpc.RPCError) as err:
            self.set_user_and_authenticated(self.test_team_coach_id)
            self.rpc.add_to_team('nouserhasthis@email.com')

        self.assertEquals(err.exception.code, 7,
                          """Test that the correct exception is raised
                          when an user tries to add an invalid email
                          to a team.""")

    def test_my_team_info_correct(self):
        self.set_user_and_authenticated(self.test_team_coach_id)
        team_info = self.rpc.my_team_info()

        self.assertEquals(team_info[0], self.test_team_id,
                          """Test that the correct team id is returned""")
        self.assertEquals(team_info[1], self.test_team_name,
                          """Test that the correct team name is
                          returned""")
        self.assertEquals(team_info[2][0], self.test_team_coach_id,
                          """Test that the first member returned is
                          the correct coach""")

    def test_add_health_data_correct(self):
        user_id = 2
        date = datetime.date(2016, 12, 31)
        heart_rate = 900
        weight = 80
        comment = 'My heart rate is way too high!'
        self.set_user_and_authenticated(user_id)
        self.rpc.add_health_data(date, heart_rate, weight, comment)
        self.assertEquals(self.hdb.get_health_data(user_id, date),
                          (heart_rate, weight, comment),
                          """Test that the add_health_data RPC adds
                          the data correctly""")

    def test_add_health_data_coach(self):
        user_id = self.test_team_coach_id
        date = datetime.date(2016, 12, 31)
        heart_rate = 900
        weight = 80
        comment = 'My heart rate is way too high!'
        self.set_user_and_authenticated(user_id)
        with self.assertRaises(jsonrpc.RPCError) as err:
            self.rpc.add_health_data(date, heart_rate, weight, comment)

        self.assertEquals(err.exception.code, 8,
                          """Test that the correct exception is raised
                          when an coach tries to add health data.""")

    def test_add_health_data_not_authencitated(self):
        user_id = 2
        date = datetime.date(2016, 12, 31)
        heart_rate = 900
        weight = 80
        comment = 'My heart rate is way too high!'
        with self.assertRaises(jsonrpc.RPCError) as err:
            self.rpc.add_health_data(date, heart_rate, weight, comment)

        self.assertEquals(err.exception.code, 3,
                          """Test that the correct exception is raised
                          when an user isn't authencitated.""")

    def populate_test_user_health(self, user_id):
        self.date1 = datetime.date.today() - datetime.timedelta(days=2)
        self.date2 = datetime.date.today() - datetime.timedelta(days=6)
        self.heart_rate1 = 10
        self.heart_rate2 = 20
        self.set_user_and_authenticated(user_id)
        self.rpc.add_health_data(self.date1, self.heart_rate1, 0, "test")
        self.set_user_and_authenticated(user_id)
        self.rpc.add_health_data(self.date2, self.heart_rate2, 0, "test")

    def test_get_my_health_data_3_days(self):
        user_id = 2
        self.populate_test_user_health(2)

        self.set_user_and_authenticated(user_id)
        data = self.rpc.get_my_health_data(3)

        self.assertEquals(len(data), 1,
                          """Test that one health entry is found from
                          three days in the past to now""")
        self.assertEquals(data[0][1], self.heart_rate1)

    def test_get_my_health_data_7_days(self):
        user_id = 2
        self.populate_test_user_health(2)

        self.set_user_and_authenticated(user_id)
        data = self.rpc.get_my_health_data(7)

        self.assertEquals(len(data), 2,
                          """Test that one health entry is found from
                          three days in the past to now""")

        for entry in data:
            if entry[0] == self.date1:
                self.assertEquals(entry[1], self.heart_rate1)
            elif entry[0] == self.date2:
                self.assertEquals(entry[1], self.heart_rate2)
            else:
                self.assertTrue(False, """The entry has an incorrect
                date""")

    def test_get_my_health_data_not_authenticated(self):
        with self.assertRaises(jsonrpc.RPCError) as err:
            self.rpc.get_my_health_data(7)

        self.assertEquals(err.exception.code, 3,
                          """Test that the correct exception is raised
                          when an user isn't authencitated.""")

    def test_get_team_health_data_correct(self):
        user_id = 7
        self.set_user_and_authenticated(self.test_team_coach_id)
        self.rpc.add_to_team(self.USERS[user_id - 1][0])
        self.populate_test_user_health(user_id)

        self.set_user_and_authenticated(self.test_team_coach_id)
        team_health_data = self.rpc.get_team_health_data(3)

        self.assertEquals(len(team_health_data), 1)

        self.assertEquals(self.udb.get_user_id(team_health_data[0][0]),
                          user_id,
                          """Test that only health data from the
                          correct user (not the coach) is returned.""")

        self.assertEquals(team_health_data[0][1][0][1], self.heart_rate1)

    def test_get_team_health_data_not_authenticated(self):
        self.rpc.current_user_id = self.test_team_coach_id
        with self.assertRaises(jsonrpc.RPCError) as err:
            self.rpc.get_team_health_data(7)

        self.assertEquals(err.exception.code, 3,
                          """Test that the correct exception is raised
                          when an user isn't authencitated.""")

    def test_get_team_health_data_not_coach(self):
        user_id = 7
        self.set_user_and_authenticated(self.test_team_coach_id)
        self.rpc.add_to_team(self.USERS[user_id - 1][0])

        self.set_user_and_authenticated(user_id)
        with self.assertRaises(jsonrpc.RPCError) as err:
            self.rpc.get_team_health_data(7)

        self.assertEquals(err.exception.code, 5,
                          """Test that the correct exception is raised
                          when an user isn't a coach.""")

    def test_set_coach_status_correct_to_coach(self):
        user_id = 7
        self.tdb.add_user_to_team(self.test_team_coach_id, user_id)

        self.set_user_and_authenticated(self.test_team_coach_id)
        self.rpc.set_coach_status(self.USERS[user_id - 1][0], True)

        self.assertTrue(self.udb.get_user_team_status(user_id)[1],
                        """Test that the user is correctly marked a
                        coach""")

    def test_set_coach_status_correct_to_not_coach(self):
        user_id = 7
        self.tdb.add_user_to_team(self.test_team_coach_id, user_id)

        self.set_user_and_authenticated(self.test_team_coach_id)
        self.rpc.set_coach_status(self.USERS[user_id - 1][0], True)

        self.set_user_and_authenticated(user_id)
        self.rpc.set_coach_status(
            self.USERS[self.test_team_coach_id - 1][0], False)

        self.assertFalse(self.udb.get_user_team_status
                         (self.test_team_coach_id)[1],
                         """Test that the user is correctly marked not
                         a coach""")

    def test_set_coach_status_not_authenticated(self):
        self.rpc.current_user_id = self.test_team_coach_id

        with self.assertRaises(jsonrpc.RPCError) as err:
            self.rpc.set_coach_status(
                self.USERS[self.test_team_coach_id - 1][0], True)

        self.assertEquals(err.exception.code, 3,
                          """Test that the correct exception is raised
                          when an user isn't authencitated.""")

    def test_set_coach_status_remove_last_coach(self):
        user_id = 7
        self.tdb.add_user_to_team(self.test_team_coach_id, user_id)

        self.set_user_and_authenticated(self.test_team_coach_id)
        with self.assertRaises(jsonrpc.RPCError) as err:
            self.rpc.set_coach_status(
                self.USERS[self.test_team_coach_id - 1][0], False)

        self.assertEquals(err.exception.code, 9,
                          """Test that the correct exception is raised
                          when an coach tries to remove himself as the
                          last coach.""")

    def test_set_coach_status_non_existing_email(self):
        self.set_user_and_authenticated(self.test_team_coach_id)
        with self.assertRaises(jsonrpc.RPCError) as err:
            self.rpc.set_coach_status('nietbestaand@email.com', False)

        self.assertEquals(err.exception.code, 7,
                          """Test that the correct exception is raised when the
                          coach status is set of an non existing email
                          user.""")

    def test_remove_from_team_correct(self):
        user_id = 7
        self.tdb.add_user_to_team(self.test_team_coach_id, user_id)

        self.set_user_and_authenticated(self.test_team_coach_id)
        self.rpc.remove_from_team(self.USERS[user_id - 1][0])

        self.assertEquals(self.udb.get_user_team_status(user_id)[0],
                          None,
                          """Test that you can correctly remove an
                          user from a team.""")

    def test_remove_from_team_not_authenticated(self):
        self.rpc.current_user_id = self.test_team_coach_id

        with self.assertRaises(jsonrpc.RPCError) as err:
            self.rpc.remove_from_team(self.USERS[2][0])

        self.assertEquals(err.exception.code, 3,
                          """Test that the correct exception is raised
                          when an user isn't authencitated.""")

    def test_remove_from_team_incorrect_email(self):
        self.set_user_and_authenticated(self.test_team_coach_id)
        with self.assertRaises(jsonrpc.RPCError) as err:
            self.rpc.remove_from_team('nietbestaand@email.com')

        self.assertEquals(err.exception.code, 7,
                          """Test that the correct exception is raised
                          when an user isn't authencitated.""")

    def test_remove_from_team_not_coach(self):
        user_id = 7
        self.set_user_and_authenticated(self.test_team_coach_id)
        self.rpc.add_to_team(self.USERS[user_id - 1][0])

        self.set_user_and_authenticated(user_id)
        with self.assertRaises(jsonrpc.RPCError) as err:
            self.rpc.remove_from_team(
                self.USERS[self.test_team_coach_id - 1][0])

        self.assertEquals(err.exception.code, 5,
                          """Test that the correct exception is raised
                          when an user isn't a coach.""")

    def test_add_training_correct(self):
        user_id = 1
        time = datetime.datetime.now()
        type_is_ed = True
        comment = 'My training'
        return_interval_list = [(200, 120, 10, datetime.timedelta(seconds=10)),
                                (180, 180, 90, datetime.timedelta(seconds=30))]
        interval_list = [(200, 120, 10, 10),
                         (180, 180, 90, 30)]

        self.set_user_and_authenticated(user_id)
        self.rpc.add_training(time, type_is_ed, comment, interval_list)

        [(training_id, f_time, f_type, f_comment)] =\
            self.trdb.get_past_training_data(user_id)

        self.assertEquals(f_time, time)
        self.assertEquals(f_type, type_is_ed)
        self.assertEquals(f_comment, comment)

        [interval_1, interval_2] = self.idb\
                                       .get_training_interval_data(training_id)

        for interval in return_interval_list:
            self.assertTrue(interval == interval_1 or
                            interval == interval_2)

        self.assertFalse(interval_1 == interval_2)

    def populate_test_user_training(self, user_id):
        self.time1 = datetime.datetime.now()
        self.time2 = datetime.datetime.now() - datetime.timedelta(days=2)
        self.time3 = datetime.datetime.now() - datetime.timedelta(days=5)
        self.type_is_ed = True
        self.comment = 'My training'
        self.interval_list = [(200, 120, 10, 10),
                              (180, 180, 90, 30)]

        self.set_user_and_authenticated(user_id)
        self.rpc.add_training(self.time1, self.type_is_ed, self.comment,
                              self.interval_list)
        self.set_user_and_authenticated(user_id)
        self.rpc.add_training(self.time2, self.type_is_ed, self.comment,
                              self.interval_list)
        self.set_user_and_authenticated(user_id)
        self.rpc.add_training(self.time3, self.type_is_ed, self.comment,
                              self.interval_list)

    def test_get_my_training_data_3_days(self):
        user_id = 3
        self.populate_test_user_training(user_id)

        self.set_user_and_authenticated(user_id)
        data = self.rpc.get_my_training_data(3)

        self.assertEquals(len(data), 2,
                          """Test that two training entries are found from
                          three days in the past to now""")
        self.assertEquals(data[1][0], self.time1)
        self.assertEquals(data[0][0], self.time2)
        self.assertEquals(data[0][3][0][0], self.interval_list[0][0])

    def test_get_my_training_data_7_days(self):
        user_id = 4
        self.populate_test_user_training(user_id)

        self.set_user_and_authenticated(user_id)
        data = self.rpc.get_my_training_data(7)

        self.assertEquals(len(data), 3,
                          """Test that three training entries are found from
                          seven days in the past to now""")
        self.assertEquals(data[2][0], self.time1)
        self.assertEquals(data[1][0], self.time2)
        self.assertEquals(data[0][0], self.time3)
        self.assertEquals(data[2][3][0][0], self.interval_list[0][0])

    def test_add_training_not_authenticated(self):
        self.set_user_and_authenticated(3, False)
        with self.assertRaises(jsonrpc.RPCError) as err:
            self.rpc.add_training(None, None, None, None)

        self.assertEquals(err.exception.code, 3,
                          """Test that the correct exception is raised
                          when an incorrect key is provided to
                          create_team RPC.""")

    def test_add_training_coach(self):
        user_id = self.test_team_coach_id
        time = datetime.datetime.now()
        type_is_ed = True
        comment = 'My training'
        interval_list = [(200, 120, 10, 10),
                         (180, 180, 90, 30)]

        self.set_user_and_authenticated(user_id)

        with self.assertRaises(jsonrpc.RPCError) as err:
            self.rpc.add_training(time, type_is_ed, comment, interval_list)

        self.assertEquals(err.exception.code, 8,
                          """Test that the correct exception is raised
                          when an user is a coach.""")

    def test_get_team_training_data_no_rowers(self):
        self.set_user_and_authenticated(self.test_team_coach_id)
        team_training_data = self.rpc.get_team_training_data(7)

        self.assertEquals(team_training_data, [],
                          """Test that the team training data is an
                          empty list when there are no rowers in the
                          team""")

    def test_get_team_training_data_no_trainings(self):
        self.set_user_and_authenticated(self.test_team_coach_id)
        self.rpc.add_to_team(self.USERS[3][0])

        self.set_user_and_authenticated(self.test_team_coach_id)
        team_training_data = self.rpc.get_team_training_data(7)

        self.assertEquals(len(team_training_data), 1)
        self.assertEquals(team_training_data[0][0], self.USERS[3][0])
        self.assertEquals(team_training_data[0][1], [])

    def test_get_team_training_data_training_and_interval(self):
        user_id = 4
        user_email = self.USERS[user_id - 1][0]

        self.set_user_and_authenticated(self.test_team_coach_id)
        self.rpc.add_to_team(user_email)

        time = datetime.datetime.now()
        type_is_ed = True
        comment = 'My training'
        interval = (200, 120, 10, 10)
        return_interval = (200, 120, 10, datetime.timedelta(seconds=10))

        self.set_user_and_authenticated(user_id)
        self.rpc.add_training(time, type_is_ed, comment, [interval])

        self.set_user_and_authenticated(self.test_team_coach_id)
        team_training_data = self.rpc.get_team_training_data(7)

        self.assertEquals(team_training_data[0][0], user_email)
        self.assertEquals(team_training_data[0][1][0][0], time)
        self.assertEquals(team_training_data[0][1][0][1], type_is_ed)
        self.assertEquals(team_training_data[0][1][0][2], comment)
        self.assertEquals(team_training_data[0][1][0][3],
                          [return_interval])


if __name__ == '__main__':
    suite = u.TestLoader()\
                    .loadTestsFromTestCase(CrwJsonRpcTest)
    u.TextTestRunner(verbosity=2).run(suite)
