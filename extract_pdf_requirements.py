#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF Requirements Extraction Script
Extracts text content from the Persian PDF document for analysis
"""

import pdfplumber
import sys
import os

def extract_pdf_text(pdf_path):
    """Extract text from PDF file"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text_content = []
            
            print(f"PDF has {len(pdf.pages)} pages")
            
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"Processing page {page_num}...")
                
                # Extract text from page
                page_text = page.extract_text()
                
                if page_text:
                    text_content.append(f"\n--- PAGE {page_num} ---\n")
                    text_content.append(page_text)
                    text_content.append("\n" + "="*50 + "\n")
                
                # Also try to extract tables if any
                tables = page.extract_tables()
                if tables:
                    text_content.append(f"\n--- TABLES ON PAGE {page_num} ---\n")
                    for i, table in enumerate(tables):
                        text_content.append(f"Table {i+1}:\n")
                        for row in table:
                            if row:
                                text_content.append(" | ".join([str(cell) if cell else "" for cell in row]))
                                text_content.append("\n")
                        text_content.append("\n")
            
            return "".join(text_content)
            
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return None

def main():
    # PDF file path
    pdf_path = "طرح آسود5-7.PDF"
    
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return
    
    print("Extracting text from PDF...")
    extracted_text = extract_pdf_text(pdf_path)
    
    if extracted_text:
        # Save extracted text to file
        output_file = "PDF_REQUIREMENTS_EXTRACTED.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
        
        print(f"Text extracted and saved to: {output_file}")
        print(f"Total characters extracted: {len(extracted_text)}")
        
        # Print first 2000 characters as preview
        print("\n--- PREVIEW (First 2000 characters) ---")
        print(extracted_text[:2000])
        print("...")
        
    else:
        print("Failed to extract text from PDF")

if __name__ == "__main__":
    main()