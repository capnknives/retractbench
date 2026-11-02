$env:HF_HOME = "D:\hf-cache"
$env:PYTHONIOENCODING = "utf-8"
Set-Location D:\retractbench
$log = "D:\retractbench\results\logs\svd_q_sweep_easyedit_dev20.log"
& .\.venv\Scripts\python.exe scripts\sweep_svd_q.py --cases cases\counterfact_dev20_seed1.jsonl `
    --deltas data\easyedit_rome\dev20.pt --dtype float32 --qmax 20 *>&1 | Tee-Object $log
"EXIT $LASTEXITCODE" | Tee-Object -Append $log
