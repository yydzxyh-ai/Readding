from __future__ import annotations
import argparse, json, pathlib, re
from tenacity import retry, wait_exponential, stop_after_attempt
from .config import get_llm_client, get_settings
from .models import Summary
from .utils import split_text

SYS_PROMPT = (
    "You are a careful research summarizer. Output STRICT JSON for the 'Summary' schema. "
    "Use short, specific sentences; include key numbers/findings; extract <=2 quotes (<=25 words). "
    "Keep 3-8 concise tags. Always include: title, tl_dr, contributions, methods, results, limitations."
)

MAP_PROMPT = "Summarize this chunk: local key claims, methods, results, limitations, useful quotes with spans."
REDUCE_PROMPT = "Merge chunk summaries into ONE final JSON Summary. Deduplicate; keep strongest findings and limits."

def extract_json_from_text(text: str) -> dict:
    """Extract JSON from text, handling cases where model doesn't use JSON mode."""
    # Try direct JSON parsing first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON block in markdown or other formats
    json_patterns = [
        r'```json\s*(\{.*?\})\s*```',
        r'```\s*(\{.*?\})\s*```',
        r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})',
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
    
    # If all else fails, return a minimal structure
    return {
        "title": "Failed to parse",
        "tl_dr": "JSON parsing failed",
        "contributions": [],
        "methods": [],
        "results": [],
        "limitations": [],
        "tags": [],
        "quotes": [],
        "references": []
    }

@retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
def call_json_llm(client, prompt: str, sys_prompt: str, max_tokens: int = 1200) -> dict:
    s = get_settings()
    
    # Try with JSON mode first
    try:
        rsp = client.chat.completions.create(
            model=s.model,
            messages=[{"role":"system","content":sys_prompt},{"role":"user","content":prompt}],
            temperature=s.temperature,
            response_format={"type":"json_object"},
            max_tokens=min(s.max_tokens, max_tokens),
        )
        return extract_json_from_text(rsp.choices[0].message.content)
    except (ValueError, KeyError, AttributeError):
        # Fallback without JSON mode
        rsp = client.chat.completions.create(
            model=s.model,
            messages=[{"role":"system","content":sys_prompt},{"role":"user","content":prompt}],
            temperature=s.temperature,
            max_tokens=min(s.max_tokens, max_tokens),
        )
        return extract_json_from_text(rsp.choices[0].message.content)

def validate_and_fix_summary(data: dict, source_path: str) -> dict:
    """Validate and fix summary data to ensure it matches Summary model."""
    # Ensure required fields exist
    data.setdefault('title', 'Untitled')
    data.setdefault('tl_dr', 'No summary available')
    data.setdefault('contributions', [])
    data.setdefault('methods', [])
    data.setdefault('results', [])
    data.setdefault('limitations', [])
    data.setdefault('tags', [])
    data.setdefault('quotes', [])
    data.setdefault('references', [])
    data.setdefault('authors', [])
    data.setdefault('source_path', source_path)
    
    # Ensure lists are actually lists
    for field in ['contributions', 'methods', 'results', 'limitations', 'tags', 'authors', 'references']:
        if not isinstance(data[field], list):
            data[field] = []
    
    # Ensure quotes are properly formatted
    if not isinstance(data['quotes'], list):
        data['quotes'] = []
    else:
        fixed_quotes = []
        for quote in data['quotes']:
            if isinstance(quote, dict):
                fixed_quotes.append({
                    'text': quote.get('text', ''),
                    'span': quote.get('span', None)
                })
            elif isinstance(quote, str):
                fixed_quotes.append({'text': quote, 'span': None})
        data['quotes'] = fixed_quotes
    
    return data

def summarize_one_text(path: pathlib.Path, out_dir: pathlib.Path) -> pathlib.Path:
    """Summarize a single text file using map-reduce approach."""
    text = path.read_text(encoding='utf-8', errors='ignore')
    if not text.strip():
        raise ValueError(f"Empty or invalid text file: {path}")
    
    chunks = split_text(text, max_chars=6000, overlap=400)
    if not chunks:
        raise ValueError(f"No valid chunks extracted from: {path}")
    
    client = get_llm_client()

    # Map phase: summarize each chunk
    partials = []
    for i, chunk in enumerate(chunks):
        try:
            obj = call_json_llm(
                client, 
                f"{MAP_PROMPT}\n\nCHUNK {i+1}/{len(chunks)}:\n{chunk}", 
                SYS_PROMPT
            )
            partials.append(obj)
        except (ValueError, RuntimeError, ConnectionError) as e:
            print(f"Warning: Failed to summarize chunk {i+1}: {e}")
            # Add minimal partial for failed chunk
            partials.append({
                "title": f"Chunk {i+1}",
                "tl_dr": "Failed to summarize",
                "contributions": [],
                "methods": [],
                "results": [],
                "limitations": [],
                "tags": [],
                "quotes": [],
                "references": []
            })

    # Reduce phase: merge partial summaries
    merged_in = json.dumps({"partials": partials}, ensure_ascii=False)
    final = call_json_llm(client, f"{REDUCE_PROMPT}\n\n{merged_in}", SYS_PROMPT)

    # Validate and fix the final summary
    final = validate_and_fix_summary(final, str(path))
    
    # Try to create Summary object for validation
    try:
        summary_obj = Summary(**final)
        final = json.loads(summary_obj.model_dump_json())
    except (ValueError, TypeError, KeyError) as e:
        print(f"Warning: Summary validation failed, using raw data: {e}")
        # Ensure we have at least a valid structure
        final = validate_and_fix_summary(final, str(path))

    # Write output
    out = out_dir / (path.stem + '.json')
    out.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding='utf-8')
    return out

def main():
    ap = argparse.ArgumentParser(description='Summarize extracted texts to structured JSON via LLM.')
    ap.add_argument('--glob', required=True, help="Glob of .txt extracts e.g. 'data/extracts/*.txt'")
    ap.add_argument('--out', required=True, help='Output dir for JSON summaries')
    ap.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = ap.parse_args()

    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    files = list(pathlib.Path().glob(args.glob))
    if not files:
        print(f"No files found matching pattern: {args.glob}")
        return
    
    print(f"Found {len(files)} files to process...")
    
    success_count = 0
    error_count = 0
    
    for i, p in enumerate(files, 1):
        if args.verbose:
            print(f"[{i}/{len(files)}] Processing: {p}")
        
        try:
            out = summarize_one_text(p, out_dir)
            print(f'✓ [{i}/{len(files)}] OK: {out.name}')
            success_count += 1
        except (ValueError, RuntimeError, ConnectionError, FileNotFoundError) as e:
            err = out_dir / (p.stem + '.error.log')
            err.write_text(f"Error processing {p}:\n{str(e)}", encoding='utf-8')
            print(f'✗ [{i}/{len(files)}] FAIL: {p.name} - {e}')
            error_count += 1
    
    print(f"\nSummary: {success_count} successful, {error_count} failed")
    if error_count > 0:
        print(f"Check {out_dir}/*.error.log for error details")

if __name__ == '__main__':
    main()
