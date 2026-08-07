# Changelog

All notable Contract changes are documented here.

## [1.0.0-draft] - Unreleased

### Added

- Protocol v1 pairing, opaque envelope, HTTP route and WebSocket frame definitions.
- Stable client-facing `{code,error}` response semantics.
- JSON schemas and cross-platform pairing/AES-256-GCM test vectors.

### Security

- Pairing QR explicitly excludes and rejects endpoint override fields.
- Production Relay endpoint remains protected build configuration outside the Contract.
