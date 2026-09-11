# Dependency Log

## Zipsafe Decision
- **Result**: False
- **Reason**: Packages with data files accessed via filesystem path construction

## CLI Tools
None required. Extension uses boto3 SDK directly; no pre-installed AWS CLI or agent-level tools needed.

## Python Dependencies
- botocore==1.43.92 — Data files accessed via filesystem paths (incompatible with zip packaging)
- boto3==1.43.92 — Uses `os.path.dirname(__file__)` to locate resource data files; accesses bundled JSON resources in runtime
- s3transfer==0.19.2 — Pure Python, zip-safe; used indirectly via boto3 upload_file() method

## Analysis

### C Extensions
- Checked boto3, botocore, s3transfer: no compiled extensions (.so, .pyd files found)

### Data Files
- boto3: Contains data files (JSON resources for service definitions) accessed via `os.path.dirname(__file__)` pattern in session.py
- botocore: Contains service definitions, endpoint configuration (cacert.pem, JSON files) accessed indirectly through boto3
- s3transfer: No bundled data files

### Conclusion
boto3/botocore's use of filesystem path construction via `__file__` to access bundled service definition JSON files makes the extension not zip-safe. The extension must be packaged with zip_safe: False, allowing the 3pp dependencies to be extracted to the filesystem at runtime rather than accessed from within the zip.

## Setup Status
- ✓ boto3>=1.34,<2 requirement added to requirements.txt
- ✓ boto3/botocore/s3transfer installed and verified
- ✓ zip_safe: False configured in extension.yml
- ✓ Development requirements installed (Robot Framework, testing tools)
