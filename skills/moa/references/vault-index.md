# moa → 联邦储藏库指针

联邦储藏库（各工坊技能清单）由 `docs\vault_scan.py` 自动生成：
- 人读版：`docs\FED_VAULT.md`
- 机读版：`skills/vault_index.json`（供总台 :8800 / 座舱 :8765 渲染）

三大域：技能工坊（skills/）· 沙盒考场（fed-testbed）· 题库与评测（eval_golden + llm_bench）。

新增资产后重跑 `py vault_scan.py` 刷新索引；呈现层（总台"储藏库 Tab"）由 UI 席按 vault_index.json 渲染。
