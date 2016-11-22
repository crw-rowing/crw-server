from jsonrpc import JsonRpcServer


class ErgonJsonRpc(JsonRpcServer):
    def echo(self, s):
        return s