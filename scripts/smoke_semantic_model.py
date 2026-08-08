"""Compile the first LinkML model and prove Semantica can ingest its OWL projection."""

from __future__ import annotations

import json
from pathlib import Path

from linkml.generators.owlgen import OwlSchemaGenerator
from linkml.generators.shaclgen import ShaclGenerator
from rdflib import Graph
from semantica.ontology import ingest_ontology


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "semantic-model" / "event.yaml"
DIST_DIR = PROJECT_ROOT / "dist"
EVENT_URI = "https://tidewise.ai/ontology/Event"


def main() -> None:
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    ontology_text = OwlSchemaGenerator(
        str(MODEL_PATH),
        skip_vacuous_local_range_axioms=False,
        skip_vacuous_min_zero_cardinality_axioms=False,
        consolidate_cardinality_axioms=False,
    ).serialize()
    shapes_text = ShaclGenerator(str(MODEL_PATH), closed=True).serialize()

    ontology_path = DIST_DIR / "ontology.ttl"
    shapes_path = DIST_DIR / "shapes.ttl"
    ontology_path.write_text(ontology_text, encoding="utf-8")
    shapes_path.write_text(shapes_text, encoding="utf-8")

    ontology_data = ingest_ontology(ontology_path)
    classes = ontology_data.data.get("classes", [])
    properties = ontology_data.data.get("properties", [])

    if not any(item.get("uri") == EVENT_URI for item in classes):
        raise RuntimeError("Semantica did not ingest the Event class")
    if len(properties) != 4:
        raise RuntimeError(f"Expected 4 Event properties, got {len(properties)}")

    shapes_graph = Graph()
    shapes_graph.parse(data=shapes_text, format="turtle")

    print(
        json.dumps(
            {
                "semantic_model": str(MODEL_PATH.relative_to(PROJECT_ROOT)),
                "ontology_artifact": str(ontology_path.relative_to(PROJECT_ROOT)),
                "shacl_artifact": str(shapes_path.relative_to(PROJECT_ROOT)),
                "semantica_classes": len(classes),
                "semantica_properties": len(properties),
                "shacl_triples": len(shapes_graph),
                "status": "ok",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

