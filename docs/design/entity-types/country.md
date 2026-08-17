# Country EntityType Review

> Status: accepted for the local OpenSPG evaluation projection.

## Boundary

`Country` represents a state-level entity with a stable national identity and governance boundary
that is analyzed as a macroeconomic, trade, legal, policy or international-relations subject.

Regions, cities, cross-country economic areas, alliance organizations, government departments,
central banks, regulators, markets, companies and purely geographic mentions are excluded.

## Source-model divergence

The current Tidewise source TBox uses the broader `Economy` type for countries, regions and
cross-country economic areas. A future ABox import must select only country-level records or first
version the authoritative source TBox; this Schema does not reclassify source facts automatically.

## Domain properties

| OpenSPG field | Domain meaning |
| --- | --- |
| built-in `id` | Stable identity of the country. |
| built-in `name` | Canonical country name. |
| built-in `description` | Concise description used to understand and retrieve the country. |
| `aliases` | Other names that identify the same country. |
| `countryCode` | Governed country code. |
| `currencyCode` | Main legal-tender currency code. |
| `region` | Geographic and macro-analysis region. |

Database join keys, source discriminators, persistence status and timestamps are implementation
details and are not projected into this domain Schema.

## Relations

`Country --memberOf--> AllianceOrganization` means that the country is a formal member of the
target alliance organization and participates under its charter, rules or governance mechanism.
A country may have multiple `memberOf` relations. The inverse relation is not duplicated on
`AllianceOrganization`.

## Non-goals

- No ABox instances.
- No geographic hierarchy.
- No source-fact reclassification.
- No database join keys, source type fields, persistence status or timestamps.
