# ChatAD - Document Crawling & Curation for AI Agents

Comprehensive web crawler and document curator for ADNI and other research websites. Extracts, organizes, and prepares documents for AI agent consumption.

## Project Structure

```
ChatAD/
├── crawlers/              # Crawler scripts for different websites
│   ├── adni.py           # ADNI website exhaustive crawler
│   └── adni_curate.py    # ADNI document curator (organizes by structure)
├── results/              # Final curated outputs ready for AI agents
│   └── adni.json        # ADNI documents organized by category (curated)
├── data/                 # Intermediate raw crawl data
│   └── adni_raw.json    # Raw crawl output from adni.py (uncurated)
├── .env                  # Environment variables (FIRECRAWL_API_KEY)
├── env.example           # Example environment file
└── README.md             # This file
```

## Data Flow

```
CRAWL PHASE (crawlers/adni.py)
    ↓
Raw output: data/adni_raw.json (331 documents, site structure preserved, includes meeting notes)
    ↓
CURATION PHASE (crawlers/adni_curate.py)
    ↓
Final output: results/adni.json (290 documents, organized by category, cleaned)
```

## Quick Start

### 1. Setup

```bash
# Install dependencies
uv sync

# Copy and configure environment
cp env.example .env
# Edit .env and add your FIRECRAWL_API_KEY
```

### 2. Crawl ADNI Website

```bash
# Exhaustively crawl ADNI and extract all documents
uv run python crawlers/adni.py

# Output: data/adni_raw.json (217KB)
# Contains 331 documents with titles extracted from website link text
```

### 3. Curate Documents

```bash
# Organize documents by ADNI website structure
# Removes meeting notes, categorizes into MRI/PET/Clinical/etc.
uv run python crawlers/adni_curate.py

# Output: results/adni.json (ready for AI agents)
# Contains 290 curated documents organized by category
```

## Output Structure

### `data/adni_raw.json` (Uncurated)

Raw crawl output with all discovered documents:

```json
{
  "metadata": {
    "total_links": 1115,
    "documents_count": 331,
    "pages_count": 784,
    "publications_filtered": 26
  },
  "documents": [
    {
      "url": "https://adni.loni.usc.edu/wp-content/themes/...",
      "title": "ADNI3 Sample Telephone Visit ICF v3.0 20210105 clean.pdf",
      "file_extension": "pdf",
      "ai_title": "ADNI3 Sample Telephone Visit ICF v3.0",
      "ai_description": "ADNI Document: ADNI3 Sample Telephone Visit ICF v3.0",
      "enhanced": true
    }
  ]
}
```

### `results/adni.json` (Curated)

Hierarchically organized with meeting notes removed:

```json
{
  "metadata": {
    "total_documents": 331,
    "organized_documents": 290,
    "skipped_documents": 41,
    "source": "ADNI website structure"
  },
  "documents_by_category": {
    "MRI Protocols": {
      "General": [...],
      "ADNI3": [...],
      "ADNI2/GO": [...],
      "ADNI1": [...]
    },
    "PET Protocols": {...},
    "Clinical Protocols": {...},
    "Consent Forms": {...},
    "Policies and Procedures": {...},
    "Biospecimen Protocols": {...}
  },
  "uncategorized": {
    "documents": [...],
    "count": 0
  },
  "skipped": {
    "documents": [...],  # Meeting notes, etc.
    "count": 41
  }
}
```

## Architecture

### Crawler Flow (`adni.py`)

1. **Map entire site** → Discover 800+ pages using Firecrawl MAP endpoint
2. **Scrape key pages** → Extract markdown from documentation pages  
3. **Parse markdown** → Extract document links with their link text
4. **Deduplicate** → Remove duplicates and publications
5. **Categorize** → Auto-categorize by document properties
6. **Output** → `data/adni_raw.json` (uncurated)

### Curation Flow (`adni_curate.py`)

1. **Load raw crawl** → Read `data/adni_raw.json`
2. **Match structure** → Map against ADNI website documentation structure
3. **Skip unwanted** → Remove meeting notes and non-document content
4. **Organize** → Create hierarchical structure by category
5. **Output** → `results/adni.json` (curated for AI agents)

## Extensibility

To add crawlers for other websites:

1. Create `crawlers/{site}.py` (e.g., `crawlers/clinicaltrials.py`)
2. Implement exhaustive crawling using Firecrawl
3. Extract meaningful titles/descriptions from website
4. Output to `data/{site}_raw.json`
5. Create `crawlers/{site}_curate.py` for organization
6. Output final result to `results/{site}.json`

## API Usage

Uses **Firecrawl API** for efficient web crawling:
- `MAP endpoint`: Discover all site pages (~1 credit per domain)
- `SCRAPE endpoint`: Extract content with markdown (~1 credit per page)
- Link text extraction: Uses markdown parsing, no extra credits

**Estimated cost for ADNI:**
- Map: 1 credit
- Scrape 59 key pages: 59 credits  
- Total: ~60 credits for complete ADNI document corpus

## Environment Variables

```bash
FIRECRAWL_API_KEY=your_api_key_here
```

Get API key from [firecrawl.dev](https://firecrawl.dev)

## Notes

- ✅ Removes duplicates automatically
- ✅ Filters out publications
- ✅ Uses website link text for AI-friendly titles
- ✅ Parallel processing for efficiency
- ✅ Two-step process: crawl → curate
- ✅ Scalable architecture for multiple data sources
- ✅ Preserves raw results for inspection/debugging
