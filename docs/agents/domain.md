# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root — the project glossary. Terms there are canonical; `_Avoid_` entries are synonyms to not use.
- **`docs/adr/`** — read the ADRs that touch the area you're about to work in. There are four, and they are short:
  - `0001` 俯视 2D + 光照遮蔽作为一等机制
  - `0002` Godot 4 + GDScript
  - `0003` 永不做战斗
  - `0004` 三幕 + 强制回程
- **`docs/design/game-design.md`** — the narrative and structural blueprint (acts, beats, endings, content budget).

There is no `CONTEXT-MAP.md`; this repo is **single-context**.

If any of these files are missing, proceed silently — don't flag their absence.

## Layout

```
/
├── AGENTS.md
├── CONTEXT.md              ← glossary
├── docs/
│   ├── adr/                ← hard decisions
│   ├── agents/             ← this config
│   ├── design/             ← story + structure
│   └── research/           ← reverse-engineering notes, provenance
├── levels/act1.json        ← level data (rooms, doors, lights, items, triggers)
├── scripts/                ← Godot / GDScript
└── assets/                 ← generated art, audio, fonts
```

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a test name, a refactor proposal), use the term as defined in `CONTEXT.md`. Examples: use **承重系统**, not "核心玩法"; use **回程**, not "原路返回"; use **可归因死亡**, not "公平".

If the concept you need isn't in the glossary yet, that's a signal: either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0003 (永不做战斗), but worth reopening because…_
