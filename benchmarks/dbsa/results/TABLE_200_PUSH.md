# DBSA-v1 200-seed exact results (after push)

Run: 200 seeds × 800 events × 6 worlds. Gate: **PASS**.
Artifact: `dbsa_v1_contract_200_push.json`.

## Primary score (Brier — lower is better)

| World | Persistence | Majority | Fixed-Share | AdaHedge | Fading Bayes | Agree-discount Bayes | ACI | Aware |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| independent_stable | 0.2878 | 0.0758 | 0.0967 | 0.1629 | **0.0360** | 0.0409 | 0.0894 | 0.0842 |
| correlated_stable | 0.2871 | **0.1000** | 0.1266 | 0.1853 | 0.1038 | 0.1111 | 0.1551 | 0.1271 |
| abrupt_drift | 0.2887 | 0.0896 | 0.0483 | 0.2136 | **0.0273** | 0.0290 | 0.0465 | 0.0437 |
| recurring_crossover | 0.2883 | 0.0957 | 0.0638 | 0.2248 | **0.0539** | 0.0551 | 0.0648 | 0.0625 |
| adversarial_switch | 0.2893 | 0.1171 | 0.0963 | 0.2023 | **0.0331** | 0.0348 | 0.0686 | 0.0647 |
| bursty_missing | 0.2905 | 0.0815 | 0.1092 | 0.1761 | **0.0513** | 0.0606 | 0.0968 | 0.0865 |

## Aware vs Fixed-Share (gate comparator)

| World | Aware Brier | Fixed-Share | Δ (Aware−FS) | CI 97.5% upper | Pass δ=0.005 | Aware post-shift | FS post-shift |
|---|---:|---:|---:|---:|---|---:|---:|
| independent_stable | 0.0842 | 0.0967 | -0.0126 | -0.0118 | yes | — | — |
| correlated_stable | 0.1271 | 0.1266 | +0.0005 | +0.0013 | yes | — | — |
| abrupt_drift | 0.0437 | 0.0483 | -0.0046 | -0.0041 | yes | 0.0757 | 0.0763 |
| recurring_crossover | 0.0625 | 0.0638 | -0.0014 | -0.0008 | yes | 0.0823 | 0.0824 |
| adversarial_switch | 0.0647 | 0.0963 | -0.0316 | -0.0308 | yes | 0.1047 | 0.1584 |
| bursty_missing | 0.0865 | 0.1092 | -0.0227 | -0.0219 | yes | — | — |

## Accuracy / flip recall / false alarms / calibration / sparsity

