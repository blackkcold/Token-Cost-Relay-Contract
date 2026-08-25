# Token Cost Relay Contract

Public, implementation-neutral contract for the optional Token Cost App Relay feature.

## Status

- Protocol: `v1`
- Contract: `1.1.0`
- Stability: frozen additive Protocol v1 analytics and security contract

This repository contains no Relay server implementation, deployment configuration, production endpoint, credentials or client SDK.

## Contents

- `protocol-v1.md` — client-facing HTTP, WebSocket, pairing and cryptographic rules
- `schemas/` — JSON Schema documents for pairing, opaque envelopes and relay query responses
- `test-vectors/` — version snapshot, pairing/AES-256-GCM vectors, nonce binding and RFC 1950 zlib section vectors
- `VERSION` — canonical contract version

## Consumers

- **Token-Cost-App-OC-Codex**: Swift macOS and Dart/Flutter Android clients
- **Token-Cost-Relay**: private Node.js Relay implementation

Consumers vendor a fixed snapshot and must not fetch this repository at runtime or during a Public App build.

## Validation

```bash
python3 scripts/validate_contract.py
```

The deterministic key and nonce in `test-vectors/aes-gcm-vector.json` are test data only and must never be used in production.

## Compatibility

- Additive, optional fields require a draft review and synchronized compatibility tests.
- Removing or changing required fields, routes, frame names, cryptographic encoding or error semantics requires a new protocol version.
- Pairing payloads never carry a Relay endpoint. Production clients obtain the HTTPS endpoint only from protected build configuration.

## License

MIT — see `LICENSE`.
