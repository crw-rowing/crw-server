import unittest as u
import database as d
import crw_jsonrpc as e
import json

# Before testing, make an empty database named userdatabasetest and
# create an file named test_database.properties with one line in the
# same folder as this file, the name of the account you created the
# database under..
with open('test_database.properties') as propFile:
    user = propFile.read().splitlines()[0]
DATABASE = 'userdatabasetest'
print 'Testing with database ' + DATABASE + ' with the user ' + user


class CrwJsonRpcTest(u.TestCase):
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
        self.rpc = e.CrwJsonRpc(self.db)

    def tearDown(self):
        self.db.drop_all_tables()
        self.db.close_database_connection()

    def populate_database(self):
        """Populates the database with the users saved in the USERS
        array, by calling self.db.add_user for each."""
        for user in self.USERS:
            self.udb.add_user(user[0], user[1])

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
        self.asserTrue('error' in response_obj,
                       """Assert that the response has an error""")
        self.assertEquals(response_obj['error'][code],
                          expected_error_code, message)


if __name__ == '__main__':
    suite = u.TestLoader()\
                    .loadTestsFromTestCase(CrwJsonRpcTest)
    u.TextTestRunner(verbosity=2).run(suite)
