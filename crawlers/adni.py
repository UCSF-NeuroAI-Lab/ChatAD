#!/usr/bin/env python3
"""
ADNI Exhaustive Crawler using Firecrawl API
Crawls the ENTIRE ADNI website to find ALL documents, excluding publications
"""

import os
import json
import requests
import re
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()

FIRECRAWL_API_KEY = os.getenv('FIRECRAWL_API_KEY')
headers = {
    "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
    "Content-Type": "application/json"
}

def crawl_entire_site():
    """Use Firecrawl to crawl the ENTIRE ADNI site and get all links"""
    print("=" * 70)
    print("🔥 EXHAUSTIVE ADNI CRAWLER - Using Firecrawl API")
    print("=" * 70)
    print()
    
    # Use Firecrawl's MAP endpoint to discover ALL pages
    print("🗺️ STEP 1: Mapping ENTIRE ADNI website...")
    map_url = "https://api.firecrawl.dev/v2/map"
    
    map_payload = {
        "url": "https://adni.loni.usc.edu",
        "limit": 5000,
        "includeSubdomains": False,
        "sitemap": "include"
    }
    
    response = requests.post(map_url, json=map_payload, headers=headers)
    map_result = response.json()
    
    print(f"🔍 Map API Response: {json.dumps(map_result, indent=2)}")
    
    if not map_result.get('success'):
        print(f"❌ Error mapping site: {map_result}")
        return []
    
    # Check different possible response structures
    if 'links' in map_result:
        all_site_links = map_result['links']
    elif 'data' in map_result and 'links' in map_result['data']:
        all_site_links = map_result['data']['links']
    elif 'data' in map_result and isinstance(map_result['data'], list):
        all_site_links = map_result['data']
    else:
        all_site_links = []
    print(f"✅ Discovered {len(all_site_links)} total pages on ADNI site")
    
    # Extract just URLs from the map result
    all_urls = []
    for link in all_site_links:
        if isinstance(link, dict):
            all_urls.append(link.get('url', ''))
        elif isinstance(link, str):
            all_urls.append(link)
    
    return all_urls

def filter_and_categorize_links(all_urls: List[str]) -> Dict:
    """Filter out publications and categorize remaining links"""
    print(f"\n🔍 STEP 2: Filtering and categorizing {len(all_urls)} links...")
    
    # Filter out publications
    filtered_urls = []
    publications_filtered = 0
    
    for url in all_urls:
        if any(term in url.lower() for term in ['publication', 'adni-publications', '/wp-content/uploads/papers/']):
            publications_filtered += 1
            continue
        filtered_urls.append(url)
    
    print(f"🚫 Filtered out {publications_filtered} publication links")
    print(f"📋 Remaining links: {len(filtered_urls)}")
    
    # Categorize by file type
    document_extensions = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'png', 'jpg'}
    
    documents = []
    pages = []
    
    for url in filtered_urls:
        # Check if it's a document
        is_document = False
        file_ext = None
        
        if '.' in url:
            parts = url.split('/')[-1].split('.')
            if len(parts) > 1:
                ext = parts[-1].lower().split('?')[0]  # Remove query params
                if ext in document_extensions:
                    is_document = True
                    file_ext = ext
        
        if is_document:
            # Extract filename for title
            filename = url.split('/')[-1].split('?')[0]
            title = filename.replace('%20', ' ').replace('_', ' ')
            
            documents.append({
                "url": url,
                "title": title,
                "file_extension": file_ext,
                "type": "document"
            })
        else:
            pages.append({
                "url": url,
                "type": "page"
            })
    
    print(f"\n📄 Found {len(documents)} DOCUMENTS")
    print(f"📑 Found {len(pages)} PAGES")
    
    return {
        "metadata": {
            "total_links": len(filtered_urls),
            "documents_count": len(documents),
            "pages_count": len(pages),
            "publications_filtered": publications_filtered,
            "source": "adni.loni.usc.edu"
        },
        "documents": documents,
        "pages": pages
    }

def enhance_documents_with_descriptions(organized_data: Dict) -> Dict:
    """Use Firecrawl scrape to get context/descriptions for each document"""
    print(f"\n🤖 STEP 3: Enhancing documents with AI-extracted descriptions...")
    
    documents = organized_data['documents']
    total_docs = len(documents)
    
    print(f"📄 Processing {total_docs} documents...")
    
    scrape_url = "https://api.firecrawl.dev/v2/scrape"
    
    enhanced_documents = []
    
    for i, doc in enumerate(documents, 1):
        if i % 10 == 0:
            print(f"  Progress: {i}/{total_docs} documents processed...")
        
        # Use Firecrawl to extract metadata
        scrape_payload = {
            "url": doc['url'],
            "formats": ["extract"],
            "extract": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"}
                    }
                }
            }
        }
        
        try:
            response = requests.post(scrape_url, json=scrape_payload, headers=headers, timeout=30)
            result = response.json()
            
            if result.get('success') and 'data' in result:
                extracted = result['data'].get('extract', {})
                doc['ai_title'] = extracted.get('title', '')
                doc['ai_description'] = extracted.get('description', '')
                doc['enhanced'] = True
            else:
                doc['enhanced'] = False
                
        except Exception as e:
            print(f"    ⚠️ Error enhancing {doc['url']}: {e}")
            doc['enhanced'] = False
        
        enhanced_documents.append(doc)
    
    organized_data['documents'] = enhanced_documents
    print(f"\n✅ Enhanced {sum(1 for d in enhanced_documents if d.get('enhanced'))} documents with AI descriptions")
    
    return organized_data

