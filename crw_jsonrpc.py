from jsonrpc import JsonRpcServer
import jsonrpc
import database as d


class CrwJsonRpc(JsonRpcServer):
    def __init__(self, database):
        self.udb = d.UserDatabase(database)
        self.tdb = d.TeamDatabase(database)
        self.sdb = d.SessionDatabase(database)

    def echo(self, s):
        return s

    def create_account(self, email, password):
        try:
            self.udb.add_user(email, password)
            return True
        except ValueError, e:
            raise error_account_already_exists

    def login(self, email, password):
        """This function will verify the user and return a new session
        key if the user has been authencitated correctly."""
        if (not self.udb.does_user_email_exist(email)) or\
           (not self.udb.verify_user(email, password)):
            raise error_invalid_account_credentials

        return self.sdb.generate_session_key(
            self.udb.get_user_id(email))


error_account_already_exists = jsonrpc.RPCError(
    1, """There is already an account associated
    with this email""")
error_invalid_account_credentials = jsonrpc.RPCError(
    2, """The provided credentials are incorrect""")
