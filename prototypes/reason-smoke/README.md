# Reason Smoke Prototype

> **PROTOTYPE — disposable local data.** This directory validates one execution principle against the
> currently running local `reason-server`; it is not a production Tidewise model.

The prototype creates or reuses a private local OpenSPG project named `ReasonSmoke`, commits a
three-type Schema, writes three synthetic nodes and two relations, and runs two natural-language
queries through the KAG static Solver with the existing `DeepSeek V4 Flash` model.

```text
示例电缆公司 --produces--> 电力电缆 --usesMaterial--> 铜
```

Run the observable acceptance seam with one command:

```bash
./prototypes/reason-smoke/verify.sh
```

The command reads the existing `DeepSeek V4 Flash` and embedding settings from the local OpenSPG
metadata database and reuses OpenSPG's normal project configuration mechanism. It also creates a
protected temporary KAG runtime file inside `reason-server` and removes that file on exit.
Credentials are not written to this repository or printed. This is intentionally local evaluation
behavior, not a production credential design.

Expected behavior:

- the positive question returns `铜` and the two-hop path;
- the negative question about `铝` states that the graph has no evidence;
- the KAG trace contains both graph facts and the positive answer adds no unsupported materials;
- repeated runs upsert the same synthetic IDs instead of creating duplicates.

The scratch OpenSPG project persists so it can be inspected in the local UI. Its namespace is
`ReasonSmoke`; shared middleware and the existing `Tidewise` project are not provisioned, restarted,
or modified by the prototype.
