# Integration Examples Reference

The following production-grade Stonebranch Universal Extension templates are provided as reference. Use them to guide field naming, type selection, credential design, and action structure.

## Field Type Reference

| Type       | When to use |
|------------|-------------|
| Choice     | Fixed enumeration — action modes, providers, protocols, regions |
| Credential | UAC Credential record reference — never store secrets inline |
| Text       | Free-form string — URLs, resource names, IDs, query strings |
| Script     | Multi-line editor — SQL, JSON payloads, shell snippets, prompts |
| Boolean    | Toggle flags — SSL verify, verbose logging, dry-run, wait mode |
| Integer    | Whole numbers — timeouts (s), retry counts, page sizes, ports |
| Float      | Decimal numbers — LLM temperature, top-p, penalty weights |
| Array      | Repeating key/value pairs — HTTP headers, env vars, parameters |

Design rules:
- Use one Credential field per authentication context (source vs. destination).
- Name credential fields clearly: `api_credential`, `sftp_credential`.
- Prefer Choice over Text for any field with a known fixed set of values.
- Use Integer for all numeric tuning knobs (timeout, retries, page size).
- Use Script only for multi-line content (payloads, queries, inline code).
- Output/status fields (Text) let operators capture results as UAC variables.

---

## Most Relevant Examples

### Enhanced File Transfer — `ue-enhanced-file-transfer`
**Category:** File Transfer
**Description:** Enhanced file transfer across SFTP, FTPS and UDM. Supports single and multi-path transfers, wildcard/regex matching, fan-out to multiple destinations, post-actions (delete, rename, archive), and smart resume for fault-tolerant retries.
**Fields (41):**

| Field name | Type | Choices / Notes |
|------------|------|-----------------|
| `action` | Choice | UDM - Single-Path File Transfer, UDM - Multi-Path File Transfer, UDM - Test Connection, SFTP - Single-Path File Transfer, SFTP - Multi-Path File Transfer, SFTP - Test Connection |
| `remote_server` | Text |  |
| `ftp_credentials` | Credential |  |
| `uac_url` | Text |  |
| `uac_credentials` | Credential |  |
| `primary_udm_agent` | Choice |  |
| `secondary_udm_agent` | Choice |  |
| `primary_udm_port` | Text |  |
| `secondary_udm_port` | Text |  |
| `primary_credentials` | Credential |  |
| `secondary_credentials` | Credential |  |
| `enable_fault_tolerance` | Boolean | false |
| `retry_count` | Integer | 20 |
| `retry_interval` | Integer | 60 |
| `network_delay` | Integer | 120 |
| `ack_window` | Text | 0 |
| `command` | Choice | PUT | Primary to Secondary, GET | Secondary to Primary |
| `transfer_type` | Choice | Text, Binary |
| `encrypt` | Choice | Yes, No |
| `codepage` | Choice | --None--, ISO 8859-1, ISO 8859-2, ISO 8859-3, ISO 8859-4, ISO 8859-5 |
| `local_file_path` | Text |  |
| `remote_file_path` | Text |  |
| `local_file_name` | Choice |  |
| `remote_file_name` | Choice |  |
| `transfers` | Array |  |
| `recent_file_only` | Boolean | false |
| `limit_age` | Integer |  |
| `dest_file_creation_option` | Choice | Overwrite, Skip, Fail |
| `move` | Boolean | false |
| `fail_on_first_error` | Boolean | true |
| `fail_if_no_files_match` | Boolean | true |
| `enable_smart_resume` | Boolean | false |
| `post_action` | Choice | Archive, Rename, Checksum Verification |
| `archive_path` | Text |  |
| `dest_rename_mode` | Choice | Pattern, Find & Replace |
| `dest_rename_pattern` | Text |  |
| `dest_rename_find` | Text |  |
| `dest_rename_replace` | Text |  |
| `transfer_progress` | Text |  |
| `skipped_files` | Text |  |
| `failed_files` | Text |  |


### Web Service Integration — `ue-webservice`
**Category:** Web Services / REST
**Description:** Web Service Integration Universal Extension
**Fields (38):**

