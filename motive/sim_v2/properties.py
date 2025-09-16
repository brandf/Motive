from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class PropertyType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ENUM = "enum"
    OBJECT = "object"  # For complex nested data (lists, dicts, etc.)


@dataclass(frozen=True)
class PropertySchema:
    type: PropertyType
    default: Any = None
    # For ENUM support; ignored for other types in this MVP
    allowed_values: Optional[list] = None


class PropertyStore:
    """Typed dynamic property store with simple type enforcement.

    MVP features:
    - Enforces primitive types (string/number/boolean/enum)
    - Initializes values from schema defaults
    - get/set API with type and key validation
    """

    def __init__(self, schema: Dict[str, PropertySchema]):
        self._schema: Dict[str, PropertySchema] = dict(schema)
        self._values: Dict[str, Any] = {key: sch.default for key, sch in schema.items()}

    def get(self, key: str, default: Any = None) -> Any:
        if key not in self._schema:
            if default is not None:
                return default
            raise KeyError(f"Unknown property: {key}")
        return self._values.get(key)

    def set(self, key: str, value: Any) -> None:
        schema = self._schema.get(key)
        if schema is None:
            raise KeyError(f"Unknown property: {key}")

        if not self._is_type_compatible(schema, value):
            expected = schema.type.value
            actual = type(value).__name__
            raise TypeError(f"Property '{key}' expects type {expected}, got {actual}")

        if schema.type is PropertyType.ENUM and schema.allowed_values is not None:
            if value not in schema.allowed_values:
                raise ValueError(
                    f"Property '{key}' expects one of {schema.allowed_values}, got {value}"
                )
        self._values[key] = value

    @staticmethod
    def _is_type_compatible(schema: PropertySchema, value: Any) -> bool:
        if schema.type is PropertyType.STRING:
            return isinstance(value, str)
        if schema.type is PropertyType.NUMBER:
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        if schema.type is PropertyType.BOOLEAN:
            return isinstance(value, bool)
        if schema.type is PropertyType.ENUM:
            # Enum values are represented by their literal value (often str)
            return isinstance(value, (str, int)) or value is None
        if schema.type is PropertyType.OBJECT:
            # OBJECT type accepts any complex data (dict, list, etc.)
            return isinstance(value, (dict, list)) or value is None
        return True


