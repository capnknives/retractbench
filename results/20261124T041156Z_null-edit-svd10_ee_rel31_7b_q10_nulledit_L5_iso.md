# Run 20261124T041156Z: null-edit-svd10 ee_rel31_7b_q10_nulledit_L5_iso

## Config

```json
{
  "timestamp_utc": "20261124T041156Z",
  "editor": "null-edit-svd10",
  "editor_config": {
    "source": "null-edit",
    "layer": 5,
    "n_layers": 28,
    "revoke_mode": "svd",
    "svd_q": 10,
    "weight_dtype": "float32",
    "n_updates": 62
  },
  "git_commit": "5ae87fa",
  "python": "3.10.17",
  "platform": "Linux-4.19.0-gvisor-x86_64-with-glibc2.36",
  "model": "Qwen/Qwen2.5-7B",
  "device": "cuda",
  "dtype": "float32",
  "cases_file": "/root/retractbench/cases/counterfact_rel31x2.jsonl",
  "n_cases": 62,
  "torch": "2.6.0+cu124",
  "max_new_tokens": 8,
  "svd_q": 10,
  "deltas": "/vol/data/easyedit_rome/rel31_7b.pt",
  "null_edit": true,
  "deltas_meta": {
    "hparams_file": "/root/retractbench/configs/easyedit_rome_qwen2.5-7b.yaml",
    "hparams": {
      "layers": [
        5
      ],
      "fact_token": "subject_last",
      "v_num_grad_steps": 25,
      "v_lr": 0.5,
      "v_loss_layer": 27,
      "v_weight_decay": 0.001,
      "clamp_norm_factor": 4,
      "kl_factor": 0.0625,
      "mom2_adjustment": false,
      "context_template_length_params": [
        [
          5,
          10
        ],
        [
          10,
          10
        ]
      ],
      "rewrite_module_tmp": "model.layers.{}.mlp.down_proj",
      "layer_module_tmp": "model.layers.{}",
      "mlp_module_tmp": "model.layers.{}.mlp",
      "attn_module_tmp": "model.layers.{}.self_attn",
      "ln_f_module": "model.norm",
      "lm_head_module": "lm_head",
      "mom2_dataset": "wikipedia",
      "mom2_n_samples": 100000,
      "mom2_dtype": "float32",
      "alg_name": "ROME",
      "device": 0,
      "model_name": "Qwen/Qwen2.5-7B",
      "stats_dir": "./data/stats",
      "max_length": 40,
      "model_parallel": false,
      "fp16": false
    },
    "cases_file": "/root/retractbench/cases/counterfact_rel31x2.jsonl",
    "weight_name": "model.layers.5.mlp.down_proj.weight",
    "weight_shape": [
      3584,
      18944
    ],
    "weight_dtype": "torch.float32",
    "weight_sum_before": -71.2119342720689,
    "torch": "2.0.1+cu118",
    "transformers": "4.46.2",
    "trace_and_reverse_repo": "/root/trace-and-reverse",
    "retractbench_commit": "5ae87fa916438fdec8f383665289e1147379a1a0",
    "trace_and_reverse_commit": "d783bc180290d87e84788525bb2ddbd65a7939a0",
    "hparams_sha256": "4cfbb1c8b4c36f9d189305d3c542f0189dc7832caabbcb9101dbb14b319f2cec",
    "cases_sha256": "d25e05235fefaa9cb791b500ce69ee42960549939f0d201cb0119ba7f885b770",
    "gpu": "NVIDIA A100-SXM4-80GB",
    "modal_task_id": "ta-01M85P753FMR76QA6XREDZMTXR"
  },
  "rewrite_acc_post": {
    "cf0": 1.0,
    "cf5": 1.0,
    "cf1": 1.0,
    "cf100": 1.0,
    "cf2": 1.0,
    "cf113": 1.0,
    "cf3": 1.0,
    "cf53": 1.0,
    "cf4": 1.0,
    "cf8": 1.0,
    "cf6": 1.0,
    "cf50": 1.0,
    "cf7": 1.0,
    "cf48": 1.0,
    "cf9": 1.0,
    "cf31": 1.0,
    "cf10": 1.0,
    "cf155": 1.0,
    "cf11": 1.0,
    "cf79": 1.0,
    "cf13": 1.0,
    "cf18": 1.0,
    "cf15": 1.0,
    "cf96": 1.0,
    "cf17": 1.0,
    "cf89": 1.0,
    "cf19": 1.0,
    "cf74": 1.0,
    "cf20": 1.0,
    "cf146": 1.0,
    "cf22": 1.0,
    "cf33": 1.0,
    "cf23": 1.0,
    "cf46": 1.0,
    "cf24": 1.0,
    "cf32": 1.0,
    "cf26": 1.0,
    "cf42": 1.0,
    "cf28": 1.0,
    "cf29": 1.0,
    "cf30": 1.0,
    "cf34": 1.0,
    "cf39": 1.0,
    "cf69": 1.0,
    "cf41": 1.0,
    "cf54": 1.0,
    "cf44": 1.0,
    "cf45": 1.0,
    "cf55": 1.0,
    "cf73": 1.0,
    "cf57": 1.0,
    "cf59": 1.0,
    "cf58": 1.0,
    "cf67": 1.0,
    "cf62": 1.0,
    "cf191": 1.0,
    "cf95": 1.0,
    "cf118": 1.0,
    "cf98": 1.0,
    "cf141": 1.0,
    "cf167": 1.0,
    "cf209": 1.0
  },
  "provenance": {
    "process_started_utc": "20261124T040101Z",
    "argv": [
      "/root/retractbench/scripts/run_rome.py",
      "--model",
      "Qwen/Qwen2.5-7B",
      "--cases",
      "/root/retractbench/cases/counterfact_rel31x2.jsonl",
      "--tag",
      "ee_rel31_7b_q10_nulledit",
      "--deltas",
      "/vol/data/easyedit_rome/rel31_7b.pt",
      "--dtype",
      "float32",
      "--modes",
      "svd",
      "--svd-q",
      "10",
      "--null-edit"
    ],
    "git": {
      "commit": "5ae87fa916438fdec8f383665289e1147379a1a0",
      "dirty": false,
      "source": "env RETRACTBENCH_GIT_COMMIT"
    },
    "trace_and_reverse_commit": "d783bc180290d87e84788525bb2ddbd65a7939a0",
    "python": "3.10.17",
    "platform": "Linux-4.19.0-gvisor-x86_64-with-glibc2.36",
    "packages": {
      "torch": "2.6.0+cu124",
      "transformers": "5.20.2",
      "numpy": "2.2.6",
      "huggingface-hub": "2.4.0",
      "safetensors": "0.8.0",
      "accelerate": "1.15.0"
    },
    "gpu": {
      "cuda_available": true,
      "torch_cuda": "12.4",
      "cudnn": 90100,
      "device_name": "NVIDIA A100-SXM4-80GB",
      "device_count": 1
    },
    "modal": {
      "MODAL_TASK_ID": "ta-01M85VDF0MTC08R4HKAKRTBVZR",
      "MODAL_IMAGE_ID": "im-yrfoSAO95RZVnadRvqEAHO",
      "MODAL_ENVIRONMENT": "main",
      "MODAL_REGION": "eu",
      "MODAL_CLOUD_PROVIDER": "CLOUD_PROVIDER_UNSPECIFIED",
      "MODAL_IMAGE_BUILDER_VERSION": "2025.06"
    },
    "model_revision": null,
    "inputs_sha256": {
      "cases": "d25e05235fefaa9cb791b500ce69ee42960549939f0d201cb0119ba7f885b770",
      "deltas": "178da3d1a1886380faca596af8b0dd02ac7c5362b3698d1d88085aefeceb845e"
    }
  }
}
```

