"""
OCR functionality for scanned PDFs using pytesseract and tesseract.

This module provides OCR capabilities for processing scanned PDFs that don't
contain extractable text. It uses tesseract-ocr for text recognition and
includes layout analysis for better text extraction.
"""

from __future__ import annotations
import io
import logging
from pathlib import Path
from typing import List, Optional, Tuple
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import cv2
import numpy as np

logger = logging.getLogger(__name__)

def check_tesseract_installation() -> bool:
    """Check if tesseract is installed and accessible."""
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception as e:
        logger.warning(f"Tesseract not found: {e}")
        return False

def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Preprocess image for better OCR results.
    
    Args:
        image: Input image as numpy array
        
    Returns:
        Preprocessed image
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # Apply denoising
    denoised = cv2.fastNlMeansDenoising(gray)
    
    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    
    # Morphological operations to clean up
    kernel = np.ones((1, 1), np.uint8)
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    return cleaned

def extract_text_with_layout(image: np.ndarray, lang: str = 'eng') -> str:
    """
    Extract text from image with layout analysis.
    
    Args:
        image: Input image as numpy array
        lang: Language code for tesseract
        
    Returns:
        Extracted text
    """
    try:
        # Preprocess image
        processed = preprocess_image(image)
        
        # Use tesseract with layout analysis
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,!?;:()[]{}"\' '
        text = pytesseract.image_to_string(processed, lang=lang, config=custom_config)
        
        return text.strip()
    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        return ""

def pdf_to_images(pdf_path: Path, dpi: int = 300) -> List[np.ndarray]:
    """
    Convert PDF pages to images.
    
    Args:
        pdf_path: Path to PDF file
        dpi: Resolution for image conversion
        
    Returns:
        List of images as numpy arrays
    """
    images = []
    try:
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Convert to image with high DPI
            mat = fitz.Matrix(dpi/72, dpi/72)
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            pil_image = Image.open(io.BytesIO(img_data))
            
            # Convert to numpy array
            img_array = np.array(pil_image)
            images.append(img_array)
        
        doc.close()
        return images
        
    except Exception as e:
        logger.error(f"PDF to image conversion failed: {e}")
        return []

def ocr_pdf(pdf_path: Path, lang: str = 'eng', dpi: int = 300) -> str:
    """
    Perform OCR on a scanned PDF file.
    
    Args:
        pdf_path: Path to PDF file
        lang: Language code for tesseract
        dpi: Resolution for image conversion
        
    Returns:
        Extracted text from all pages
    """
    if not check_tesseract_installation():
        raise RuntimeError("Tesseract is not installed. Please install tesseract-ocr.")
    
    logger.info(f"Starting OCR processing for {pdf_path}")
    
    # Convert PDF to images
    images = pdf_to_images(pdf_path, dpi)
    if not images:
        logger.warning(f"No images extracted from {pdf_path}")
        return ""
    
    # Extract text from each page
    all_text = []
    for i, image in enumerate(images):
        logger.info(f"Processing page {i+1}/{len(images)}")
        page_text = extract_text_with_layout(image, lang)
        if page_text:
            all_text.append(f"--- Page {i+1} ---\n{page_text}")
    
    full_text = "\n\n".join(all_text)
    logger.info(f"OCR completed. Extracted {len(full_text)} characters from {len(images)} pages")
    
    return full_text

def is_scanned_pdf(pdf_path: Path, threshold: float = 0.1) -> bool:
    """
    Determine if a PDF is scanned (image-based) rather than text-based.
    
    Args:
        pdf_path: Path to PDF file
        threshold: Minimum ratio of extractable text to consider as text-based
        
    Returns:
        True if PDF appears to be scanned
    """
    try:
        doc = fitz.open(pdf_path)
        total_text_length = 0
        total_pages = len(doc)
        
        for page_num in range(min(total_pages, 3)):  # Check first 3 pages
            page = doc.load_page(page_num)
            text = page.get_text()
            total_text_length += len(text.strip())
        
        doc.close()
        
        # If average text per page is very low, likely scanned
        avg_text_per_page = total_text_length / min(total_pages, 3)
        is_scanned = avg_text_per_page < threshold * 1000  # Less than 100 chars per page
        
        logger.info(f"PDF {pdf_path.name}: {avg_text_per_page:.1f} chars/page, {'scanned' if is_scanned else 'text-based'}")
        return is_scanned
        
    except Exception as e:
        logger.error(f"Error checking PDF type: {e}")
        return True  # Assume scanned if we can't determine

def extract_text_with_ocr_fallback(pdf_path: Path, lang: str = 'eng') -> str:
    """
    Extract text from PDF, using OCR if it appears to be scanned.
    
    Args:
        pdf_path: Path to PDF file
        lang: Language code for tesseract
        
    Returns:
        Extracted text
    """
    try:
        # First try normal text extraction
        doc = fitz.open(pdf_path)
        text = ""
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text() + "\n"
        
        doc.close()
        
        # If we got very little text, try OCR
        if len(text.strip()) < 100 or is_scanned_pdf(pdf_path):
            logger.info(f"PDF appears to be scanned, using OCR: {pdf_path}")
            return ocr_pdf(pdf_path, lang)
        else:
            logger.info(f"PDF is text-based, using normal extraction: {pdf_path}")
            return text
            
    except Exception as e:
        logger.error(f"Text extraction failed for {pdf_path}: {e}")
        # Fallback to OCR
        try:
            return ocr_pdf(pdf_path, lang)
        except Exception as ocr_error:
            logger.error(f"OCR fallback also failed: {ocr_error}")
            return ""
