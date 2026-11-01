# Run 20261101T223752Z: rome-subject-inverse-cov cf100_L4_iso

## Config

```json
{
  "timestamp_utc": "20261101T223752Z",
  "editor": "rome-subject-inverse-cov",
  "editor_config": {
    "layer": 4,
    "n_layers": 28,
    "key_position": "subject",
    "revoke_mode": "inverse",
    "covariance": "calibration",
    "weight_dtype": "float32",
    "steps": 100,
    "lr": 0.5,
    "tol": 0.05,
    "clamp_factor": 4.0,
    "ridge": 1.0,
    "inverse_tokens": 3,
    "fallback_cases": [
      "cf18862"
    ]
  },
  "git_commit": "4473023-dirty",
  "python": "3.10.0",
  "platform": "Windows-10-10.0.26200-SP0",
  "model": "Qwen/Qwen2.5-1.5B",
  "device": "cuda",
  "dtype": "bfloat16",
  "cases_file": "cases\\counterfact_100_seed0.jsonl",
  "n_cases": 100,
  "torch": "2.6.0+cu124"
}
```

## Summary

| Metric | Value |
| --- | --- |
| n_cases | 100 |
| edit_success | 0.990 |
| edit_success_loose | 1.000 |
| paraphrase_generalization | 0.575 |
| locality | 0.777 |
| locality_hard | 0.652 |
| revocation_exact | 0.000 |
| target_leak_after_revoke | 0.020 |
| apply_ms_mean | 927.143 |
| revoke_ms_mean | 1509.224 |

## Per case

