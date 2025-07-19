"""
This module provides storage modules for Broadworks OCI Schema types.
"""
import sqlite3
import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLiteOCITypeStore:
    """
    Provides an interface for storing and retrieving Broadworks OCI types in a SQLite database.
    """
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "oci_schema.db")
        self.conn = sqlite3.connect(db_path)
        self.cur = self.conn.cursor()

    def close(self):
        """
        Closes the database connection.
        """
        self.conn.close()

    def types(self, kind=None, filter=None):
        """
        Retrieves a list of OCI types from the database, optionally filtered by kind and name.
        Args:
            kind: The kind of OCI type to filter by (e.g., complexType, simpleType).
            filter: A string to filter the type names.
        Returns:
            A list of type names that match the criteria.
        """
        query = "SELECT name FROM oci_types"
        conditions = []
        params = []
        if kind:
            conditions.append("kind = ?")
            params.append(kind)
        if filter:
            conditions.append("name LIKE ?")
            params.append(f"%{filter}%")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY name"
        logger.debug("Executing query: %s with params: %s", query, params)
        return [r[0] for r in self.cur.execute(query, params)]

    def doc(self, name):
        """
        Retrieves the documentation for a given OCI type.
        Args:
            name: The name of the OCI type.
        Returns:
            The documentation string for the type, or None if not found.
        """
        self.cur.execute("SELECT documentation FROM oci_docs WHERE name = ?", (name,))
        row = self.cur.fetchone()
        return row[0] if row else None

    def parameters(self, name):
        """
        Retrieves the parameters for a given OCI type.
        Args:
            name: The name of the OCI type.
        Returns:
            A list of parameters as dictionaries, or None if not found.
        """
        self.cur.execute("SELECT parameters FROM oci_parameters WHERE name = ?", (name,))
        row = self.cur.fetchone()
        return json.loads(row[0]) if row else None

    def schema(self, name):
        """
        Retrieves the XML schema for a given OCI type.
        Args:
            name: The name of the OCI type.
        Returns:
            The XML schema string for the type, or None if not found.
        """
        self.cur.execute("SELECT xml FROM oci_raw_schema WHERE name = ?", (name,))
        row = self.cur.fetchone()
        return row[0] if row else None

    def example(self, name):
        """
        Retrieves an example oci json parameter for a given OCI type.
        Args:
            name: The name of the OCI type.
        Returns:
            The example JSON string for the type, or None if not found.
        
        Assumptions:
          - This assumes that the parameters will remain in order
            - This works in python, but did not work in perl
          - We may work around this by reordering the parameters on request
        """
        logger.debug("Generating example for type: %s", name)
        parameters = self.parameters(name)
        def walk_parameters(parameters):
            """
            Recursively walks through parameters to build an example.
            Args:
                parameters: A list of parameter dictionaries.
            Returns:
                A dictionary representing the example structure.
            """
            example = {}
            for param in parameters:
                if "children" in param:
                    example[param["name"]] = walk_parameters(param["children"])
                else:
                    if 'minOccurs' in param and param['minOccurs'] == 0:
                        example[param["name"]] = None
                    else:
                        example[param["name"]] = ""
            return example
        return walk_parameters(parameters)