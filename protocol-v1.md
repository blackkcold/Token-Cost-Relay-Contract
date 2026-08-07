# Relay Protocol v1

Contract version: `1.0.0-draft`

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
{"action":"balance.refresh","issuedAtMilliseconds":1700000000000,"nonce":"unique-client-nonce"}
```

The request timestamp must be within five minutes of the receiver's clock. The plaintext nonce is 16–100 characters and must not be replayed.

Decrypted response payload:

```json
{"generatedAtMilliseconds":1700000000000,"snapshots":[]}
```

The exact `BalanceSnapshot` product model is owned by the Public App. Unknown snapshot providers or fields must not weaken envelope validation.

## 7. Client error response

Client-facing API errors use a stable machine code and a safe human-readable message:

```json
{"code":"PC_OFFLINE","error":"PC offline"}
```

Stable v1 codes:

```text
ALREADY_PAIRED
DEVICE_NOT_FOUND
DEVICE_RATE_LIMITED
DUPLICATE_REQUEST
INTERNAL_ERROR
INVALID_APP_CREDENTIALS
INVALID_CREDENTIALS
INVALID_DEVICE_CREDENTIALS
INVALID_PAIRING_PAYLOAD
INVALID_PC_CREDENTIALS
INVALID_RELAY_ENVELOPE
INVALID_REQUEST
IP_BLOCKED
NOT_FOUND
PAIRING_INVALID_OR_EXPIRED
PAIRING_RATE_LIMITED
PC_DISCONNECTED
PC_OFFLINE
PC_RESPONSE_TIMEOUT
PC_SEND_FAILED
REGISTRATION_RATE_LIMITED
RELAY_INTERNAL_ERROR
SERVER_SHUTDOWN
TOO_MANY_REQUESTS
```

Clients branch on `code`, never by matching the `error` text.

## 8. Versioning and freeze gate

The `1.0.0-draft` contract may change only with synchronized Swift, Dart and Node compatibility updates. It becomes `1.0.0` and may be tagged only after:

1. All three implementations pass the published vectors.
2. Staging completes register, pair, query, decrypt, reconnect, timeout, revoke and delete flows.
3. QR, UI and logs are verified not to expose or override the Production endpoint.
