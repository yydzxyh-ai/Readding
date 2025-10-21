# AI Reading Lab Makefile
# Provides commands for development, testing, and weekly processing

.PHONY: help install test test-quality lint format clean weekly quality-check

# Default target
help:
	@echo "AI Reading Lab - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install     - Install dependencies"
	@echo "  test        - Run all tests"
	@echo "  test-quality - Run quality and snapshot tests"
	@echo "  lint        - Run linting checks"
	@echo "  format      - Format code with black and ruff"
	@echo "  clean       - Clean temporary files"
	@echo ""
	@echo "Processing:"
	@echo "  weekly      - Run full weekly processing pipeline"
	@echo "  weekly-full - Run weekly pipeline with notifications"
	@echo "  quality-check - Run quality metrics and validation"
	@echo ""
	@echo "Individual Steps:"
	@echo "  ingest      - Extract text from documents (with OCR)"
	@echo "  summarize   - Generate JSON summaries"
	@echo "  aggregate   - Create weekly digest"
	@echo ""
	@echo "Advanced Features:"
	@echo "  crawl       - Download papers from arXiv/DOI"
	@echo "  notify      - Send notifications via Slack/Email"

# Installation
install:
	pip install -e ".[dev]"
	pre-commit install

# Testing
test:
	python3 -m pytest tests/ -v

test-quality:
	python3 -m pytest tests/test_snapshots.py tests/test_aggregate.py -v

# Code quality
lint:
	ruff check ai_lab/ tests/
	mypy ai_lab/

format:
	black ai_lab/ tests/
	ruff check --fix ai_lab/ tests/

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/

# Quality checks (pre-weekly validation)
quality-check: test-quality
	@echo "Running quality metrics validation..."
	@python3 -c "from ai_lab.utils import calculate_coverage_metrics, evaluate_summary_quality; print('✓ Quality metrics functions available')"
	@echo "✓ Quality check completed"

# Weekly processing pipeline
weekly: quality-check
	@echo "Starting weekly processing pipeline..."
	@echo "Step 1: Ingesting documents..."
	@python3 -m ai_lab.ingest --glob "data/**/*.pdf" --out data/extracts
	@echo "Step 2: Generating summaries..."
	@python3 -m ai_lab.summarize --glob "data/extracts/*.txt" --out summaries/json
	@echo "Step 3: Creating weekly digest..."
	@python3 -m ai_lab.aggregate --json_glob "summaries/json/*.json" --out summaries/WEEKLY_DIGEST.md --verbose
	@echo "✓ Weekly processing completed!"

# Individual processing steps
ingest:
	@echo "Ingesting documents from data/..."
	@python3 -m ai_lab.ingest --glob "data/**/*.pdf" --out data/extracts

summarize:
	@echo "Generating summaries from extracts..."
	@python3 -m ai_lab.summarize --glob "data/extracts/*.txt" --out summaries/json

aggregate:
	@echo "Creating weekly digest..."
	@python3 -m ai_lab.aggregate --json_glob "summaries/json/*.json" --out summaries/WEEKLY_DIGEST.md --verbose

# Advanced features
crawl:
	@echo "Crawling papers from arXiv/DOI..."
	@python3 -m ai_lab.crawl --file config/paper_ids.txt --output data/downloads --verbose

notify:
	@echo "Sending notifications..."
	@python3 -m ai_lab.notify --config config/notifications.json --digest summaries/WEEKLY_DIGEST.md

# Full pipeline with notifications
weekly-full: weekly notify
	@echo "✓ Full weekly pipeline with notifications completed"

# Development helpers
dev-setup: install
	@echo "Setting up development environment..."
	@mkdir -p data extracts summaries/json
	@echo "✓ Development environment ready"

# CI/CD helpers
ci-test: test lint
	@echo "✓ CI tests passed"

# Documentation
docs:
	@echo "Generating documentation..."
	@echo "# AI Reading Lab" > docs/README.md
	@echo "Generated on $$(date)" >> docs/README.md
	@echo "✓ Documentation generated"