import os
import sys
import json
import re
import fitz  # pip install pymupdf
from ebooklib import epub
from bs4 import BeautifulSoup


def extract_text_from_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text


def extract_text_from_epub(file_path):
    book = epub.read_epub(file_path)
    chapters = []
    for item in book.get_items():
        if item.get_type() == 9:  # 文本文档
            soup = BeautifulSoup(item.get_body_content(), "html.parser")
            chapters.append(soup.get_text())
    return "\n".join(chapters)


def split_text(text, max_length=5000):
    """将文本按长度切分"""
    chunks = []
    for i in range(0, len(text), max_length):
        chunks.append(text[i : i + max_length])
    return chunks


def detect_paper_sections(text):
    """基于关键词识别论文常见章节"""
    sections = {}
    patterns = [
        ("title", r"^(.*)\n"),  # 第一行标题
        ("abstract", r"abstract(.*?)(?=\n\s*(introduction|1\s))"),
        ("introduction", r"(introduction|1\sintroduction)(.*?)(?=\n\s*(method|2\s))"),
        (
            "method",
            r"(method|approach|2\smethod)(.*?)(?=\n\s*(experiment|results|3\s))",
        ),
        (
            "experiment",
            r"(experiment|results|evaluation|3\sexperiment)(.*?)(?=\n\s*(conclusion|discussion|4\s))",
        ),
        (
            "conclusion",
            r"(conclusion|discussion|summary)(.*?)(?=\n\s*(reference|bibliography))",
        ),
        ("references", r"(reference|bibliography)(.*)"),
    ]

    for name, pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            sections[name] = match.group(0).strip()
    return sections


def save_chunks(chunks, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    file_paths = []
    for i, chunk in enumerate(chunks, 1):
        file_path = os.path.join(output_dir, f"chunk_{i}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(chunk)
        file_paths.append(file_path)
    return file_paths


def main(file_path, output_dir="output_chunks", max_length=5000, mode="auto"):
    ext = os.path.splitext(file_path)[1].lower()

    # Step 1: 提取全文
    if ext == ".txt":
        text = extract_text_from_txt(file_path)
    elif ext == ".pdf":
        text = extract_text_from_pdf(file_path)
    elif ext == ".epub":
        text = extract_text_from_epub(file_path)
    else:
        print("❌ 不支持的文件格式，仅支持 .txt / .pdf / .epub")
        return

    # Step 2: 保存完整文本
    with open("book_clean.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print("📖 已保存完整文本到 book_clean.txt")

    # Step 3: 判断模式
    if mode == "auto" and ext == ".pdf":
        # 粗略假设 PDF 默认是论文
        mode = "paper"
    elif mode == "auto":
        mode = "book"

    toc = {}

    if mode == "paper":
        print("🔬 使用论文模式解析...")
        sections = detect_paper_sections(text)
        toc["sections"] = {}

        for sec_name, sec_text in sections.items():
            sec_dir = os.path.join(output_dir, sec_name)
            os.makedirs(sec_dir, exist_ok=True)
            chunks = split_text(sec_text, max_length=max_length)
            file_paths = save_chunks(chunks, sec_dir)
            toc["sections"][sec_name] = file_paths

        with open("toc.json", "w", encoding="utf-8") as f:
            json.dump(toc, f, indent=2, ensure_ascii=False)
        print("✅ 已生成 toc.json，包含章节目录")

    else:
        print("📚 使用书籍模式解析...")
        chunks = split_text(text, max_length=max_length)
        file_paths = save_chunks(chunks, output_dir)
        toc["sections"] = {"full_text": file_paths}
        with open("toc.json", "w", encoding="utf-8") as f:
            json.dump(toc, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "用法: python main.py <文件路径> [输出目录] [切分长度] [模式: book/paper/auto]"
        )
    else:
        file_path = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else "output_chunks"
        max_length = int(sys.argv[3]) if len(sys.argv) > 3 else 5000
        mode = sys.argv[4] if len(sys.argv) > 4 else "auto"
        main(file_path, output_dir, max_length, mode)
