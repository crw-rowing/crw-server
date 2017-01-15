import json
import datetime


class JsonRpcServer:
    """
    Superclass for JSON-RPC method servers.
    Subclasses can simply implement methods, which will be automatically
    available for the JSON-RPC protocol.
    Reserved method names are `version`, `rpc_invoke`, `rpc_invoke_single`
    and the default object members.
    """
    version = '2.0'

    def rpc_invoke_single(self, data):
        response = {
            'jsonrpc': JsonRpcServer.version,
            'id': None
        }
        try:
            if type(data) != dict or \
               'jsonrpc' not in data or \
               data['jsonrpc'] != JsonRpcServer.version or \
                    'method' not in data:
                raise RPCError.invalid_request

            if 'id' in data:
                response['id'] = data['id']
            else:
                response = None

            meth = data['method']
            params = data.get('params', None)

            if params is not None and type(params) not in (dict, list):
                raise RPCError.invalid_params

            # Ensure it is a method overridden in JsonRpcServer subclass
            if hasattr(self, meth) and not hasattr(JsonRpcServer, meth):
                m = getattr(self, meth)
                if type(params) is list:
                    result = m(*params)
                elif type(params) is dict:
                    result = m(**params)
                else:
                    result = m()

                if response is not None:
                    response['result'] = result
            else:
                raise RPCError.method_not_found
        except RPCError as e:
            if response is not None:
                response['error'] = e.serialize()
        except Exception as e:
            response['error'] = RPCError.internal_error(e).serialize()
        finally:
            return response

    def rpc_invoke(self, payload):
        """
        Execute a JSON-RPC request and return the response as JSON.
        Supports batch requests.
        """
        response = {
            'jsonrpc': JsonRpcServer.version,
            'id': None,
        }
        try:
            data = json.loads(payload)
            if type(data) == list:  # Batch response
                response = filter(lambda x: x is not None,
                                  map(rpc_invoke_single, data))
            else:
                response = self.rpc_invoke_single(data)
        except ValueError:
            response['error'] = RPCError.parse.serialize()
        except RPCError as e:
            response['error'] = e.serialize()
        finally:
            return None if response is None else json.dumps(
                response, cls=DateTimeEncoder)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return (datetime.datetime.min + obj).time().isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)         


class RPCError(Exception):
    """
    JSON-RPC specific error.
    """
    def __init__(self, code, message, data=None):
        self.code = code
        self.message = message
        self.data = data

    def __str__(self):
        return '{}, {}, {}'.format(self.code, self.message, self.data)

    def serialize(self):
        """
        Format the error as a dict which can
        be used in the error response JSON.
        """
        d = {
            'code': self.code,
            'message': self.message
        }

        if self.data is not None:
            d['data'] = str(self.data)

        return d


RPCError.parse = RPCError(-32700, 'Invalid JSON')
RPCError.invalid_request = RPCError(-32600, 'Invalid request')
RPCError.method_not_found = RPCError(-32601, 'Method not found')
RPCError.invalid_params = RPCError(-32602, 'Invalid method parameters')
RPCError.internal_error = lambda e: \
    RPCError(-32603, 'Internal JSON-RPC error', data=e)
