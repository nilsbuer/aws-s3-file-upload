"""ActionOutput dataclass for extension output control and formatting."""

from dataclasses import dataclass, field
from typing import Optional, Any, Dict, List


@dataclass
class ActionOutput:
    """Extension output payload for STDOUT and Extension Output JSON.

    Fields represent the result object sent to UAC Controller.
    These are NOT the same as OutputFields (real-time UI updates).
    """

    bucket_name: Optional[str] = None
    region: Optional[str] = None
    object_count: Optional[int] = None
    s3_uri: Optional[str] = None
    status_message: Optional[str] = None
    source_file: Optional[str] = None
    object_key: Optional[str] = None
    file_size: Optional[int] = None
    prefix: Optional[str] = None
    objects: Optional[List[Dict[str, Any]]] = None

    message: Optional[str] = None

    stdout_options: List[str] = field(default_factory=list)
    output_options: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize control fields with fallback."""
        if self.stdout_options is None:
            self.stdout_options = []
        if self.output_options is None:
            self.output_options = []

    def print_output(self) -> None:
        """Print formatted output to STDOUT."""
        print_all = len(self.stdout_options) == 0

        if self.status_message:
            print(f"\n{self.status_message}")

        if (print_all or "bucket_info" in self.stdout_options) and self.bucket_name:
            print(f"Bucket: {self.bucket_name}")
            if self.region:
                print(f"Region: {self.region}")

        if (print_all or "objects" in self.stdout_options) and self.objects is not None:
            print(f"\nObjects: {self.object_count}")
            for obj in self.objects[:10]:
                print(f"  - {obj.get('key', 'N/A')}")

        if (print_all or "s3_uri" in self.stdout_options) and self.s3_uri:
            print(f"S3 URI: {self.s3_uri}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for Extension Output JSON.

        Returns:
            Dict with action-specific result fields (no errors key on success)
        """
        include_all = len(self.output_options) == 0
        output = {}

        if self.bucket_name:
            output["bucket_name"] = self.bucket_name

        if self.region:
            output["region"] = self.region

        if self.object_count is not None:
            output["object_count"] = int(self.object_count)

        if self.s3_uri:
            output["s3_uri"] = self.s3_uri

        if self.status_message:
            output["status_message"] = self.status_message

        if self.source_file:
            output["source_file"] = self.source_file

        if self.object_key:
            output["object_key"] = self.object_key

        if self.file_size is not None:
            output["file_size"] = int(self.file_size)

        if self.prefix is not None:
            output["prefix"] = self.prefix

        if (include_all or "objects" in self.output_options) and self.objects:
            output["objects"] = self.objects

        return output
