"""Utility classes for AWS S3 extension operations."""

import logging
import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

import boto3
from botocore.exceptions import (
    ClientError,
    NoCredentialsError,
    EndpointConnectionError,
    ConnectTimeoutError,
    ReadTimeoutError,
)

from exceptions import (
    AWSConnectionError,
    AWSAuthenticationError,
    AWSAccessDeniedError,
    AWSBucketNotFoundError,
    FileValidationError,
    UnexpectedError,
)
from fields.types import Credential

logger = logging.getLogger("UNV")


class CredentialsHandler:
    """Manages credential extraction from UAC Credential fields."""

    @staticmethod
    def extract_credentials(credential: Credential) -> tuple[str, str]:
        """Extract AWS Access Key ID and Secret Access Key from credential.

        Args:
            credential: UAC Credential object

        Returns:
            Tuple of (access_key_id, secret_access_key)

        Raises:
            AWSAuthenticationError: If credential is invalid or missing required fields
        """
        if credential is None:
            logger.error("Credential object is None")
            raise AWSAuthenticationError("AWS credentials not provided")

        try:
            access_key_id = credential.user
            secret_access_key = credential.password

            if not access_key_id or not secret_access_key:
                logger.error("Credential fields are empty or missing")
                raise AWSAuthenticationError("AWS credentials are incomplete")

            return access_key_id, secret_access_key
        except AttributeError as e:
            logger.error("Failed to extract credentials: %s", str(e))
            raise AWSAuthenticationError(f"Invalid credential format: {str(e)}")


class S3ClientManager:
    """Manages boto3 S3 client initialization and lifecycle with error handling."""

    def __init__(self, region: str, access_key_id: str, secret_access_key: str) -> None:
        """Initialize S3 client manager.

        Args:
            region: AWS region (e.g., us-east-1)
            access_key_id: AWS Access Key ID
            secret_access_key: AWS Secret Access Key

        Raises:
            AWSConnectionError: If region is invalid or endpoint unreachable
            AWSAuthenticationError: If credentials are invalid
        """
        self._region = region
        self._client: Optional[Any] = None
        self._connect(access_key_id, secret_access_key)

    def _connect(self, access_key_id: str, secret_access_key: str) -> None:
        """Create and initialize S3 client.

        Args:
            access_key_id: AWS Access Key ID
            secret_access_key: AWS Secret Access Key

        Raises:
            AWSConnectionError: If endpoint unreachable
            AWSAuthenticationError: If credentials invalid
        """
        try:
            logger.info("Initializing S3 client for region: %s", self._region)
            self._client = boto3.client(
                "s3",
                region_name=self._region,
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
            )
            logger.info("S3 client initialized successfully")
        except (EndpointConnectionError, ConnectTimeoutError, ReadTimeoutError) as e:
            logger.error("Connection error: %s", str(e))
            raise AWSConnectionError(f"Failed to reach AWS endpoint in region {self._region}")
        except NoCredentialsError as e:
            logger.error("Credentials error: %s", str(e))
            raise AWSAuthenticationError("AWS credentials not provided or invalid")
        except Exception as e:
            logger.error("Unexpected error during client initialization: %s", str(e))
            raise

    def get_client(self) -> Any:
        """Get the S3 client.

        Returns:
            boto3 S3 client
        """
        return self._client

    def close(self) -> None:
        """Close the S3 client connection."""
        if self._client:
            try:
                self._client.close()
                logger.info("S3 client closed")
            except Exception as e:
                logger.error("Error closing client: %s", str(e))


class FileValidator:
    """Validates source file paths for Upload File action."""

    @staticmethod
    def validate(file_path: str) -> tuple[bool, Optional[str]]:
        """Validate source file path.

        Checks:
        1. File exists
        2. Path is a regular file (not directory or symlink)
        3. File is readable

        Args:
            file_path: Absolute path to source file

        Returns:
            Tuple of (is_valid, error_message)
            is_valid=True and error_message=None if valid
            is_valid=False and error_message contains specific error if invalid

        Raises:
            FileValidationError: Raises immediately with specific error message
        """
        if not file_path:
            logger.error("File path is empty")
            raise FileValidationError("Source file path is required")

        path = Path(file_path)

        if not path.exists():
            logger.error("File does not exist: %s", file_path)
            raise FileValidationError(f"Source file does not exist: {file_path}")

        if not path.is_file():
            logger.error("Path is not a regular file: %s", file_path)
            raise FileValidationError(f"Source path is not a regular file: {file_path}")

        try:
            if not os.access(path, os.R_OK):
                logger.error("File is not readable: %s", file_path)
                raise FileValidationError(f"Source file is not readable: {file_path} (check permissions)")
        except OSError as e:
            logger.error("Error checking file permissions: %s", str(e))
            raise FileValidationError(f"Source file is not readable: {file_path} (check permissions)")

        logger.info("File validation passed: %s", file_path)
        return True, None


