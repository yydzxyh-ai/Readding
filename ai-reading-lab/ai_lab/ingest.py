from __future__ import annotations
import argparse, json, pathlib
import fitz  # PyMuPDF
from .utils import clean_text

# Optional OCR import
try:
    from .ocr import extract_text_with_ocr_fallback
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

def extract_text_from_pdf(path: str, use_ocr: bool = True) -> str:
    """
    Extract text from PDF, using OCR if needed.
    
    Args:
        path: Path to PDF file
        use_ocr: Whether to use OCR for scanned PDFs
        
    Returns:
        Extracted text
    """
    if use_ocr and OCR_AVAILABLE:
        return extract_text_with_ocr_fallback(pathlib.Path(path))
    elif use_ocr and not OCR_AVAILABLE:
        print("Warning: OCR requested but pytesseract not available. Using text extraction only.")
    
    # Original method without OCR (fallback or when OCR disabled)
    doc = fitz.open(path)
    texts = [page.get_text('text') for page in doc]
    doc.close()
    return "\n".join(texts)

def extract_from_md_or_txt(path: str) -> str:
    return pathlib.Path(path).read_text(encoding='utf-8', errors='ignore')

def main():
    ap = argparse.ArgumentParser(description='Extract & normalize text from PDFs/MD/TXT.')
    ap.add_argument('--glob', required=True, help="Glob pattern e.g. 'data/**/*.pdf'")
    ap.add_argument('--out', required=True, help='Directory for extracts')
    ap.add_argument('--no-ocr', action='store_true', help='Disable OCR for scanned PDFs')
    ap.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = ap.parse_args()

    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    files = [p for p in pathlib.Path().glob(args.glob)]
    
    if not files:
        print(f"No files found matching pattern: {args.glob}")
        return
    
    print(f"Found {len(files)} files to process...")
    
    ok, fail = 0, 0
    for i, p in enumerate(files, 1):
        if args.verbose:
            print(f"[{i}/{len(files)}] Processing: {p}")
        
        stem = p.stem
        txt_out = out_dir / f'{stem}.txt'
        meta_out = out_dir / f'{stem}.meta.json'
        err_out = out_dir / f'{stem}.error.log'
        
        try:
            if p.suffix.lower() == '.pdf':
                raw = extract_text_from_pdf(str(p), use_ocr=not args.no_ocr)
            else:
                raw = extract_from_md_or_txt(str(p))
            
            cleaned = clean_text(raw)
            txt_out.write_text(cleaned, encoding='utf-8')
            
            # Enhanced metadata
            metadata = {
                'source_path': str(p),
                'extraction_method': 'ocr' if (p.suffix.lower() == '.pdf' and not args.no_ocr) else 'text',
                'text_length': len(cleaned),
                'processed_at': pathlib.Path().cwd().name  # Simple timestamp placeholder
            }
            
            meta_out.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
            ok += 1
            
            if args.verbose:
                print(f"  ✓ Extracted {len(cleaned)} characters")
                
        except Exception as e:
            err_out.write_text(str(e), encoding='utf-8')
            fail += 1
            if args.verbose:
                print(f"  ✗ Failed: {e}")
    
    print(f'Extracted {ok} OK, {fail} failed.')

if __name__ == '__main__':
    main()
