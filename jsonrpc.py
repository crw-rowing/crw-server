import json


class JsonRPC:
    version = '2.0'

    def execute(self, payload):
        def execute_single(data):
            if type(data) != dict or \
                'jsonrpc' not in data or \
                data['jsonrpc'] != JsonRPC.version:
                raise ValueError

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
            response['error'] = {
                'code': -32700,
                'message': 'Invalid request'
            }
        finally:
            return None if response is None else json.dumps(response)