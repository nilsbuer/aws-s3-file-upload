"""InputFields dataclass for input parsing and validation."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any, Dict, List, get_type_hints, Union, get_origin, get_args
from fields.output import OutputFields
from fields.types import (
    Text,
    Integer,
    Float,
    Boolean,
    SingleChoice,
    MultiChoice,
    Credential,
    Script,
    Array,
)
from exceptions import DataValidationError
from manager import ExtensionManager
from dataclasses import fields as dataclass_fields
from dataclasses import asdict

extension_manager = ExtensionManager()


@dataclass
class InputFields:
    """Input fields from UAC with validation.

    Define fields based on your template.json fields using wrapper types.
    All fields should use wrapper types from fields.types for type safety.

    All user-defined fields should be Optional[Type] = None
    - UAC Controller enforces required field validation (template.json)
    - By the time fields reach the extension, they may be None
    - Only validate fields that have values (check for None first)
    """

    action: Optional[SingleChoice] = None
    aws_credential: Optional[Credential] = None
    aws_region: Optional[Text] = None
    bucket_name: Optional[Text] = None
    prefix: Optional[Text] = None
    max_objects: Optional[Integer] = None
    source_file: Optional[Text] = None
    object_key: Optional[Text] = None

    # Previous run output (auto-populated for re-runs)
    previous_output: Optional[OutputFields] = None

    # Skip validation flag (internal use only)
    _skip_validation: bool = False

    @staticmethod
    def preprocess_fields(fields: dict) -> dict:
        """Preprocess raw UAC fields before creating InputFields.

        Converts raw UAC values to wrapper type instances:
        1. Filters out flattened credential fields (containing dots)
        2. Wraps values in appropriate wrapper types based on field type hints
        3. Extracts previous OutputFields if present (from re-runs)
        """

        processed = {}
        previous_output_data = {}

        # Get all OutputFields field names for detection
        output_field_names = {f.name for f in dataclass_fields(OutputFields)}

        # Get type hints to detect wrapper types
        type_hints = get_type_hints(InputFields)

        # Map field names to their wrapper types
        field_wrapper_types = {}
        for field_name, field_type in type_hints.items():
            # Get base type (unwrap Optional)
            base_type = field_type
            if get_origin(field_type) is Union:
                args = get_args(field_type)
                # Filter out NoneType to get the actual type
                non_none_args = [arg for arg in args if arg is not type(None)]
                if non_none_args:
                    base_type = non_none_args[0]

            field_wrapper_types[field_name] = base_type

        for key, value in fields.items():
            # Skip flattened credential fields (e.g., "api_credential.token")
            if "." in key:
                continue

            # Check if this field belongs to OutputFields (previous run data)
            if key in output_field_names:
                previous_output_data[key] = value
                continue

            # Skip None values
            if value is None:
                processed[key] = value
                continue

            # Get the wrapper type for this field
            wrapper_type = field_wrapper_types.get(key)

            # Convert to appropriate wrapper type
            if wrapper_type == SingleChoice:
                # UAC sends as list, SingleChoice expects list
                if isinstance(value, list):
                    value = SingleChoice(_values=value)
                else:
                    value = SingleChoice(_values=[value])

            elif wrapper_type == MultiChoice:
                # UAC sends as list, MultiChoice expects list
                if isinstance(value, list):
                    value = MultiChoice(values=value)
                else:
                    value = MultiChoice(values=[value])

            elif wrapper_type == Script:
                # UAC sends as string path, Script expects Path object
                if isinstance(value, str):
                    value = Script(path=Path(value))

            elif wrapper_type == Credential:
                # UAC sends as dict, Credential expects kwargs
                if isinstance(value, dict):
                    value = Credential.from_dict(value)

            elif wrapper_type == Text:
                # Wrap string in Text
                if isinstance(value, str):
                    value = Text(value=value)

            elif wrapper_type == Integer:
                # Wrap int in Integer
                if isinstance(value, int):
                    value = Integer(value=value)

            elif wrapper_type == Float:
                # Wrap float in Float
                if isinstance(value, (int, float)):
                    value = Float(value=float(value))

            elif wrapper_type == Boolean:
                # Wrap bool in Boolean
                if isinstance(value, bool):
                    value = Boolean(value=value)

            elif wrapper_type == Array:
                # UAC sends as list of dicts, Array expects list of dicts
                if isinstance(value, list):
                    value = Array(pairs=value)

            processed[key] = value

        # If we found previous output fields, create OutputFields instance
        if previous_output_data:
            # Wrap Text fields in previous output
            for key, val in previous_output_data.items():
                if isinstance(val, str):
                    previous_output_data[key] = Text(value=val)
            processed["previous_output"] = OutputFields(**previous_output_data)

        return processed

    def to_dict(self) -> dict:
        """Convert to dict, unwrapping wrapper types and excluding internal fields.

        Returns:
            Dict with unwrapped field values, excluding _skip_validation and None previous_output
        """

        result = {}
        for f in dataclass_fields(self):
            key = f.name

            # Skip internal fields
            if key == "_skip_validation":
                continue

            value = getattr(self, key)

            # Skip None previous_output
            if key == "previous_output" and value is None:
                continue

            result[key] = self._unwrap(value)

        return result

    @staticmethod
    def _unwrap(value):
        """Unwrap a single wrapper-type instance to its raw value.

        Dispatches on the actual instance type rather than dict shape, since
        asdict()-style shape-sniffing breaks for wrapper types that carry
        extra fields alongside `value` (e.g. Integer's min_value/max_value).
        """
        if isinstance(value, SingleChoice):
            return value.value
        if isinstance(value, MultiChoice):
            return value.values
        if isinstance(value, (Text, Integer, Float, Boolean)):
            return value.value
        if isinstance(value, Script):
            return str(value.path)
        if isinstance(value, Array):
            return value.pairs
        if isinstance(value, Credential):
            return asdict(value)
        if isinstance(value, OutputFields):
            return value.to_dict()
        return value

    def __post_init__(self):
        """Validate fields after initialization."""
        if self._skip_validation:
            return

        self._validate_action()
        self._validate_aws_credential()
        self._validate_aws_region()
        self._validate_bucket_name()
        self._validate_prefix()
        self._validate_max_objects()
        self._validate_source_file()
        self._validate_object_key()

        if extension_manager.has_errors():
            raise DataValidationError(
                f"Validation failed with {extension_manager.error_count()} error(s)"
            )

    def _validate_action(self):
        """Validate action field (SingleChoice wrapper)."""
        if self.action is not None:
            valid_actions = ["List Files", "Upload File"]
            if self.action.value not in valid_actions:
                exc = DataValidationError(
                    f"Invalid action '{self.action.value}'. Valid actions: {', '.join(valid_actions)}"
                )
                extension_manager.add_error(exc, field="action", value=self.action.value)

    def _validate_aws_credential(self):
        """Validate aws_credential field (Credential wrapper)."""
        if self.aws_credential is not None:
            if not self.aws_credential.user or not self.aws_credential.password:
                exc = DataValidationError(
                    "AWS credentials must include Access Key ID (user) and Secret Access Key (password)"
                )
                extension_manager.add_error(exc, field="aws_credential")

    def _validate_aws_region(self):
        """Validate aws_region field (Text wrapper)."""
        if self.aws_region is not None:
            region_value = self.aws_region.value.strip()
            if not region_value:
                exc = DataValidationError("AWS region cannot be empty")
                extension_manager.add_error(exc, field="aws_region")

    def _validate_bucket_name(self):
        """Validate bucket_name field (Text wrapper)."""
        if self.bucket_name is not None:
            bucket_value = self.bucket_name.value.strip()
            if not bucket_value:
                exc = DataValidationError("Bucket name cannot be empty")
                extension_manager.add_error(exc, field="bucket_name")

    def _validate_prefix(self):
        """Validate prefix field (Text wrapper).

        Prefix is optional. Whitespace-only values are treated as empty.
        """
        if self.prefix is not None and self.prefix.value:
            prefix_value = self.prefix.value.strip()
            if not prefix_value:
                self.prefix = Text(value="")

    def _validate_max_objects(self):
        """Validate max_objects field (Integer wrapper).

        Optional field, must be 1-1000 if provided.
        """
        if self.max_objects is not None:
            if self.max_objects.value < 1 or self.max_objects.value > 1000:
                exc = DataValidationError(
                    f"max_objects must be between 1 and 1000, got {self.max_objects.value}"
                )
                extension_manager.add_error(exc, field="max_objects", value=self.max_objects.value)

    def _validate_source_file(self):
        """Validate source_file field (Text wrapper).

        Required only when action is "Upload File".
        """
        if self.action and self.action.value == "Upload File":
            if self.source_file is None or not self.source_file.value.strip():
                exc = DataValidationError("source_file is required for Upload File action")
                extension_manager.add_error(exc, field="source_file")

    def _validate_object_key(self):
        """Validate object_key field (Text wrapper).

        Required only when action is "Upload File".
        """
        if self.action and self.action.value == "Upload File":
            if self.object_key is None or not self.object_key.value.strip():
                exc = DataValidationError("object_key is required for Upload File action")
                extension_manager.add_error(exc, field="object_key")

