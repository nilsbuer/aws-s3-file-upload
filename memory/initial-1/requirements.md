# Build a New Stonebranch Universal Extension: AWS S3 MVP

## Goal

Create a new **Stonebranch Universal Extension / Universal Task** for **Universal Automation Center (UAC)** that demonstrates a simple AWS S3 integration.

This is intentionally an **MVP / demo integration**. Keep it small, easy to understand, and easy to demonstrate.

The Universal Task must support exactly two operations:

1. **List Files** in an AWS S3 bucket
2. **Upload File** from the Linux server where the Stonebranch Universal Agent is running to an AWS S3 bucket

Use the Python **boto3** SDK.

The extension package must **bundle boto3 and its required Python dependencies** so that the Universal Agent does **not** need boto3 or the AWS CLI preinstalled.

Do **not** use the `aws` command-line tool.

---

# 1. Suggested Extension Identity

Recommended:

```text
Display Name:
AWS S3

Extension Name / ID:
aws-s3
```

Description:

```text
Lists objects in an Amazon S3 bucket and uploads files from a Stonebranch Universal Agent host to Amazon S3.
```

This is an MVP. Do not add unnecessary enterprise features.

---

# 2. Universal Task Design

Use one Universal Task with an `action` Choice field.

Actions:

```text
List Files
Upload File
```

Do not create separate Universal Templates for each operation.
Do not use task-instance Commands for this MVP.

---

# 3. Input Fields

## `action`

```text
Label       : Action
Type        : Choice
Required    : Yes
Values      :
  List Files
  Upload File
Default     : List Files
```

## `aws_credential`

```text
Label       : AWS Credential
Type        : Credential
Required    : Yes
```

Map:

```text
Credential User     -> AWS Access Key ID
Credential Password -> AWS Secret Access Key
```

Never log either value.

For this MVP, do not implement:

```text
STS AssumeRole
AWS SSO
Web Identity
EC2 Instance Profile
IAM Roles Anywhere
temporary Session Token
```

## `aws_region`

```text
Label       : AWS Region
Type        : Text
Required    : Yes
Example     : eu-central-1
```

Do not hard-code a region.

## `bucket_name`

```text
Label       : S3 Bucket Name
Type        : Text
Required    : Yes
Example     : stonebranch-demo-bucket
```

---

# 4. List Files Fields

## `prefix`

```text
Label       : Prefix
Type        : Text
Required    : No
Example     : inbound/
```

Empty means list from bucket root.

Show only when:

```text
action = List Files
```

Use the Action field's `fieldMapping` in `showIfField`, not its field `name`.

## `max_objects`

```text
Label       : Maximum Objects
Type        : Integer
Required    : No
Default     : 100
Minimum     : 1
Maximum     : 1000
```

Show only for `List Files`.

---

# 5. Upload File Fields

## `source_file`

```text
Label       : Source File
Type        : Text
Required    : Yes for Upload File
Example     : /tmp/report.csv
```

This is a file path on the **Linux server where the Universal Agent executes the task**.

Validate:

```text
path exists
path is a regular file
path is readable
```

Do not implement directory upload or wildcards.

Show only for `Upload File`.

## `object_key`

```text
Label       : S3 Object Key
Type        : Text
Required    : Yes for Upload File
Example     : inbound/report.csv
```

Do not automatically alter the object key.

Show only for `Upload File`.

---

# 6. Keep the MVP Small

Do not add:

```text
ACL
Storage Class
KMS
SSE options
Metadata
Tags
Delete
Download
Copy
Move
Presigned URLs
Endpoint URL
S3-compatible storage
Proxy settings
IAM role assumption
AWS session token
Recursive directory upload
Wildcard upload
```

---

# 7. Bundle boto3

The extension must bundle **boto3** and all required transitive dependencies.

Use the normal dependency mechanism of the generated Stonebranch Universal Extension workspace.

Add boto3 to the existing dependency file, for example:

```text
requirements.txt
```

Suggested requirement:

```text
boto3>=1.34,<2
```

Ensure the final extension artifact contains/resolves boto3 dependencies such as:

```text
botocore
s3transfer
jmespath
python-dateutil
urllib3
```

Do not manually vendor only a single boto3 file.
Do not require AWS CLI.

