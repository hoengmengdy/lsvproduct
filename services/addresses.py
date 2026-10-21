import json
import re
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def location_data():
    path = Path(__file__).resolve().parent.parent / "static" / "data" / "cambodia-addresses.json"
    return {kind: {row["code"]: row for row in rows} for kind, rows in json.loads(path.read_text(encoding="utf-8")).items()}


def address_values(form):
    values = {key: form.get(key, "").strip() for key in
              ("first_name", "last_name", "phone", "province_code", "district_code", "commune_code", "street")}
    if not all(values.values()):
        raise ValueError("Complete all address fields.")
    if any(len(values[key]) > 60 for key in ("first_name", "last_name")) or len(values["street"]) > 500:
        raise ValueError("The name or street is too long.")
    locations = location_data()
    province = locations["province"].get(values["province_code"])
    district = locations["district"].get(values["district_code"])
    commune = locations["commune"].get(values["commune_code"])
    if not province or not district or not commune or district["parent"] != province["code"] or commune["parent"] != district["code"]:
        raise ValueError("Select a valid province, district and commune.")
    phone = re.sub(r"[\s()-]", "", values["phone"])
    if phone.startswith("+855"):
        phone = phone[4:]
    if phone.startswith("0"):
        phone = phone[1:]
    if not re.fullmatch(r"[1-9][0-9]{7,8}", phone):
        raise ValueError("Enter a valid Cambodian mobile phone number.")
    values["phone"] = "+855" + phone
    values["is_default"] = form.get("is_default") in {"on", "true", "1"}
    return values


def serialize_address(address, lang="en"):
    values = {key: getattr(address, key) for key in
              ("id", "first_name", "last_name", "phone", "province_code", "district_code", "commune_code", "street", "is_default")}
    locations = location_data()
    name_key = "name_km" if lang == "km" else "name"
    parts = [address.street]
    for kind in ("commune", "district", "province"):
        row = locations[kind][getattr(address, kind + "_code")]
        values[kind] = row[name_key]
        parts.append(row[name_key])
    values["name"] = address.first_name + " " + address.last_name
    values["formatted"] = ", ".join(parts)
    return values
