import json


class JsonRPC:
    version = '2.0'

    def execute(self, payload):
        def execute_single(data):
            if type(data) != dict or \
                    'jsonrpc' not in data or \
                    data['jsonrpc'] != JsonRPC.version:
                raise RPCError.invalid_request

            response = {
                'jsonrpc': JsonRPC.version,
            }

            # TODO execute method

            if 'id' in data:
                response['id'] = data['id']
            else:
                response = None

            return response

        response = {
            'jsonrpc': JsonRPC.version,
            'id': None,
        }

        try:
            data = json.loads(payload)
            if type(data) == list:  # Batch response
                response = filter(lambda x: x is not None,
                                  map(execute_single, data))
            else:
                response = execute_single(data)
        except ValueError:
            response['error'] = RPCError.parse.serialize()
        except RPCError as e:
            response['error'] = e.serialize()
        finally:
            return None if response is None else json.dumps(response)


class RPCError(Exception):
    parse = RPCError(-32700, 'Invalid JSON')
    invalid_request = RPCError(-32600, 'Invalid request')
    method_not_found = RPCError(-32601, 'Method not found')
    invalid_params = RPCError(-32602, 'Invalid method parameters')
    internal_error = RPCError(-32603, 'Internal JSON-RPC error')

    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return '{}, {}'.format(self.code, self.message)

    def serialize(self):
        return {
            'code': self.code,
            'message': self.message
        }
