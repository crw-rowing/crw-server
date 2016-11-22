import json


class JsonRPC:
    version = '2.0'

    def execute(self, payload):
        def execute_single(data):
            if type(data) != dict:
                raise ValueError

            response = {
                'jsonrpc': JsonRPC.version,
            }
            
            # TODO execute method

            if 'id' in data:
                response[id] = data[id]
            else:
                response = None

            return response

        response = {
            'jsonrpc': JsonRPC.version,
        }

        try:
            data = json.loads(payload)
            if type(data) == list:  # Batch response
                response = filter(lambda x: x is not None,
                                  map(execute_single, data))
            else:
                response = execute_single(data)
        except ValueError:
            # TODO invalid JSON error (-32700)
            pass
        finally:
            return None if response is None else json.dumps(response)