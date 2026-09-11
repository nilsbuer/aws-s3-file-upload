"""List Files action for AWS S3 extension."""

import logging
from typing import Any, Optional
from fields import InputFields
from fields.output import OutputFields
from actions.output import ActionOutput
from manager import ExtensionManager
from utility import CredentialsHandler, S3ClientManager, ObjectListingHandler, OutputFormatter
from exceptions import ExecutionError

logger = logging.getLogger("UNV")
extension_manager = ExtensionManager()


class ListFiles:
    """Action to list objects from an S3 bucket."""

    def __init__(self, input_data: InputFields) -> None:
        """Initialize List Files action.

        Args:
            input_data: Input fields from UAC

        Raises:
            ExecutionError: If initialization fails
        """
        self._input = input_data
        self._output_fields = OutputFields()
        self._s3_manager: Optional[S3ClientManager] = None

    def execute(self) -> ActionOutput:
        """Execute List Files action.

        Returns:
            ActionOutput with result data

        Raises:
            ExecutionError: If execution fails
        """
        try:
            logger.info("Starting List Files action")

            if extension_manager.is_cancelled():
                raise ExecutionError("Operation cancelled before start")

            access_key_id, secret_access_key = CredentialsHandler.extract_credentials(
                self._input.aws_credential
            )

            region = self._input.aws_region.value
            bucket_name = self._input.bucket_name.value
            prefix = self._input.prefix.value.strip() if self._input.prefix and self._input.prefix.value else ""
            max_objects = self._input.max_objects.value if self._input.max_objects else 100

            logger.info(
                "List Files parameters: bucket=%s, region=%s, prefix=%s, max_objects=%d",
                bucket_name,
                region,
                prefix or "(root)",
                max_objects,
            )

            self._s3_manager = S3ClientManager(region, access_key_id, secret_access_key)
            client = self._s3_manager.get_client()

            logger.info("Listing objects from S3 bucket")
            objects = ObjectListingHandler.list_objects(client, bucket_name, prefix, max_objects)

            self._output_fields.update(
                bucket_name=bucket_name,
                region=region,
                object_count=str(len(objects)),
                status_message="List Files completed successfully",
            )

            stdout_output = OutputFormatter.format_list_files_stdout(
                bucket_name, region, prefix, objects
            )
            print(stdout_output)

            return ActionOutput(
                bucket_name=bucket_name,
                region=region,
                prefix=prefix,
                object_count=len(objects),
                objects=objects,
                status_message="List Files completed successfully",
            )

        except ExecutionError:
            raise
        except Exception as e:
            logger.error("Unexpected error in List Files: %s", str(e), exc_info=True)
            raise
        finally:
            if self._s3_manager:
                self._s3_manager.close()
