#!/usr/bin/env python3
"""
Curate ADNI documents by organizing them according to the ADNI website structure
Removes meeting notes and organizes into hierarchical categories
"""

import json
import os
from typing import Dict, List, Tuple

# Define ADNI documentation structure from the website
ADNI_STRUCTURE = {
    "MRI Protocols": {
        "General": ["ADNI MRI Overview", "ADNI MRI Method for Non-ADNI Studies", "MRI Acquisition Table"],
        "ADNI3": ["ADNI3 MRI Analysis Manual", "ADNI3 MRI Technical Manual", "ADNI 3 MRI Protocols Quick Guide", "ADNI3 MRI Scanner Protocols"],
        "ADNI2/GO": ["ADNI GO MRI Technical Procedures", "ADNI GO/2 MRI Training Manual", "ADNI 2 MRI Technical Procedures", "ADNI2/GO MRI Scanner Protocols"],
        "ADNI1": ["ADNI 1 MRI Technical Procedures", "ADNI MRI Core Protocol Selection Summary", "ADNI1 MRI Scanner Protocols", "ADNI1 Standardized MRI Collections", "ADNI1 MRI Processed Image Types"]
    },
    "PET Protocols": {
        "General": ["ADNI 1 PET Technical Procedures", "PET PIB Technical Manual", "ADNI GO PET Technical Procedures", "ADNI 2 PET Technical Procedures", "ADNI 3 PET Technical Manual", "ADNI Centiloids"]
    },
    "Clinical Protocols": {
        "ADNI1": ["ADNI 1 Clinical Protocols"],
        "ADNI GO": ["ADNI GO Clinical Protocols"],
        "ADNI2": ["ADNI 2 Clinical Protocols"],
        "ADNI3": ["ADNI 3 Clinical Protocols"]
    },
    "Biospecimen Protocols": {
        "CSF": ["CSF Biomarker Test Instructions", "Lumbar Puncture Protocol"],
        "Brain Tissue": ["Neuropathology Sort Protocol", "Neuropathology Manual"],
        "Samples": ["ADNI3 Biomarker Sample Collection", "Genetics Sample Collection", "Biofluid Collections"]
    },
    "Policies and Procedures": {
        "General": ["Data Sharing and Publication Policy", "ADNI Data Use Agreement", "ADNI Manuscript Citations", "ADNI Acknowledgement List", "Groups Acknowldgements", "Access to ADNI Samples", "ADNI RARC Biomarker Application", "ADNI RARC Biomarker Policies"]
    },
    "Consent Forms": {
        "ADNI4": ["ADNI4 Clinical To Digital Study Partner", "ADNI4 Remote Blood Cohort", "ADNI4 Remote Digital Cohort", "ADNI4 Remote Digital Study Partner", "ADNI4 Clinical To Digital Monitoring", "New Participant ICF", "Rollover Participant ICF", "Study Partner ICF", "Telephone Visit ICF", "Amyloid PET Scan"],
        "ADNI3": ["ADNI3 ProtocolVersion", "ADNI3_Sample_Early Frames", "ADNI3_Sample_Brain Donation", "ADNI3 Sample New Subject", "ADNI3 Sample_Rollover Subject", "ADNI3 Sample Telephone Visit Addendum", "ADNI3 Sample Telephone Visit ICF", "ADNI3 Schedule of Activites"],
        "ADNI2": ["ADNI2 Sample New Subjects", "ADNI2 Sample Follow-up Subjects"]
    }
}

def categorize_document(doc_title: str, doc_url: str) -> Tuple:
    """
    Categorize a document based on its title and URL.
    Returns (category, subcategory) or (None, None) to skip
    """
    
    title_lower = doc_title.lower()
    url_lower = doc_url.lower()
    
    # Skip meeting notes
    if any(term in title_lower for term in ['meeting', 'notes']):
        if any(term in url_lower for term in ['meetingnotes', 'meeting_notes']):
            return None, None  # Skip
    
    # Check each category
    for category, subcategories in ADNI_STRUCTURE.items():
        for subcat, keywords in subcategories.items():
            for keyword in keywords:
                if keyword.lower() in title_lower:
                    return category, subcat
    
    # Auto-categorize based on keywords
    if 'mri' in title_lower:
        return 'MRI Protocols', 'Other'
    elif 'pet' in title_lower:
        return 'PET Protocols', 'Other'
    elif 'clinical' in title_lower or 'protocol' in title_lower:
        return 'Clinical Protocols', 'Other'
    elif 'consent' in title_lower or 'icf' in title_lower:
        return 'Consent Forms', 'Other'
    elif 'biospecimen' in title_lower or 'biofluid' in title_lower or 'csf' in title_lower:
        return 'Biospecimen Protocols', 'Other'
    elif 'policy' in title_lower or 'procedures' in title_lower or 'agreement' in title_lower:
        return 'Policies and Procedures', 'Other'
    
    # Default category for unclassified
    return 'Other', 'Uncategorized'

def main():
    print("=" * 70)
    print("🗂️ ADNI DOCUMENT CURATION")
    print("=" * 70)
    print()
    
    # Load raw results
    input_file = "data/adni_raw.json"
    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        return
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    documents = data.get('documents', [])
    print(f"📄 Loaded {len(documents)} documents")
    
    # Categorize and organize
    organized = {}
    skipped = []
    uncategorized = []
    
    for doc in documents:
        category, subcat = categorize_document(doc['ai_title'], doc['url'])
        
        if category is None:
            skipped.append(doc)
            continue
        
        if category not in organized:
            organized[category] = {}
        
        if subcat not in organized[category]:
            organized[category][subcat] = []
        
        organized[category][subcat].append(doc)
        
        if category == 'Other' and subcat == 'Uncategorized':
            uncategorized.append(doc)
    
    print(f"\n✅ Organized into categories")
    print(f"📊 DOCUMENT BREAKDOWN:")
    total_organized = 0
    for category in sorted(organized.keys()):
        count = sum(len(docs) for docs in organized[category].values())
        total_organized += count
        print(f"  {category}: {count} documents")
        for subcat in organized[category]:
            print(f"    - {subcat}: {len(organized[category][subcat])} documents")
    
    print(f"\n🚫 Skipped (meetings, etc.): {len(skipped)} documents")
    print(f"❓ Uncategorized: {len(uncategorized)} documents")
    print(f"📈 Total organized: {total_organized} documents")
    
    # Create hierarchical output
    curated_data = {
        "metadata": {
            "total_documents": len(documents),
            "organized_documents": total_organized,
            "skipped_documents": len(skipped),
            "uncategorized_documents": len(uncategorized),
            "source": "ADNI website structure",
            "structure_version": "documentation_page_v1"
        },
        "documents_by_category": organized,
        "uncategorized": {
            "documents": uncategorized,
            "count": len(uncategorized)
        },
        "skipped": {
            "documents": skipped,
            "count": len(skipped),
            "reason": "Meeting notes and other non-document content"
        }
    }
    
    # Save curated results
    output_file = "adni_documents_curated.json"
    with open(output_file, 'w') as f:
        json.dump(curated_data, f, indent=2)
    
    print(f"\n💾 Saved curated results to: {output_file}")
    print()
    print("=" * 70)
    print("🎉 CURATION COMPLETE!")
    print("=" * 70)
    print(f"✨ {total_organized} ADNI documents organized by category")
    print(f"📚 Ready for AI agent consumption!")

if __name__ == "__main__":
    main()