| Case | Edit | Paraphrase gen. | Locality | Locality (hard) | Exact revoke | Leak |
| --- | --- | --- | --- | --- | --- | --- |
| cf12623 | True | 0.00 | 1.00 | 0.60 | False | 0.00 |
| cf13781 | True | 0.50 | 1.00 | 1.00 | False | 0.00 |
| cf1326 | True | 0.50 | 1.00 | 0.80 | False | 0.00 |
| cf8484 | True | 0.00 | 0.67 | 0.40 | False | 0.00 |
| cf16753 | True | 0.50 | 1.00 | 0.80 | False | 0.00 |
| cf15922 | True | 1.00 | 1.00 | 1.00 | False | 0.00 |
| cf13268 | True | 0.50 | 1.00 | 0.80 | False | 0.00 |
| cf9938 | True | 0.50 | 1.00 | 0.80 | False | 0.00 |
| cf15617 | True | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf11732 | True | 1.00 | 0.67 | 0.80 | False | 0.00 |
| cf19116 | True | 0.50 | 0.67 | 0.80 | False | 0.00 |
| cf7157 | False | 0.00 | 0.67 | 0.80 | False | 0.00 |
| cf16537 | True | 0.50 | 0.33 | 0.40 | False | 0.00 |
| cf4563 | True | 0.50 | 0.33 | 0.80 | False | 0.00 |
| cf9235 | True | 0.00 | 0.67 | 0.80 | False | 0.00 |
| cf4579 | True | 0.00 | 1.00 | 0.80 | False | 0.00 |
| cf3107 | True | 0.50 | 1.00 | 1.00 | False | 0.00 |
| cf20262 | True | 1.00 | 1.00 | 1.00 | False | 0.00 |
| cf8208 | True | 1.00 | 0.67 | 0.60 | False | 0.00 |
| cf17451 | True | 0.00 | 0.33 | 0.20 | False | 0.00 |
| cf19723 | True | 0.00 | 1.00 | 0.40 | False | 0.00 |
| cf4815 | True | 0.50 | 1.00 | 0.60 | False | 0.00 |
| cf10162 | True | 1.00 | 1.00 | 0.80 | False | 0.00 |
| cf3236 | True | 1.00 | 0.67 | 0.20 | False | 0.00 |
| cf2416 | True | 0.50 | 1.00 | 1.00 | False | 0.00 |
| cf10819 | True | 1.00 | 0.33 | 0.20 | False | 0.00 |
| cf15471 | True | 0.50 | 0.67 | 0.60 | False | 0.00 |
| cf18343 | True | 1.00 | 1.00 | 0.60 | False | 0.00 |
| cf3299 | True | 1.00 | 0.67 | 0.80 | False | 0.00 |
| cf11593 | True | 0.50 | 0.67 | 0.60 | False | 0.00 |
| cf14226 | True | 1.00 | 0.33 | 1.00 | False | 0.00 |
| cf10361 | True | 1.00 | 1.00 | 0.60 | False | 0.33 |
| cf20017 | True | 0.50 | 1.00 | 0.60 | False | 0.00 |
| cf20985 | True | 1.00 | 1.00 | 0.80 | False | 0.00 |
| cf6700 | True | 0.50 | 0.33 | 0.40 | False | 0.00 |
| cf18105 | True | 0.50 | 0.67 | 1.00 | False | 0.00 |
| cf15630 | True | 0.00 | 0.67 | 0.80 | False | 0.00 |
| cf14506 | True | 1.00 | 1.00 | 0.00 | False | 0.00 |
| cf17083 | True | 1.00 | 0.67 | 0.00 | False | 0.00 |
| cf8535 | True | 1.00 | 0.33 | 0.00 | False | 0.00 |
| cf2040 | True | 1.00 | 1.00 | 0.80 | False | 0.00 |
| cf17979 | True | 0.50 | 0.33 | 0.60 | False | 0.00 |
| cf460 | True | 1.00 | 0.67 | 0.80 | False | 0.00 |
| cf3056 | True | 1.00 | 1.00 | 0.60 | False | 0.00 |
| cf13068 | True | 1.00 | 1.00 | 0.60 | False | 0.00 |
| cf21894 | True | 0.50 | 1.00 | 0.40 | False | 0.00 |
| cf20488 | True | 0.50 | 0.33 | 0.80 | False | 0.00 |
| cf37 | True | 1.00 | 0.67 | 0.00 | False | 0.00 |
| cf20050 | True | 0.50 | 0.67 | 0.60 | False | 0.33 |
| cf16173 | True | 1.00 | 1.00 | 0.60 | False | 0.00 |
| cf10916 | True | 1.00 | 0.67 | 0.80 | False | 0.00 |
| cf7992 | True | 1.00 | 0.67 | 0.60 | False | 0.00 |
| cf10656 | True | 0.50 | 0.67 | 0.40 | False | 0.00 |
| cf2063 | True | 0.50 | 0.33 | 0.80 | False | 0.00 |
| cf6260 | True | 0.00 | 1.00 | 0.80 | False | 0.00 |
| cf18596 | True | 1.00 | 1.00 | 0.40 | False | 0.00 |
| cf7264 | True | 1.00 | 1.00 | 0.80 | False | 0.00 |
| cf7818 | True | 0.50 | 0.67 | 0.60 | False | 0.00 |
| cf4669 | True | 1.00 | 1.00 | 0.20 | False | 0.00 |
| cf17792 | True | 0.00 | 0.67 | 0.80 | False | 0.00 |
| cf14679 | True | 0.00 | 0.67 | 0.40 | False | 0.00 |
| cf2988 | True | 0.50 | 1.00 | 0.80 | False | 0.00 |
| cf2636 | True | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf10487 | True | 0.50 | 0.67 | 0.80 | False | 0.00 |
| cf16644 | True | 1.00 | 1.00 | 0.60 | False | 0.00 |
| cf16032 | True | 1.00 | 1.00 | 0.00 | False | 0.00 |
| cf3573 | True | 0.50 | 1.00 | 0.60 | False | 0.00 |
| cf9877 | True | 0.50 | 1.00 | 0.80 | False | 0.00 |
| cf18063 | True | 0.50 | 1.00 | 1.00 | False | 0.00 |
| cf9538 | True | 1.00 | 0.33 | 1.00 | False | 0.00 |
| cf4089 | True | 0.00 | 0.67 | 0.80 | False | 0.00 |
| cf17938 | True | 0.50 | 0.67 | 0.80 | False | 0.00 |
| cf10903 | True | 1.00 | 1.00 | 0.60 | False | 0.00 |
| cf17704 | True | 0.50 | 1.00 | 0.80 | False | 0.00 |
| cf6658 | True | 1.00 | 0.67 | 0.80 | False | 0.00 |
| cf19765 | True | 0.50 | 0.33 | 0.40 | False | 0.33 |
| cf17931 | True | 0.50 | 1.00 | 1.00 | False | 0.00 |
| cf19255 | True | 0.00 | 0.67 | 0.60 | False | 0.00 |
| cf9425 | True | 1.00 | 1.00 | 0.80 | False | 0.67 |
| cf14581 | True | 0.50 | 1.00 | 1.00 | False | 0.00 |
| cf3002 | True | 0.50 | 0.67 | 1.00 | False | 0.00 |
| cf19539 | True | 0.00 | 1.00 | 0.60 | False | 0.00 |
| cf12612 | True | 0.50 | 1.00 | 0.80 | False | 0.00 |
| cf10388 | True | 1.00 | 0.33 | 0.80 | False | 0.00 |
| cf18862 | True | 0.50 | 0.67 | 0.40 | False | 0.33 |
| cf7933 | True | 0.00 | 0.33 | 0.40 | False | 0.00 |
| cf9513 | True | 0.50 | 0.67 | 0.80 | False | 0.00 |
| cf6025 | True | 0.50 | 0.67 | 0.40 | False | 0.00 |
| cf6205 | True | 0.00 | 0.67 | 0.60 | False | 0.00 |
| cf6118 | True | 0.50 | 1.00 | 0.80 | False | 0.00 |
| cf1080 | True | 0.00 | 1.00 | 0.80 | False | 0.00 |
| cf20079 | True | 1.00 | 1.00 | 0.60 | False | 0.00 |
| cf21517 | True | 1.00 | 1.00 | 0.60 | False | 0.00 |
| cf8521 | True | 0.00 | 0.67 | 0.40 | False | 0.00 |
| cf15614 | True | 0.50 | 1.00 | 1.00 | False | 0.00 |
| cf2263 | True | 0.00 | 0.67 | 0.20 | False | 0.00 |
| cf2943 | True | 0.50 | 0.67 | 0.60 | False | 0.00 |
| cf4267 | True | 0.50 | 0.33 | 0.80 | False | 0.00 |
| cf4900 | True | 0.50 | 0.67 | 0.00 | False | 0.00 |
| cf1266 | True | 1.00 | 0.67 | 0.80 | False | 0.00 |
