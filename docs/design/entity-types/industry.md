# Industry EntityType Review

> Status: reviewed and published to the local OpenSPG evaluation project through a targeted Schema
> API update.

## Boundary

`Industry` is a stable category of economic activity defined by the products or services supplied.
It may contain multiple companies and product categories. Market sectors, research concepts,
industry chains and individual companies or products are excluded.

## Domain properties

| OpenSPG field | Domain meaning |
| --- | --- |
| built-in `id` | Stable identity of the Industry. |
| built-in `name` | Canonical Industry name. |
| built-in `description` | Concise description used to understand and retrieve the Industry. |
| `aliases` | Other names that identify the same Industry. |
| `industryCode` | Stable code in the canonical Tidewise Industry ontology. |
| `definition` | Economic activities, products and services covered by the Industry. |
| `boundaryNote` | Inclusion, exclusion and adjacent-Industry boundaries. |

## Hierarchy

`Industry --parentIndustry--> Industry` expresses the canonical direct-parent relationship. A root
Industry has no parent. Classification level and hierarchy path are derived from this relation and
are not duplicated as properties.

Classification system and version describe an ontology release as a whole. They are not repeated
on every Industry entity.

## Non-goals

- No external classification-system projection.
- No duplicated classification level or hierarchy path.
- No static relation between Industry and Country.
- No ABox instances or automatic OpenSPG submission.
