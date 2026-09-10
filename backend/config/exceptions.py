"""
Custom DRF exception handler conforming to API_SPECIFICATION.md:
Error responses follow { "code", "message", "details"? }
"""

from rest_framework import status
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        data = response.data
        code = "error"
        message = "An error occurred."
        details = None

        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            code = "authentication_failed"
            message = "Authentication credentials were not provided or are invalid."
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            code = "permission_denied"
            message = "You do not have permission to perform this action."
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            code = "not_found"
            message = "The requested resource was not found."
        elif response.status_code == status.HTTP_400_BAD_REQUEST:
            code = "validation_error"
            message = "Invalid input data."
        elif response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            code = "method_not_allowed"
            message = "Method not allowed for this resource."
        elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            code = "rate_limit_exceeded"
            message = "Request was throttled. Please slow down."

        # Process message and details from DRF payload
        if isinstance(data, dict):
            if "detail" in data:
                message = str(data["detail"])
                remaining_details = {k: v for k, v in data.items() if k != "detail"}
                if remaining_details:
                    details = remaining_details
            else:
                details = data
        elif isinstance(data, list):
            details = data

        custom_data = {
            "code": code,
            "message": message,
        }
        if details is not None:
            custom_data["details"] = details

        response.data = custom_data

    return response
