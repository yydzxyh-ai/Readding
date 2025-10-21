# Cursor Rules（项目规则）
- **目标**：把 PDF/MD 文档自动抽取→分块→LLM 摘要（JSON）→周报汇总。
- **代码规范**：Python 3.11；类型注解；`ruff + black`；`pytest` 覆盖核心函数。
- **架构**：`ai_lab/` 下模块化：config/models/utils/ingest/summarize/aggregate。
- **错误处理**：CLI 用 `argparse`；单文件失败写 `*.error.log`，不中断批次。
- **LLM 调用**：统一走 `ai_lab.config.get_llm_client()` 与环境变量；优先 JSON 输出。
- **安全**：不执行文档代码；外部请求有超时与重试；禁止硬编码密钥。
- **测试**：先写测试后重构；对 `split_text`/`merge_json_summaries` 建单测。
- **提交**：新增依赖需更新 `requirements.txt` 与 README。
