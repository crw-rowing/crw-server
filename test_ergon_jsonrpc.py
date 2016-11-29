import unittest as u
import database as d
import ergon_jsonrpc as e
import json

# Before testing, make an empty database named userdatabasetest and
# create an file named test_database.properties with one line in the
# same folder as this file, the name of the account you created the
# database under..
with open('test_database.properties') as propFile:
    user = propFile.readline()
DATABASE = 'userdatabasetest'
print 'Testing with database ' + DATABASE + ' with the user ' + user


class ErgonJsonRpcTest(u.TestCase):
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
        self.rpc = e.ErgonJsonRpc(self.db)

    def tearDown(self):
        self.db.drop_user_table()
        self.db.close_database_connection()

    def populate_database(self):
        """Populates the database with the users saved in the USERS
        array, by calling self.db.add_user for each."""
        for user in self.USERS:
            self.db.add_user(user[0], user[1])

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

        self.assertTrue('result' in response_obj,
                        """Test that the response includes a result
                        field""")
        self.assertEquals(response_obj['result'], True)

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

        self.assertTrue(self.db.verify_user('nieuw@email.com',
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
        response_obj = json.loads(rpc_response)

        self.assertTrue('error' in response_obj,
                        """Test that the response contains an error
                        field (since adding a duplicate account should
                        return an error).""")

        rpc_error = response_obj['error']
        self.assertEquals(rpc_error['code'], -32000,
                          """Test that the correct error code is
                          returned for a duplicate account""")


if __name__ == '__main__':
    suite = u.TestLoader()\
                    .loadTestsFromTestCase(ErgonJsonRpcTest)
    u.TextTestRunner(verbosity=2).run(suite)
