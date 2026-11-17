"""Public terminal failures shared by host adapters and the legacy parity fixture."""


class TerminalError(RuntimeError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
