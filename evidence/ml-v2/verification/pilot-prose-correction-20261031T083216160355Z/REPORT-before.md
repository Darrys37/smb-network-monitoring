# ML v2 internal pilot benchmark

42 valid runs across 2 blocks; last observation per run.

| Method | Correct / runs | Macro-F1 | Coverage |
|---|---:|---:|---:|
| majority | 6/42 | 0.036 | 100.0% |
| cart_numeric | 42/42 | 1.000 | 100.0% |
| cart_discrete | 42/42 | 1.000 | 100.0% |
| fp_classifier | 41/42 | 0.987 | 97.6% |
| cart_no_quality | 42/42 | 1.000 | 100.0% |
| cart_missingness | 19/42 | 0.389 | 100.0% |
| cart_common | 35/42 | 0.815 | 100.0% |

## Later-block holdout

Train on earlier block; test on pilot-v2-s02. This is the forward-in-time internal comparison.

| Method | Correct / runs | Macro-F1 | Coverage |
|---|---:|---:|---:|
| majority | 3/21 | 0.036 | 100.0% |
| cart_numeric | 21/21 | 1.000 | 100.0% |
| cart_discrete | 21/21 | 1.000 | 100.0% |
| fp_classifier | 20/21 | 0.971 | 95.2% |
| cart_no_quality | 21/21 | 1.000 | 100.0% |
| cart_missingness | 10/21 | 0.390 | 100.0% |
| cart_common | 17/21 | 0.804 | 100.0% |

Leave-one-session-out; preprocessing/mining/pruning fits training sessions only. Domain bins are fixed.

This is internal pilot validation: same host, same lab, same day and only two collection blocks. The initial pilot was seen during method design. No untouched final test, cross-host accuracy, production FPR or calibrated diagnosis probability is claimed.

Expert output remains six independent matched/not_matched/insufficient assessments. It is not forced into a single class or treated as healthy when no rule matches. Read the same-evidence JSON before any per-family evaluation.

Unknown metric values and history coverage can reveal data availability. Evaluate missingness ablation on new data before deployment. CPU/RAM discretization at 90% is a fixed benchmark choice, not a learned optimal threshold.

Predefined ablations use the same held-out sessions: cart_no_quality removes CPU coverage/gap columns; cart_missingness sees availability only and no measured values; cart_common removes local HTTP and DNS probes. Strong missingness-only results reveal a shortcut in this controlled dataset, not fault diagnosis from symptoms.

19 FP candidates fitted on all pilot rows are training-only artifacts, distinct from fold models. Confidence/lift are not calibrated causal probabilities. No candidate is activated.

Prediction timings are tiny offline batches and exclude evidence collection/API time.
