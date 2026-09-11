---
extension_name: AWS S3
work_item_id: initial-1
ticket_id: ""
status: pending_review
approved_by: ""
approved_at: ""
---

# AWS S3 - Implementation Analysis

**Extension Name:** *AWS S3 (ue-aws-s3)*
**Universal Template Name:** *AWS S3*
**Builds On:** *initial-1*
**Target Platform:** Linux

---

## Extension Overview

This extension provides AWS S3 integration for Universal Automation Center (UAC), enabling UAC agents to perform two core S3 operations: listing objects in S3 buckets with optional prefix filtering and uploading local files from the Linux agent host to S3. The extension uses boto3 SDK with bundled dependencies, requiring no pre-installed AWS CLI or global boto3 on the agent host.

---

## Template Fields

### 1. Input Fields

**action**
- **Type**: Choice Field (Single-select)
- **Required When**: always
- **Options**:
  - List Files - List objects in an S3 bucket
  - Upload File - Upload a file to an S3 bucket
- **Default**: List Files
- **Validation**:
  - Must be one of the options
- **Purpose**: Specifies which S3 operation to perform; controls visibility of action-specific fields

**aws_credential**
- **Type**: Credential Field
- **Required When**: always
- **Visible When**: always
- **Validation**:
  - Must provide valid AWS credentials with Access Key ID and Secret Access Key
- **Purpose**: AWS authentication credentials for S3 access
- **Credential Mapping**:
  - Credential User field → AWS Access Key ID
  - Credential Password field → AWS Secret Access Key

**aws_region**
- **Type**: Text Field
- **Required When**: always
- **Visible When**: always
- **Validation**:
  - Must be a valid AWS region identifier (e.g., us-east-1, eu-central-1, ap-southeast-1)
- **Purpose**: AWS region where the S3 bucket is located; must match the bucket's actual region
- **Example**: eu-central-1

**bucket_name**
- **Type**: Text Field
- **Required When**: always
- **Visible When**: always
- **Validation**:
  - Must be a non-empty string
  - Bucket must exist and be accessible with provided credentials
- **Purpose**: Name of the S3 bucket to list or upload to
- **Example**: stonebranch-demo-bucket

**prefix**
- **Type**: Text Field
- **Required When**: not required
- **Visible When**: action value is equal to "List Files"
- **Validation**:
  - Optional; empty string means no prefix filter
  - Whitespace-only values are treated as empty
  - Values are trimmed of leading/trailing whitespace before use
- **Default Value**: "" (empty string)
- **Purpose**: S3 object key prefix for filtering listed objects; list from bucket root if empty
- **Example**: inbound/

**max_objects**
- **Type**: Int Field
- **Required When**: not required
- **Visible When**: action value is equal to "List Files"
- **Validation**:
  - Must be an integer value between 1 and 1000
- **Default Value**: 100
- **Purpose**: Maximum number of objects to return in the List Files result; pagination stops after reaching this limit
- **Example**: 100

**source_file**
- **Type**: Text Field
- **Required When**: action value is equal to "Upload File"
- **Visible When**: action value is equal to "Upload File"
- **Validation**:
  - Path must exist on the Universal Agent's filesystem
  - Path must be a regular file (not a directory, symlink, or device)
  - File must be readable by the process executing the extension
  - If validation fails, return specific error message indicating which validation rule was violated
- **Purpose**: Absolute path to the local file on the Universal Agent host to upload
- **Example**: /tmp/report.csv

**object_key**
- **Type**: Text Field
- **Required When**: action value is equal to "Upload File"
- **Visible When**: action value is equal to "Upload File"
- **Validation**:
  - Must be a non-empty string
- **Purpose**: S3 object key (path and filename) for the uploaded object; used exactly as provided without modification
- **Example**: inbound/report.csv

---

### 2. Output Fields

**bucket_name**
- **Type**: Text Output
- **Visible When**: always
- **Purpose**: Name of the S3 bucket involved in the operation
- **Examples**: "stonebranch-demo-bucket"

**region**
- **Type**: Text Output
- **Visible When**: always
- **Purpose**: AWS region of the S3 bucket
- **Examples**: "eu-central-1"

**object_count**
- **Type**: Text Output
- **Visible When**: action is "List Files"
- **Purpose**: Total number of objects returned by the List Files operation
- **Examples**: "2", "0"

