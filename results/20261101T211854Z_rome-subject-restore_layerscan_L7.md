# Run 20261101T211854Z: rome-subject-restore layerscan_L7

## Config

```json
{
  "timestamp_utc": "20261101T211854Z",
  "editor": "rome-subject-restore",
  "editor_config": {
    "layer": 7,
    "n_layers": 28,
    "key_position": "subject",
    "revoke_mode": "restore",
    "covariance": "identity",
    "weight_dtype": "float32",
    "steps": 100,
    "lr": 0.5,
    "tol": 0.05,
    "clamp_factor": 4.0,
    "ridge": 1.0,
    "inverse_tokens": 3,
    "fallback_cases": []
  },
  "git_commit": "86502ea-dirty",
  "python": "3.10.0",
  "platform": "Windows-10-10.0.26200-SP0",
  "model": "Qwen/Qwen2.5-1.5B",
  "device": "cuda",
  "dtype": "bfloat16",
  "cases_file": "cases\\counterfact_100_seed0.jsonl",
  "n_cases": 10,
  "torch": "2.6.0+cu124"
}
```

## Summary

| Metric | Value |
| --- | --- |
| n_cases | 10 |
| edit_success | 0.900 |
| edit_success_loose | 1.000 |
| paraphrase_generalization | 0.350 |
| locality | 0.800 |
| locality_hard | 0.440 |
| revocation_exact | 1.000 |
| target_leak_after_revoke | 0.000 |
| apply_ms_mean | 623.793 |
| revoke_ms_mean | 52.443 |

## Per case

| Case | Edit | Paraphrase gen. | Locality | Locality (hard) | Exact revoke | Leak |
| --- | --- | --- | --- | --- | --- | --- |
| cf12623 | True | 0.00 | 1.00 | 0.00 | True | 0.00 |
| cf13781 | True | 0.50 | 0.33 | 0.40 | True | 0.00 |
| cf1326 | True | 0.50 | 1.00 | 0.40 | True | 0.00 |
| cf8484 | True | 0.00 | 0.33 | 0.40 | True | 0.00 |
| cf16753 | True | 0.00 | 1.00 | 0.60 | True | 0.00 |
| cf15922 | True | 1.00 | 1.00 | 0.80 | True | 0.00 |
| cf13268 | True | 0.50 | 1.00 | 0.80 | True | 0.00 |
| cf9938 | True | 0.00 | 1.00 | 0.40 | True | 0.00 |
| cf15617 | False | 0.00 | 0.67 | 0.40 | True | 0.00 |
| cf11732 | True | 1.00 | 0.67 | 0.20 | True | 0.00 |
