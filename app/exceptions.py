"""Custom exceptions for Eagle Bank API.

This module defines specific exceptions used across the API layer to convey
precise business rule violations and detailed validation errors.
"""


class BadRequestException(Exception):
    """Exception raised when a request is invalid or violates validation constraints.

    Maps to the HTTP 400 BadRequestErrorResponse.

    Attributes:
        message: The high-level error message.
        field: The specific request field that failed validation.
        detail_message: The descriptive message of why validation failed.
        error_type: The type category of the error (e.g., 'value_error').
    """

    def __init__(
        self,
        message: str,
        field: str,
        detail_message: str,
        error_type: str = "value_error",
    ):
        """Initialize BadRequestException."""
        super().__init__(message)
        self.message = message
        self.field = field
        self.detail_message = detail_message
        self.error_type = error_type
