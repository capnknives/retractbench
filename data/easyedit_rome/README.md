# EasyEdit ROME edits behind the write-up

Each file holds the rank-one updates that the authors' EasyEdit ROME code (bundled in
github.com/paulyoussef/trace-and-reverse) made for one case file, as the two vectors
whose outer product ROME adds to `model.layers.5.mlp.down_proj.weight`, plus the
export's metadata. They are the inputs to every `--deltas` run in `results/`, so the
scoring can be rerun without the authors' pinned environment (torch 2.0.1,
transformers 4.46.2).

Load them with `retractbench.editors.precomputed.load_easyedit_updates`, which uses
`torch.load(..., weights_only=True)`. Note that it builds the full update matrices: about
40 MB per edit on Qwen2.5-1.5B and 270 MB per edit on Qwen2.5-7B, so the 7B test file
needs about 27 GB of memory. To inspect a 7B file on a small machine, load it the same
way and read `blob["cases"][id]["left"]` and `["right"]` instead.

| File | Model | Cases | Bytes | SHA256 |
| --- | --- | --- | --- | --- |
| `cf100.pt` | Qwen/Qwen2.5-1.5B | `cases/counterfact_100_seed0.jsonl` (100) | 4,246,621 | `d1783b053e98ae94e42d9b1afbb53ca8c0f803d48616c99f4f3abaf32e899444` |
| `dev20.pt` | Qwen/Qwen2.5-1.5B | `cases/counterfact_dev20_seed1.jsonl` (20) | 851,225 | `7024aded9ec1c8a5f4f9101be8b5b31b140cbb4e31b822d073787cb996a55dae` |
| `cf100_7b.pt` | Qwen/Qwen2.5-7B | `cases/counterfact_100_seed0.jsonl` (100) | 9,073,369 | `374eed5900508a707c833a8f189a946d66a1749651d6229604889848f0802683` |
| `dev20_7b.pt` | Qwen/Qwen2.5-7B | `cases/counterfact_dev20_seed1.jsonl` (20) | 1,816,533 | `89d6adbcd396284c5c56859d49bdfee0bda096f8414dcd317eb4319fb0fcef4f` |

How they were made (LOG.md has the dated entries):

- 1.5B, on the local RTX 3070, 2026-11-02, in the authors' venv:
  `scripts/easyedit_rome_export.py --cases cases/<file> --tag cf100|dev20 --hparams configs/easyedit_rome_qwen2.5-1.5b.yaml`
- 7B, on a Modal A100 80 GB, 2026-11-03, with the authors' unchanged config:
  `modal run scripts/modal_app.py --step export --tag cf100_7b|dev20_7b --cases cases/<file>`
  (copied from the Modal volume `retractbench-vol`, `data/easyedit_rome/`, on 2026-11-03).
- Both used the authors' code at trace-and-reverse commit `d783bc1` (2026-04-15). That
  commit was not recorded in the files at export time. The local checkout was cloned at
  `d783bc1` on 2026-11-02 at 07:22, before any export, its reflog shows no later checkout,
  and it has no changes to tracked files; the 7B exports uploaded that same checkout.
  Exports from now on record it (`meta["trace_and_reverse_commit"]`).

Checked on 2026-11-03: each file has the expected weight name, shape and case count. The
7B files were copied from the same volume path the 7B runs read them from. For both test
files, the norm of every stored update agrees with the `edit_fro` logged by the matching
restore run (`results/20261102T183353Z_..._editorlog.json` and
`results/20261103T185042Z_..._7b_..._editorlog.json`) to within 0.09% on 1.5B and 0.4% on
7B. That is within the accuracy of a float32 norm over the full matrix: on 7B it
underestimates the exact (float64) norm by up to 0.8%, and the result depends on the
order of summation (the 7B runs computed it on a GPU, this check on a CPU). So the logged
`edit_fro` values carry that bias too. This check shows the files are consistent with the
runs; it is not a bit-level proof that they are the same files, since no run recorded a
hash of its edit file. Runs from now on do (`meta["provenance"]["inputs_sha256"]`).
