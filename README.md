# retractbench

**Can an edit to a language model be fully taken back?**

Model-editing methods (GRACE, WISE, ROME/MEMIT, LoRA adapters, trained KV caches like Cartridges) let you add or change a fact without retraining. Many of them also claim, or are assumed, to be reversible. `retractbench` tests that claim directly, with the same protocol for every method:

1. Record the base model's answers to a set of probes.
2. Write the edit.
3. Probe: the exact prompt, paraphrases, unrelated prompts, and *hard negatives* (same kind of question, different subject).
4. Revoke the edit.
5. Probe again and compare against step 1.

## Metrics

| Metric | Question it answers |
| --- | --- |
| `edit_success` | Does the output on the exact prompt *start with* the new target (word boundary required: "OMEGA-999" does not count for "OMEGA-99")? |
| `edit_success_loose` | Plain substring match, kept for comparison. |
| `paraphrase_generalization` | Is the target newly mentioned in answers to reworded prompts? |
| `locality` | Are answers to unrelated prompts unchanged while the edit is in? |
| `locality_hard` | Are answers to hard negatives unchanged while the edit is in? |
| `revocation_exact` | After revoking, is every probe's output identical to the base model's? |
| `target_leak_after_revoke` | After revoking, how often is the edited target mentioned where the base model didn't mention it? |
| `apply_ms`, `revoke_ms` | Wall-clock cost of writing and undoing. |

For distance-keyed editors, `retractbench separability` measures, without training anything, whether *any* threshold can separate paraphrases from hard negatives (AUC, and paraphrase recall at a fixed hard-negative trigger rate).

## Scope and limits

Revoking an edit can only undo what the edit added. Nothing here removes knowledge the base model learned in pretraining; that is the subject of *unlearning* benchmarks (see Related work). The fictional cases use invented facts, so "revoked" means back to not knowing. The CounterFact cases rewrite real facts, so there "revoked" means back to the original answer.

## Quick start

```bash
pip install -e ".[torch,dev]"
pytest   # harness tests (no torch needed) + GRACE mechanics on a tiny random model (CPU)

retractbench run --model Qwen/Qwen2.5-1.5B --cases cases/fictional_v0.jsonl
retractbench separability --model Qwen/Qwen2.5-1.5B --cases cases/counterfact_100_seed0.jsonl \
    --key-position subject --key-space raw
python scripts/run_matched.py --cases cases/counterfact_100_seed0.jsonl --tag cf100
```

Results go to `results/` as JSON (full outputs for every probe) and a Markdown summary, with the git commit, config and library versions recorded.

## Cases

| File | What |
| --- | --- |
| `cases/fictional_v0.jsonl` | 5 hand-written fictional facts, each with 3 paraphrases, 3 unrelated prompts and 3 hard negatives. |
| `cases/counterfact_100_seed0.jsonl` | 100 records sampled from CounterFact (Meng et al., 2022) with a fixed seed; 2 paraphrases, 5 neighborhood prompts as hard negatives, 3 prompts from other relations as unrelated. Rebuild with `scripts/make_counterfact_cases.py`. |

## Editors

