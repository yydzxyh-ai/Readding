# AI Reading Lab

> 面向 **Cursor** 的“读论文/书籍 → 总结归纳 → 代码生成/更新”的自动化框架。
> - 文档放 `data/`（PDF/Markdown/TXT）
> - `ai_lab/ingest.py` 抽取与切分
> - `ai_lab/summarize.py` 调用 LLM 生成 **结构化 JSON 摘要**
> - `ai_lab/aggregate.py` 生成 **WEEKLY_DIGEST.md**
> - GitHub Actions `.github/workflows/weekly_digest.yml` **每周定时**跑总结（需 `OPENAI_API_KEY`）
> - `prompts/` 内置 **Cursor 任务卡**（Task Recipes）和 **系统提示**

## 快速开始
```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...  # 或在 GitHub Secrets 配置
python -m ai_lab.ingest --glob "data/**/*.pdf" --out data/extracts
python -m ai_lab.summarize --glob "data/extracts/*.txt" --out summaries/json
python -m ai_lab.aggregate --json_glob "summaries/json/*.json" --out summaries/WEEKLY_DIGEST.md
```

## 目录
```
ai-reading-lab/
  ai_lab/
    __init__.py
    config.py
    models.py
    ingest.py
    summarize.py
    aggregate.py
    utils.py
  prompts/
    CURSOR_RULES.md
    agent_system_prompt.md
    cursor_task_recipes.md
  data/              # 你的 PDF/MD/TXT 放这里
  summaries/         # 生成的 JSON/周报
  scripts/
    run_weekly.sh
  tests/
    test_ingest.py
  .github/workflows/weekly_digest.yml
  requirements.txt
  Makefile
  README.md
```
