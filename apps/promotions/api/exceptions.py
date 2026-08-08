from rest_framework.views import exception_handler

from .responses import error_response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        # Handle standard DRF exceptions
        code = "invalid_request"
        message = str(exc)

        if response.status_code == 404:
            code = "not_found"
            message = "The requested resource was not found."

        return error_response(
            code=code, message=message, status_code=response.status_code
        )

    # Unhandled exceptions (500)
    if isinstance(exc, Exception):
        return error_response(
            code="internal_error",
            message="An unexpected error occurred.",
            status_code=500,
        )

    return None
