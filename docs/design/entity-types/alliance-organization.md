# AllianceOrganization EntityType Review

> Status: review candidate. Not merged into the complete project Schema and not submitted to
> OpenSPG.

## Boundary

`AllianceOrganization` uses a WTO-like organizational boundary: independent countries, economies,
institutions or other formal members establish a persistent organization under a treaty, charter or
institutional rules. The organization must have a stable identity, an explicit membership boundary,
ongoing governance or decision-making and standing functions.

Initiatives, agreements, free-trade arrangements, summits, temporary forums, non-institutionalized
cooperation mechanisms and one-off partnerships are excluded even when multiple countries
participate in them.

## Source-model divergence

PostgreSQL `alliance_org@1` currently has a broader definition and classifies 45 active records under
the type. Some records, including the Belt and Road Initiative, RCEP, USMCA and the China-Central
Asia Summit, do not satisfy the narrower organizational boundary. Before importing ABox data, the
authoritative Tidewise TBox must be versioned and those records must be reviewed for reclassification;
this OpenSPG fragment does not silently redefine existing PostgreSQL facts.

## Domain projection

| OpenSPG field | Domain meaning |
| --- | --- |
| built-in `id` | Stable identity of the alliance organization. |
| built-in `name` | Canonical organization name. |
| built-in `description` | Concise description used to understand and retrieve the organization. |
| `aliases` | Other names that identify the same organization. |
| `abbreviation` | Governed abbreviation used by the organization. |
| `leadershipSummary` | Main founders, core members, leadership bodies or governance leadership. |
| `influenceScopeSummary` | Geographic, functional and governance scope of the organization. |

Database join keys, source discriminators, storage-layer lifecycle state and timestamps belong to
the ingestion adapter or source system. They are not properties of the alliance organization domain
object and therefore are not projected into this Schema.

The current PostgreSQL snapshot contains 45 active records classified as `alliance_org@1`. All 45
have non-empty aliases, abbreviation, leadership summary and influence-scope summary; `name`
currently equals `canonical_name` for every row. Property completeness does not imply that every
record satisfies the revised organizational boundary.

## Relations

The current formal edge is `Economy --member_of--> AllianceOrganization` (133 active instances).
OpenSPG relations are declared on their source type, so `memberOf` belongs in the future `Economy`
review fragment. Its target records must pass the same reclassification review. This fragment does
not invent an inverse `memberEconomy` relation.

## Non-goals

- No ABox instances.
- No synthetic organization hierarchy.
- No database join keys, source type fields, persistence status or timestamps.
- No automatic OpenSPG submission.
