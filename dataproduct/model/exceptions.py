from dataproduct.model.run import ResultEnum


class DataProductException(Exception):
    """A handled error surfaced as a check in the run result (no traceback)."""

    def __init__(
        self,
        type: str,
        name: str,
        reason: str,
        engine: str = "dataproduct",
        result: ResultEnum = ResultEnum.error,
    ):
        self.type = type
        self.name = name
        self.reason = reason
        self.engine = engine
        self.result = result
        super().__init__(reason)

    def __str__(self) -> str:
        return f"{self.name}: {self.reason}"