class ObjectListingHandler:
    """Handles boto3 paginator logic for listing S3 objects."""

    @staticmethod
    def list_objects(
        client: Any, bucket_name: str, prefix: Optional[str], max_objects: int
    ) -> List[Dict[str, Any]]:
        """List objects from S3 bucket with pagination.

        Args:
            client: boto3 S3 client
            bucket_name: S3 bucket name
            prefix: Object key prefix for filtering (None or empty string for root)
            max_objects: Maximum number of objects to return

        Returns:
            List of object metadata dicts with keys: key, size, last_modified (ISO 8601)

        Raises:
            AWSAuthenticationError: If authentication fails
            AWSAccessDeniedError: If user lacks s3:ListBucket permission
            AWSBucketNotFoundError: If bucket does not exist
            AWSConnectionError: If connection fails
            UnexpectedError: For unexpected errors
        """
        try:
            logger.info(
                "Listing objects from bucket: %s, prefix: %s, max_objects: %d",
                bucket_name,
                prefix or "(root)",
                max_objects,
            )

            # Normalize prefix
            if not prefix or not prefix.strip():
                prefix = ""
            else:
                prefix = prefix.strip()

            # Use paginator to list objects
            paginator = client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

            objects = []
            for page in page_iterator:
                if "Contents" not in page:
                    continue

                for obj in page["Contents"]:
                    if len(objects) >= max_objects:
                        logger.info("Reached max_objects limit: %d", max_objects)
                        break

                    last_modified = obj["LastModified"]
                    # Convert to ISO 8601 UTC format
                    if hasattr(last_modified, "isoformat"):
                        iso_timestamp = last_modified.isoformat().replace("+00:00", "Z")
                    else:
                        iso_timestamp = last_modified

                    objects.append(
                        {
                            "key": obj["Key"],
                            "size": obj["Size"],
                            "last_modified": iso_timestamp,
                        }
                    )

                if len(objects) >= max_objects:
                    break

            logger.info("Listed %d objects from bucket", len(objects))
            return objects

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            error_message = e.response.get("Error", {}).get("Message", "")

            if error_code == "NoSuchBucket" or "404" in str(e):
                logger.error("Bucket not found: %s", bucket_name)
                raise AWSBucketNotFoundError(f"Bucket '{bucket_name}' does not exist or is not accessible")

            if error_code == "InvalidAccessKeyId":
                logger.error("Invalid access key")
                raise AWSAuthenticationError("Invalid AWS Access Key ID")

            if error_code == "SignatureDoesNotMatch":
                logger.error("Invalid secret access key")
                raise AWSAuthenticationError("Invalid AWS Secret Access Key")

            if error_code == "AccessDenied" or "not have permission" in error_message:
                logger.error("Access denied to bucket: %s", bucket_name)
                raise AWSAccessDeniedError(f"User lacks s3:ListBucket permission on bucket '{bucket_name}'")

            logger.error("AWS error during list: %s - %s", error_code, error_message)
            raise AWSConnectionError(f"Failed to list objects: {error_message}")

        except (EndpointConnectionError, ConnectTimeoutError, ReadTimeoutError) as e:
            logger.error("Connection error during list: %s", str(e))
            raise AWSConnectionError("Failed to connect to AWS S3 endpoint")

        except NoCredentialsError as e:
            logger.error("Credentials error: %s", str(e))
            raise AWSAuthenticationError("AWS credentials not provided")

        except Exception as e:
            logger.error("Unexpected error during list: %s", str(e))
            raise UnexpectedError(f"Unexpected error listing objects: {str(e)}")


class FileUploadHandler:
    """Handles file upload operations to S3."""

    @staticmethod
    def upload_file(
        client: Any, source_file: str, bucket_name: str, object_key: str
    ) -> Dict[str, Any]:
        """Upload file to S3 bucket.

        Args:
            client: boto3 S3 client
            source_file: Absolute path to local file
            bucket_name: S3 bucket name
            object_key: S3 object key (path/filename)

        Returns:
            Dict with upload metadata: bucket_name, region, object_key, s3_uri, source_file, file_size

        Raises:
            AWSAuthenticationError: If authentication fails
            AWSAccessDeniedError: If user lacks s3:PutObject permission
            AWSBucketNotFoundError: If bucket does not exist
            AWSConnectionError: If connection fails
            UnexpectedError: For unexpected errors
        """
        try:
            file_size = Path(source_file).stat().st_size
            logger.info("Uploading file: %s (size: %d bytes) to s3://%s/%s", source_file, file_size, bucket_name, object_key)

            # Upload file
            client.upload_file(source_file, bucket_name, object_key)

            s3_uri = f"s3://{bucket_name}/{object_key}"
            logger.info("File uploaded successfully: %s", s3_uri)

            return {
                "bucket_name": bucket_name,
                "region": client.meta.region_name,
                "object_key": object_key,
                "s3_uri": s3_uri,
                "source_file": source_file,
                "file_size": file_size,
            }

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            error_message = e.response.get("Error", {}).get("Message", "")

            if error_code == "NoSuchBucket" or "404" in str(e):
                logger.error("Bucket not found: %s", bucket_name)
                raise AWSBucketNotFoundError(f"Bucket '{bucket_name}' does not exist or is not accessible")

            if error_code == "InvalidAccessKeyId":
                logger.error("Invalid access key")
                raise AWSAuthenticationError("Invalid AWS Access Key ID")

            if error_code == "SignatureDoesNotMatch":
                logger.error("Invalid secret access key")
                raise AWSAuthenticationError("Invalid AWS Secret Access Key")

            if error_code == "AccessDenied" or "not have permission" in error_message:
                logger.error("Access denied to bucket: %s", bucket_name)
                raise AWSAccessDeniedError(f"User lacks s3:PutObject permission on bucket '{bucket_name}'")

            logger.error("AWS error during upload: %s - %s", error_code, error_message)
            raise AWSConnectionError(f"Failed to upload file: {error_message}")

        except (EndpointConnectionError, ConnectTimeoutError, ReadTimeoutError) as e:
            logger.error("Connection error during upload: %s", str(e))
            raise AWSConnectionError("Failed to connect to AWS S3 endpoint")

        except NoCredentialsError as e:
            logger.error("Credentials error: %s", str(e))
            raise AWSAuthenticationError("AWS credentials not provided")

        except Exception as e:
            logger.error("Unexpected error during upload: %s", str(e))
            raise UnexpectedError(f"Unexpected error uploading file: {str(e)}")