| World | Method | Acc | Flip recall | False alarm | ECE | Used | Events/s |
|---|---|---:|---:|---:|---:|---:|---:|
| independent_stable | Persistence | 0.701 | 0.119 | 0.112 | 0.280 | 12.00 | 119375 |
| independent_stable | Majority | 0.958 | 0.957 | 0.040 | 0.193 | 12.00 | 89654 |
| independent_stable | Fixed-Share | 0.875 | 0.873 | 0.121 | 0.086 | 12.00 | 17629 |
| independent_stable | AdaHedge | 0.788 | 0.784 | 0.207 | 0.112 | 12.00 | 11116 |
| independent_stable | Fading Bayes | 0.949 | 0.953 | 0.043 | 0.021 | 12.00 | 19360 |
| independent_stable | Agree-discount Bayes | 0.949 | 0.953 | 0.043 | 0.061 | 12.00 | 14460 |
| independent_stable | ACI | 0.904 | 0.888 | 0.081 | 0.109 | 5.03 | 1449 |
| independent_stable | Aware | 0.915 | 0.904 | 0.071 | 0.106 | 5.13 | 1036 |
| correlated_stable | Persistence | 0.701 | 0.116 | 0.113 | 0.279 | 12.00 | 119164 |
| correlated_stable | Majority | 0.870 | 0.870 | 0.124 | 0.091 | 12.00 | 89150 |
| correlated_stable | Fixed-Share | 0.812 | 0.811 | 0.182 | 0.038 | 12.00 | 17622 |
| correlated_stable | AdaHedge | 0.771 | 0.768 | 0.221 | 0.156 | 12.00 | 11084 |
| correlated_stable | Fading Bayes | 0.861 | 0.867 | 0.128 | 0.084 | 12.00 | 19322 |
| correlated_stable | Agree-discount Bayes | 0.861 | 0.867 | 0.128 | 0.092 | 12.00 | 14403 |
| correlated_stable | ACI | 0.796 | 0.734 | 0.173 | 0.125 | 2.28 | 1536 |
| correlated_stable | Aware | 0.855 | 0.818 | 0.122 | 0.094 | 2.56 | 1060 |
| abrupt_drift | Persistence | 0.700 | 0.118 | 0.113 | 0.281 | 12.00 | 118834 |
| abrupt_drift | Majority | 0.950 | 0.949 | 0.048 | 0.214 | 12.00 | 89174 |
| abrupt_drift | Fixed-Share | 0.940 | 0.940 | 0.058 | 0.063 | 12.00 | 17593 |
| abrupt_drift | AdaHedge | 0.745 | 0.741 | 0.252 | 0.184 | 12.00 | 11097 |
| abrupt_drift | Fading Bayes | 0.962 | 0.968 | 0.030 | 0.020 | 12.00 | 19312 |
| abrupt_drift | Agree-discount Bayes | 0.962 | 0.968 | 0.030 | 0.028 | 12.00 | 14428 |
| abrupt_drift | ACI | 0.958 | 0.960 | 0.032 | 0.121 | 4.00 | 1466 |
| abrupt_drift | Aware | 0.964 | 0.967 | 0.027 | 0.119 | 4.04 | 1046 |
| recurring_crossover | Persistence | 0.701 | 0.118 | 0.113 | 0.280 | 12.00 | 118373 |
| recurring_crossover | Majority | 0.941 | 0.940 | 0.056 | 0.215 | 12.00 | 89033 |
| recurring_crossover | Fixed-Share | 0.916 | 0.913 | 0.082 | 0.056 | 12.00 | 17599 |
| recurring_crossover | AdaHedge | 0.729 | 0.720 | 0.266 | 0.192 | 12.00 | 11110 |
| recurring_crossover | Fading Bayes | 0.930 | 0.935 | 0.063 | 0.038 | 12.00 | 19316 |
| recurring_crossover | Agree-discount Bayes | 0.930 | 0.935 | 0.063 | 0.033 | 12.00 | 14436 |
| recurring_crossover | ACI | 0.937 | 0.936 | 0.052 | 0.113 | 4.15 | 1465 |
| recurring_crossover | Aware | 0.942 | 0.942 | 0.047 | 0.112 | 4.19 | 1046 |
| adversarial_switch | Persistence | 0.700 | 0.117 | 0.113 | 0.282 | 12.00 | 118411 |
| adversarial_switch | Majority | 0.881 | 0.875 | 0.116 | 0.168 | 12.00 | 89173 |
| adversarial_switch | Fixed-Share | 0.865 | 0.865 | 0.133 | 0.053 | 12.00 | 17615 |
| adversarial_switch | AdaHedge | 0.768 | 0.763 | 0.228 | 0.180 | 12.00 | 11123 |
| adversarial_switch | Fading Bayes | 0.954 | 0.959 | 0.038 | 0.022 | 12.00 | 19328 |
| adversarial_switch | Agree-discount Bayes | 0.954 | 0.959 | 0.038 | 0.034 | 12.00 | 14441 |
| adversarial_switch | ACI | 0.927 | 0.919 | 0.061 | 0.096 | 4.81 | 1454 |
| adversarial_switch | Aware | 0.935 | 0.930 | 0.054 | 0.094 | 4.88 | 1039 |
| bursty_missing | Persistence | 0.698 | 0.118 | 0.115 | 0.282 | 9.24 | 118972 |
| bursty_missing | Majority | 0.940 | 0.940 | 0.058 | 0.171 | 9.24 | 92545 |
| bursty_missing | Fixed-Share | 0.847 | 0.846 | 0.149 | 0.046 | 9.24 | 18988 |
| bursty_missing | AdaHedge | 0.780 | 0.775 | 0.214 | 0.138 | 9.24 | 12879 |
| bursty_missing | Fading Bayes | 0.929 | 0.935 | 0.062 | 0.026 | 9.24 | 23353 |
| bursty_missing | Agree-discount Bayes | 0.929 | 0.935 | 0.062 | 0.083 | 9.24 | 17373 |
| bursty_missing | ACI | 0.895 | 0.879 | 0.090 | 0.127 | 4.85 | 1813 |
| bursty_missing | Aware | 0.916 | 0.908 | 0.070 | 0.118 | 5.04 | 1271 |
