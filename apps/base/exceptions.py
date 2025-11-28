class BusinessLogicException(Exception):
    """Custom exception for business logic errors."""
    def __init__(self, code, message, data=None):
        self.code = code
        self.message = message
        self.data = data or {}
        super().__init__(self.message)
