# Security Policy

## Public boundary

This repository is limited to client-facing protocol documentation, JSON schemas, stable error codes and deterministic test vectors. Do not add:

- Relay server source, database schema, Admin implementation or deployment internals
- Production hostnames, IP addresses, reverse-proxy configuration or infrastructure identifiers
- Tokens, cookies, passwords, private keys, signing material or `.env` files
- Personal absolute filesystem paths

Pairing payloads must not contain a Relay endpoint. Test-vector keys and nonces are public deterministic fixtures and must never be reused in production.

## Reporting

Report vulnerabilities privately through GitHub Security Advisories for this repository or the affected product repository. Do not include live credentials or user data in an issue.

## Supported version

Only the latest published Contract version is supported. Contract `1.1.0` keeps Protocol v1 and adds analytics sections, nonce binding, explicit pairing approval and bounded RFC 1950 encoding.
