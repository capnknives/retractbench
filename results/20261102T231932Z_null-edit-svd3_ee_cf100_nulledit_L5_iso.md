# Run 20261102T231932Z: null-edit-svd3 ee_cf100_nulledit_L5_iso

## Config

```json
{
  "timestamp_utc": "20261102T231932Z",
  "editor": "null-edit-svd3",
  "editor_config": {
    "source": "null-edit",
    "layer": 5,
    "n_layers": 28,
    "revoke_mode": "svd",
    "svd_q": 3,
    "weight_dtype": "float32",
    "n_updates": 100
  },
  "git_commit": "c10647f-dirty",
  "python": "3.10.0",
  "platform": "Windows-10-10.0.26200-SP0",
  "model": "Qwen/Qwen2.5-1.5B",
  "device": "cuda",
  "dtype": "float32",
  "cases_file": "cases\\counterfact_100_seed0.jsonl",
  "n_cases": 100,
  "torch": "2.6.0+cu124",
  "deltas": "data\\easyedit_rome\\cf100.pt",
  "null_edit": true,
  "deltas_meta": {
    "hparams_file": "D:\\retractbench\\configs\\easyedit_rome_qwen2.5-1.5b.yaml",
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
      "model_name": "Qwen/Qwen2.5-1.5B",
      "stats_dir": "./data/stats",
      "max_length": 40,
      "model_parallel": false,
      "fp16": false
    },
    "cases_file": "D:\\retractbench\\cases\\counterfact_100_seed0.jsonl",
    "weight_name": "model.layers.5.mlp.down_proj.weight",
    "weight_shape": [
      1536,
      8960
    ],
    "weight_dtype": "torch.float32",
    "weight_sum_before": 92.8255407679826,
    "torch": "2.0.1+cu118",
    "transformers": "4.46.2",
    "trace_and_reverse_repo": "D:\\trace-and-reverse"
  },
  "rewrite_acc_post": {
    "cf12623": 1.0,
    "cf13781": 1.0,
    "cf1326": 1.0,
    "cf8484": 1.0,
    "cf16753": 1.0,
    "cf15922": 1.0,
    "cf13268": 1.0,
    "cf9938": 1.0,
    "cf15617": 1.0,
    "cf11732": 1.0,
    "cf19116": 1.0,
    "cf7157": 1.0,
    "cf16537": 1.0,
    "cf4563": 1.0,
    "cf9235": 1.0,
    "cf4579": 1.0,
    "cf3107": 1.0,
    "cf20262": 1.0,
    "cf8208": 1.0,
    "cf17451": 1.0,
    "cf19723": 1.0,
    "cf4815": 1.0,
    "cf10162": 1.0,
    "cf3236": 1.0,
    "cf2416": 1.0,
    "cf10819": 1.0,
    "cf15471": 1.0,
    "cf18343": 1.0,
    "cf3299": 1.0,
    "cf11593": 1.0,
    "cf14226": 1.0,
    "cf10361": 1.0,
    "cf20017": 1.0,
    "cf20985": 1.0,
    "cf6700": 1.0,
    "cf18105": 1.0,
    "cf15630": 1.0,
    "cf14506": 1.0,
    "cf17083": 1.0,
    "cf8535": 1.0,
    "cf2040": 1.0,
    "cf17979": 1.0,
    "cf460": 1.0,
    "cf3056": 1.0,
    "cf13068": 1.0,
    "cf21894": 1.0,
    "cf20488": 1.0,
    "cf37": 1.0,
    "cf20050": 1.0,
    "cf16173": 1.0,
    "cf10916": 1.0,
    "cf7992": 1.0,
    "cf10656": 1.0,
    "cf2063": 1.0,
    "cf6260": 1.0,
    "cf18596": 1.0,
    "cf7264": 1.0,
    "cf7818": 1.0,
    "cf4669": 1.0,
    "cf17792": 1.0,
    "cf14679": 1.0,
    "cf2988": 1.0,
    "cf2636": 1.0,
    "cf10487": 1.0,
    "cf16644": 1.0,
    "cf16032": 1.0,
    "cf3573": 1.0,
    "cf9877": 1.0,
    "cf18063": 1.0,
    "cf9538": 1.0,
    "cf4089": 1.0,
    "cf17938": 1.0,
    "cf10903": 1.0,
    "cf17704": 1.0,
    "cf6658": 1.0,
    "cf19765": 1.0,
    "cf17931": 1.0,
    "cf19255": 1.0,
    "cf9425": 1.0,
    "cf14581": 1.0,
    "cf3002": 1.0,
    "cf19539": 1.0,
    "cf12612": 1.0,
    "cf10388": 1.0,
    "cf18862": 1.0,
    "cf7933": 1.0,
    "cf9513": 1.0,
    "cf6025": 1.0,
    "cf6205": 1.0,
    "cf6118": 1.0,
    "cf1080": 1.0,
    "cf20079": 1.0,
    "cf21517": 1.0,
    "cf8521": 1.0,
    "cf15614": 1.0,
    "cf2263": 1.0,
    "cf2943": 1.0,
    "cf4267": 1.0,
    "cf4900": 1.0,
    "cf1266": 1.0
  }
}
```

## Summary

| Metric | Value |
| --- | --- |
| n_cases | 100 |
| edit_success | 0.030 |
| edit_success_loose | 0.040 |
| paraphrase_generalization | 0.000 |
| locality | 1.000 |
| locality_hard | 1.000 |
| revocation_exact | 0.000 |
| target_leak_after_revoke | 0.003 |
| target_leak_excl_true | 0.000 |
| apply_ms_mean | 54.458 |
| revoke_ms_mean | 349.551 |
| es_base | 0.190 |
| ps_base | 0.200 |
| ns_base | 0.808 |
| es_after_write | 0.190 |
| ps_after_write | 0.200 |
| ns_after_write | 0.808 |
| es_after_revoke | 0.220 |
| ps_after_revoke | 0.200 |
| ns_after_revoke | 0.800 |

## Per case

| Case | Edit | Paraphrase gen. | Locality | Locality (hard) | Exact revoke | Leak |
| --- | --- | --- | --- | --- | --- | --- |
| cf12623 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf13781 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf1326 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf8484 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf16753 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf15922 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf13268 | False | 0.00 | 1.00 | 1.00 | False | 0.33 |
| cf9938 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf15617 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf11732 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf19116 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf7157 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf16537 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf4563 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf9235 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf4579 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf3107 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf20262 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf8208 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf17451 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf19723 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf4815 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf10162 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf3236 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf2416 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf10819 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf15471 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf18343 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf3299 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf11593 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf14226 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf10361 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf20017 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf20985 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf6700 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf18105 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf15630 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf14506 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf17083 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf8535 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf2040 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf17979 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf460 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf3056 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf13068 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf21894 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf20488 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf37 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf20050 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf16173 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf10916 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf7992 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf10656 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf2063 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf6260 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf18596 | True | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf7264 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf7818 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf4669 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf17792 | True | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf14679 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf2988 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf2636 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf10487 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf16644 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf16032 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf3573 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf9877 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf18063 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf9538 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf4089 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf17938 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf10903 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf17704 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf6658 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf19765 | True | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf17931 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf19255 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf9425 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf14581 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf3002 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf19539 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf12612 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf10388 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf18862 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf7933 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf9513 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf6025 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf6205 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf6118 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf1080 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf20079 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf21517 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf8521 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf15614 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf2263 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf2943 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf4267 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf4900 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
| cf1266 | False | 0.00 | 1.00 | 1.00 | False | 0.00 |
