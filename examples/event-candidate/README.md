# Event Candidate Agent Scenario

The first proposed public seam is a CLI scenario:

```text
semantica-runtime run-event-scenario --text <source-supported statement>
```

The scenario will:

1. load the published Event Concept Card through the Semantic Runtime;
2. assemble task-scoped Agent context;
3. ask a replaceable model adapter for a strict Event Candidate;
4. validate the candidate against the active semantic release;
5. return the candidate plus semantic release and evidence references.

The first tracer case will use this input:

```text
宁德时代于2026年8月8日宣布其福建基地新增一条动力电池生产线。
```

Expected observable behavior:

- the output is typed as `EventCandidate`, not a formal `Event`;
- `title` and `factual_summary` are non-empty and factual;
- `occurred_at` is `2026-08-08` with explicit timezone/precision semantics to be fixed;
- the response identifies the Event Concept Card and Semantic Model release used;
- model output that violates the concept constraints is rejected.

No behavior test or implementation is added until this public seam is confirmed.

