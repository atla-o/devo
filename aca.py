"""ACA subsidized-insurance intake: validate, persist, look up status.

Production (Cloud Run, K_SERVICE set) writes to Firestore in GCP project
devo-holding, collection aca_applications. Local/tests use a JSON file.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

GCP_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "devo-holding")
COLLECTION = "aca_applications"
FIRESTORE_ROOT = (
    f"https://firestore.googleapis.com/v1/projects/{GCP_PROJECT}"
    "/databases/(default)/documents"
)
METADATA_TOKEN_URL = (
    "http://metadata.google.internal/computeMetadata/v1/"
    "instance/service-accounts/default/token"
)

STATUSES = (
    "received",
    "in_review",
    "needs_info",
    "submitted_to_marketplace",
)

STATUS_LABELS = {
    "received": "Received",
    "in_review": "In review",
    "needs_info": "Needs info",
    "submitted_to_marketplace": "Submitted to marketplace",
}

STATUS_DETAIL = {
    "received": "Devo has your interest form.",
    "in_review": "Devo is reviewing your information.",
    "needs_info": "Devo needs more information. Check email or update your notes.",
    "submitted_to_marketplace": (
        "Ready for enrollment through HealthCare.gov or your state exchange."
    ),
}

INCOME_BANDS = {
    "under-20k": "Under $20,000",
    "20k-40k": "$20,000–$40,000",
    "40k-60k": "$40,000–$60,000",
    "60k-80k": "$60,000–$80,000",
    "80k-100k": "$80,000–$100,000",
    "100k-150k": "$100,000–$150,000",
    "over-150k": "Over $150,000",
}

US_STATES = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "DC": "District of Columbia",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ZIP_RE = re.compile(r"^(\d{5})(?:-?\d{4})?$")
CONTACT_CHOICES = ("email", "phone")

_FILE_LOCK = threading.Lock()
_TOKEN: dict[str, Any] = {"access_token": None, "expiry": 0.0}


class ValidationError(Exception):
    def __init__(self, fields: dict[str, str]) -> None:
        super().__init__("validation")
        self.fields = fields


class StoreError(Exception):
    pass


def store_mode() -> str:
    explicit = os.environ.get("ACA_STORE", "").strip().lower()
    if explicit in {"json", "firestore"}:
        return explicit
    if os.environ.get("K_SERVICE"):
        return "firestore"
    return "json"


def data_path() -> Path:
    raw = os.environ.get("ACA_DATA_PATH", "/tmp/devo-aca-applications.json")
    return Path(raw)


def new_receipt_id() -> str:
    return "aca_" + secrets.token_hex(8)


def public_view(doc: dict[str, Any]) -> dict[str, Any]:
    status = doc.get("status") if doc.get("status") in STATUSES else "received"
    return {
        "receipt_id": doc["receipt_id"],
        "status": status,
        "status_label": STATUS_LABELS[status],
        "status_detail": STATUS_DETAIL[status],
        "created_at": doc.get("created_at"),
        "name": doc.get("name"),
        "email": doc.get("email"),
        "phone": doc.get("phone"),
        "state": doc.get("state"),
        "zip": doc.get("zip"),
        "household_size": doc.get("household_size"),
        "income_band": doc.get("income_band"),
        "income_band_label": INCOME_BANDS.get(str(doc.get("income_band") or ""), ""),
        "preferred_contact": doc.get("preferred_contact"),
        "notes": doc.get("notes") or "",
    }


def _clean(value: Any, *, max_len: int, allow_newline: bool = False) -> str:
    if value is None:
        return ""
    text = str(value)
    if allow_newline:
        text = "".join(ch for ch in text if ch == "\n" or ch >= " ")
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
    else:
        text = "".join(ch for ch in text if ch >= " ")
        text = re.sub(r"\s+", " ", text)
    return text.strip()[:max_len]


def _normalize_phone(raw: str) -> str | None:
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        return None
    return digits


def validate(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValidationError({"_form": "Send a JSON object."})

    errors: dict[str, str] = {}
    name = _clean(payload.get("name"), max_len=120)
    if len(name) < 2:
        errors["name"] = "Enter your name."

    email = _clean(payload.get("email"), max_len=254).lower()
    if not EMAIL_RE.match(email):
        errors["email"] = "Enter a valid email."

    phone = _normalize_phone(_clean(payload.get("phone"), max_len=32))
    if phone is None:
        errors["phone"] = "Enter a 10-digit US phone number."

    state = _clean(payload.get("state"), max_len=2).upper()
    if state not in US_STATES:
        errors["state"] = "Choose a state."

    zip_raw = _clean(payload.get("zip"), max_len=10)
    zip_match = ZIP_RE.match(zip_raw)
    if not zip_match:
        errors["zip"] = "Enter a 5-digit ZIP code."
    zip_code = zip_match.group(1) if zip_match else ""

    try:
        household = int(payload.get("household_size"))
        if household < 1 or household > 15:
            raise ValueError
    except (TypeError, ValueError):
        household = 0
        errors["household_size"] = "Household size must be 1–15."

    income_band = _clean(payload.get("income_band"), max_len=32)
    if income_band not in INCOME_BANDS:
        errors["income_band"] = "Choose an income range."

    preferred = _clean(payload.get("preferred_contact"), max_len=16).lower()
    if preferred not in CONTACT_CHOICES:
        errors["preferred_contact"] = "Choose email or phone."

    notes = _clean(payload.get("notes"), max_len=2000, allow_newline=True)

    if errors:
        raise ValidationError(errors)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    receipt_id = new_receipt_id()
    return {
        "receipt_id": receipt_id,
        "status": "received",
        "created_at": now,
        "updated_at": now,
        "name": name,
        "email": email,
        "email_normalized": email,
        "phone": phone,
        "state": state,
        "zip": zip_code,
        "household_size": household,
        "income_band": income_band,
        "preferred_contact": preferred,
        "notes": notes,
    }


def create(payload: Any) -> dict[str, Any]:
    doc = validate(payload)
    _save(doc)
    return public_view(doc)


def lookup(*, receipt_id: str | None = None, email: str | None = None) -> dict[str, Any] | None:
    rid = _clean(receipt_id, max_len=40)
    mail = _clean(email, max_len=254).lower()
    doc = None
    if rid:
        if not re.fullmatch(r"aca_[0-9a-f]{16}", rid):
            return None
        doc = _get_by_id(rid)
    elif mail:
        if not EMAIL_RE.match(mail):
            return None
        doc = _get_by_email(mail)
    else:
        return None
    return public_view(doc) if doc else None


def _save(doc: dict[str, Any]) -> None:
    if store_mode() == "firestore":
        _fs_create(doc)
        return
    _json_upsert(doc)


def _get_by_id(receipt_id: str) -> dict[str, Any] | None:
    if store_mode() == "firestore":
        return _fs_get(receipt_id)
    return _json_all().get(receipt_id)


def _get_by_email(email: str) -> dict[str, Any] | None:
    if store_mode() == "firestore":
        return _fs_find_email(email)
    matches = [
        doc
        for doc in _json_all().values()
        if doc.get("email_normalized") == email
    ]
    matches.sort(key=lambda d: str(d.get("created_at") or ""), reverse=True)
    return matches[0] if matches else None


def _json_all() -> dict[str, dict[str, Any]]:
    path = data_path()
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StoreError("Could not read applications.") from exc
    if not isinstance(raw, dict):
        return {}
    return {str(k): v for k, v in raw.items() if isinstance(v, dict)}


def _json_upsert(doc: dict[str, Any]) -> None:
    path = data_path()
    with _FILE_LOCK:
        data = _json_all()
        data[doc["receipt_id"]] = doc
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(path)


def _access_token() -> str:
    now = time.time()
    cached = _TOKEN.get("access_token")
    if cached and now < float(_TOKEN["expiry"]) - 60:
        return str(cached)
    req = urllib.request.Request(
        METADATA_TOKEN_URL,
        headers={"Metadata-Flavor": "Google"},
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        raise StoreError("Could not authenticate to Firestore.") from exc
    token = data.get("access_token")
    if not token:
        raise StoreError("Could not authenticate to Firestore.")
    _TOKEN["access_token"] = token
    _TOKEN["expiry"] = now + int(data.get("expires_in") or 3600)
    return str(token)


def _fs_request(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any] | list[Any] | None]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {_access_token()}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read().decode("utf-8")
            parsed = json.loads(raw) if raw else {}
            return resp.status, parsed
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8") if exc.fp else ""
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {}
        return exc.code, parsed if isinstance(parsed, (dict, list)) else {}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        raise StoreError("Could not reach Firestore in devo-holding.") from exc


def _to_fs_fields(doc: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for key, value in doc.items():
        if value is None:
            fields[key] = {"nullValue": None}
        elif isinstance(value, bool):
            fields[key] = {"booleanValue": value}
        elif isinstance(value, int) and not isinstance(value, bool):
            fields[key] = {"integerValue": str(value)}
        else:
            fields[key] = {"stringValue": str(value)}
    return fields


def _from_fs_fields(fields: dict[str, Any] | None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if not fields:
        return out
    for key, value in fields.items():
        if "stringValue" in value:
            out[key] = value["stringValue"]
        elif "integerValue" in value:
            out[key] = int(value["integerValue"])
        elif "nullValue" in value:
            out[key] = None
        elif "booleanValue" in value:
            out[key] = bool(value["booleanValue"])
    return out


def _fs_create(doc: dict[str, Any]) -> None:
    url = (
        f"{FIRESTORE_ROOT}/{COLLECTION}?"
        + urllib.parse.urlencode({"documentId": doc["receipt_id"]})
    )
    code, _ = _fs_request("POST", url, {"fields": _to_fs_fields(doc)})
    if code not in (200, 201):
        raise StoreError("Could not save application to Firestore.")


def _fs_get(receipt_id: str) -> dict[str, Any] | None:
    code, payload = _fs_request(
        "GET",
        f"{FIRESTORE_ROOT}/{COLLECTION}/{urllib.parse.quote(receipt_id, safe='')}",
    )
    if code == 404:
        return None
    if code != 200 or not isinstance(payload, dict):
        raise StoreError("Could not read application from Firestore.")
    return _from_fs_fields(payload.get("fields"))


def _fs_find_email(email: str) -> dict[str, Any] | None:
    query = {
        "structuredQuery": {
            "from": [{"collectionId": COLLECTION}],
            "where": {
                "fieldFilter": {
                    "field": {"fieldPath": "email_normalized"},
                    "op": "EQUAL",
                    "value": {"stringValue": email},
                }
            },
            "limit": 5,
        }
    }
    code, payload = _fs_request("POST", f"{FIRESTORE_ROOT}:runQuery", query)
    if code != 200:
        raise StoreError("Could not look up application in Firestore.")
    rows = payload if isinstance(payload, list) else []
    docs: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        document = row.get("document")
        if not isinstance(document, dict):
            continue
        parsed = _from_fs_fields(document.get("fields"))
        if parsed:
            docs.append(parsed)
    docs.sort(key=lambda d: str(d.get("created_at") or ""), reverse=True)
    return docs[0] if docs else None
