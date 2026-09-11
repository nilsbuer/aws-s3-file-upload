Create a new **Stonebranch Universal Extension for Universal Automation Center (UAC)**.

The extension should provide a very simple AWS S3 integration with two functions:

a) List files/objects in an AWS S3 bucket

b) Upload a file from a Linux server, where the Stonebranch Universal Agent is installed, to an AWS S3 bucket

The extension should use the Python `boto3` SDK. `boto3` and all required dependencies should be bundled with the Universal Extension so that nothing needs to be installed separately on the Universal Agent.

This should be an **MVP/demo integration only**. The purpose is simply to demonstrate that this type of AWS S3 integration can be built with Stonebranch.

Please keep the implementation as simple as possible and avoid unnecessary advanced features.
