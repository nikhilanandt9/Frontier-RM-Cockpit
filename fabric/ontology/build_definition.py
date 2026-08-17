from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SPEC_PATH = ROOT / "spec.json"
ID_MAP_PATH = ROOT / "id-map.json"
DEFINITION_PATH = ROOT / "definition"
ID_NAMESPACE = uuid.UUID("f2f09a11-77c7-4ba2-9f02-6250b8cb1bf1")


def stable_integer(name: str) -> str:
    digest = int.from_bytes(hashlib.sha256(name.encode("ascii")).digest()[:8], "big")
    return str(100_000_000_000_000 + digest % 899_900_000_000_000_000)


def stable_uuid(name: str) -> str:
    return str(uuid.uuid5(ID_NAMESPACE, name))


def build_id_map(spec: dict) -> dict:
    entity_types = {}
    bindings = {}
    for entity in spec["entityTypes"]:
        entity_types[entity["name"]] = {
            "id": stable_integer(f"entity:{entity['name']}"),
            "properties": {
                prop["name"]: stable_integer(f"property:{entity['name']}:{prop['name']}")
                for prop in entity["properties"]
            },
        }
        bindings[entity["name"]] = stable_uuid(f"binding:{entity['name']}")

    relationship_types = {
        relationship["name"]: {
            "id": stable_integer(f"relationship:{relationship['name']}"),
            "contextualizationId": stable_uuid(f"contextualization:{relationship['name']}"),
        }
        for relationship in spec["relationshipTypes"]
    }
    return {
        "ontologyName": spec["displayName"],
        "entityTypes": entity_types,
        "relationshipTypes": relationship_types,
        "bindings": bindings,
    }


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="ascii", newline="\n")


def build_tree(spec: dict, id_map: dict, output: Path) -> None:
    write_json(output / ".platform", {"metadata": {"type": "Ontology", "displayName": spec["displayName"]}})
    (output / "definition.json").write_text("{}", encoding="ascii", newline="")

    entities = {entity["name"]: entity for entity in spec["entityTypes"]}
    for entity_name, entity in entities.items():
        entity_ids = id_map["entityTypes"][entity_name]
        properties = [
            {
                "id": entity_ids["properties"][prop["name"]],
                "name": prop["name"],
                "valueType": prop["valueType"],
            }
            for prop in entity["properties"]
        ]
        source_to_id = {
            prop["sourceColumnName"]: entity_ids["properties"][prop["name"]]
            for prop in entity["properties"]
        }
        entity_definition = {
            "id": entity_ids["id"],
            "namespace": "usertypes",
            "name": entity_name,
            "entityIdParts": [source_to_id[entity["keyColumn"]]],
            "displayNamePropertyId": source_to_id[entity["displayNameColumn"]],
            "namespaceType": "Custom",
            "visibility": "Visible",
            "properties": properties,
            "timeseriesProperties": [],
        }
        binding_id = id_map["bindings"][entity_name]
        binding = {
            "id": binding_id,
            "dataBindingConfiguration": {
                "dataBindingType": "NonTimeSeries",
                "propertyBindings": [
                    {
                        "sourceColumnName": prop["sourceColumnName"],
                        "targetPropertyId": entity_ids["properties"][prop["name"]],
                    }
                    for prop in entity["properties"]
                ],
                "sourceTableProperties": {
                    "sourceType": "LakehouseTable",
                    "workspaceId": spec["workspaceId"],
                    "itemId": spec["lakehouseId"],
                    "sourceTableName": entity["sourceTableName"],
                    "sourceSchema": spec["sourceSchema"],
                },
            },
        }
        entity_root = output / "EntityTypes" / entity_ids["id"]
        write_json(entity_root / "definition.json", entity_definition)
        write_json(entity_root / "DataBindings" / f"{binding_id}.json", binding)

    for relationship in spec["relationshipTypes"]:
        relationship_ids = id_map["relationshipTypes"][relationship["name"]]
        source = relationship["sourceEntityType"]
        target = relationship["targetEntityType"]
        source_ids = id_map["entityTypes"][source]
        target_ids = id_map["entityTypes"][target]
        source_key_name = next(
            prop["name"] for prop in entities[source]["properties"]
            if prop["sourceColumnName"] == entities[source]["keyColumn"]
        )
        target_key_name = next(
            prop["name"] for prop in entities[target]["properties"]
            if prop["sourceColumnName"] == entities[target]["keyColumn"]
        )
        relationship_definition = {
            "namespace": "usertypes",
            "id": relationship_ids["id"],
            "name": relationship["name"],
            "namespaceType": "Custom",
            "source": {"entityTypeId": source_ids["id"]},
            "target": {"entityTypeId": target_ids["id"]},
        }
        contextualization_id = relationship_ids["contextualizationId"]
        contextualization = {
            "id": contextualization_id,
            "dataBindingTable": {
                "sourceType": "LakehouseTable",
                "workspaceId": spec["workspaceId"],
                "itemId": spec["lakehouseId"],
                "sourceTableName": relationship["sourceTableName"],
                "sourceSchema": spec["sourceSchema"],
            },
            "sourceKeyRefBindings": [{
                "sourceColumnName": relationship["sourceKeyColumn"],
                "targetPropertyId": source_ids["properties"][source_key_name],
            }],
            "targetKeyRefBindings": [{
                "sourceColumnName": relationship["targetKeyColumn"],
                "targetPropertyId": target_ids["properties"][target_key_name],
            }],
        }
        relationship_root = output / "RelationshipTypes" / relationship_ids["id"]
        write_json(relationship_root / "definition.json", relationship_definition)
        write_json(
            relationship_root / "Contextualizations" / f"{contextualization_id}.json",
            contextualization,
        )


def files_equal(left: Path, right: Path) -> bool:
    left_files = {path.relative_to(left) for path in left.rglob("*") if path.is_file()}
    right_files = {path.relative_to(right) for path in right.rglob("*") if path.is_file()}
    return left_files == right_files and all((left / path).read_bytes() == (right / path).read_bytes() for path in left_files)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the local Frontier RM Ontology definition tree.")
    parser.add_argument("--check", action="store_true", help="Verify the committed ID map and definition tree.")
    args = parser.parse_args()

    spec = json.loads(SPEC_PATH.read_text(encoding="ascii"))
    expected_id_map = build_id_map(spec)
    if args.check:
        actual_id_map = json.loads(ID_MAP_PATH.read_text(encoding="ascii"))
        if actual_id_map != expected_id_map:
            raise SystemExit("Ontology id-map.json is stale")
        with tempfile.TemporaryDirectory() as temporary:
            generated = Path(temporary) / "definition"
            build_tree(spec, actual_id_map, generated)
            if not files_equal(generated, DEFINITION_PATH):
                raise SystemExit("Ontology definition tree is stale")
        print("Ontology ID map and definition tree are current")
        return

    write_json(ID_MAP_PATH, expected_id_map)
    if DEFINITION_PATH.exists():
        shutil.rmtree(DEFINITION_PATH)
    build_tree(spec, expected_id_map, DEFINITION_PATH)
    print(f"Built Ontology definition with {len(spec['entityTypes'])} entities and {len(spec['relationshipTypes'])} relationships")


if __name__ == "__main__":
    main()