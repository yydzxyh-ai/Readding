# AI Reading Lab

> 面向 **Cursor** 的“读论文/书籍 → 总结归纳 → 代码生成/更新”的自动化框架。
> - 文档放 `data/`（PDF/Markdown/TXT）
> - `ai_lab/ingest.py` 抽取与切分
> - `ai_lab/summarize.py` 调用 LLM 生成 **结构化 JSON 摘要**
> - `ai_lab/aggregate.py` 生成 **WEEKLY_DIGEST.md**
> - GitHub Actions `.github/workflows/weekly_digest.yml` **每周定时**跑总结（需 `OPENAI_API_KEY`）
> - `prompts/` 内置 **Cursor 任务卡**（Task Recipes）和 **系统提示**

## 快速开始

### 开发环境初始化
```bash
# 1. 克隆仓库
git clone <repository-url>
cd ai-reading-lab

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -e ".[dev]"

# 4. 安装 pre-commit hooks
pre-commit install

# 5. 运行测试
pytest -q

# 6. 代码格式化检查
black --check .
ruff check .
mypy ai_lab/
```

### 环境变量配置
```bash
# 必需：OpenAI API 密钥
export OPENAI_API_KEY=sk-...

# 可选：模型配置
export OPENAI_MODEL=gpt-4o-mini  # 默认模型
export MAX_TOKENS=1200           # 默认最大 token 数
export TEMPERATURE=0.2           # 默认温度参数
```

### 使用

#### 快速开始
```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...  # 或在 GitHub Secrets 配置
python -m ai_lab.ingest --glob "data/**/*.pdf" --out data/extracts
python -m ai_lab.summarize --glob "data/extracts/*.txt" --out summaries/json
python -m ai_lab.aggregate --json_glob "summaries/json/*.json" --out summaries/WEEKLY_DIGEST.md
```

#### 使用 Makefile（推荐）
```bash
# 完整周报流程（包含质量检查）
make weekly

# 单独步骤
make ingest      # 文档抽取
make summarize   # 生成摘要
make aggregate   # 创建周报

# 质量检查
make quality-check  # 运行质量指标和快照测试
make test-quality   # 仅运行质量相关测试
```

### 质量检查流程

#### 自动化质量指标
系统内置了多种质量评估指标：

- **Faithfulness Proxy**: 评估摘要与原文的忠实度（基于词汇重叠）
- **Coverage Metrics**: 评估摘要的完整性和多样性
- **Field Completeness**: 检查必需字段的完整性
- **Content Richness**: 评估内容的丰富程度

#### 质量检查命令
```bash
# 运行所有质量检查
make quality-check

# 运行快照测试（确保输出一致性）
make test-quality

# 手动运行质量指标
python -c "
from ai_lab.utils import calculate_coverage_metrics, evaluate_summary_quality
# 使用示例...
"
```

#### CI/CD 集成

##### GitHub Actions 自动周报
- **定时执行**: 每周一 03:00 UTC（东京时间 12:00）自动运行
- **完整流程**: 安装依赖 → 质量检查 → 文档处理 → 生成周报 → 自动提交
- **质量验证**: 处理前自动运行快照测试和质量指标验证
- **自动提交**: 生成的周报自动提交到仓库

##### 配置 GitHub Secrets
在 GitHub 仓库设置中添加以下 Secrets：

1. **`OPENAI_API_KEY`**: OpenAI API 密钥
   ```
   sk-your-openai-api-key-here
   ```

2. **`GH_TOKEN`**: GitHub Personal Access Token（需要写权限）
   ```
   github_pat_your-token-here
   ```
   
   创建步骤：
   - 访问 GitHub Settings → Developer settings → Personal access tokens
   - 生成新 token，选择 `repo` 权限
   - 复制 token 并添加到仓库 Secrets

##### 本地定时任务
使用 `scripts/run_weekly.sh` 设置本地 cron：

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每周一 12:00 执行）
0 12 * * 1 /path/to/ai-reading-lab/scripts/run_weekly.sh

# 或者使用 Makefile
make weekly
```

**本地脚本选项**：
```bash
# 基本用法
./scripts/run_weekly.sh

# 详细输出
./scripts/run_weekly.sh --verbose

# 跳过 git 提交
./scripts/run_weekly.sh --no-commit

# 查看帮助
./scripts/run_weekly.sh --help
```

#### 本地开发
```bash
# 开发环境设置
make dev-setup

# 代码质量检查
make lint        # 代码风格检查
make format      # 自动格式化
make test        # 运行所有测试

# 清理
make clean       # 清理临时文件
```

## 高级功能

### OCR 扫描 PDF 处理
系统支持对扫描版 PDF 进行 OCR 文字识别：

```bash
# 安装 tesseract（系统依赖）
# macOS: brew install tesseract
# Ubuntu: sudo apt-get install tesseract-ocr
# Windows: 下载安装包

# 自动 OCR 处理（默认启用）
python -m ai_lab.ingest --glob "data/**/*.pdf" --out data/extracts

# 禁用 OCR（仅文本提取）
python -m ai_lab.ingest --glob "data/**/*.pdf" --out data/extracts --no-ocr
```

**OCR 特性**：
- 自动检测扫描版 PDF
- 图像预处理和版面识别
- 多语言支持（通过 tesseract 语言包）
- 高质量文字识别

### arXiv/DOI 论文抓取
自动从 arXiv 和 DOI 源抓取论文和元数据：

```bash
# 抓取单个论文
python -m ai_lab.crawl --identifiers "1912.07753" "10.1038/nature12373"

# 从文件批量抓取
python -m ai_lab.crawl --file config/paper_ids.txt --output data/downloads

# 设置请求延迟（遵守使用条款）
python -m ai_lab.crawl --identifiers "1912.07753" --delay 2.0
```

**抓取功能**：
- arXiv 论文下载和元数据提取
- DOI 论文查找和下载
- 自动重试和错误处理
- 遵守使用条款和频率限制
- 元数据保存（标题、作者、摘要等）

### 通知推送
支持 Slack 和 Email 通知：

```bash
# 发送周报摘要到 Slack
python -m ai_lab.notify --slack-webhook "https://hooks.slack.com/..." --digest summaries/WEEKLY_DIGEST.md

# 发送邮件通知
python -m ai_lab.notify --email-smtp smtp.gmail.com --email-user user@gmail.com --email-password app-password --email-from user@gmail.com --email-to recipient@example.com --digest summaries/WEEKLY_DIGEST.md

# 使用配置文件
python -m ai_lab.notify --config config/notifications.json --digest summaries/WEEKLY_DIGEST.md
```

**通知特性**：
- Slack Webhook 集成
- SMTP 邮件发送
- 摘要自动提取
- 附件发送
- 多通道配置

### 配置文件示例

#### 通知配置 (`config/notifications.json`)
```json
{
  "slack": [
    {
      "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
      "channel": "#research-digest"
    }
  ],
  "email": [
    {
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "username": "your-email@gmail.com",
      "password": "your-app-password",
      "from_email": "your-email@gmail.com",
      "to_emails": ["recipient@example.com"]
    }
  ]
}
```

#### 论文 ID 列表 (`config/paper_ids.txt`)
```
# arXiv 论文
1912.07753
2001.00001v1

# DOI 论文
10.1038/nature12373
10.1126/science.1234567
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
