# Tidewise Graphiti Ontology

`ontology` is the Reason-owned extraction contract for Graphiti. Tidewise Data remains the owner of
all projected Entity and Link facts; these Pydantic models only constrain LLM extraction and expose
the stable fields needed for entity resolution.

## Version

The first catalog is `evidence-curation/v1` and contains:

- Entity types: `Country`, `Region`, `Organization`, `Industry`, `Concept`, `IndustryChain`,
  `ChainNode`.
- Entity-link types: `CountryInRegion`, `CountryMemberOfOrganization`, `OrganizationInRegion`,
  `IndustryHasParent`, `IndustryChainPrimaryCountry`, `IndustryChainContainsNode`,
  `IndustryChainMappedToIndustry`, `IndustryChainMappedToConcept`,
  `ChainNodeInputTo`, `ChainNodeIsComponentOf`, `ChainNodeDependsOn`.

The field and relation semantics are derived from Tidewise Data's versioned `doctype/*.schema`,
Data Context and PostgreSQL relation contracts. Graphiti-protected properties such as `name`,
`summary` and `created_at` are not redeclared. `data_object_id` is optional during extraction and
may only be populated by Data projection or successful canonical entity resolution; an LLM must
never invent it.

Each `ontology/entities/<entity>.py` file owns one Entity model and all relationships for which that
Entity is the source. The file exports its local `ENTITY_TYPES`, `EDGE_TYPES` and `EDGE_TYPE_MAP`;
`ontology/catalog.py` only validates and aggregates those registrations. Relationships remain
independent Graphiti edge models and are never encoded as Entity attributes.

## Graphiti usage

Pass model definitions—not all Entity instances—to Graphiti:

```python
from ontology import EDGE_TYPE_MAP, EDGE_TYPES, ENTITY_TYPES

await graphiti.add_episode(
    name=evidence_id,
    episode_body=evidence_json,
    source_description="Tidewise Atomic Evidence",
    reference_time=reference_time,
    group_id="evidence-curation",
    entity_types=ENTITY_TYPES,
    edge_types=EDGE_TYPES,
    edge_type_map=EDGE_TYPE_MAP,
)
```

Canonical Entity and stable Link facts are projected once into the target `group_id`. Each Evidence
call contains only the current Evidence Episode. Future foundation, Evidence and Event adapters may
select smaller catalog subsets; they must not copy every graph fact into every Episode.
