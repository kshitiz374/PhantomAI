# Security & Privacy — PHANTOM

## Threat model (v1)

PHANTOM treats **imported artifacts as untrusted data**. They may contain prompt-injection patterns; the backend flags common patterns and system prompts instruct the model not to obey embedded commands.

## What PHANTOM does not do

- Automatic filesystem scanning
- Executing imported file contents as shell commands
- Sending artifact text to third-party APIs (unless you configure external tooling outside this repo)
- Claiming access to OS sensors, network, or paths you did not import

## User responsibilities

- Only import files you intend to analyze
- Review Ollama/model vendor privacy policies for local inference
- Delete investigations via Settings when finished (`DELETE /api/investigations/{id}`)

## Reporting

Open a GitHub issue or contact maintainers for vulnerabilities in this application code.
