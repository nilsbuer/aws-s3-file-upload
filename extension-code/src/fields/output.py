"""OutputFields dataclass for real-time UI updates."""

from dataclasses import dataclass, fields as dataclass_fields
from typing import Optional
from universal_extension import ui
from fields.types import Text


@dataclass
class OutputFields:
    """Real-time output fields for UAC UI updates.

    Define fields for progress tracking during execution.
    These fields sync with the UAC UI in real-time and are available
    in subsequent re-runs via InputFields.previous_output.

    All output fields should use the Text wrapper type.
    """

    bucket_name: Optional[Text] = None
    region: Optional[Text] = None
    object_count: Optional[Text] = None
    s3_uri: Optional[Text] = None
    status_message: Optional[Text] = None

    def update(self, **fields):
        """Update fields and sync with UAC UI in real-time.

        Args:
            **fields: Field names and values to update (strings will be wrapped in Text)
        """
        for field_name, field_value in fields.items():
            if hasattr(self, field_name):
                # Wrap string values in Text type
                if isinstance(field_value, str):
                    field_value = Text(field_value)
                setattr(self, field_name, field_value)
        ui.update_output_fields(fields)

    def to_dict(self) -> dict:
        """Get current fields as dictionary.

        Returns:
            Dict with non-None field values (Text wrappers unwrapped to strings)
        """
        result = {}
        for field in dataclass_fields(self):
            v = getattr(self, field.name)
            if v is not None:
                result[field.name] = v.value if isinstance(v, Text) else v
        return result

    def clear(self):
        """Reset all fields to None."""
        self.bucket_name = None
        self.region = None
        self.object_count = None
        self.s3_uri = None
        self.status_message = None
