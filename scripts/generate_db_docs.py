"""
Generate Database Schema Documentation
=======================================

This script generates comprehensive documentation for the KeneyApp database schema,
including tables, columns, relationships, and indexes.

Usage:
    python scripts/generate_db_docs.py > docs/database/schema.md
"""

import os
import sys
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import inspect, MetaData
from sqlalchemy.engine import create_engine
from app.core.database import Base
from app.core.config import settings


def generate_table_documentation(inspector, table_name: str) -> str:
    """Generate markdown documentation for a single table."""
    doc = f"\n### {table_name}\n\n"

    # Get table comment if exists
    try:
        comment = inspector.get_table_comment(table_name)
        if comment and comment.get('text'):
            doc += f"_{comment['text']}_\n\n"
    except:
        pass

    # Columns
    columns = inspector.get_columns(table_name)
    doc += "#### Columns\n\n"
    doc += "| Column | Type | Nullable | Default | Description |\n"
    doc += "|--------|------|----------|---------|-------------|\n"

    for col in columns:
        name = col['name']
        col_type = str(col['type'])
        nullable = "Yes" if col['nullable'] else "No"
        default = str(col['default']) if col['default'] else "-"
        comment = col.get('comment', '')

        doc += f"| `{name}` | {col_type} | {nullable} | {default} | {comment} |\n"

    doc += "\n"

    # Primary Key
    pk = inspector.get_pk_constraint(table_name)
    if pk and pk['constrained_columns']:
        doc += "#### Primary Key\n\n"
        doc += f"- **Columns**: {', '.join(f'`{col}`' for col in pk['constrained_columns'])}\n\n"

    # Foreign Keys
    fks = inspector.get_foreign_keys(table_name)
    if fks:
        doc += "#### Foreign Keys\n\n"
        for fk in fks:
            referred_table = fk['referred_table']
            constrained_cols = ', '.join(f'`{col}`' for col in fk['constrained_columns'])
            referred_cols = ', '.join(f'`{col}`' for col in fk['referred_columns'])
            doc += f"- **{fk.get('name', 'FK')}**: {constrained_cols} → `{referred_table}`({referred_cols})\n"
        doc += "\n"

    # Indexes
    indexes = inspector.get_indexes(table_name)
    if indexes:
        doc += "#### Indexes\n\n"
        doc += "| Index Name | Columns | Unique |\n"
        doc += "|------------|---------|--------|\n"
        for idx in indexes:
            name = idx['name']
            cols = ', '.join(f'`{col}`' for col in idx['column_names'])
            unique = "Yes" if idx['unique'] else "No"
            doc += f"| {name} | {cols} | {unique} |\n"
        doc += "\n"

    return doc


def main():
    """Generate complete database schema documentation."""
    # Connect to database
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)

    # Header
    print("# KeneyApp Database Schema Documentation")
    print("\n**Auto-generated from database schema**\n")
    print(f"Database: {settings.DATABASE_URL.split('@')[-1]}\n")
    print("---\n")

    # Table of Contents
    table_names = sorted(inspector.get_table_names())
    print("## Table of Contents\n")
    for table in table_names:
        print(f"- [{table}](#{table.lower().replace('_', '-')})")
    print("\n---\n")

    # Generate documentation for each table
    print("## Tables\n")
    for table_name in table_names:
        try:
            print(generate_table_documentation(inspector, table_name))
        except Exception as e:
            print(f"\n⚠️ Error documenting table {table_name}: {e}\n")

    # Entity Relationship Summary
    print("\n---\n")
    print("## Entity Relationships\n")
    print("```")
    print("users → appointments (created_by_id)")
    print("users → patients (created_by)")
    print("users → messages (sender_id, receiver_id)")
    print("patients → appointments (patient_id)")
    print("patients → medical_documents (patient_id)")
    print("patients → prescriptions (patient_id)")
    print("patients → lab_tests (patient_id)")
    print("patients → medical_record_shares (patient_id)")
    print("tenants → users (tenant_id)")
    print("tenants → patients (tenant_id)")
    print("messages → messages (reply_to_id, thread_id)")
    print("```")

    # Statistics
    print("\n## Database Statistics\n")
    print(f"- **Total Tables**: {len(table_names)}")

    total_columns = sum(len(inspector.get_columns(t)) for t in table_names)
    print(f"- **Total Columns**: {total_columns}")

    total_indexes = sum(len(inspector.get_indexes(t)) for t in table_names)
    print(f"- **Total Indexes**: {total_indexes}")

    total_fks = sum(len(inspector.get_foreign_keys(t)) for t in table_names)
    print(f"- **Total Foreign Keys**: {total_fks}")

    print("\n---\n")
    print("*Documentation generated automatically - do not edit manually*\n")


if __name__ == "__main__":
    main()