**s3_uri**
- **Type**: Text Output
- **Visible When**: action is "Upload File"
- **Purpose**: Full S3 URI of the uploaded object in format s3://bucket_name/object_key
- **Examples**: "s3://stonebranch-demo-bucket/inbound/report.csv"

**status_message**
- **Type**: Text Output
- **Visible When**: always
- **Purpose**: Human-readable status message describing success or failure
- **Examples**: "List Files completed successfully", "Upload File completed successfully", "AWS authentication failed"

---

### 3. Field Ordering

The task form uses a **2-column grid layout**. Fields can be displayed in two ways:

- **Full-width fields**: Span both columns (typically for dropdowns, credentials, or primary selections)
- **Half-width fields**: Occupy one column, allowing two fields side-by-side (typically for related pairs)

**Layout Rules:**
- Credential fields ALWAYS span full-width (both columns)
- Action selection field spans full-width for prominence
- Connection fields (region, bucket_name) group side-by-side as a pair
- Action-specific fields show only when relevant

**Field Order (Visual Layout):**

```
┌─────────────────────────────────────────┐
│              action                     │  ← Full-width (action selector)
├─────────────────────────────────────────┤
│           aws_credential                │  ← Full-width (credential)
├─────────────────────────────────────────┤
│ aws_region          │   bucket_name     │  ← Half-width pair (connection)
├─────────────────────┼───────────────────┤
│ prefix (List Files) │ max_objects       │  ← Half-width pair (List Files only)
├─────────────────────┼───────────────────┤
│ source_file         │ object_key        │  ← Half-width pair (Upload File only)
├─────────────────────────────────────────┤
│             Output Fields                │  ← Full-width output section
└─────────────────────────────────────────┘
```

---

## Actions

### Action 1: List Files

**Description**: List objects from a specified S3 bucket with optional prefix filtering, returning object metadata (key, size, last modified timestamp) up to a configurable maximum limit.

#### Input Requirements

- **action** = "List Files"
- **aws_credential** (required)
- **aws_region** (required)
- **bucket_name** (required)
- **prefix** (optional)
- **max_objects** (optional, default 100)

#### Execution Flow

**Step 1: Initialize boto3 S3 Client**
- Create a boto3 S3 client using the provided aws_region
- Configure client with explicit credentials from aws_credential (Access Key ID and Secret Access Key)
- Do not use environment variables or default credential chain
- Do not enable boto3 debug logging

**Step 2: Normalize Prefix**
- If prefix is empty, None, or whitespace-only, use empty string (list from bucket root)
- Otherwise, trim leading/trailing whitespace from prefix and use as-is
- No modification or path normalization is applied to the prefix

**Step 3: Validate max_objects**
- Ensure max_objects is within range 1-1000
- Use default 100 if not provided or invalid

**Step 4: List Objects Using Paginator**
- Use boto3's `list_objects_v2()` API with paginator pattern
- Paginate through bucket contents automatically
- For each object, retrieve: Key, Size (in bytes), LastModified (datetime object)
- Stop pagination once object count reaches max_objects limit
- Handle empty bucket as success (return 0 objects, not an error)

**Step 5: Format Results**
- For each object collected, format LastModified timestamp to ISO 8601 UTC format: YYYY-MM-DDTHH:MM:SSZ
- Prepare object list in memory with all metadata

**Step 6: Generate Output**
- Return exit code 0 on success
- Write human-readable STDOUT format showing:
  - AWS S3 header
  - Action: "List Files"
  - Bucket information (name, region, prefix used or "(root)" if empty)
  - Numbered object list with key, size (comma-formatted), and last modified timestamp
  - Summary: total object count
- For empty results, display "No objects found" instead of object list
- Populate output fields: bucket_name, region, object_count, status_message
- Build Extension Output JSON with exit_code, status_description, metadata, and result object containing all objects

#### Output Examples

**STDOUT**:
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
   Last Modified : 2026-09-11T08:15:22Z

2. inbound/customer_002.csv
   Size          : 8,104 bytes
   Last Modified : 2026-09-11T08:18:03Z

