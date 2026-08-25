#!/usr/bin/env python3
import base64
import json
import re
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load_json(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
contract = load_json("test-vectors/contract.json")
pairing = load_json("test-vectors/pairing-valid.json")
vector = load_json("test-vectors/aes-gcm-vector.json")
query_vector = load_json("test-vectors/request-v1.1.json")
response_vector = load_json("test-vectors/response-v1.1.json")
zlib_vector = load_json("test-vectors/section-zlib-vector.json")

if version != "1.1.0" or contract.get("contractVersion") != version:
    raise SystemExit("VERSION and contractVersion must both be 1.1.0")
if contract.get("protocolVersion") != 1:
    raise SystemExit("protocolVersion must be 1")

pairing_fields = ["version", "deviceID", "pairCode", "e2eKey", "expiresAtMilliseconds"]
if contract.get("pairingFields") != pairing_fields or list(pairing) != pairing_fields:
    raise SystemExit("pairing fields are out of sync")
if "serverBaseURL" in pairing:
    raise SystemExit("pairing payload must not contain an endpoint override")
if pairing.get("version") != 1 or len(base64.b64decode(pairing["e2eKey"], validate=True)) != 32:
    raise SystemExit("pairing vector key must decode to 32 bytes")
if not re.fullmatch(r"[A-Za-z0-9_-]{16,80}", pairing["deviceID"]):
    raise SystemExit("pairing vector deviceID is invalid")

envelope = vector.get("envelope", {})
if list(envelope) != ["v", "nonce", "ciphertext", "tag"] or envelope.get("v") != 1:
    raise SystemExit("AES-GCM envelope fields are invalid")
if len(base64.b64decode(vector["key"], validate=True)) != 32:
    raise SystemExit("AES-GCM vector key must decode to 32 bytes")
if len(base64.b64decode(envelope["nonce"], validate=True)) != 12:
    raise SystemExit("AES-GCM nonce must decode to 12 bytes")
if len(base64.b64decode(envelope["tag"], validate=True)) != 16:
    raise SystemExit("AES-GCM tag must decode to 16 bytes")
base64.b64decode(envelope["ciphertext"], validate=True)
base64.b64decode(vector["plaintext"], validate=True)

sections = contract.get("analyticsSections")
expected_sections = ["overview", "cache", "cost", "usage", "modelDistribution", "trend", "heatmap"]
if sections != expected_sections or query_vector.get("requestedSections") != expected_sections:
    raise SystemExit("analytics section whitelist is out of sync")
if response_vector.get("requestNonce") != query_vector.get("nonce"):
    raise SystemExit("response vector is not bound to request nonce")
compressed = base64.b64decode(zlib_vector["data"], validate=True)
decompressed = zlib.decompress(compressed)
if decompressed.decode("utf-8") != zlib_vector["plaintext"]:
    raise SystemExit("zlib vector plaintext mismatch")
if len(decompressed) != zlib_vector["uncompressedBytes"]:
    raise SystemExit("zlib vector size mismatch")

required_vectors = {
    "contract.json", "pairing-valid.json", "aes-gcm-vector.json",
    "request-v1.1.json", "response-v1.1.json", "section-zlib-vector.json",
}
actual_vectors = {path.name for path in (ROOT / "test-vectors").glob("*.json")}
if not required_vectors.issubset(actual_vectors):
    raise SystemExit(f"missing required vectors: {sorted(required_vectors - actual_vectors)}")

for schema_path in sorted((ROOT / "schemas").glob("*.schema.json")):
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise SystemExit(f"unexpected JSON Schema dialect: {schema_path.name}")

unix_users = "/" + "Users/"
windows_users = "C:" + chr(92) + "Users" + chr(92)
personal_path = re.compile(
    r"(?:" + re.escape(unix_users) + "|" + re.escape(windows_users) + r")(?!<)[^\s`\"']+"
)
for path in ROOT.rglob("*"):
    if not path.is_file() or ".git" in path.parts or path.stat().st_size > 1_000_000:
        continue
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    if personal_path.search(content):
        raise SystemExit(f"personal absolute path found: {path.relative_to(ROOT)}")

print("Relay Contract validation: PASS")
