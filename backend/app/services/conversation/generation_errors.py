"""Provider-independent generation failures at the GenerationPort boundary."""

class GenerationFailure(RuntimeError):
    """Base for safe, provider-independent generation failure categories."""


class GenerationTimeout(GenerationFailure, TimeoutError):
    pass


class GenerationCancelled(GenerationFailure):
    pass


class GenerationUnavailable(GenerationFailure):
    pass


class GenerationMalformed(GenerationFailure, ValueError):
    pass


class GenerationVersionUnsupported(GenerationFailure, ValueError):
    pass


