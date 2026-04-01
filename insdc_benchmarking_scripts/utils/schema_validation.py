import json
from jsonschema import validate


def load_schema(schema_path: str):
    with open(schema_path, "r") as f:
        return json.load(f)


def validate_result(result: dict, schema_path: str):
    schema = load_schema(schema_path)
    validate(instance=result, schema=schema)