| Field name | Type | Choices / Notes |
|------------|------|-----------------|
| `protocol` | Choice | HTTP(S)/REST |
| `http_version` | Choice | 1.1 |
| `authorization_type` | Choice | Basic, Token, API Key, None, OAuth 2.0 |
| `credentials` | Credential |  |
| `api_key` | Credential |  |
| `access_token_url` | Text |  |
| `grant_type` | Choice | Client Credentials, Password Credentials |
| `scope` | Text |  |
| `client_credentials` | Credential |  |
| `resource_owner_credentials` | Credential |  |
| `client_authentication` | Choice | Send Client Credentials in Body, Send as Basic Auth Header |
| `oauth2_token` | Text |  |
| `add_authorization_data_to` | Choice | Request Header, Request URL |
| `authorization_header_prefix` | Text | Bearer |
| `additional_credentials` | Credential |  |
| `use_ssl` | Boolean | false |
| `ssl_hostname_check` | Boolean | true |
| `trusted_certificates_file` | Text |  |
| `private_key_certificate` | Text |  |
| `public_key_certificate` | Text |  |
| `http_method` | Choice | GET, POST, PUT, PATCH, DELETE |
| `timeout` | Float |  |
| `url` | Text |  |
| `url_query_parameters` | Array |  |
| `http_headers` | Array |  |
| `payload_type` | Choice | Raw, Form Data |
| `payload_source` | Choice | Form, Script |
| `payload_script` | Script |  |
| `mime_type` | Choice | application/javascript , application/json, application/xml, text/html, text/plain, text/xml |
| `other_value_for_mime_type` | Text |  |
| `form_data` | Array |  |
| `payload` | Text |  |
| `proxies` | Text |  |
| `result_body_medium` | Choice | --None--, STDOUT |
| `process_exit_code_mapping` | Boolean | false |
| `path_expression` | Text |  |
| `exit_code_mapping` | Array |  |
| `response_code` | Text |  |


### Kong AI Gateway — `ue-kong-ai-gateway`
**Category:** AI / API Gateway
**Description:** LLM chat and autonomous agentic MCP-tool automation via Kong AI Gateway.
**Fields (47):**

| Field name | Type | Choices / Notes |
|------------|------|-----------------|
| `action` | Choice | Chat, Agentic MCP, List MCP Tools |
| `auth_method` | Choice | OAuth2 (Client Credentials), Kong API Key (key-auth) |
| `credential` | Credential |  |
| `api_key_header_name` | Text | apikey |
| `kong_gateway_url` | Text |  |
| `activate_dynamic_choices` | Boolean | false |
| `activate_overrides` | Boolean | false |
| `kong_admin_api_url` | Text |  |
| `kong_admin_api_token` | Credential |  |
| `llm_service` | Choice |  |
| `model` | Choice |  |
| `mcp_connections` | Choice |  |
| `mcp_connections_override` | Text |  |
| `allowed_tools` | Choice |  |
| `allowed_tools_override` | Text |  |
| `system_prompt_source` | Choice | Inline Text, UAC Script |
| `system_prompt_text` | Text | You are a helpful assistant. |
| `system_prompt_script` | Script |  |
| `user_prompt_source` | Choice | Inline Text, UAC Script |
| `user_prompt_text` | Text |  |
| `user_prompt_script` | Script |  |
| `response_format_type` | Choice | Text, JSON (Prompt Described), JSON Schema (API Enforced) |
| `response_format_schema` | Script |  |
| `advanced_options` | Boolean | false |
| `temperature` | Float | 1.0 |
| `top_p` | Float | 1.0 |
| `frequency_penalty` | Float | 0.0 |
| `presence_penalty` | Float | 0.0 |
| `max_tokens` | Integer | 1000 |
| `seed` | Integer |  |
| `stop_sequences` | Text |  |
| `max_turns` | Integer | 20 |
| `poll_interval` | Integer | 5 |
| `dry_run` | Boolean | false |
| `save_options` | Choice | -- None --, Save Latest Response / Final Answer, Save Entire Conversation |
| `save_destination` | Text |  |
| `chat_stdout_options` | Choice | Latest Response Only, Entire Conversation |
| `agentic_stdout_options` | Choice | Final Answer Only, Loop Progress + Final Answer |
| `chat_output_options` | Choice | Token Usage and Metadata, Complete Conversation |
| `agentic_output_options` | Choice | Token Usage and Metadata, Tool-Call Transcript |
| `prompt_tokens` | Integer |  |
| `completion_tokens` | Integer |  |
| `total_tokens` | Integer |  |
| `finish_reason` | Text |  |
| `turns_used` | Integer |  |
| `tool_call_count` | Integer |  |
| `tool_count` | Integer |  |

