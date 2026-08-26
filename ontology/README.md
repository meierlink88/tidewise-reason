# Tidewise Graphiti Ontology

`ontology` is the Reason-owned extraction contract for Graphiti. Tidewise Data remains the owner of
all projected Entity and Link facts; these Pydantic models only constrain LLM extraction and expose
the stable fields needed for entity resolution.

## Version

The current catalog is `reasoning-ontology/v3` and contains:

- Entity types: `Country`, `Region`, `Organization`, `Industry`, `Concept`, `IndustryChain`,
  `ChainNode`, `Variable`, `GeopoliticRivalry`, `MacroEconomic`.
- Entity-link types: `CountryInRegion`, `CountryMemberOfOrganization`,
  `CountryImplementsMacroEconomic`, `OrganizationInRegion`,
  `IndustryHasParent`, `IndustryChainMappedToIndustry`, `IndustryChainMappedToConcept`,
  `ChainNodeBelongsToIndustryChain`,
  `ChainNodeInputTo`, `ChainNodeIsComponentOf`, `ChainNodeDependsOn`.

The field and relation semantics are derived from Tidewise Data's versioned `doctype/*.schema`,
Data Context and PostgreSQL relation contracts. Graphiti-protected properties such as `name`,
`summary` and `created_at` are not redeclared. `data_object_id` is optional during extraction and
may only be populated by Data projection or successful canonical entity resolution; an LLM must
never invent it.

`IndustryChain.primary_country_id` is retained only as a canonical Data property. The ontology does
not expose `IndustryChainPrimaryCountry` or an inverse ChainNode containment relation.
`ChainNodeBelongsToIndustryChain` stores only the chain-scoped `contextual_stage` and `position`.
The three directed ChainNode topology links store only their canonical Data edge ID and owning
IndustryChain ID. Review, evidence and provenance fields remain in Tidewise Data and are not
duplicated into Graphiti.

`Variable` is one globally reusable controlled dimension from the Reason-owned versioned catalog.
`allowed_anchor_types` limits where a Variable is meaningful; it never creates Anchor-specific
Variable identities or static Variable-to-Anchor facts. Direction, impact period and the concrete
Anchor belong to a later Signal Fact.

`GeopoliticRivalry` is a stable geopolitical topic blueprint rather than one concrete Event.
`MacroEconomic` is a reusable policy action such as a rate hike or fiscal stimulus; its `category`
is one of ten controlled macro-policy lines and the country name is never encoded into its identity.
`CountryImplementsMacroEconomic` expresses institutional applicability, not a claim that the country
is currently executing the policy. Geopolitical actor and region texts remain reviewed text and do
not establish Country, Region or Organization facts.

All public Pydantic entity/link docstrings and field descriptions are written in Chinese so they can
be reviewed directly and used as clear LLM extraction instructions. Python type names, field names,
enum values and stable business keys remain English for contract compatibility.

Each `ontology/entities/<entity>.py` file owns one Entity model and all relationships for which that
Entity is the source. The file exports its local `ENTITY_TYPES`, `EDGE_TYPES` and `EDGE_TYPE_MAP`;
`ontology/catalog.py` only validates and aggregates those registrations. Relationships remain
independent Graphiti edge models and are never encoded as Entity attributes.

## Graphiti usage

Pass model definitions—not all Entity instances—to Graphiti:

```python
from ontology import EDGE_TYPE_MAP, EDGE_TYPES, ENTITY_TYPES

await graphiti.add_episode(
    name=event_id,
    episode_body=event_json,
    source_description="Published canonical Event from Data Service",
    reference_time=reference_time,
    group_id="neo4j",
    entity_types=ENTITY_TYPES,
    edge_types=EDGE_TYPES,
    edge_type_map=EDGE_TYPE_MAP,
)
```

Canonical Entity and stable Link facts are projected once into the real Neo4j Community `neo4j`
group. Evidence is not projected into Graphiti. Each native `add_episode` call contains only the
current formal Event; foundation and Event adapters may select smaller catalog subsets and must not
copy every graph fact into every Episode.
