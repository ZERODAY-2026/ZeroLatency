class TriageError(Exception):
    pass


class DocumentError(TriageError):
    pass


class UnsupportedFormat(DocumentError):
    pass


class EncryptedDocument(DocumentError):
    pass


class UnreadableDocument(DocumentError):
    pass


class NoExtractableText(DocumentError):
    pass


class ModelError(TriageError):
    pass


class OllamaUnavailable(ModelError):
    pass


class ModelMissing(ModelError):
    pass


class ModelTimeout(ModelError):
    pass


class InvalidModelOutput(ModelError):
    pass


class EmptyQuestion(TriageError):
    pass


class PrivacyViolation(TriageError):
    pass


class UnsupportedModel(ModelError):
    """The requested model identifier is not on the allowlist."""


class InsufficientMemory(ModelError):
    pass


class AnalysisCancelled(TriageError):
    pass


class DocumentNotFound(TriageError):
    pass


class Busy(TriageError):
    """Another analysis or question is already running on the local model."""


class LimitExceeded(TriageError):
    pass
