# references/snippets — canonical render/assert code

> **What this is**: data files, not a library — copy/adapt into your own per-job build script.
> Same register as `references/formats/README.md` and `references/wiki/README.md`. Each `.py`
> file here is a single-purpose reference implementation of a mechanism a card or agent
> currently re-derives from prose on every job (the render recipe, the OOXML zip-integrity
> checks, the pptx shape assertion, the G7 engine-version-drift check). Every file is runnable
> standalone (`if __name__ == "__main__":` self-check) and stdlib-safe to import — an optional
> library (`pptx`/`pypdf`) is only required when you actually *call* the function that needs it,
> never at module import time.

## How cards/agents point here

A card or agent that names one of these mechanisms adds one line after the recipe/check it
motivates:

```
Canonical implementation: `references/snippets/<file>.py::<function>`.
```

The recipe/trap *prose* stays in the card — the snippet is only the executable pattern. The
pointer names the exact function so a reader (or `doc-builder`/`doc-verifier`) copies the
tested code instead of re-deriving it from memory.

## Non-goal

`doc-builder` and `doc-verifier` **copy these into their own per-job script**
(e.g. `.omd/<slug>/assert_shapes.py`); they do **not** `import` this package at runtime. This
is the "rebuild, don't wrap" rule — no `lib/` framework, no `pip install -e`. The only code that
imports these files directly is this repo's own `tests/test_snippets_*.py` suite.
