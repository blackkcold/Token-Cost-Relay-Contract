# Relay Protocol v1

Contract version: `1.1.0`

## 1. Scope and trust boundary

The Relay forwards opaque end-to-end encrypted envelopes between one macOS PC client and one paired Android app client. Provider credentials and decrypted balance data remain on the clients. The Relay authenticates devices, enforces limits and correlates requests, but must not interpret encrypted payloads.

All Production HTTP and WebSocket traffic uses HTTPS/WSS. Paths below are relative to an externally configured Relay base URL. The endpoint is not part of this contract and must never be encoded in a pairing QR.

## 2. Pairing QR

URI form:

```text
balance-relay://pair?data=<base64url(JSON)>
```

Decoded JSON fields:

| Field | Type | Rule |
|---|---|---|
| `version` | integer | Exactly `1` |
| `deviceID` | string | 16–80 characters, `[A-Za-z0-9_-]` |
| `pairCode` | string | 24–100 characters, single-use and short-lived |
| `e2eKey` | string | Standard Base64 encoding of exactly 32 random bytes |
| `expiresAtMilliseconds` | integer | Unix epoch milliseconds; must be in the future |

Unknown endpoint override fields, including legacy `serverBaseURL`, are rejected.

## 3. Authentication

Authenticated device routes use:

```http
Authorization: Bearer <device token>
X-Device-Id: <deviceID>
```

PC-only routes require the PC token. App-only routes require the App token. Revoke/delete and registration-status accept the credential types documented by the implementation while preserving the response semantics below.

## 4. Client-facing routes

| Method and path | Purpose | Successful response |
|---|---|---|
| `POST /api/v1/devices/register` | Register PC | `{deviceId, pcToken}` |
| `POST /api/v1/pair/start` | Create pairing code | `{deviceId, pairCode, expiresAt}` |
| `POST /api/v1/pair/approve` | Explicitly approve the current pairing code from a 1.1-capable PC | `{ok, approved}` |
| `POST /api/v1/pair/claim` | Claim pairing from app | `{deviceId, appToken}` |
| `POST /api/v1/devices/revoke` | Revoke registration | `{ok, changed}` |
| `DELETE /api/v1/devices` | Delete/revoke device | `{ok, deleted}` |
| `POST /api/v1/device/registration-status` | Distinguish missing/registered/invalid credential | `{registered, paired, disabled}` |
| `GET /api/v1/device/status` | App view of device state | `{deviceId, online, appOnline, appLastSeenAt}` |
| `GET /api/v1/device/pairing-status` | PC view of pairing state | `{deviceId, paired, online, appOnline, appLastSeenAt}` |
| `POST /api/v1/relay/query` | Forward opaque app request | `{requestId, envelope}` |

`POST /api/v1/relay/query` accepts `schemas/request.schema.json`. `requestId` is unique per device for at least the replay window.

## 5. WebSocket

PC connection path:

```text
/ws/pc
```

The upgrade request uses the PC authentication headers from section 3.

Relay to PC:

```json
{"type":"relay.request","requestId":"request_identifier","envelope":{"v":1,"nonce":"...","ciphertext":"...","tag":"..."}}
```

PC to Relay:

```json
{"type":"relay.response","requestId":"request_identifier","envelope":{"v":1,"nonce":"...","ciphertext":"...","tag":"..."}}
```

Text frames are canonical. Implementations may accept UTF-8 JSON in legacy binary frames during migration, without changing message semantics.

## 6. Opaque envelope and E2EE payloads

Envelope fields are defined by `schemas/envelope.schema.json`:

- Algorithm: AES-256-GCM
- Key: the 32-byte `e2eKey` exchanged in the pairing QR
- Nonce: fresh 12 random bytes for every encryption, Standard Base64 encoded
- Authentication tag: 16 bytes, Standard Base64 encoded
- Ciphertext: Standard Base64 encoded
- Envelope version `v`: exactly `1`

Decrypted request payload:

```json
{
  "action": "balance.refresh",
  "issuedAtMilliseconds": 1700000000000,
  "nonce": "unique-client-nonce",
  "requestedSections": ["overview", "cache", "cost", "usage", "modelDistribution", "trend", "heatmap"],
  "sectionParams": {"trend": {"days": 30}, "heatmap": {"weeks": 52}}
}
```

The request timestamp must be within five minutes of the receiver's clock. The plaintext nonce is 16–100 characters and must not be replayed. Missing or empty `requestedSections` preserves the legacy snapshots-only response. Section names are unique and restricted to the published whitelist. `trend.days` is `1...90` (default 30); `heatmap.weeks` is `1...52` (default 52).

