"""
OLI Legal Document Downloader
Downloads Canadian immigration laws from Justice.gc.ca XML API

Source: https://laws-lois.justice.gc.ca/eng/XML/Legis.xml
"""

import httpx
import xml.etree.ElementTree as ET
from pathlib import Path
from dataclasses import dataclass
from typing import Generator
import re
import json
import time
import sys

# Keywords to identify immigration-related laws
IMMIGRATION_KEYWORDS = [
    "immigration", "immigrant", "refugee", "citizenship", "passport",
    "visa", "border", "asylum", "foreign national", "permanent resident",
    "temporary resident", "work permit", "study permit", "ircc",
    "immigration and refugee", "citizenship and immigration"
]

@dataclass
class LegalDocument:
    """Represents a Canadian legal document (Act or Regulation)"""
    unique_id: str
    official_number: str
    language: str
    title: str
    xml_url: str
    html_url: str
    current_to_date: str
    doc_type: str  # "Act" or "Regulation"
    content: str = ""


class ImmigrationLawDownloader:
    """
    Downloads immigration-related laws from Justice Canada XML API
    """
    
    INDEX_URL = "https://laws-lois.justice.gc.ca/eng/XML/Legis.xml"
    BASE_URL = "https://laws-lois.justice.gc.ca"
    
    def __init__(self, output_dir: str = "backend/data/laws"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.Client(timeout=60.0, follow_redirects=True)
        self.downloaded_docs: list[LegalDocument] = []
    
    def fetch_index(self) -> str:
        """Fetch the main legislation index XML"""
        print(f"📥 Fetching legislation index from {self.INDEX_URL}...")
        response = self.client.get(self.INDEX_URL)
        response.raise_for_status()
        return response.text
    
    def parse_index(self, xml_content: str) -> Generator[LegalDocument, None, None]:
        """Parse the XML index and yield immigration-related documents"""
        root = ET.fromstring(xml_content)
        
        # Parse Acts
        for act in root.findall(".//Act"):
            doc = self._parse_document(act, "Act")
            if doc and self._is_immigration_related(doc):
                yield doc
        
        # Parse Regulations
        for reg in root.findall(".//Regulation"):
            doc = self._parse_document(reg, "Regulation")
            if doc and self._is_immigration_related(doc):
                yield doc
    
    def _parse_document(self, element: ET.Element, doc_type: str) -> LegalDocument | None:
        """Parse a single Act or Regulation element"""
        try:
            # Only get English versions for now
            language = element.findtext("Language", "")
            if language != "eng":
                return None
            
            return LegalDocument(
                unique_id=element.findtext("UniqueId", ""),
                official_number=element.findtext("OfficialNumber", ""),
                language=language,
                title=element.findtext("Title", ""),
                xml_url=element.findtext("LinkToXML", ""),
                html_url=element.findtext("LinkToHTMLToC", ""),
                current_to_date=element.findtext("CurrentToDate", ""),
                doc_type=doc_type
            )
        except Exception as e:
            print(f"  ⚠️ Error parsing document: {e}")
            return None
    
    def _is_immigration_related(self, doc: LegalDocument) -> bool:
        """Check if a document is immigration-related based on title"""
        title_lower = doc.title.lower()
        return any(kw in title_lower for kw in IMMIGRATION_KEYWORDS)
    
    def download_document_content(self, doc: LegalDocument) -> str:
        """Download the full XML content of a document"""
        try:
            print(f"  📄 Downloading: {doc.title[:60]}...")
            response = self.client.get(doc.xml_url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"  ❌ Failed to download {doc.unique_id}: {e}")
            return ""
    
    def extract_text_from_xml(self, xml_content: str) -> str:
        """Extract readable text from legal XML document"""
        if not xml_content:
            return ""
        
        try:
            root = ET.fromstring(xml_content)
            
            # Remove namespaces for easier parsing
            for elem in root.iter():
                if '}' in elem.tag:
                    elem.tag = elem.tag.split('}')[1]
            
            text_parts = []
            
            # Extract title
            title = root.findtext(".//Title") or root.findtext(".//LongTitle")
            if title:
                text_parts.append(f"# {title}\n")
            
            # Extract all text content from sections
            for section in root.iter():
                if section.tag in ["Section", "Subsection", "Paragraph", "Subparagraph", 
                                   "Definition", "MarginalNote", "Text", "FormulaParagraph"]:
                    # Get section number if available
                    section_num = section.get("id", "")
                    
                    # Get all text content
                    text = " ".join(section.itertext()).strip()
                    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
                    
                    if text and len(text) > 10:
                        if section_num:
                            text_parts.append(f"[{section_num}] {text}")
                        else:
                            text_parts.append(text)
            
            return "\n\n".join(text_parts)
            
        except ET.ParseError as e:
            print(f"  ⚠️ XML parse error: {e}")
            # Fallback: just extract all text between tags
            text = re.sub(r'<[^>]+>', ' ', xml_content)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
    
    def save_document(self, doc: LegalDocument, text_content: str):
        """Save document to disk"""
        # Create safe filename
        safe_title = re.sub(r'[^\w\s-]', '', doc.title)[:50]
        safe_title = safe_title.replace(' ', '_')
        
        # Save as JSON with metadata
        doc_data = {
            "unique_id": doc.unique_id,
            "official_number": doc.official_number,
            "title": doc.title,
            "doc_type": doc.doc_type,
            "language": doc.language,
            "xml_url": doc.xml_url,
            "html_url": doc.html_url,
            "current_to_date": doc.current_to_date,
            "content": text_content
        }
        
        filename = f"{doc.doc_type}_{doc.unique_id}_{safe_title}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(doc_data, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def run(self, max_docs: int = None) -> list[Path]:
        """
        Main execution: download all immigration-related laws
        
        Args:
            max_docs: Maximum number of documents to download (None = all)
        
        Returns:
            List of paths to downloaded files
        """
        print("=" * 60)
        print("🍁 OLI - Canadian Immigration Law Downloader")
        print("=" * 60)
        
        # Fetch and parse index
        xml_index = self.fetch_index()
        
        # Find immigration-related documents
        docs = list(self.parse_index(xml_index))
        print(f"\n📋 Found {len(docs)} immigration-related documents")
        
        if max_docs:
            docs = docs[:max_docs]
            print(f"   (Limited to {max_docs} documents)")
        
        # Download each document
        saved_files = []
        for i, doc in enumerate(docs, 1):
            print(f"\n[{i}/{len(docs)}] Processing: {doc.title[:50]}...")
            
            # Download XML content
            xml_content = self.download_document_content(doc)
            
            if xml_content:
                # Extract text
                text_content = self.extract_text_from_xml(xml_content)
                doc.content = text_content
                
                # Save to disk
                filepath = self.save_document(doc, text_content)
                saved_files.append(filepath)
                print(f"  ✅ Saved: {filepath.name}")
                
                self.downloaded_docs.append(doc)
            
            # Be nice to the server
            time.sleep(0.5)
        
        # Save summary
        self._save_summary()
        
        print("\n" + "=" * 60)
        print(f"✅ Downloaded {len(saved_files)} documents to {self.output_dir}")
        print("=" * 60)
        
        return saved_files
    
    def _save_summary(self):
        """Save a summary of all downloaded documents"""
        summary = {
            "total_documents": len(self.downloaded_docs),
            "download_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source_url": self.INDEX_URL,
            "documents": [
                {
                    "unique_id": d.unique_id,
                    "title": d.title,
                    "doc_type": d.doc_type,
                    "html_url": d.html_url
                }
                for d in self.downloaded_docs
            ]
        }
        
        summary_path = self.output_dir / "_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 Summary saved to {summary_path}")
    
    def close(self):
        """Close HTTP client"""
        self.client.close()


def main():
    """CLI entry point"""
    import argparse
    import sys
    import io
    
    # Fix Windows console encoding
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    parser = argparse.ArgumentParser(description="Download Canadian immigration laws")
    parser.add_argument("--max", type=int, default=None, 
                        help="Maximum number of documents to download")
    parser.add_argument("--output", type=str, default="backend/data/laws",
                        help="Output directory for downloaded files")
    args = parser.parse_args()
    
    downloader = ImmigrationLawDownloader(output_dir=args.output)
    try:
        downloader.run(max_docs=args.max)
    finally:
        downloader.close()


if __name__ == "__main__":
    main()

