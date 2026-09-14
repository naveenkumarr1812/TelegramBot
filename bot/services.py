from database import get_required_channels, get_resource


def parse_resource_parameter(parameter: str | None) -> int | None:
    if not parameter or not parameter.startswith("resource_"):
        return None
    value = parameter[len("resource_"):]
    return int(value) if value.isdigit() else None


__all__ = ["parse_resource_parameter", "get_resource", "get_required_channels"]
