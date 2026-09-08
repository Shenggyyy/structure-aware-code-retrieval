# Benchmark Suite Audit

Suite: `repository-suite-v1`; digest: `42f9000256c73dc9b9bd21f04046b41d2efcc6d79113cd839644ee55783f2e3d`.

No retrieval was executed. Annotation completeness is separate from source validation.

| Role | Queries | Judgments | Repositories | Annotation status |
| --- | --- | --- | --- | --- |
| dev | 40 | 55 | 2 | provisional |
| test | 120 | 164 | 5 | provisional |
| public | 10 | 10 | 1 | provisional |

## Indexed corpus sizes

| Repository | Files | Symbols | Chunks | SQLite bytes |
| --- | --- | --- | --- | --- |
| requests | 36 | 789 | 867 | 2748416 |
| click | 70 | 1452 | 1771 | 4476928 |
| flask | 82 | 1644 | 2030 | 4993024 |
| rich | 190 | 2206 | 2539 | 8474624 |
| networkx | 657 | 8184 | 9252 | 37695488 |
| packaging | 31 | 671 | 719 | 2334720 |
| tomlkit | 27 | 677 | 707 | 1830912 |
| marshmallow | 37 | 1757 | 2118 | 5165056 |

Annotation status is declared, not independently authenticated.
Repository disjointness and exact-text checks do not prove semantic independence or absence of model-training contamination.
Public adapted scores must be reported separately from the repository question benchmark.
