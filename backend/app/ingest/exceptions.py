class IngestError(Exception):
    """Base exception for ingest errors"""
    pass


class UnparseableFileError(IngestError):
    """Raised when a file cannot be parsed"""
    def __init__(self, filename: str, reason: str):
        self.filename = filename
        self.reason = reason
        super().__init__(f"File '{filename}' is unparseable: {reason}")


class NotMachineReadableError(IngestError):
    """Raised when a file contains no extractable text"""
    def __init__(self, filename: str):
        self.filename = filename
        super().__init__(f"File '{filename}' contains no extractable text (not machine-readable)")