Result
------
Objects Found : 2
```

For empty bucket:
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

**Extension Output result object (JSON)**:

The Extension output should include exit_code, status_description, metadata, and input_fields elements that are added automatically during implementation time. Show only the result element:

```json
{
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

#### Success Criteria

1. Connection to AWS S3 endpoint for specified region succeeds
2. AWS authentication using provided credentials succeeds
3. User has s3:ListBucket permission on the target bucket
4. S3 list operation completes without error
5. Object metadata (key, size, last modified) retrieved successfully for all objects up to max_objects limit
6. STDOUT displays formatted object list with correct timestamp formatting
7. Extension Output JSON contains all object metadata with correct structure
8. Exit code is 0 and status_description indicates successful completion

---

### Action 2: Upload File

**Description**: Upload a local file from the Universal Agent host to a specified S3 bucket using a specified object key, with source file validation and overwrite semantics.

#### Input Requirements

- **action** = "Upload File"
- **aws_credential** (required)
- **aws_region** (required)
- **bucket_name** (required)
- **source_file** (required)
- **object_key** (required)

#### Execution Flow

**Step 1: Validate Source File**
- Check if source_file path exists on the agent filesystem
- If not exists: return exit code 2 with error message "Source file does not exist: {path}"
- Check if path is a regular file (not directory, symlink, device file)
- If not regular file: return exit code 2 with error message "Source path is not a regular file: {path}"
- Check if file is readable by the process (stat check for read permission)
- If not readable: return exit code 2 with error message "Source file is not readable: {path} (check permissions)"
- Continue only after all three validations pass

**Step 2: Initialize boto3 S3 Client**
- Create a boto3 S3 client using the provided aws_region
- Configure client with explicit credentials from aws_credential (Access Key ID and Secret Access Key)
- Do not use environment variables or default credential chain
- Do not enable boto3 debug logging

**Step 3: Retrieve File Size**
- Get source file size in bytes from filesystem (for output reporting)

**Step 4: Upload File**
- Use boto3's `upload_file(local_path, bucket_name, object_key)` method
- This method includes built-in integrity verification
- Overwrite existing object key without confirmation (overwrite semantics)
- Do not implement or call additional post-upload verification (head_object)

**Step 5: Generate Output**
- Return exit code 0 on success
- Write human-readable STDOUT format showing:
  - AWS S3 header
  - Action: "Upload File"
  - Source file information (path, size in bytes with comma formatting)
  - Destination information (bucket name, region, object key)
  - Result: confirmation message and full S3 URI
- Populate output fields: bucket_name, region, s3_uri, status_message
- Build Extension Output JSON with exit_code, status_description, metadata, and result object containing upload details

#### Output Examples

**STDOUT**:
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

**Extension Output result object (JSON)**:

The Extension output should include exit_code, status_description, metadata, and input_fields elements that are added automatically during implementation time. Show only the result element:

```json
{
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

#### Success Criteria

1. Source file validation passes (file exists, is regular file, is readable)
2. Connection to AWS S3 endpoint for specified region succeeds
3. AWS authentication using provided credentials succeeds
4. User has s3:PutObject permission on the target bucket
5. File upload completes without error
6. boto3's built-in integrity verification confirms successful upload
7. STDOUT displays formatted upload confirmation with S3 URI
8. Extension Output JSON contains all upload metadata with correct structure
9. Exit code is 0 and status_description indicates successful completion

---

## Progress Reporting

Progress Reporting (percentage of completion report) is not required for this extension. Both List Files and Upload File operations are typically short-lived and do not have measurable, reportable progress stages.

---

## Dynamic Choice Field Population

No Dynamic choice fields should be implemented for this extension. All choice fields use static, predefined options.

---

## Cancellation Behavior

Default cancellation logic is used. When the user cancels an in-progress task:
- TERM signal is sent to the extension process
- Any active boto3 API call (list_objects_v2, upload_file) is terminated
- Extension must exit gracefully without committing partial results
- For List Files: no partial results written if canceled mid-pagination
- For Upload File: partially uploaded object remains in S3 (cannot be rolled back); no output is written until upload completes
- Extension returns non-zero exit code to indicate cancellation
- STDOUT and Extension Output indicate task was canceled, not that it completed successfully

---

## Re-Run Behavior

Re-runs are treated as initial executions with no custom logic required.

**List Files:** Fully idempotent; re-running returns the same object list (unless S3 bucket contents have changed between runs).

**Upload File:** Overwrites the existing object key if present, per the documented overwrite semantics; re-running uploads the file again to the same key. No special re-run detection or deduplication is needed.

---

## Dynamic Commands

No Dynamic commands should be implemented for this extension.

---

## Utility Modules

### Required Utility Modules

#### 1. AWS S3 Client Manager

**Purpose:** Manages boto3 S3 client initialization, configuration, and connection lifecycle with consistent error handling across all operations.

**Required Capabilities:**
- Initialize boto3 S3 client with explicit credentials (Access Key ID, Secret Access Key) and specified region
- Handle client initialization errors (invalid credentials, invalid region, network unreachable)
- Provide close/cleanup interface for connection management
- Map botocore exceptions to appropriate custom exceptions (authentication errors, access denied, bucket not found, network errors)
- Log detailed error information to STDERR without exposing credentials
- Ensure S3 client is closed on normal exit and error exit

**Used By:** List Files action, Upload File action

---

#### 2. File Validation Utility

**Purpose:** Validates source file paths for Upload File action before AWS operations begin.

**Required Capabilities:**
- Check file path existence on filesystem
- Verify file is a regular file (not directory, symlink, device)
- Verify file is readable by process (permission check)
- Return specific error messages per validation type
- Support absolute Linux file paths (e.g., /tmp/report.csv)

**Used By:** Upload File action

---

#### 3. Object Listing Handler

**Purpose:** Handles boto3 paginator logic for listing S3 objects with configurable limits and metadata extraction.

**Required Capabilities:**
- Use boto3 list_objects_v2 paginator pattern
- Apply prefix filter to bucket list operation
- Collect objects up to max_objects limit, stopping pagination when limit reached
- Extract and normalize object metadata: Key, Size, LastModified (as datetime)
- Format LastModified to ISO 8601 UTC format (YYYY-MM-DDTHH:MM:SSZ)
- Handle empty bucket results
- Map AWS errors to appropriate custom exceptions

**Used By:** List Files action

---

#### 4. Output Formatter

**Purpose:** Formats extension output consistently across actions for STDOUT and Extension Output JSON.

**Required Capabilities:**

**STDOUT Formatting:**
- Generate human-readable ASCII table format for List Files output
- Format file sizes with comma separators (e.g., 12,483)
- Format timestamps to ISO 8601 UTC format with readable alignment
- Generate structured sections: Action, Bucket/Source/Destination, Objects/Result, Summary
- Handle empty object lists gracefully with "(root)" for empty prefix and "No objects found" message

**Extension Output JSON:**
- Build JSON structure with exit_code, status_description, metadata, input_fields (auto), result
- Populate result object with action-specific fields (bucket_name, region, prefix, object_count, objects for List Files; bucket_name, region, object_key, s3_uri, source_file, file_size for Upload File)
- Set appropriate status_description for success and error scenarios
- Include metadata with extension name and action

**Error Output:**
- Format error messages with category prefix: "Category: Description" pattern
- Do not include raw exception stack traces in user-facing output
- Log full exception details to STDERR only

**Used By:** List Files action, Upload File action

---

#### 5. Credentials Handler

**Purpose:** Manages credential extraction and ensures credentials are never exposed in logs or output.

**Required Capabilities:**
- Extract Access Key ID and Secret Access Key from UAC Credential object
- Map credential fields correctly: user → Access Key ID, password → Secret Access Key
- Ensure credentials are passed only to boto3 client initialization
- Implement credential redaction in all logging output
- Never log or print credential values in STDOUT, STDERR, or Extension Output
- Validate credential object structure before use

**Used By:** AWS S3 Client Manager, both actions

---

## Exception Mapping Strategy

**HTTP Communication and Connection Errors:**
- `EndpointConnectionError` (cannot reach S3 endpoint) → AWSConnectionError (exit code 1, transient)
- `ConnectTimeoutError` (connection timeout) → AWSConnectionError (exit code 1, transient)
- `ReadTimeoutError` (read timeout) → AWSConnectionError (exit code 1, transient)
- `ConnectionError` (general network failure) → AWSConnectionError (exit code 1, transient)

**Authentication Errors:**
- `InvalidAccessKeyId` → AWSAuthenticationError (exit code 1, non-transient, user config)
- `SignatureDoesNotMatch` (invalid secret access key) → AWSAuthenticationError (exit code 1, non-transient, user config)
- `NoCredentialsError` (credentials not provided) → AWSAuthenticationError (exit code 1, non-transient, user config)

**Access Control Errors:**
- `AccessDenied` (user lacks IAM permissions) → AWSAccessDeniedError (exit code 1, non-transient, user config)
- Any error with message containing "not have permission" → AWSAccessDeniedError (exit code 1, non-transient, user config)

**Bucket Errors:**
- `NoSuchBucket` (bucket does not exist) → AWSBucketNotFoundError (exit code 1, non-transient, user config)
- `404 NoSuchBucket` HTTP error → AWSBucketNotFoundError (exit code 1, non-transient, user config)

**File Validation Errors (Upload File only):**
- File not exists (os.path.exists returns False) → FileValidationError (exit code 2, non-transient, user input)
- File is directory or not regular file (os.path.isfile returns False) → FileValidationError (exit code 2, non-transient, user input)
- File not readable (permission denied on file read check) → FileValidationError (exit code 2, non-transient, user input)

**Unexpected System Errors:**
- All other exceptions (unexpected error, bug in extension code) → UnexpectedError (exit code 1, transient, system)

**Exit Code Guide:**
- Exit code 0: Successful completion
- Exit code 1: Authentication error, access denied, bucket not found, network error, or unexpected system error (non-transient failures and transient failures that are exhausted)
- Exit code 2: Validation error (source file validation for Upload File only)

**Error Handling Implementation:**
- Catch botocore.exceptions.ClientError and map to specific exception based on error code and message
- Catch botocore.exceptions.NoCredentialsError explicitly
- Catch botocore.exceptions.EndpointConnectionError, ConnectTimeoutError, ReadTimeoutError explicitly
- For Upload File, catch OSError and FileNotFoundError for file validation
- Log full exception details (stack trace) to STDERR only
- Display concise, actionable error message to STDOUT and Extension Output
- Never dump raw boto3 exception or stack traces to user-facing output

---

## Dependencies

### 1. External API Dependencies

No Web APIs are required. The extension integrates directly with Amazon S3 via boto3 SDK.

---

### 2. Python version dependency

Python 3.8 and later (3.8+).

---

### 3. Target Platform

Linux (x86_64), manylinux_2_17_x86_64. The extension supports Linux targets only and does not require pre-installed AWS CLI or global boto3 on the Universal Agent host.

---

### 4. Python Library Dependencies

**1. boto3**
- **Purpose**: High-level AWS SDK providing S3 client for list_objects_v2 and upload_file operations
- **Version**: >=1.34,<2 (boto3 versions 1.34.x through 1.99.x; does not force upgrade to 2.0+)
- **Installation**: `pip install 'boto3>=1.34,<2'`
- **Usage**: S3 client initialization and operations (listing, uploading); credentials handling
- **Features Used**: boto3.client("s3"), list_objects_v2 paginator, upload_file(), ClientError exception handling

**2. botocore**
- **Purpose**: Low-level AWS SDK core used by boto3 for service communication and error handling
- **Version**: Auto-pinned with boto3 (e.g., boto3 1.34.x → botocore 1.34.x)
- **Installation**: Automatic transitive dependency of boto3
- **Usage**: Implicitly used by boto3 for service operations and error mapping
- **Features Used**: Exception classes (ClientError, NoCredentialsError, EndpointConnectionError, etc.) for detailed error handling

**3. s3transfer**
- **Purpose**: High-level S3 transfer library handling multipart uploads, retries, and integrity verification
- **Version**: Auto-resolved as boto3 dependency
- **Installation**: Automatic transitive dependency of boto3
- **Usage**: Used indirectly via boto3's upload_file() method
- **Features Used**: Built-in integrity checking and retry logic for file uploads

---

### 5. Python Standard Library Dependencies

**1. os**
- **Purpose**: File system operations (path existence, file type checking, file size)
- **Features Used**: os.path.exists(), os.path.isfile(), os.stat() for file validation

**2. datetime**
- **Purpose**: Timestamp handling and formatting
- **Features Used**: datetime.isoformat(), UTC timezone handling for LastModified timestamp formatting

**3. json**
- **Purpose**: JSON serialization for Extension Output
- **Features Used**: json.dumps() for structured output generation

---

### 6. CLI Tool Dependencies

No Dependencies

---

### 7. Environment Variables

No Specific Environment Variables Supported