def save_results(data: Dict, filename: str = "data/adni_raw.json"):
    """Save results to JSON file"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"💾 Saved results to: {filename}")

def extract_links_with_titles_from_markdown(markdown: str) -> Dict[str, str]:
    """Extract links and their titles from markdown text"""
    link_titles = {}
    
    # Match markdown links: [text](url)
    pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    matches = re.findall(pattern, markdown)
    
    for link_text, url in matches:
        # Only store if it's a document URL
        if any(ext in url.lower() for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.png']):
            link_titles[url] = link_text.strip()
    
    return link_titles

def scrape_pages_for_documents(page_urls: List[str]) -> Dict[str, str]:
    """Scrape each page to find embedded document links"""
    print(f"\n🔍 STEP 2: Scraping pages to find embedded documents...")
    
    scrape_url = "https://api.firecrawl.dev/v2/scrape"
    link_titles_map = {}  # Map of URL -> link text from website
    
    # Focus on key pages that likely have documents, SKIP publications
    key_pages = []
    for url in page_urls:
        # Skip publications
        if any(term in url.lower() for term in ['publication', 'adni-publications']):
            continue
        # Include pages likely to have documents
        if any(term in url.lower() for term in [
            'documentation', 'help-faqs', 'data-samples', 'governance', 'about', 'methods'
        ]):
            key_pages.append(url)
    
    print(f"📄 Scraping {len(key_pages)} key content pages for document links...")
    
    for i, page_url in enumerate(key_pages, 1):
        if i % 10 == 0:
            print(f"  Progress: {i}/{len(key_pages)} pages scraped...")
        
        scrape_payload = {
            "url": page_url,
            "formats": ["markdown"]  # Get markdown to extract link text
        }
        
        try:
            response = requests.post(scrape_url, json=scrape_payload, headers=headers, timeout=30)
            result = response.json()
            
            if result.get('success') and 'data' in result:
                markdown = result['data'].get('markdown', '')
                
                # Extract document links with their titles from markdown
                page_link_titles = extract_links_with_titles_from_markdown(markdown)
                link_titles_map.update(page_link_titles)
                
        except Exception as e:
            print(f"    ⚠️ Error scraping {page_url}: {e}")
            continue
    
    print(f"✅ Extracted {len(link_titles_map)} document links with titles from content pages")
    return link_titles_map

def main():
    # Step 1: Map site to discover all pages
    all_page_urls = crawl_entire_site()
    
    if not all_page_urls:
        print("❌ Failed to crawl site")
        return
    
    # Step 2: Scrape key pages to find embedded documents WITH their link text
    link_titles_map = scrape_pages_for_documents(all_page_urls)  # Dict of URL -> title
    
    # Step 3: Filter and categorize all links (pages + embedded documents)
    all_urls = list(set(all_page_urls + list(link_titles_map.keys())))
    print(f"\n📊 Total unique links after combining: {len(all_urls)}")
    
    organized_data = filter_and_categorize_links(all_urls)
    
    # Step 4: Add the link text as ai_title for documents
    print(f"\n✨ Adding website link text as document titles...")
    for doc in organized_data.get('documents', []):
        url = doc['url']
        if url in link_titles_map:
            doc['ai_title'] = link_titles_map[url]
            doc['ai_description'] = f"ADNI Document: {link_titles_map[url]}"
            doc['enhanced'] = True
    
    enhanced_count = sum(1 for d in organized_data.get('documents', []) if d.get('enhanced'))
    print(f"✅ Enhanced {enhanced_count} documents with website link text")
    
    organized_data['metadata']['enhanced_from_website'] = True
    organized_data['metadata']['enhanced_count'] = enhanced_count
    
    # Save results
    save_results(organized_data)
    
    # Print summary
    print(f"\n" + "=" * 70)
    print("🎉 EXHAUSTIVE CRAWL COMPLETE!")
    print("=" * 70)
    print(f"📄 Total Documents: {organized_data['metadata']['documents_count']}")
    print(f"📑 Total Pages: {organized_data['metadata']['pages_count']}")
    print(f"🚫 Publications Filtered: {organized_data['metadata']['publications_filtered']}")
    print(f"\n🤖 Documents are ready for AI agents!")
    print(f"💾 Saved to: data/adni_raw.json")

if __name__ == "__main__":
    main()