## Summary

| Metric | Value |
| --- | --- |
| n_cases | 62 |
| edit_success | 0.000 |
| edit_success_loose | 0.016 |
| paraphrase_generalization | 0.000 |
| locality | 1.000 |
| locality_hard | 1.000 |
| revocation_exact | 0.065 |
| target_leak_after_revoke | 0.000 |
| target_leak_excl_true | 0.000 |
| apply_ms_mean | 371.478 |
| revoke_ms_mean | 1837.520 |
| es_base | 0.145 |
| ps_base | 0.153 |
| ns_base | 0.823 |
| es_after_write | 0.145 |
| ps_after_write | 0.153 |
| ns_after_write | 0.823 |
| es_after_revoke | 0.145 |
| ps_after_revoke | 0.177 |
| ns_after_revoke | 0.810 |

## Per case

| Case | Edit | Paraphrase gen. | Locality | Locality (hard) | Exact revoke | Leak |
| --- | --- | --- | --- | --- | --- | --- |
| cf0 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf5 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf1 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf100 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf2 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf113 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf3 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf53 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf4 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf8 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf6 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf50 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf7 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf48 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf9 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf31 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf10 | False | 0.00 | 1.00 | 1.00 | True | 0.00 |
| cf155 | False | 0.00 | 1.00 | 1.00 | True | 0.00 |
| cf11 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf79 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf13 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf18 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf15 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf96 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf17 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf89 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf19 | False | 0.00 | 1.00 | 1.00 | True | 0.00 |
| cf74 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf20 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf146 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf22 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf33 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf23 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf46 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf24 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf32 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf26 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf42 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf28 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf29 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf30 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf34 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf39 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf69 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf41 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf54 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf44 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf45 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf55 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf73 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf57 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf59 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf58 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf67 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf62 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf191 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf95 | False | 0.00 | 1.00 | 1.00 | True | 0.00 |
| cf118 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf98 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf141 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf167 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf209 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
