"""
Broadworks OCI XSD Parser
This script parses the Broadworks OCI XSD schema and generates JSON representations
"""
import json
import xml.etree.ElementTree as ET
from xmlschema import XMLSchema
from lxml import etree


schema = XMLSchema("OCISchemaAS.xsd")

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
            return etree.tostring(
                xsd_type.elem, pretty_print=True, encoding="unicode"
            )
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

if __name__ == "__main__":
    for name in schema.types:
        if "Request" in name or "Response" in name:
            print(name)
            result = build_type_tree(schema.types.get(name))
            with open(f"output/{name}.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
    # command = 'UserModifyRequest22'
    # result = build_type_tree(schema.types.get(command))
    # example = build_example(result["parameters"])
    # print(f"Example for {command}:")
    # print(json.dumps(example, indent=2, ensure_ascii=False))
