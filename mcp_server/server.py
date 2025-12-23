#!/usr/bin/env python3
"""
ADNI MCP Server - Exposes ADNI documentation catalog and PDF content as MCP resources
Enables AI assistants to search and retrieve ADNI documents
"""

import os
import json
import hashlib
import requests
from pathlib import Path
from urllib.parse import unquote, quote
from PyPDF2 import PdfReader
from io import BytesIO

from mcp.server.fastmcp import FastMCP

# Paths
BASE_DIR = Path(__file__).parent.parent
CATALOG_PATH = BASE_DIR / "results" / "adni.json"
PDF_CACHE_DIR = BASE_DIR / "data" / "pdf_cache"

# Ensure cache directory exists
PDF_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Initialize FastMCP server
mcp = FastMCP("adni-docs")

# Resources (for Cursor to browse)
@mcp.resource("adni://catalog")
def get_catalog_resource() -> str:
    """Complete ADNI document catalog"""
    with open(CATALOG_PATH, 'r') as f:
        catalog = json.load(f)
    return json.dumps(catalog, indent=2)

@mcp.resource("adni://mri-protocols")
def get_mri_protocols_resource() -> str:
    """MRI protocol documents"""
    with open(CATALOG_PATH, 'r') as f:
        catalog = json.load(f)
    
    filtered = {
        "category": "MRI Protocols",
        "documents": catalog.get("documents_by_category", {}).get("MRI Protocols", {})
    }
    return json.dumps(filtered, indent=2)

@mcp.resource("adni://pet-protocols")
def get_pet_protocols_resource() -> str:
    """PET protocol documents"""
    with open(CATALOG_PATH, 'r') as f:
        catalog = json.load(f)
    
    filtered = {
        "category": "PET Protocols",
        "documents": catalog.get("documents_by_category", {}).get("PET Protocols", {})
    }
    return json.dumps(filtered, indent=2)

@mcp.resource("adni://clinical-protocols")
def get_clinical_protocols_resource() -> str:
    """Clinical protocol documents"""
    with open(CATALOG_PATH, 'r') as f:
        catalog = json.load(f)
    
    filtered = {
        "category": "Clinical Protocols",
        "documents": catalog.get("documents_by_category", {}).get("Clinical Protocols", {})
    }
    return json.dumps(filtered, indent=2)

@mcp.resource("adni://consent-forms")
def get_consent_forms_resource() -> str:
    """Consent form documents"""
    with open(CATALOG_PATH, 'r') as f:
        catalog = json.load(f)
    
    filtered = {
        "category": "Consent Forms",
        "documents": catalog.get("documents_by_category", {}).get("Consent Forms", {})
    }
    return json.dumps(filtered, indent=2)

# Tools (for agents to call)

@mcp.tool()
def fetch_pdf(url: str) -> str:
    """
    Fetch and extract text content from an ADNI PDF document.
    
    Args:
        url: The full URL of the PDF document from the catalog
    
    Returns:
        JSON containing the PDF text content with citation
    """
    with open(CATALOG_PATH, 'r') as f:
        catalog = json.load(f)
    
    return fetch_pdf_content(url, catalog)

def fetch_pdf_content(url: str, catalog: dict) -> str:
    """Fetch and extract PDF text content with caching"""
    
    # Find document metadata from catalog
    doc_info = None
    for doc in catalog.get("documents", []):
        if doc.get("url") == url:
            doc_info = doc
            break
    
    # Generate cache filename from URL hash
    url_hash = hashlib.md5(url.encode()).hexdigest()
    cache_file = PDF_CACHE_DIR / f"{url_hash}.txt"
    
    # Check cache first
    if cache_file.exists():
        with open(cache_file, 'r', encoding='utf-8') as f:
            cached_content = f.read()
        
        # Return first 50,000 chars to avoid huge responses
        content_preview = cached_content[:50000]
        if len(cached_content) > 50000:
            content_preview += f"\n\n[... Content truncated. Full document has {len(cached_content)} characters ...]"
        
        result = {
            "title": doc_info.get("ai_title", "") if doc_info else "",
            "url": url,
            "cached": True,
            "content": content_preview,
            "citation": f"Source: {doc_info.get('ai_title', url)} - {url}" if doc_info else f"Source: {url}"
        }
        return json.dumps(result, indent=2)
    
    # Download PDF
    try:
        response = requests.get(url, timeout=60, stream=True)
        response.raise_for_status()
        
        # Extract text from PDF
        pdf_file = BytesIO(response.content)
        reader = PdfReader(pdf_file)
        
        text_content = []
        # Limit to first 20 pages to avoid timeouts
        max_pages = min(20, len(reader.pages))
        
        for page_num in range(max_pages):
            page = reader.pages[page_num]
            text = page.extract_text()
            if text.strip():
                text_content.append(f"[Page {page_num + 1}]\n{text}")
        
        full_text = "\n\n".join(text_content)
        
        if len(reader.pages) > max_pages:
            full_text += f"\n\n[... Showing first {max_pages} of {len(reader.pages)} pages ...]"
        
        # Cache the extracted text
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        # Return first 50,000 chars
        content_preview = full_text[:50000]
        if len(full_text) > 50000:
            content_preview += f"\n\n[... Content truncated. Full document has {len(full_text)} characters ...]"
        
        result = {
            "title": doc_info.get("ai_title", "") if doc_info else "",
            "url": url,
            "cached": False,
            "pages": len(reader.pages),
            "pages_extracted": max_pages,
            "content": content_preview,
            "citation": f"Source: {doc_info.get('ai_title', url)} - {url}" if doc_info else f"Source: {url}"
        }
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to fetch PDF: {str(e)}",
            "url": url
        })

if __name__ == "__main__":
    # FastMCP handles the server loop automatically
    mcp.run()