class OutputFormatter:
    """Formats extension output for STDOUT and Extension Output JSON."""

    @staticmethod
    def format_list_files_stdout(
        bucket_name: str, region: str, prefix: str, objects: List[Dict[str, Any]]
    ) -> str:
        """Format List Files output for STDOUT.

        Args:
            bucket_name: S3 bucket name
            region: AWS region
            prefix: Object key prefix (empty string for root)
            objects: List of object metadata dicts

        Returns:
            Formatted string for STDOUT
        """
        output = []
        output.append("AWS S3")
        output.append("======")
        output.append("")
        output.append("Action")
        output.append("------")
        output.append("List Files")
        output.append("")
        output.append("Bucket")
        output.append("------")
        output.append(f"Name       : {bucket_name}")
        output.append(f"Region     : {region}")
        prefix_display = prefix if prefix else "(root)"
        output.append(f"Prefix     : {prefix_display}")
        output.append("")
        output.append("Objects")
        output.append("-------")

        if not objects:
            output.append("No objects found.")
        else:
            for idx, obj in enumerate(objects, 1):
                output.append(f"{idx}. {obj['key']}")
                output.append(f"   Size          : {obj['size']:,} bytes")
                output.append(f"   Last Modified : {obj['last_modified']}")
                output.append("")

        output.append("Result")
        output.append("------")
        output.append(f"Objects Found : {len(objects)}")

        return "\n".join(output)

    @staticmethod
    def format_upload_file_stdout(
        source_file: str, file_size: int, bucket_name: str, region: str, object_key: str, s3_uri: str
    ) -> str:
        """Format Upload File output for STDOUT.

        Args:
            source_file: Path to source file
            file_size: File size in bytes
            bucket_name: S3 bucket name
            region: AWS region
            object_key: S3 object key
            s3_uri: Full S3 URI

        Returns:
            Formatted string for STDOUT
        """
        output = []
        output.append("AWS S3")
        output.append("======")
        output.append("")
        output.append("Action")
        output.append("------")
        output.append("Upload File")
        output.append("")
        output.append("Source")
        output.append("------")
        output.append(f"File       : {source_file}")
        output.append(f"Size       : {file_size:,} bytes")
        output.append("")
        output.append("Destination")
        output.append("-----------")
        output.append(f"Bucket     : {bucket_name}")
        output.append(f"Region     : {region}")
        output.append(f"Object Key : {object_key}")
        output.append("")
        output.append("Result")
        output.append("------")
        output.append("Upload completed successfully.")
        output.append(f"S3 URI     : {s3_uri}")

        return "\n".join(output)

    @staticmethod
    def build_extension_output(
        exit_code: int,
        status_description: str,
        result: Dict[str, Any],
        action: str,
    ) -> Dict[str, Any]:
        """Build Extension Output JSON structure.

        Args:
            exit_code: Exit code (0 for success, non-zero for error)
            status_description: Human-readable status message
            result: Action-specific result object
            action: Action name (List Files or Upload File)

        Returns:
            Dict with extension output structure
        """
        return {
            "exit_code": exit_code,
            "status_description": status_description,
            "metadata": {
                "extension_name": "AWS S3",
                "action": action,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "result": result,
        }

    @staticmethod
    def format_error_message(error_type: str, error_detail: str) -> str:
        """Format error message with category prefix.

        Args:
            error_type: Category of error (e.g., "AWS Connection Error")
            error_detail: Detailed error message

        Returns:
            Formatted error message
        """
        return f"{error_type}: {error_detail}"