---

# 8. boto3 Client

Create a small helper:

```python
import boto3

def create_s3_client(access_key_id, secret_access_key, region_name):
    return boto3.client(
        "s3",
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=region_name,
    )
```

Never log:

```text
AWS Access Key ID
AWS Secret Access Key
Authorization headers
signed request headers
```

Do not enable boto3/botocore wire debug logging.

---

# 9. Action: List Files

Use:

```python
s3.get_paginator("list_objects_v2")
```

or repeated `list_objects_v2()` calls.

Inputs:

```text
bucket_name
prefix
max_objects
```

Stop after `max_objects`.

For each object collect:

```text
Key
Size
LastModified
```

If no objects match, return success with:

```text
0 objects found
```

Do not treat an empty bucket as an error.

---

# 10. List Files Task Output

Example:

```text
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

For no matches:

```text
Objects
-------
No objects found.

Result
------
Objects Found : 0
```

Do not use `tabulate`.
Use simple Python formatting.

Recommended machine-readable output:

```text
bucket_name
prefix
object_count
objects
```

If UAC output fields cannot represent arrays cleanly, keep `bucket_name`, `prefix`, and `object_count` as normal output fields and return the object list as JSON output.

---

# 11. Action: Upload File

Validate the local path with `pathlib.Path`.

Example:

```python
from pathlib import Path

source = Path(source_file)

if not source.exists():
    raise DataValidationError(
        f"Source file does not exist: {source_file}"
    )

if not source.is_file():
    raise DataValidationError(
        f"Source path is not a regular file: {source_file}"
    )
```

Upload with:

```python
s3.upload_file(
    str(source),
    bucket_name,
    object_key,
)
```

After upload, optionally call:

```python
s3.head_object(
    Bucket=bucket_name,
    Key=object_key,
)
```

to confirm size/ETag.

---

# 12. Upload Semantics

For the MVP:

```text
If the object key already exists, upload_file overwrites the current object.
```

Document this behavior.
Do not add overwrite confirmation or version management.

---

# 13. Upload Task Output

Example:

```text
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

Recommended structured output:

```text
bucket_name
object_key
s3_uri
source_file
file_size
```

Optional:

```text
etag
```

---

# 14. Error Handling

Translate common boto3/botocore errors into user-friendly messages.

Use appropriate botocore exceptions, for example:

```python
from botocore.exceptions import (
    ClientError,
    NoCredentialsError,
    EndpointConnectionError,
    ConnectTimeoutError,
    ReadTimeoutError,
)
```

Examples:

### Authentication

For `InvalidAccessKeyId` / `SignatureDoesNotMatch`:

```text
AWS authentication failed. Verify the configured AWS credential.
```

### Access denied

For `AccessDenied`:

```text
AWS access denied for bucket '<bucket>'. Verify the IAM permissions assigned to the AWS credential.
```

### Bucket not found

For `NoSuchBucket`:

```text
S3 bucket '<bucket>' does not exist or is not accessible.
```

### Network

```text
Unable to connect to the AWS S3 endpoint for region '<region>'.
```

Do not dump long boto3 stack traces into normal Task Output.

---

# 15. Minimum IAM Permissions

Document the minimum IAM permissions required for the demo credential.

List:

```text
s3:ListBucket
```

Upload:

```text
s3:PutObject
```

Example policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListBucket",
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": ["arn:aws:s3:::stonebranch-demo-bucket"]
    },
    {
      "Sid": "UploadObjects",
      "Effect": "Allow",
      "Action": ["s3:PutObject"],
      "Resource": ["arn:aws:s3:::stonebranch-demo-bucket/*"]
    }
  ]
}
```

Documentation only. The extension must not manage IAM.

---

# 16. UAC Template Rules

Follow the generated Stonebranch Universal Extension scaffold and current schema.

Important:

1. Keep `variablePrefix` as:

   ```text
   ops_var
   ```

2. Preserve all required top-level Universal Template properties generated by the scaffold.

3. `showIfField` / `requireIfField` must use the controlling field's **fieldMapping**, not its `name`.

4. Every field must have a unique 32-character hexadecimal `sysId` when required.

5. Use only field types supported by the current Universal Template schema.

6. Normalize Choice values because UAC may provide:

   ```python
   ["List Files"]
   ```

   or:

   ```python
   []
   ```

7. Do not invent unsupported field types.

---

# 17. Suggested Project Structure

Use the structure generated by the Stonebranch scaffold.

A simple layout could be:

```text
extension-code/
  src/
    extension.py
    actions/
      list_files.py
      upload_file.py
    fields/
      input_fields.py
      output_fields.py
    utility/
      s3_client.py
      output_formatter.py
    exceptions.py
  requirements.txt
