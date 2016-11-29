from jsonrpc import JsonRpcServer
import jsonrpc


class ErgonJsonRpc(JsonRpcServer):
    def __init__(self, user_database):
        self.user_database = user_database

    def echo(self, s):
        return s

    def create_account(self, email, password):
        try:
            self.user_database.add_user(email, password)
            return True
        except ValueError, e:
            raise ErgonJsonRpc.account_already_exists


ErgonJsonRpc.account_already_exists = jsonrpc.RPCError(
    -32000, """There is already an account associated
    with this email""")
