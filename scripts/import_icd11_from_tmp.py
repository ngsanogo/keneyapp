#!/usr/bin/env python3
"""
Import ICD-11 codes from GNU Health diseases.xml (tmp/his/tryton/health_icd11/data/diseases.xml)
into KeneyApp's medical_codes table.

Usage (from repo root):
    python scripts/import_icd11_from_tmp.py \
        --xml-path tmp/his/tryton/health_icd11/data/diseases.xml \
        --limit 1000  # optional for dry-run/sampling

Notes:
- Only imports code, display (name), and sets code_system='icd11'.
- Skips inactive records.
- Upserts by (code_system, code).
"""

import argparse
import sys
from typing import Iterator, Tuple
import xml.etree.ElementTree as ET

from app.core.database import SessionLocal
from app.models.medical_code import MedicalCode, CodeSystem


def iter_icd11_records(xml_path: str) -> Iterator[Tuple[str, str, bool]]:
    """Yield (code, name, active) from GNU Health diseases.xml records lazily.

    The XML contains records like:
        <record model="gnuhealth.pathology" id="1A00"> ...
          <field name="code">1A00</field>
          <field name="name">Cholera</field>
          <field name="active">True</field>
        </record>
    """
    context = ET.iterparse(xml_path, events=("end",))
    for event, elem in context:
        if elem.tag == "record" and elem.attrib.get("model") == "gnuhealth.pathology":
            code = None
            name = None
            active = True
            for field in elem.findall("field"):
                fname = field.attrib.get("name")
                if fname == "code":
                    code = (field.text or "").strip()
                elif fname == "name":
                    name = (field.text or "").strip()
                elif fname == "active":
                    active = (field.text or "True").strip().lower() == "true"

            if code and name:
                yield code, name, active

            # Clear to free memory
            elem.clear()


def upsert_icd11(db, code: str, display: str) -> None:
    """Upsert a single ICD-11 code into medical_codes.

    If a record exists with same code_system+code, update display if changed.
    """
    existing = (
        db.query(MedicalCode)
        .filter(MedicalCode.code_system == CodeSystem.ICD11.value, MedicalCode.code == code)
        .first()
    )
    if existing:
        if existing.display != display:
            existing.display = display
            db.add(existing)
    else:
        mc = MedicalCode(code_system=CodeSystem.ICD11, code=code, display=display)
        db.add(mc)


def main() -> int:
    parser = argparse.ArgumentParser(description="Import ICD-11 codes into KeneyApp")
    parser.add_argument(
        "--xml-path",
        default="tmp/his/tryton/health_icd11/data/diseases.xml",
        help="Path to GNU Health diseases.xml",
    )
    parser.add_argument("--limit", type=int, default=0, help="Limit number of records (0=all)")
    parser.add_argument(
        "--batch-size", type=int, default=1000, help="DB commit batch size for performance"
    )
    args = parser.parse_args()

    db = SessionLocal()
    count = 0
    try:
        for code, name, active in iter_icd11_records(args.xml_path):
            if not active:
                continue
            upsert_icd11(db, code, name)
            count += 1
            if count % args.batch_size == 0:
                db.commit()
            if args.limit and count >= args.limit:
                break
        db.commit()
        print(f"Imported/updated {count} ICD-11 codes")
        return 0
    except FileNotFoundError:
        print(f"ERROR: XML file not found at {args.xml_path}", file=sys.stderr)
        return 1
    except ET.ParseError as e:
        print(f"ERROR: Failed to parse XML: {e}", file=sys.stderr)
        return 2
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
