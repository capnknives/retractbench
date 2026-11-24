# Runbook: the paper's own relations, Qwen2.5-7B (62 edits)

Plan and predictions: LOG.md, "2026-11-23: plan and predictions, the paper's own relations". Nothing here has
been run. Windows PC, PowerShell. Project `D:\retractbench`, Modal client `D:\modal-venv`. Rules from CLAUDE.md:
always `modal run --detach`, wait about 20 seconds between launches, keep files off C:, never hand-edit `results/`.

A note on "builds from the git commit": `scripts/modal_app.py` uploads the working tree (`src`, `scripts`, `cases`,
`configs`), not a commit. The commit is only recorded in each result file (`meta.provenance`, with `-dirty` if tracked
files changed). So commit and push the case file first: an untracked file would still be uploaded, but the
provenance would not say which commit it came from.

## 0. Check the Modal credit first

Open https://modal.com/settings (Usage and Billing) and note the remaining free credit and this month's spend.
The CLI has no credit command that this runbook relies on. Note the numbers again at the end (see "What to send back").

## 1. Pull

```powershell
cd D:\retractbench
git checkout main
git pull
git status --short          # must print nothing
.\.venv\Scripts\python.exe -m pytest -q
```

## 2. The case file (skip if `cases\counterfact_rel31x2.jsonl` is already in the repo)

```powershell
$env:HF_HOME = "D:\hf-cache"
.\.venv\Scripts\python.exe scripts\make_counterfact_cases.py --per-relation 2 --name counterfact_rel31x2
(Get-Content cases\counterfact_rel31x2.jsonl | Where-Object { $_ -notmatch '^#' }).Count    # expect 62
.\.venv\Scripts\python.exe -c "import json; rows=[json.loads(l) for l in open('cases/counterfact_rel31x2.jsonl', encoding='utf-8') if l.strip() and not l.startswith('#')]; print(len(rows), len({r['relation_id'] for r in rows}))"   # expect 62 31
```

Check for overlap with the two earlier case files. Report any overlap; do not remove it, the point is to match the
paper's records:

```powershell
.\.venv\Scripts\python.exe -c "import json; ids=lambda f: {json.loads(l)['id'] for l in open(f, encoding='utf-8') if l.strip() and not l.startswith('#')}; n=ids('cases/counterfact_rel31x2.jsonl'); print(sorted(n & ids('cases/counterfact_100_seed0.jsonl')), sorted(n & ids('cases/counterfact_dev20_seed1.jsonl')))"
git add cases\counterfact_rel31x2.jsonl
git commit -m "Case file: first 2 records of each of the 31 large CounterFact relations"
git push
git status --short          # clean again
```

## 3. Dry run, 1 edit

```powershell
$env:MODAL_IMAGE_BUILDER_VERSION = "2025.06"
D:\modal-venv\Scripts\modal.exe run --detach scripts/modal_app.py --step export --tag rel31_dry --cases cases/counterfact_rel31x2.jsonl --limit 1
```

Wait for it to finish (the Modal dashboard, or `D:\modal-venv\Scripts\modal.exe app list`). Then, 20 seconds later at
the earliest:

```powershell
D:\modal-venv\Scripts\modal.exe run --detach scripts/modal_app.py --step score --tag rel31_dry --cases cases/counterfact_rel31x2.jsonl --deltas rel31_dry --modes restore,svd --svd-q 15 --limit 1
```

Look at the logs of both: the export should print `1/1 ... rewrite_acc` and `ALL DONE`; the score step should end
without a traceback. Dry-run files stay on the volume only; do not copy them into `results/`.

## 4. Export the 62 edits (authors' environment, A100)

```powershell
D:\modal-venv\Scripts\modal.exe run --detach scripts/modal_app.py --step export --tag rel31_7b --cases cases/counterfact_rel31x2.jsonl
```

Same tag resumes from the checkpoint if it is interrupted. Done when the log ends with
`N/62 edits with rewrite_acc 1.0 (their script keeps only these)` and `ALL DONE`. Write down N.

## 5. The q sweep (first-token reversal at every q from 0 to 20)

```powershell
D:\modal-venv\Scripts\modal.exe run --detach scripts/modal_app.py --step sweep --tag rel31_7b --cases cases/counterfact_rel31x2.jsonl --deltas rel31_7b
```

