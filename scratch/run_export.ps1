param([string]$Cases, [string]$Tag, [int]$Limit = 0)
$env:HF_HOME = "D:\hf-cache"
$env:PYTHONIOENCODING = "utf-8"
Set-Location D:\trace-and-reverse
$log = "D:\retractbench\results\logs\easyedit_export_$Tag.log"
$extra = @()
if ($Limit -gt 0) { $extra = @("--limit", "$Limit") }
& .\.venv\Scripts\python.exe D:\retractbench\scripts\easyedit_rome_export.py --cases $Cases --tag $Tag `
    --hparams D:\retractbench\configs\easyedit_rome_qwen2.5-1.5b.yaml @extra *>&1 | Tee-Object $log
"EXIT $LASTEXITCODE" | Tee-Object -Append $log
