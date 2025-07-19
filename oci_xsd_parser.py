"""
Broadworks OCI XSD Parser
This script parses the Broadworks OCI XSD schema and generates JSON representations
"""

import json
import xml.etree.ElementTree as ET
import sqlite3
from xmlschema import XMLSchema
from lxml import etree

schema = XMLSchema("Rel_2024_10_260_OCISchemaAS/OCISchemaAS.xsd")


def initialize_db(db_path="oci_schema.db"):
    """Initializes the SQLite database and creates necessary tables.
    Args:
        db_path: The path to the SQLite database file.
    Returns:
        A tuple containing the database connection and cursor.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS oci_types (
        name TEXT PRIMARY KEY,
        kind TEXT
    );
    CREATE TABLE IF NOT EXISTS oci_docs (
        name TEXT PRIMARY KEY REFERENCES oci_types(name),
        documentation TEXT
    );
    CREATE TABLE IF NOT EXISTS oci_raw_schema (
        name TEXT PRIMARY KEY REFERENCES oci_types(name),
        xml TEXT
    );
    CREATE TABLE IF NOT EXISTS oci_parameters (
        name TEXT PRIMARY KEY REFERENCES oci_types(name),
        parameters TEXT
    );
    """)
    return conn, cur


def insert_type(cur, name, kind, doc, raw_xml, params):
    """
    Inserts or updates a type in the database.
    Args:
        cur: The database cursor.
        name: The name of the type.
        kind: The kind of the type (e.g., complexType, simpleType).
        doc: Documentation for the type.
        raw_xml: Raw XML representation of the type.
        params: Parameters of the type as a list of dictionaries.
    """
    cur.execute(
        "INSERT OR REPLACE INTO oci_types (name, kind) VALUES (?, ?)", (name, kind)
    )
    if doc:
        cur.execute(
            "INSERT OR REPLACE INTO oci_docs (name, documentation) VALUES (?, ?)",
            (name, doc),
        )
    if raw_xml:
        cur.execute(
            "INSERT OR REPLACE INTO oci_raw_schema (name, xml) VALUES (?, ?)",
            (name, raw_xml),
        )
    cur.execute(
        "INSERT OR REPLACE INTO oci_parameters (name, parameters) VALUES (?, ?)",
        (name, json.dumps(params)),
    )


def get_documentation(xsd_type):
    """
    Extracts documentation from the XSD type's annotation.
    Args:
        xsd_type: The XSD type to extract documentation from.
    Returns:
        A string containing the documentation, or None if not found.
    """
    annotation = xsd_type.elem.find("{http://www.w3.org/2001/XMLSchema}annotation")
    if annotation is not None:
        doc_elem = annotation.find("{http://www.w3.org/2001/XMLSchema}documentation")
        if doc_elem is not None and doc_elem.text:
            return doc_elem.text.strip()
    return None


def get_raw_schema(xsd_type):
    """
    Converts the XSD type element to a string representation.
    Args:
        xsd_type: The XSD type to convert.
    Returns:
        A string containing the raw schema representation.
    """
    if xsd_type.elem is not None:
        try:
            return etree.tostring(xsd_type.elem, pretty_print=True, encoding="unicode")
        except TypeError:
            return ET.tostring(xsd_type.elem, encoding="unicode")
    return None


def build_type_tree(xsd_type, seen=None):
    """
    Recursively builds a tree structure from the XSD type, capturing its
    parameters and documentation.
    Args:
        xsd_type: The XSD type to parse.
        seen: A list to track already processed types to avoid circular references.
    Returns:
        A dictionary representing the type, its parameters, documentation, and raw schema.
    """
    if seen is None:
        seen = []

    if xsd_type in seen:
        return {"type": xsd_type.name, "parameters": [{"$ref": xsd_type.name}]}
    seen.append(id(xsd_type))

    params = []
    if hasattr(xsd_type, "content") and hasattr(xsd_type.content, "__iter__"):
        for e in xsd_type.content:
            if not hasattr(e, "type"):
                continue  # skip non-element content like XsdGroup or XsdChoice
            child = {"name": e.name}
            if hasattr(e, "min_occurs"):
                child["minOccurs"] = e.min_occurs
            if hasattr(e, "max_occurs"):
                child["maxOccurs"] = e.max_occurs

            if hasattr(e.type, "content") and hasattr(e.type.content, "__iter__"):
                child["children"] = build_type_tree(e.type, seen)["parameters"]
            else:
                child["type"] = getattr(e.type, "name", str(e.type))
            params.append(child)
    seen.pop()  # remove the current type from seen
    doc = get_documentation(xsd_type)
    raw_schema = get_raw_schema(xsd_type)
    return {
        "type": xsd_type.name,
        "documentation": doc,
        "parameters": params,
        "raw_schema": raw_schema,
    }


def build_example(parameters):
    """
    Builds an example JSON structure based on the parameters of the XSD type.
    Args:
        parameters: The parameters of the XSD type.
    Returns:
        A dictionary representing an example structure for the parameters.
    """
    print("Building example for parameters:", parameters)
    example = {}
    for param in parameters:
        print("Processing parameter:", param)
        if "children" in param:
            example[param["name"]] = build_example(param["children"])
        else:
            example[param["name"]] = ""
    return example


def main():
    """main logic to parse the XSD schema and populate the database."""
    conn, cur = initialize_db()
    for name, xsd_type in schema.types.items():
        kind = "complexType" if hasattr(xsd_type, "content") else "simpleType"
        doc = get_documentation(xsd_type)
        raw_xml = get_raw_schema(xsd_type)
        params = build_type_tree(xsd_type)["parameters"]
        insert_type(cur, name, kind, doc, raw_xml, params)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