Output on the volume: `rb/results/<stamp>_svd_q_sweep_easyedit_counterfact_rel31x2.json`. Its `table` has
`reversal_1` (first token equals base) and `reversal` (all 5 tokens) per q, over the edits that took by our criterion;
`table_their_filter` is the same restricted to edits with rewrite_acc 1.0. Denominators are in the file (`n`).

## 6. Scored runs: undo and null-edit control at q=15, 10 and 3

Eight launches, 20 seconds apart. `--modes restore,svd` only on the q=15 undo; the controls use `--modes svd`.

```powershell
D:\modal-venv\Scripts\modal.exe run --detach scripts/modal_app.py --step score --tag ee_rel31_7b_q15 --cases cases/counterfact_rel31x2.jsonl --deltas rel31_7b --modes restore,svd --svd-q 15
Start-Sleep -Seconds 25
D:\modal-venv\Scripts\modal.exe run --detach scripts/modal_app.py --step score --tag ee_rel31_7b_q15_nulledit --cases cases/counterfact_rel31x2.jsonl --deltas rel31_7b --modes svd --svd-q 15 --null-edit
Start-Sleep -Seconds 25
D:\modal-venv\Scripts\modal.exe run --detach scripts/modal_app.py --step score --tag ee_rel31_7b_q10 --cases cases/counterfact_rel31x2.jsonl --deltas rel31_7b --modes svd --svd-q 10
Start-Sleep -Seconds 25
D:\modal-venv\Scripts\modal.exe run --detach scripts/modal_app.py --step score --tag ee_rel31_7b_q10_nulledit --cases cases/counterfact_rel31x2.jsonl --deltas rel31_7b --modes svd --svd-q 10 --null-edit
Start-Sleep -Seconds 25
D:\modal-venv\Scripts\modal.exe run --detach scripts/modal_app.py --step score --tag ee_rel31_7b_q3 --cases cases/counterfact_rel31x2.jsonl --deltas rel31_7b --modes svd --svd-q 3
Start-Sleep -Seconds 25
D:\modal-venv\Scripts\modal.exe run --detach scripts/modal_app.py --step score --tag ee_rel31_7b_q3_nulledit --cases cases/counterfact_rel31x2.jsonl --deltas rel31_7b --modes svd --svd-q 3 --null-edit
```

## 7. The graded KL test at q=15, with and without the control

```powershell
Start-Sleep -Seconds 25
D:\modal-venv\Scripts\modal.exe run --detach scripts/modal_app.py --step kl --tag ee_rel31_7b_q15 --cases cases/counterfact_rel31x2.jsonl --deltas rel31_7b --modes restore,svd --svd-qs 15
Start-Sleep -Seconds 25
D:\modal-venv\Scripts\modal.exe run --detach scripts/modal_app.py --step kl --tag ee_rel31_7b_q15_nulledit --cases cases/counterfact_rel31x2.jsonl --deltas rel31_7b --modes svd --svd-qs 15 --null-edit
```

(The `kl` result files start `_kl_`, so the same tag as the scored runs does not clash.)

## 8. Fetch the results

The volume also holds the November results, so fetch to a scratch folder on D: and copy only the new files:

```powershell
D:\modal-venv\Scripts\modal.exe volume get retractbench-vol rb/results/ D:\scratch\rel31_fetch
Get-ChildItem D:\scratch\rel31_fetch -Recurse -File | Where-Object { $_.Name -match 'rel31' } | Select-Object Name, Length
Get-ChildItem D:\scratch\rel31_fetch -Recurse -File | Where-Object { $_.Name -match 'rel31' } | ForEach-Object { Copy-Item $_.FullName results\ -ErrorAction Stop }
D:\modal-venv\Scripts\modal.exe volume get retractbench-vol data/easyedit_rome/rel31_7b.pt data\easyedit_rome\rel31_7b.pt
Get-FileHash data\easyedit_rome\rel31_7b.pt -Algorithm SHA256
```

`Copy-Item` without `-Force` stops on an existing file, so nothing is overwritten. Files are copied unchanged.
(`volume get` may place files under a `results` subfolder of the target; the `-Recurse` handles that.)

## 9. Analysis (our venv, pure Python on the result files)