```

Do not force this exact structure if the scaffold uses another supported layout.

---

# 18. Main Extension Flow

Conceptually:

```python
action = normalize_scalar(fields.get("action"))

if action == "List Files":
    return list_files(...)

if action == "Upload File":
    return upload_file(...)

raise DataValidationError(
    f"Unsupported action: {action}"
)
```

Do not add more actions.

---

# 19. Logging

INFO examples:

```text
AWS S3 extension started
Action requested: List Files
Listing objects in bucket stonebranch-demo-bucket
Found 2 objects
AWS S3 extension completed successfully
```

Upload:

```text
Action requested: Upload File
Uploading /tmp/report.csv to s3://stonebranch-demo-bucket/inbound/report.csv
Upload completed successfully
```

Never log credentials.

---

# 20. Tests

Keep tests focused and mock AWS.

## List Files

Test:

```text
successful list
empty bucket
prefix filtering
max_objects limit
AccessDenied
NoSuchBucket
invalid credentials
```

## Upload File

Test:

```text
successful upload
missing local file
path is a directory
AccessDenied
NoSuchBucket
invalid credentials
network failure
```

Do not require a live AWS account for unit tests.

---

# 21. Documentation

Generate a short README / extension documentation with:

```text
Purpose
Prerequisites
Required IAM permissions
How to create the Stonebranch Credential
List Files example
Upload File example
Known MVP limitations
```

Credential mapping:

```text
Stonebranch Credential:
User     = AWS Access Key ID
Password = AWS Secret Access Key
```

List example:

```text
Action          : List Files
AWS Region      : eu-central-1
S3 Bucket Name  : stonebranch-demo-bucket
Prefix          : inbound/
Maximum Objects : 100
```

Upload example:

```text
Action          : Upload File
AWS Region      : eu-central-1
S3 Bucket Name  : stonebranch-demo-bucket
Source File     : /tmp/report.csv
S3 Object Key   : inbound/report.csv
```

Explicitly state:

```text
The Source File path is evaluated on the Linux host where the Universal Agent runs.
```

---

# 22. MVP Limitations

Document:

```text
No download
No delete
No directory upload
No wildcard upload
No S3-compatible endpoints
No AssumeRole
No AWS session token
No IAM role authentication
No object metadata/tags
No encryption options
No presigned URLs
No bucket creation/deletion
```

This is intentional.

---

# 23. Acceptance Criteria

The extension is complete when:

1. It builds successfully as a Stonebranch Universal Extension.
2. It imports successfully into Universal Automation Center.
3. boto3 and required dependencies are bundled.
4. The Universal Agent does not require AWS CLI or a global boto3 install.
5. The task provides exactly:
   - `List Files`
   - `Upload File`
6. List Files can list S3 objects.
7. Prefix filtering works.
8. `Maximum Objects` prevents excessive output.
9. Upload File can upload a local Linux file from the Universal Agent host.
10. The configured object key is used exactly.
11. Existing keys may be overwritten and this is documented.
12. AWS credentials are supplied through a Stonebranch Credential.
13. Credentials are never logged.
14. Task Output is concise and user-friendly.
15. Common AWS errors are translated into readable messages.
16. Unit tests mock AWS.
17. The code stays intentionally small and understandable.

---

# 24. Scope Guard

Do not over-engineer this integration.

Do not add:

```text
AWS CLI
CloudFormation
Terraform
IAM administration
additional AWS services
asynchronous monitoring
complex abstraction layers
sub-agents
```

The final result should be a clean **AWS S3 MVP Universal Extension** demonstrating:

```text
Stonebranch UAC
    |
    v
Universal Agent on Linux
    |
    v
Bundled boto3 SDK
    |
    v
Amazon S3
```

with only:

```text
List Files
Upload File
```
