---
extension_name: AWS S3
work_item_id: initial-1
ticket_id: ""
status: pending_review
approved_by: ""
approved_at: ""
---

# Universal Extension Requirements (Refined)

**Extension Name:** AWS S3
**Created:** 2026-09-11T08:09:08Z
**Work Item:** initial-1
**Initial Requirements Assessment:** High Detail
**Target Platform:** Linux

---

# Table of Contents

1. [Overview](#overview)
2. [Actions](#actions)
   - 2.1 [Action 1: List Files](#action-1-list-files)
   - 2.2 [Action 2: Upload File](#action-2-upload-file)
3. [Input Requirements](#input-requirements)
   - 3.1 [Common Fields](#common-fields)
   - 3.2 [List Files Fields](#list-files-fields)
   - 3.3 [Upload File Fields](#upload-file-fields)
4. [Output Requirements](#output-requirements)
   - 4.1 [List Files Output](#list-files-output)
   - 4.2 [Upload File Output](#upload-file-output)
5. [Authentication Requirements](#authentication-requirements)
6. [Environment Variables](#environment-variables)
7. [Operational Behavior Section](#operational-behavior-section)
8. [Implementation Notes](#implementation-notes)
   - 8.1 [Python Compatibility](#python-compatibility)
   - 8.2 [Target Platform](#target-platform)
   - 8.3 [Third-Party Services and Tools Section](#third-party-services-and-tools-section)
   - 8.4 [Error Handling](#error-handling)
   - 8.5 [Resource Cleanup](#resource-cleanup)
9. [References](#references)

---

# Overview

This extension provides AWS S3 integration for Universal Automation Center (UAC), allowing Stonebranch Universal Agents to list objects in S3 buckets and upload files from the Linux server to Amazon S3.

**Integration Purpose:** The AWS S3 extension enables users to manage S3 bucket contents programmatically through UAC tasks, supporting two core operations: listing S3 objects with prefix filtering and uploading local files to S3 buckets. This MVP integration demonstrates clean boto3 integration with bundled dependencies, requiring no pre-installed AWS CLI or global boto3 installation on the Universal Agent host.

---

# Actions

## Action 1: List Files

**Functional Requirements:**

- Must list objects from a specified S3 bucket using the boto3 `list_objects_v2` API via paginator pattern
- Must support optional prefix filtering to list objects within a specific bucket path
- Must respect a configurable maximum object limit (1 to 1000 objects)
- Must retrieve and display the following attributes for each object: Key, Size (in bytes), and LastModified timestamp
- Must treat an empty bucket as a successful result returning 0 objects, not an error
- Must stop pagination after reaching the configured maximum object limit
- Must format LastModified timestamp in ISO 8601 UTC format (YYYY-MM-DD HH:MM:SS UTC)
- Must paginate through bucket contents automatically, handling any number of objects up to the configured limit
- Must display results in a user-friendly STDOUT format showing bucket information, object list, and summary count

## Action 2: Upload File

**Functional Requirements:**

- Must upload a local file from the Universal Agent host to a specified S3 bucket with a specified object key
- Must validate the source file path before upload: path must exist, must be a regular file, and must be readable
- Must use the exact object key provided by the user without modification or automatic path alteration
- Must accept local file paths on the Universal Agent's Linux filesystem (absolute paths such as /tmp/report.csv)
- Must overwrite existing S3 objects with the same key without confirmation (overwrite semantics)
- Must document the overwrite behavior clearly in logs and output
- Must use boto3's `upload_file()` method, which includes built-in integrity verification
- Must not require or implement additional post-upload verification calls (head_object)
- Must display upload results in a user-friendly STDOUT format showing source, destination, and confirmation
- Must include the S3 URI in the output for reference

---

# Input Requirements

## Common Fields

### action (Choice)

- **Description:** Specifies which S3 operation to perform
- **Data Type:** Choice (scalar)
- **Conditionality:** Required
- **Default Value:** List Files
- **Available Options:**
  - List Files
  - Upload File
- **Default Presented Option:** List Files
- **Field Mapping:** Used in showIfField/requireIfField conditionals; refer to this field's `fieldMapping` property, not its `name` property
- **Behavior:** Selection of this field controls which additional input fields are displayed (Dynamic Choice Fields behavior)

### aws_credential (Credential)

- **Description:** AWS credential containing Access Key ID and Secret Access Key for S3 authentication
- **Data Type:** Credential
- **Conditionality:** Required (applies to both List Files and Upload File actions)
- **Applicability:** Both List Files and Upload File actions
- **Credential Mapping:**
  - Credential User field → AWS Access Key ID
  - Credential Password field → AWS Secret Access Key
- **Security Requirement:** Never log or display either the Access Key ID or Secret Access Key in any output
- **Note:** This MVP does not support STS AssumeRole, AWS SSO, Web Identity, EC2 Instance Profile, IAM Roles Anywhere, or temporary session tokens

### aws_region (Text)

- **Description:** AWS region where the S3 bucket is located (must match the bucket's actual region)
- **Data Type:** Text
- **Conditionality:** Required (applies to both List Files and Upload File actions)
- **Example:** eu-central-1
- **Applicability:** Both List Files and Upload File actions
- **Validation:** Must be a valid AWS region identifier
- **Note:** Region must not be hard-coded; users must specify it explicitly

### bucket_name (Text)

- **Description:** Name of the S3 bucket to list or upload to
- **Data Type:** Text
- **Conditionality:** Required (applies to both List Files and Upload File actions)
- **Example:** stonebranch-demo-bucket
- **Applicability:** Both List Files and Upload File actions
- **Validation:** Bucket must exist and be accessible with the provided credentials

## List Files Fields

### prefix (Text)

- **Description:** Optional S3 object key prefix for filtering listed objects
- **Data Type:** Text
- **Conditionality:** Optional; when omitted or empty, lists from bucket root with no prefix filter
- **Example:** inbound/
- **Applicability:** List Files action only
- **Default Value:** None (empty string means no prefix filter)
- **Visibility:** Show only when `action` field equals List Files (use the action field's `fieldMapping` in showIfField condition)
- **Behavior:** Empty string, null, and whitespace-only values are treated identically as "list from bucket root"; non-empty values are trimmed of leading/trailing whitespace before use

### max_objects (Integer)

- **Description:** Maximum number of objects to return in the List Files result
- **Data Type:** Integer
- **Conditionality:** Optional
- **Default Value:** 100
- **Minimum Value:** 1
- **Maximum Value:** 1000
- **Applicability:** List Files action only
- **Visibility:** Show only when `action` field equals List Files
- **Behavior:** Pagination stops after reaching this limit; if fewer objects exist, all are returned

## Upload File Fields

### source_file (Text)

- **Description:** Absolute path to the local file on the Universal Agent host to upload
- **Data Type:** Text
- **Conditionality:** Required for Upload File action
- **Example:** /tmp/report.csv
- **Applicability:** Upload File action only
- **Visibility:** Show only when `action` field equals Upload File
- **Validation Rules:**
  1. Path must exist on the Universal Agent's filesystem
  2. Path must be a regular file (not a directory, symlink, or device)
  3. File must be readable by the process executing the extension
- **Error Behavior:** If validation fails, return a validation error with a specific message indicating which validation rule was violated
- **Limitations:** Does not support directory upload, wildcards, or recursive directory uploads

### object_key (Text)

- **Description:** S3 object key (path and filename) for the uploaded object
- **Data Type:** Text
- **Conditionality:** Required for Upload File action
- **Example:** inbound/report.csv
- **Applicability:** Upload File action only
- **Visibility:** Show only when `action` field equals Upload File
- **Behavior:** The key is used exactly as provided without automatic alteration or path normalization
- **Note:** If an object with this key already exists, it will be overwritten (see Upload Semantics)

---

# Output Requirements

## List Files Output

### On Success

- **Return Code:** 0
- **Status Description:** "List Files completed successfully" (or similar indicating successful completion)
- **Output Fields:**
  - `bucket_name` (Text): The name of the S3 bucket listed
  - `prefix` (Text): The prefix used for filtering (empty string if no prefix was applied)
  - `object_count` (Integer): The total number of objects returned
- **Extension Output (JSON):** Standard structured format with the following schema:
  ```json
  {
    "exit_code": 0,
    "status_description": "List Files completed successfully",
    "metadata": {
      "extension": "aws-s3",
      "action": "List Files"
    },
    "result": {
      "bucket_name": "stonebranch-demo-bucket",
      "region": "eu-central-1",
      "prefix": "inbound/",
      "object_count": 2,
      "objects": [
        {
          "key": "inbound/customer_001.csv",
          "size": 12483,
          "last_modified": "2026-09-11T08:15:22Z"
        },
        {
          "key": "inbound/customer_002.csv",
          "size": 8104,
          "last_modified": "2026-09-11T08:18:03Z"
        }
      ]
    }
  }
  ```
- **STDOUT Output Format:** Human-readable text format:
  ```
  AWS S3
  ======

  Action
  ------
  List Files

  Bucket
  ------
  Name       : stonebranch-demo-bucket
  Region     : eu-central-1
  Prefix     : inbound/

  Objects
  -------
  1. inbound/customer_001.csv
     Size          : 12,483 bytes
     Last Modified : 2026-09-11 08:15:22 UTC

  2. inbound/customer_002.csv
     Size          : 8,104 bytes
     Last Modified : 2026-09-11 08:18:03 UTC

  Result
  ------
  Objects Found : 2
  ```
  For empty results (0 objects found):
  ```
  AWS S3
  ======

  Action
  ------
  List Files

  Bucket
  ------
  Name   : stonebranch-demo-bucket
  Region : eu-central-1
  Prefix : (root)

  Objects
  -------
  No objects found.

  Result
  ------
  Objects Found : 0
  ```
- **Success Criteria:**
  1. Connection to AWS S3 endpoint for specified region succeeds
  2. AWS authentication using provided credentials succeeds
  3. User has s3:ListBucket permission on the target bucket
  4. S3 list operation completes without error
  5. Object details (Key, Size, LastModified) are retrieved for all objects up to max_objects limit

### On Error

- **Failure Scenarios:**

  **Scenario 1: Invalid AWS Credentials**
  - Root Causes: Access Key ID is invalid, Secret Access Key is incorrect, or credentials are malformed
  - Return Code: Non-zero (specific code TBD by implementation, but distinct from other failures)
  - Status Description: "AWS authentication failed. Verify the configured AWS credential."
  - Extension Output JSON:
    ```json
    {
      "exit_code": 1,
      "status_description": "AWS authentication failed. Verify the configured AWS credential.",
      "metadata": {
        "extension": "aws-s3",
        "action": "List Files",
        "error_category": "authentication"
      },
      "result": null
    }
    ```

  **Scenario 2: Access Denied**
  - Root Causes: Credentials are valid but do not have s3:ListBucket permission on the bucket, or bucket access is restricted by bucket policy
  - Return Code: Non-zero (distinct return code)
  - Status Description: "AWS access denied for bucket '<bucket_name>'. Verify the IAM permissions assigned to the AWS credential."
  - Extension Output JSON:
    ```json
    {
      "exit_code": 1,
      "status_description": "AWS access denied for bucket 'stonebranch-demo-bucket'. Verify the IAM permissions assigned to the AWS credential.",
      "metadata": {
        "extension": "aws-s3",
        "action": "List Files",
        "error_category": "access_denied"
      },
      "result": null
    }
    ```

  **Scenario 3: Bucket Not Found**
  - Root Causes: Bucket does not exist in AWS, bucket exists in a different region, or bucket was deleted
  - Return Code: Non-zero (distinct return code)
  - Status Description: "S3 bucket '<bucket_name>' does not exist or is not accessible."
  - Extension Output JSON:
    ```json
    {
      "exit_code": 1,
      "status_description": "S3 bucket 'stonebranch-demo-bucket' does not exist or is not accessible.",
      "metadata": {
        "extension": "aws-s3",
        "action": "List Files",
        "error_category": "bucket_not_found"
      },
      "result": null
    }
    ```

  **Scenario 4: Network Failure**
  - Root Causes: Unable to connect to AWS S3 endpoint, network timeout, temporary AWS service unavailability
  - Return Code: Non-zero (distinct return code)
  - Status Description: "Unable to connect to the AWS S3 endpoint for region '<region>'. Verify network connectivity and region configuration."
  - Extension Output JSON:
    ```json
    {
      "exit_code": 1,
      "status_description": "Unable to connect to the AWS S3 endpoint for region 'eu-central-1'. Verify network connectivity and region configuration.",
      "metadata": {
        "extension": "aws-s3",
        "action": "List Files",
        "error_category": "network"
      },
      "result": null
    }
    ```

- **STDERR Requirements:** Detailed error information must be logged to STDERR for troubleshooting, but STDOUT must contain user-friendly messages only (no stack traces or raw boto3 error dumps)
- **Input Validation:** No input-level validation errors for List Files; all inputs are optional or provided by the extension framework. Validation errors are AWS-level errors.

## Upload File Output

### On Success

- **Return Code:** 0
- **Status Description:** "Upload File completed successfully"
- **Output Fields:**
  - `bucket_name` (Text): The name of the S3 bucket the file was uploaded to
  - `object_key` (Text): The S3 object key where the file was stored
  - `s3_uri` (Text): The full S3 URI in format s3://bucket_name/object_key
  - `file_size` (Integer): The size of the uploaded file in bytes
  - `source_file` (Text): The source file path used for upload
- **Extension Output (JSON):** Standard structured format with the following schema:
  ```json
  {
    "exit_code": 0,
    "status_description": "Upload File completed successfully",
    "metadata": {
      "extension": "aws-s3",
      "action": "Upload File"
    },
    "result": {
      "bucket_name": "stonebranch-demo-bucket",
      "region": "eu-central-1",
      "object_key": "inbound/report.csv",
      "s3_uri": "s3://stonebranch-demo-bucket/inbound/report.csv",
      "source_file": "/tmp/report.csv",
      "file_size": 24981
    }
  }
  ```
- **STDOUT Output Format:** Human-readable text format:
  ```
  AWS S3
  ======

  Action
  ------
  Upload File

  Source
  ------
  File       : /tmp/report.csv
  Size       : 24,981 bytes

  Destination
  -----------
  Bucket     : stonebranch-demo-bucket
  Region     : eu-central-1
  Object Key : inbound/report.csv

  Result
  ------
  Upload completed successfully.
  S3 URI     : s3://stonebranch-demo-bucket/inbound/report.csv
  ```
- **Success Criteria:**
  1. Source file validation passes (file exists, is regular file, is readable)
  2. Connection to AWS S3 endpoint for specified region succeeds
  3. AWS authentication using provided credentials succeeds
  4. User has s3:PutObject permission on the target bucket
  5. File upload completes without error
  6. boto3's built-in integrity verification confirms successful upload

### On Error

- **Failure Scenarios:**

  **Scenario 1: Source File Does Not Exist**
  - Root Causes: File path does not exist on the Universal Agent filesystem
  - Return Code: Non-zero (specific code for validation error)
  - Status Description: "Source file does not exist: /path/to/file"
  - Extension Output JSON:
    ```json
    {
      "exit_code": 2,
      "status_description": "Source file does not exist: /tmp/report.csv",
      "metadata": {
        "extension": "aws-s3",
        "action": "Upload File",
        "error_category": "validation_error"
      },
      "result": null
    }
    ```

  **Scenario 2: Source Path Is Not a Regular File**
  - Root Causes: Path points to a directory, symlink, device file, or other non-regular file type
  - Return Code: Non-zero (validation error return code)
  - Status Description: "Source path is not a regular file: /path/to/directory"
  - Extension Output JSON:
    ```json
    {
      "exit_code": 2,
      "status_description": "Source path is not a regular file: /tmp/directory",
      "metadata": {
        "extension": "aws-s3",
        "action": "Upload File",
        "error_category": "validation_error"
      },
      "result": null
    }
    ```

  **Scenario 3: Source File Not Readable**
  - Root Causes: File exists but process does not have read permission
  - Return Code: Non-zero (validation error return code)
  - Status Description: "Source file is not readable: /path/to/file (check permissions)"
  - Extension Output JSON:
    ```json
    {
      "exit_code": 2,
      "status_description": "Source file is not readable: /tmp/report.csv (check permissions)",
      "metadata": {
        "extension": "aws-s3",
        "action": "Upload File",
        "error_category": "validation_error"
      },
      "result": null
    }
    ```

  **Scenario 4: Invalid AWS Credentials**
  - Root Causes: Access Key ID is invalid, Secret Access Key is incorrect
  - Return Code: Non-zero (authentication error return code)
  - Status Description: "AWS authentication failed. Verify the configured AWS credential."
  - Extension Output JSON:
    ```json
    {
      "exit_code": 1,
      "status_description": "AWS authentication failed. Verify the configured AWS credential.",
      "metadata": {
        "extension": "aws-s3",
        "action": "Upload File",
        "error_category": "authentication"
      },
      "result": null
    }
    ```

  **Scenario 5: Access Denied**
  - Root Causes: Credentials are valid but do not have s3:PutObject permission on the bucket
  - Return Code: Non-zero (access denied return code)
  - Status Description: "AWS access denied for bucket '<bucket_name>'. Verify the IAM permissions assigned to the AWS credential."
  - Extension Output JSON:
    ```json
    {
      "exit_code": 1,
      "status_description": "AWS access denied for bucket 'stonebranch-demo-bucket'. Verify the IAM permissions assigned to the AWS credential.",
      "metadata": {
        "extension": "aws-s3",
        "action": "Upload File",
        "error_category": "access_denied"
      },
      "result": null
    }
    ```

  **Scenario 6: Bucket Not Found**
  - Root Causes: Bucket does not exist, bucket in different region, bucket deleted
  - Return Code: Non-zero (bucket not found return code)
  - Status Description: "S3 bucket '<bucket_name>' does not exist or is not accessible."
  - Extension Output JSON:
    ```json
    {
      "exit_code": 1,
      "status_description": "S3 bucket 'stonebranch-demo-bucket' does not exist or is not accessible.",
      "metadata": {
        "extension": "aws-s3",
        "action": "Upload File",
        "error_category": "bucket_not_found"
      },
      "result": null
    }
    ```

  **Scenario 7: Network Failure**
  - Root Causes: Cannot connect to AWS endpoint, network timeout, AWS service unavailability
  - Return Code: Non-zero (network error return code)
  - Status Description: "Unable to connect to the AWS S3 endpoint for region '<region>'. Verify network connectivity and region configuration."
  - Extension Output JSON:
    ```json
    {
      "exit_code": 1,
      "status_description": "Unable to connect to the AWS S3 endpoint for region 'eu-central-1'. Verify network connectivity and region configuration.",
      "metadata": {
        "extension": "aws-s3",
        "action": "Upload File",
        "error_category": "network"
      },
      "result": null
    }
    ```

- **STDERR Requirements:** Detailed error information and stack traces must be logged to STDERR only for troubleshooting; STDOUT must show user-friendly error messages without raw exception data
- **Input Validation:** The following input-level validation errors must be caught before AWS operations:
  1. source_file path existence check: "Source file does not exist: <path>"
  2. source_file type check: "Source path is not a regular file: <path>"
  3. source_file readability check: "Source file is not readable: <path>"

---

# Authentication Requirements

The extension supports a single authentication method:

**AWS IAM Access Keys via Stonebranch Credential**

- Credentials are supplied through a Stonebranch Credential object with the following mapping:
  - Credential User → AWS Access Key ID
  - Credential Password → AWS Secret Access Key
- The extension uses these credentials to create a boto3 S3 client with explicit authentication
- Credentials must never be logged or displayed in any output (STDOUT, STDERR, or Extension Output JSON)
- Explicit credential redaction must be implemented in the extension code; no credential values are passed to print() or logging calls
- This MVP does not support AWS STS AssumeRole, AWS SSO, Web Identity Federation, EC2 Instance Profile, IAM Roles Anywhere, or temporary AWS session tokens

---

# Environment Variables

None. All configuration must be provided through input fields. The extension does not read AWS configuration from environment variables (such as AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY).

---

# Operational Behavior Section

## Dynamic Choice Fields

When the `action` field changes, the Universal Extension framework automatically shows/hides input fields based on the field's `showIfField` condition.

- When `action` = "List Files": Display `prefix` and `max_objects` fields; hide `source_file` and `object_key` fields
- When `action` = "Upload File": Display `source_file` and `object_key` fields; hide `prefix` and `max_objects` fields

Note: The `showIfField` condition must use the action field's `fieldMapping` property value, not the field's `name` property.

## Cancel Action

If the user cancels an in-progress task:
- Any S3 API call in progress (e.g., `list_objects_v2`, `upload_file`) is terminated
- The extension must handle cancellation gracefully and exit with a non-zero return code
- No partial results are committed; if List Files is canceled mid-pagination, no output is written
- For Upload File, if upload is canceled mid-transfer, the partially uploaded object remains in S3 (partial files cannot be "rolled back")
- STDOUT and Extension Output should indicate the task was canceled, not that it completed successfully

## Re-run Capability

The extension can be safely re-run on the same inputs:

- **List Files:** Is fully idempotent; re-running returns the same object list (unless S3 bucket contents have changed)
- **Upload File:** Overwrites the existing object key if present, per the documented Upload Semantics; re-running uploads the file again to the same key

## Progress Reporting

**Progress Bar:**
- List Files: Shows pagination progress (e.g., "Fetched 100/1000 objects") if result exceeds single page
- Upload File: Shows file upload progress as a percentage (0-100%) if supported by boto3's upload_file method

**Logging:**
- INFO level: "AWS S3 extension started", action description, intermediate steps ("Listing objects...", "Uploading file..."), final completion message
- No DEBUG level logging of boto3/botocore wire-level details; boto3 debug logging is not enabled
- Never log credentials or sensitive information

## Dynamic Commands

Not applicable to this MVP. No task-instance commands are implemented.

---

# Implementation Notes

## Python Compatibility

Targeting Python 3.8 and later. Ensure all code and dependencies (boto3, botocore, s3transfer, etc.) support Python 3.8+.

## Target Platform

Linux (x86_64). All code and bundled dependencies must be pure-Python modules compatible with manylinux_2_17_x86_64 wheels. C extension modules are viable if they provide manylinux_2_17_x86_64 wheels; however, all core AWS functionality can be satisfied with pure-Python modules.

## Third-Party Services and Tools Section

**boto3 (AWS SDK for Python)**
- **Description:** High-level, object-oriented Python interface to Amazon Web Services (AWS). Provides the primary S3 operations API.
- **Version Constraint:** `>=1.34,<2` (accepts boto3 versions from 1.34.x through 1.99.x; does not force upgrade when 2.0 is released)
- **Integration Approach:** Imported and used directly in extension code; S3 client created via `boto3.client("s3", ...)` with explicit credentials; boto3 and all transitive dependencies bundled in the extension package

**botocore (AWS SDK Core for Python)**
- **Description:** Low-level, data-driven AWS SDK core; handles service communication, response parsing, and error handling. Automatically installed as a transitive dependency of boto3.
- **Version Constraint:** Auto-pinned with boto3 major/minor version (e.g., boto3 1.34.x → botocore 1.34.x)
- **Integration Approach:** Used indirectly via boto3; specific botocore exceptions (ClientError, NoCredentialsError, EndpointConnectionError, etc.) are caught for detailed error handling

**s3transfer (AWS S3 Multipart Upload Library)**
- **Description:** High-level S3 operations library; handles efficient file uploads, including multipart transfers and retries. Automatically installed as a dependency of boto3.
- **Version Constraint:** Auto-resolved as boto3 dependency
- **Integration Approach:** Used indirectly via boto3's upload_file() method; provides built-in integrity checking and retry logic

**jmespath (JSON Query Language)**
- **Description:** JSON query language library for parsing and filtering AWS API responses. Automatically installed as a transitive dependency of botocore.
- **Version Constraint:** Auto-resolved as botocore dependency
- **Integration Approach:** Used indirectly via botocore for response parsing

**python-dateutil (Date/Time Utilities)**
- **Description:** Date and time parsing and manipulation library; used by botocore for AWS timestamp parsing. Automatically installed as a transitive dependency of botocore.
- **Version Constraint:** Auto-resolved as botocore dependency
- **Integration Approach:** Used indirectly via botocore

**urllib3 (HTTP Client Library)**
- **Description:** HTTP client library for making HTTP requests; used by botocore for AWS API communication. Automatically installed as a transitive dependency of botocore.
- **Version Constraint:** Auto-resolved as botocore dependency
- **Integration Approach:** Used indirectly via botocore

**Required Bundling Approach:**
- Add `boto3>=1.34,<2` to `requirements.txt`
- Ensure the final extension artifact includes boto3 and all transitive dependencies
- The Universal Agent must not require pre-installed AWS CLI or global boto3 installation
- Use the Stonebranch Universal Extension build/packaging mechanism to bundle all dependencies

## Error Handling

**High Level Error Categories:**

1. **Validation Errors** (Input Validation)
   - Source file path does not exist
   - Source path is not a regular file
   - Source file is not readable
   - Return Code: 2

2. **Authentication Errors**
   - Invalid Access Key ID (AWS InvalidAccessKeyId exception)
   - Incorrect Secret Access Key (AWS SignatureDoesNotMatch exception)
   - Missing/malformed credentials
   - Return Code: 1

3. **Access Control Errors**
   - User lacks s3:ListBucket permission (List Files)
   - User lacks s3:PutObject permission (Upload File)
   - Bucket policy denies access
   - Return Code: 1

4. **Bucket Errors**
   - Bucket does not exist (AWS NoSuchBucket exception)
   - Bucket is in a different region
   - Return Code: 1

5. **Network/Connectivity Errors**
   - Cannot reach AWS S3 endpoint (EndpointConnectionError)
   - Connection timeout (ConnectTimeoutError)
   - Read timeout during upload/list operation (ReadTimeoutError)
   - Temporary AWS service unavailability
   - Return Code: 1

6. **Transient Failures** (Handled Transparently)
   - Rate limiting / throttling (AWS returns 503)
   - Botocore's built-in retry logic (enabled by default) automatically retries transient failures
   - No additional extension-level retry logic is implemented
   - If retries are exhausted, failure falls into Network/Connectivity error category

**Error Handling Strategy:**

- Catch boto3/botocore exceptions and map them to user-friendly error messages
- Log detailed error information (exception details, stack trace) to STDERR only
- Display concise, actionable error messages in STDOUT and Extension Output JSON
- Do not dump raw boto3 stack traces into STDOUT
- Translate common AWS exceptions:
  - `InvalidAccessKeyId`, `SignatureDoesNotMatch` → "AWS authentication failed..."
  - `AccessDenied` → "AWS access denied for bucket..."
  - `NoSuchBucket` → "S3 bucket '<bucket>' does not exist..."
  - `EndpointConnectionError`, `ConnectTimeoutError`, `ReadTimeoutError` → "Unable to connect to AWS S3 endpoint..."
- All error responses must include:
  - Non-zero exit_code in Extension Output JSON
  - Clear status_description in both STDOUT and Extension Output JSON
  - Metadata identifying the error category

**Recovery Mechanisms:**

- Validation errors: User must correct input (file path, credentials, etc.) and re-run
- Authentication errors: User must verify AWS credential configuration and re-run
- Access control errors: User must contact AWS administrator to grant required permissions and re-run
- Bucket errors: User must verify bucket name and region are correct and re-run
- Network/Connectivity errors: User can re-run the task; botocore's built-in retry logic may succeed on retry
- No automatic recovery or fallback strategies are implemented in the extension

## Resource Cleanup

**Cleanup Scenarios:**

1. **Normal Completion (Success)**
   - S3 client connection is closed automatically by boto3 when the script exits
   - No open file handles or network connections remain
   - No temporary files are created or need cleanup

2. **Upload Interruption/Cancellation**
   - If upload is canceled mid-transfer, the partially uploaded object remains in S3
   - No automatic cleanup of partial S3 objects is performed
   - No temporary files are created locally, so no local cleanup is needed

3. **Error Conditions**
   - S3 client connection is closed automatically even on error
   - Temporary memory buffers are freed by Python garbage collection
   - No dangling resources

**Strategy Description:**

- The extension maintains minimal resource state: only an active boto3 S3 client connection
- No temporary files are created on the Universal Agent filesystem during operations
- For Upload File, boto3 streams the file directly from disk to S3 without intermediate buffering
- For List Files, pagination results are processed immediately and not cached
- boto3 client connections are managed by context managers or explicit close calls to ensure cleanup on exit
- No manual resource cleanup code is required beyond ensuring boto3 client is properly closed

---

# References

- **Original Requirements Document:** memory/initial-1/requirements.md
- **Original Requirements Q&A Document:** memory/initial-1/requirements-QnA.md