Replace `<...>` with the file names that landed in `results\`. The sweep file name has no tag; it is the
`*_svd_q_sweep_easyedit_counterfact_rel31x2.json` one.

```powershell
# first-token reversal per q (and the 5-token criterion): read the table straight from the sweep file
$f = (Get-ChildItem results\*_svd_q_sweep_easyedit_counterfact_rel31x2.json | Sort-Object Name | Select-Object -Last 1).FullName
$d = Get-Content $f -Raw | ConvertFrom-Json
"edits that took: $($d.n_edits_ok) of $($d.n_cases); also pass their filter: $($d.n_edits_ok_and_their_filter)"
$d.table | Where-Object { $_.q -in 0,3,10,15,20 } | Format-Table q, n, reversal_1, reversal, edit_kept
$d.table_their_filter | Where-Object { $_.q -in 0,3,10,15,20 } | Format-Table q, n, reversal_1, reversal, edit_kept

# undo vs control at each q: exact match, leak, ES
.\.venv\Scripts\python.exe scripts\compare_null_svd.py results\<q15 undo>.json results\<q15 nulledit>.json results\<stamp>_rel31_q15_null_svd_compare.json
.\.venv\Scripts\python.exe scripts\compare_null_svd.py results\<q10 undo>.json results\<q10 nulledit>.json results\<stamp>_rel31_q10_null_svd_compare.json
.\.venv\Scripts\python.exe scripts\compare_null_svd.py results\<q3 undo>.json results\<q3 nulledit>.json results\<stamp>_rel31_q3_null_svd_compare.json

# per probe type (edited prompt equal to base, undo vs control) and the paired ES test
.\.venv\Scripts\python.exe scripts\probe_types.py results\<q15 undo>.json results\<q15 nulledit>.json cases\counterfact_rel31x2.jsonl results\<stamp>_rel31_q15_probe_types.json

# graded KL: ratios with bootstrap CI, first-position KL, near-ties
.\.venv\Scripts\python.exe scripts\analyze_kl.py results\<stamp>_kl_ee_rel31_7b_q15.json results\<stamp>_kl_ee_rel31_7b_q15_nulledit.json svd15 results\<stamp>_rel31_q15_kl_analysis.json
```

Where the numbers for the predictions come from:
1. to 3.: sweep file, `reversal_1` at q = 15, 3, 10.
4.: `analyze_kl` output, `first_kl_edited_prompt.undo_mean`.
5. and 6.: `analyze_kl` output, `answer_kl_target.ratio` and `answer_kl_away.ratio` (with `ratio_ci95`).
7.: `probe_types` output, edited-prompt row: `undo_eq_base` against `control_eq_base`, out of 62.

Commit the analysis outputs and the copied run files (and, if wanted, the edit file: `.gitignore` already allows
`data/easyedit_rome/rel31_7b.pt`; add its row, with the SHA256 from step 8, to `data/easyedit_rome/README.md`).
The results go in a new dated LOG.md entry against the predictions; do not edit the 2026-11-23 entry.

## Rough time and cost

From LOG.md (2026-11-03 13:30 entry): on the A100 80GB the authors' ROME export took about 11 s per edit, so 62 edits
are about 12 minutes plus the container start and model load. CLAUDE.md's 105 s per edit is the local RTX 3070.
The LOG records no per-run time for the 7B scoring on the A100. The local 1.5B scored runs on 100 cases took 14-16
minutes each (2026-11-03 entries), and the 7B runs had the same probes, so plan on roughly 10-20 minutes per scored
run for 62 cases, which is a guess, not a measurement. The sweep (62 edits x 21 values of q, 5 tokens) should be of
the same order. Eight scored/KL runs, one sweep and one export, plus two dry runs: roughly 2.5-4 GPU-hours.
Cost: the author's note is that the 3 November 7B runs (120 edits exported, the sweep and about ten scored runs)
used about half of the $30 monthly credit (about $15; LOG 2026-11-03 21:20 says the KL runs were extra and not
costed, and a reviewer could not verify the $15). This run is about half the edits and a similar number of runs, so
expect below $15; the dashboard figures before and after are the real answer.

## What to send back

- The credit shown before starting and after finishing (Modal Usage and Billing), and the date of each reading.
- Step 2: the case count, the number of relations, and the two overlap lists (empty or not).
- Step 4: the line `N/62 edits with rewrite_acc 1.0`, and the time it took.
- Step 5: the sweep table for q = 0, 3, 10, 15, 20 (both `table` and `table_their_filter`), with `n_edits_ok` and
  `n_edits_ok_and_their_filter`.
- The new file names in `results\` (or the files themselves), and the SHA256 of `rel31_7b.pt`.
- The `compare_null_svd`, `probe_types` and `analyze_kl` outputs.
- Any step that failed, with the last 30 lines of its log, and any step you had to repeat.