| Editor | Status |
| --- | --- |
| GRACE-style activation codebook (`retractbench.editors.grace`) | Minimal re-implementation. Options: `key_position` = `last` (original GRACE) or `subject`; `key_space` = `raw` or `standardized`. To be checked against EasyEdit's GRACE. |
| ROME-style rank-one weight edit (`retractbench.editors.rome`) | Simplified ROME (crude covariance from calibration sentences). Undo modes: `restore` (saved copy), `subtract` (remove the update), `inverse` (counter-edit to the base model's tokens or, with `inverse_target="true"`, to the true object). |
| SVD-truncation reversal (Youssef et al., ICLR 2026) | Undo mode `svd` (drop the top-q singular components); q chosen on a held-out dev set (`scripts/sweep_svd_q.py`). |
| Genuine ROME edits from the authors' EasyEdit (`editors/precomputed.py`) | Made by the EasyEdit in [trace-and-reverse](https://github.com/paulyoussef/trace-and-reverse) in its own environment (`scripts/easyedit_rome_export.py`), replayed here with undo modes `restore`, `subtract`, `svd`. |
| WISE | planned |
| LoRA adapter | planned |
| Cartridges | planned |
| RAG baseline | planned |

Any object with `generate`, `apply`, `revoke` and `config` methods works as an editor (see `src/retractbench/types.py`).

## Related work

retractbench is not the first work to ask whether model edits can be undone. Its aim is to make that question **standard and cross-method**: one protocol, the same probes and the same strict metrics, applied to editing methods that live in very different places (activation codebooks, weight edits, adapters, trained KV caches, retrieval).

**Reversing knowledge edits**
- Youssef, Zhao, Seifert & Schlötterer, *Tracing and Reversing Edits in LLMs*, ICLR 2026. Traces and reverses rank-one weight edits (ROME, r-ROME) from the edited weights alone, without the original model; Qwen2.5-7B was the hardest model to reverse (62.9% reversal accuracy, scored on the next token only). [arXiv:2505.20819](https://arxiv.org/abs/2505.20819), [code](https://github.com/paulyoussef/trace-and-reverse)
- Jiang et al., *Selective Knowledge Edit Reversal via Gated Singular Vector Shrinkage*, 2026. Reverses selected weight edits while keeping others. [arXiv:2609.02091](https://arxiv.org/abs/2609.02091)
- Luo et al., *Reversible Lifelong Model Editing via Semantic Routing-Based LoRA* (SoLA), 2026. One adapter per edit, undone by deleting its routing key. [arXiv:2603.11239](https://arxiv.org/abs/2603.11239)
- Caddeo, Sanguinetti & Atzori, *On Reversibility as Language Model Behavioral Property in Parametric Knowledge Editing*, Applied Sciences 16(13), 2026. Edit-then-revert cycles with ROME and MEMIT on CounterFact (GPT-2 XL, GPT-J), with revert as an inverse edit; measures efficacy, paraphrase, neighborhood and perplexity after reverting. [doi:10.3390/app16136567](https://doi.org/10.3390/app16136567)
- *How to Make LLMs Forget: On Reversing In-Context Knowledge Edits*, NAACL 2025. Detects and reverses prompt-based (in-context) edits. [arXiv:2410.12586](https://arxiv.org/abs/2410.12586)

**Knowledge-editing benchmarks and methods**
- CounterFact and ROME: Meng et al., *Locating and Editing Factual Associations in GPT* (NeurIPS 2022).
- GRACE: Hartvigsen et al., *Aging with GRACE* (NeurIPS 2023). WISE: Wang et al. (NeurIPS 2024).
- EasyEdit (zjunlp) and UniEdit (NeurIPS 2025 Datasets & Benchmarks) for broad editing evaluation.

**Unlearning benchmarks** (removing knowledge learned in training, a different problem)
- OpenUnlearning: Dorna et al., NeurIPS 2025 Datasets & Benchmarks. Unifies 13 unlearning methods and 16 evaluations across TOFU, MUSE and WMDP.
- *Unlearning or Obfuscating? Jogging the Memory of Unlearned LLMs via Benign Relearning* (2024): unlearned knowledge can return after light fine-tuning. [arXiv:2406.13356](https://arxiv.org/abs/2406.13356)
- Goel, Ritter & Gurevych, *Auditing Language Model Unlearning via Information Decomposition*, 2026: "forgotten" data stays linearly decodable from hidden states. [arXiv:2601.15111](https://arxiv.org/abs/2601.15111)
- Yoon, Jun & No, *Position: The Term "Machine Unlearning" Is Overused in LLMs*, ICML 2026: papers should name their guarantee and reference model. [PMLR](https://proceedings.mlr.press/v306/yoon26g.html)

**How retractbench differs from the reversal papers above**
- **Cross-method.** Each of those studies one family of editors; retractbench runs the same protocol over any editor.
- **Strict return-to-base.** Revocation is judged by exact output equality with the unedited model on every probe, plus a separate leak check, not only by efficacy on the original prompt.
- **Hard negatives as a first-class metric.** Look-alike questions about other subjects are reported separately from easy unrelated prompts, because that's where distance-keyed edits fail (see LOG.md, 2026-11-01).

- **Return-to-model, not return-to-fact.** Most reversal work counts an undo as successful when the original fact comes back. retractbench asks whether the original *model* comes back. On our ROME-style runs these diverge sharply: a counter-edit to the true object restores the fact on 99% of prompts but leaves only 1% identical to the base model (LOG.md, 2026-11-01).

## Roadmap

| When | What |
| --- | --- |
| Nov 2–8, 2026 | ICLR SVD reversal on genuine ROME edits from the authors' code (dev sweep done, reproduces their first-token numbers; 100-case scoring running); distributional undo test (built, cross-checked against Gao et al.'s package); second leak count for real-world facts |
| Nov 9–15, 2026 | Short public write-up of the return-to-fact vs return-to-model result (then arXiv). If the ICLR code won't run, publish without it and note it |
| After the write-up | Contact the reversal-paper authors |
| Dec 2026 – Jan 2027 | Hidden-state probe after undo; relearning test; multi-hop/ripple leak probes; a 7B model; deliberate drift experiment |
| Feb 2027 (month 3) | Decide: keep standalone or contribute a revocation evaluator to EasyEdit; first conversations to test demand for verification |

## Status

Early and in progress. See [LOG.md](LOG.md) for the working log, including what failed.

## License

MIT
