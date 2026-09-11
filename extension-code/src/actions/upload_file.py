"""Upload File action for AWS S3 extension."""

import logging
from typing import Optional
from fields import InputFields
from fields.output import OutputFields
from actions.output import ActionOutput
from manager import ExtensionManager
from utility import (
    CredentialsHandler,
    S3ClientManager,
    FileValidator,
    FileUploadHandler,
    OutputFormatter,
)
from exceptions import ExecutionError

logger = logging.getLogger("UNV")
extension_manager = ExtensionManager()


class UploadFile:
    """Action to upload a file to an S3 bucket."""

    def __init__(self, input_data: InputFields) -> None:
        """Initialize Upload File action.

        Args:
            input_data: Input fields from UAC

        Raises:
            ExecutionError: If initialization fails
        """
        self._input = input_data
        self._output_fields = OutputFields()
        self._s3_manager: Optional[S3ClientManager] = None

    def execute(self) -> ActionOutput:
        """Execute Upload File action.

        Returns:
            ActionOutput with result data

        Raises:
            ExecutionError: If execution fails
        """
        try:
            logger.info("Starting Upload File action")

            if extension_manager.is_cancelled():
                raise ExecutionError("Operation cancelled before start")

            source_file = self._input.source_file.value
            object_key = self._input.object_key.value

            logger.info("Validating source file: %s", source_file)
            FileValidator.validate(source_file)

            access_key_id, secret_access_key = CredentialsHandler.extract_credentials(
                self._input.aws_credential
            )

            region = self._input.aws_region.value
            bucket_name = self._input.bucket_name.value

            logger.info(
                "Upload File parameters: bucket=%s, region=%s, object_key=%s, source_file=%s",
                bucket_name,
                region,
                object_key,
                source_file,
            )

            self._s3_manager = S3ClientManager(region, access_key_id, secret_access_key)
            client = self._s3_manager.get_client()

            logger.info("Uploading file to S3")
            upload_result = FileUploadHandler.upload_file(client, source_file, bucket_name, object_key)

            self._output_fields.update(
                bucket_name=bucket_name,
                region=region,
                s3_uri=upload_result["s3_uri"],
                status_message="Upload File completed successfully",
            )

            stdout_output = OutputFormatter.format_upload_file_stdout(
                source_file,
                upload_result["file_size"],
                bucket_name,
                region,
                object_key,
                upload_result["s3_uri"],
            )
            print(stdout_output)

            return ActionOutput(
                bucket_name=bucket_name,
                region=region,
                object_key=object_key,
                s3_uri=upload_result["s3_uri"],
                source_file=source_file,
                file_size=upload_result["file_size"],
                status_message="Upload File completed successfully",
            )

        except ExecutionError:
            raise
        except Exception as e:
            logger.error("Unexpected error in Upload File: %s", str(e), exc_info=True)
            raise
        finally:
            if self._s3_manager:
                self._s3_manager.close()
