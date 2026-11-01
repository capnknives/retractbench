# retractbench

**Can an edit to a language model be fully taken back?**

Model-editing methods (GRACE, WISE, AlphaEdit, LoRA adapters, trained KV caches like Cartridges) let you add or change a fact without retraining. Many of them also claim the edit can be removed. `retractbench` tests that claim directly:

1. Record the base model's answers to a set of probes.
2. Write the edit.
3. Probe: the exact prompt, paraphrases of it, and unrelated prompts.
4. Revoke the edit.
5. Probe again and compare against step 1.

## Metrics

| Metric | Question it answers |
| --- | --- |
| `edit_success` | Does the model give the new answer on the exact prompt? |
| `paraphrase_generalization` | Does it give the new answer on reworded prompts? |
| `locality` | Are answers to unrelated prompts unchanged while the edit is in? |
| `revocation_exact` | After revoking, is every probe's output identical to the base model's? |
| `target_leak_after_revoke` | After revoking, how often does the edited answer still appear where the base model didn't produce it? |
| `apply_ms`, `revoke_ms` | Wall-clock cost of writing and undoing. |

## Scope and limits

Revoking an edit can only undo what the edit added. Nothing here removes knowledge the base model learned in pretraining. The bundled cases use fictional facts so "revoked" has a clean meaning: back to not knowing.

## Quick start

```bash
pip install -e ".[torch,dev]"
pytest                      # harness tests + GRACE mechanics on a tiny random model (CPU)
retractbench run --model meta-llama/Llama-3.2-1B --cases cases/fictional_v0.jsonl
```

Results are written to `results/` as JSON (full outputs for every probe) and a Markdown summary, with the git commit, config and library versions recorded.

## Editors

| Editor | Status |
| --- | --- |
| GRACE-style activation codebook (`retractbench.editors.grace`) | v0, minimal re-implementation; to be checked against EasyEdit |
| WISE | planned |
| LoRA adapter | planned |
| Cartridges | planned |
| RAG baseline | planned |

Any object with `generate`, `apply`, `revoke` and `config` methods works as an editor (see `retractbench/types.py`).

## Status

Early and in progress. See [LOG.md](LOG.md) for the working log, including what failed.
