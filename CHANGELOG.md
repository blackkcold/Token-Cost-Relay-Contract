# Changelog

All notable Contract changes are documented here.

## [1.1.0] - 2026-08-25

### Added

- Protocol v1 pairing, opaque envelope, HTTP route and WebSocket frame definitions.
- Stable client-facing `{code,error}` response semantics.
- JSON schemas and cross-platform pairing/AES-256-GCM test vectors.
- Optional analytics sections, bounded RFC 1950 zlib encoding and section parameter limits.
- Request nonce binding and asymmetric fail-closed compatibility rules.

### Security

- Pairing QR explicitly excludes and rejects endpoint override fields.
- Production Relay endpoint remains protected build configuration outside the Contract.
- Pair claims require explicit macOS approval for 1.1-capable clients.
