class ExecutorError(Exception):
    """Base executor failure."""


class UnknownExecutorError(ExecutorError):
    def __init__(self, executor: str) -> None:
        super().__init__(f"Unknown executor: {executor}")
        self.executor = executor


class MissingTemplateArgError(ExecutorError):
    def __init__(self, arg_name: str) -> None:
        super().__init__(f"Missing template argument: {arg_name}")
        self.arg_name = arg_name


class ConnectorConfigError(ExecutorError):
    pass