Decrypted response payload:

```json
{
  "generatedAtMilliseconds": 1700000000000,
  "requestNonce": "unique-client-nonce",
  "snapshots": [],
  "compression": "zlib",
  "sections": {
    "overview": {"encoding": "json+zlib", "uncompressedBytes": 143, "data": "..."}
  }
}
```

The exact `BalanceSnapshot` product model is owned by the Public App. Unknown snapshot providers or fields must not weaken envelope validation. Every 1.1 response, including an encrypted business error, binds `requestNonce` to the decrypted request nonce. New clients reject a missing or mismatched nonce and require the macOS client to be upgraded.

### Analytics section encoding and limits

- The whitelist is `overview`, `cache`, `cost`, `usage`, `modelDistribution`, `trend`, and `heatmap`.
- Section JSON is encoded as UTF-8, compressed as an RFC 1950 zlib stream, then Standard Base64 encoded.
- Compression occurs before the response AES-256-GCM operation. The Relay still sees only the opaque outer envelope.
- Each decompressed section is limited to 131,072 bytes and all decompressed sections together to 524,288 bytes.
- The complete HTTP body or WebSocket frame is limited to 65,536 bytes. Implementations measure the final serialized transport object, not only the ciphertext.
- A receiver must enforce decompressed output limits while decoding; the untrusted `uncompressedBytes` declaration is only a preflight hint.
- Oversized responses are not truncated. The PC returns a nonce-bound `RESPONSE_TOO_LARGE` error so the app can request deterministic section batches.

### Pairing approval

The pair code is visible to the Relay because the app submits it over HTTPS. A 1.1-capable PC sends `X-Relay-Contract: 1.1.0` when starting a pairing. Such a code is unapproved until the PC calls `POST /api/v1/pair/approve` after an explicit user confirmation. Claiming an unapproved code returns `PAIRING_APPROVAL_REQUIRED`. Legacy PC clients omit the capability header and retain the 1.0 auto-approved behavior during migration.

## 7. Client error response

Client-facing API errors use a stable machine code and a safe human-readable message:

```json
{"code":"PC_OFFLINE","error":"PC offline"}
```

Stable v1 codes:

```text
ALREADY_PAIRED
ANALYTICS_UNAVAILABLE
DECOMPRESSION_LIMIT_EXCEEDED
DEVICE_NOT_FOUND
DEVICE_RATE_LIMITED
DUPLICATE_REQUEST
INTERNAL_ERROR
INVALID_APP_CREDENTIALS
INVALID_CREDENTIALS
INVALID_COMPRESSION
INVALID_DEVICE_CREDENTIALS
INVALID_PAIRING_PAYLOAD
INVALID_PC_CREDENTIALS
INVALID_RELAY_ENVELOPE
INVALID_REQUEST
INVALID_SECTION
INVALID_SECTION_PARAMS
IP_BLOCKED
NOT_FOUND
PAIRING_APPROVAL_REQUIRED
PAIRING_INVALID_OR_EXPIRED
PAIRING_RATE_LIMITED
PC_DISCONNECTED
PC_OFFLINE
PC_RESPONSE_TIMEOUT
PC_SEND_FAILED
REGISTRATION_RATE_LIMITED
REQUEST_RATE_LIMITED
REQUEST_REPLAYED
REQUEST_TIMEOUT
RELAY_INTERNAL_ERROR
RESPONSE_TOO_LARGE
SECTION_TOO_LARGE
SECTIONS_TOO_LARGE
SERVER_SHUTDOWN
TOO_MANY_REQUESTS
UPGRADE_REQUIRED
```

Clients branch on `code`, never by matching the `error` text.

## 8. Compatibility

- Old Android with a 1.1 macOS client remains supported; additive response fields are ignored.
- A missing `requestedSections` field receives snapshots only.
- A new Android client with an old macOS client fails closed because the old response lacks `requestNonce`; the client displays `UPGRADE_REQUIRED` rather than accepting a replayable response.
- Unknown section names and invalid parameters fail with stable encrypted errors instead of being silently ignored.

## 9. Versioning and freeze gate

The `1.1.0` contract may be tagged only after:

1. All three implementations pass the published vectors.
2. Staging completes register, pair, query, decrypt, reconnect, timeout, revoke and delete flows.
3. QR, UI and logs are verified not to expose or override the Production endpoint.

The `1.1.0` freeze gate was completed on 2026-08-25 before publication.
