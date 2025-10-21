# Cursor Task Recipes（逐步粘贴执行）

## Task 1 — Bootstrap & Lint/Test
1) 读取 `prompts/CURSOR_RULES.md`；
2) 生成 `pyproject.toml`（black/ruff/mypy/pytest）；
3) 在 `tests/` 增加 `test_ingest.py`（对 `split_text` 的长度与重叠断言）；
4) 生成 `pre-commit` 并更新 README 安装步骤。

## Task 2 — Ingestion & Chunking
- 完善 `ai_lab/ingest.py`：
  - `extract_text_from_pdf(path)`, `extract_from_md_or_txt(path)`, `split_text(text, max_chars=6000, overlap=400)`
  - 输出 `data/extracts/<stem>.txt` 与 `<stem>.meta.json`；失败写 `<stem>.error.log`。

## Task 3 — LLM Summarization(JSON)
- 完善 `ai_lab/summarize.py`：实现 map-reduce：chunk→局部摘要→合并→全局摘要；
- 严格输出 `models.Summary` JSON（title/authors/year/tl_dr/contributions/methods/results/limitations/tags/quotes/references/source_path）。

## Task 4 — Aggregation & Digest
- 完善 `ai_lab/aggregate.py`：
  - `merge_json_summaries(glob)` 收集列表；
  - `render_markdown_digest(items)` 生成 `summaries/WEEKLY_DIGEST.md`（带目录、分组、来源路径）。

## Task 5 — Evaluations & Regression
- 在 `ai_lab/utils.py` 添加 `faithfulness_proxy` 与覆盖率占位指标；
- 在 `tests/` 增加对 `merge_json_summaries` 的快照测试。

## Task 6 — CI / Scheduler
- 完成 `.github/workflows/weekly_digest.yml`：
  - cron: `0 3 * * 1`（UTC，每周一，等于东京 12:00）；
  - 安装→三步 CLI→提交 `summaries/` 更新（需 `OPENAI_API_KEY` + `GH_TOKEN`）。

## 可选 Task X — 增强
- 扫描版 PDF 的 OCR（pytesseract + tesseract）；
- arXiv/DOI 抓取器（遵守版权/使用条款）；
- 发送周报到 Slack/Email（webhook/SMTP）。
