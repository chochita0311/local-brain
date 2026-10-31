"""Bounded, non-identifying diagnostics shared by models and explicit tools."""


class ExperimentError(ValueError):
    """Only fixed, non-identifying diagnostics cross the command boundary."""


def require(condition, code="INVALID_INPUT"):
    if not condition:
        raise ExperimentError(code)
