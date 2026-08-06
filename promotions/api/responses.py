from rest_framework.response import Response

def success_response(data, meta=None, status_code=200):
    """
    Standard format for successful responses.
    List endpoints should provide a 'meta' dictionary.
    """
    payload = {"data": data}
    if meta is not None:
        payload["meta"] = meta
    return Response(payload, status=status_code)

def error_response(code, message, status_code=400):
    """
    Standard format for error responses.
    """
    payload = {
        "error": {
            "code": code,
            "message": message
        }
    }
    return Response(payload, status=status_code)
