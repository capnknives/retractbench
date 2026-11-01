# Run 20261101T175244Z: grace-last-standardized fictional

## Config

```json
{
  "timestamp_utc": "20261101T175244Z",
  "editor": "grace-last-standardized",
  "editor_config": {
    "layer": 14,
    "eps": 0.023686110973358154,
    "steps": 100,
    "lr": 1.0,
    "tol": 0.05,
    "n_layers": 28,
    "key_position": "last",
    "key_space": "standardized",
    "fallback_cases": []
  },
  "git_commit": "e81c3fe-dirty",
  "python": "3.10.0",
  "platform": "Windows-10-10.0.26200-SP0",
  "model": "Qwen/Qwen2.5-1.5B",
  "device": "cuda",
  "dtype": "bfloat16",
  "cases_file": "cases\\fictional_v0.jsonl",
  "n_cases": 5,
  "torch": "2.6.0+cu124",
  "budget": 0.05
}
```

## Summary

| Metric | Value |
| --- | --- |
| n_cases | 5 |
| edit_success | 0.800 |
| edit_success_loose | 1.000 |
| paraphrase_generalization | 0.000 |
| locality | 1.000 |
| locality_hard | 1.000 |
| revocation_exact | 1.000 |
| target_leak_after_revoke | 0.000 |
| apply_ms_mean | 1289.760 |
| revoke_ms_mean | 0.010 |

## Per case

| Case | Edit | Paraphrase gen. | Locality | Locality (hard) | Exact revoke | Leak |
| --- | --- | --- | --- | --- | --- | --- |
| titan | False | 0.00 | 1.00 | 1.00 | True | 0.00 |
| velmora | True | 0.00 | 1.00 | 1.00 | True | 0.00 |
| orrin | True | 0.00 | 1.00 | 1.00 | True | 0.00 |
| kestrel | True | 0.00 | 1.00 | 1.00 | True | 0.00 |
| lumen | True | 0.00 | 1.00 | 1.00 | True | 0.00 |
