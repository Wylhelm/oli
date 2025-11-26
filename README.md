# OLI - Overlay Legal Intelligence

> 🛡️ **Overlay Legal Intelligence** - Legal intelligence layer for government employees

## Overview

OLI is an innovative Chrome extension that acts as an "administrative augmented reality overlay". It analyzes documents and forms from legacy government systems in real-time to automatically identify regulatory non-compliance issues.

**Phase 3 New Features**: Improved interface, PDF support, custom logo, and intelligent field highlighting.

## Features

### 🤖 AI Analysis with RAG (Retrieval-Augmented Generation)
- **Legal Knowledge Base**: 76 immigration laws and regulations (7,898 chunks indexed)
- **Semantic Search**: ChromaDB with multilingual embeddings
- **LLM**: Ollama with configurable model (e.g., `gpt-oss:120b-cloud`)
- **Legal Citations**: Direct references to Justice.gc.ca

### 🔍 Multi-Rule Analysis
- **LICO Verification** - Financial sufficiency threshold (IRPR R179)
- **Document Validity** - Freshness verification (IRPR R54)
- **Identity Verification** - Completeness check (IRPR R52)
- **Proof of Funds** - Documentation type validation (IRPR R76)

### 📊 Intelligent Dashboard
- Circular risk score (0-100)
- Case completeness indicator
- Intuitive color coding: 🟢 Compliant | 🟡 Warning | 🔴 Critical
- Clickable legal references to Justice.gc.ca
- **"New Analysis" button** to restart without reloading

### 📄 PDF Support
- **Automatic Detection** of PDFs on the page
- **Text Extraction** with PDF.js
- **One-Click Analysis** of detected PDF documents

### 🎯 Advanced DOM Injection
- **Intelligent Highlighting** of at-risk fields
- Automatic detection in forms and tables
- Interactive tooltips positioned next to the correct field
- Alert badges (!, ?, ✓) on highlighted elements
- Floating global status indicator
- Smooth animations and visual effects

### 🔒 Security & Privacy (Microsoft Presidio)
- **Advanced Anonymization** with Microsoft Presidio (NER + regex)
- **Canadian PII**: SIN, UCI, postal codes, passports
- **Standard PII**: Names, emails, phone numbers, credit cards
- **Automatic language detection** (French/English)
- **No personal data sent to the LLM**

### 🎨 Accessibility & Display
- **Fully Translated Interface** (English)
- **Display Modes**:
  - ☀️ Standard Mode
  - 🌙 **Dark Mode** (Optimized for low light)
  - 👁️ **High Contrast** (For visual impairments)
  - 🔠 **Senior Mode** (Larger text)
- **Persistence**: Settings are saved between sessions


## Architecture

```
OLI/
├── backend/                    # FastAPI Server (Python)
│   ├── main.py                # Compliance analysis API
│   ├── requirements.txt
│   ├── rag/                   # RAG System
│   │   ├── downloader.py      # Download laws from Justice.gc.ca
│   │   ├── vector_store.py    # ChromaDB + embeddings
│   │   └── retriever.py       # Legal context retrieval
│   ├── llm/                   # LLM Integration
│   │   ├── ollama_client.py   # Ollama API Client
│   │   ├── prompts.py         # Prompt templates
│   │   └── compliance_chain.py # Complete RAG+LLM pipeline
│   └── data/
│       ├── laws/              # 76 legal documents (JSON)
│       └── chroma_db/         # Vector database
├── extension/                  # Chrome Extension (React/Vite)
│   ├── src/
│   │   ├── App.tsx            # Main interface
│   │   └── lib/
│   │       ├── dom-scanner.ts # DOM Scanner with MutationObserver
│   │       ├── pdf-handler.ts # PDF extraction with PDF.js
│   │       ├── anonymizer.ts  # Data anonymization
│   │       └── utils.ts
│   ├── public/
│   │   ├── content.js         # DOM injection script
│   │   ├── manifest.json
│   │   ├── logo.png           # OLI Logo
│   │   └── service-worker.js
│   └── dist/                  # Production build
├── test_documents/             # Test documents
│   ├── legacy-portal.html     # Simulated IRCC portal (4 test cases)
│   ├── index.html             # Test hub
│   └── *.pdf                  # Generated test PDFs
├── logo.png                    # OLI logo source
├── create_test_pdf.py          # PDF generation script
└── serve_test_docs.py          # Local HTTP server for testing
```

## Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Ollama (for local LLM)
- Conda (recommended)

### 1. Backend (API + RAG + LLM + Presidio)

```bash
cd backend

# Create conda environment
conda create -n OLI python=3.11
conda activate OLI

# Install dependencies
pip install -r requirements.txt

# Install spaCy models for Presidio (NER anonymization)
python -m spacy download en_core_web_sm
python -m spacy download fr_core_news_sm

# Download immigration laws (first time only)
python rag/downloader.py

# Ingest into vector database (first time only)
python rag/vector_store.py

# Test Presidio anonymization (optional)
python test_presidio.py

# Start the server
uvicorn main:app --reload --port 8001
```

Server starts at `http://localhost:8001`

### 2. Ollama (LLM)

```bash
# Install a compatible model
ollama pull qwen3:32b
# or
ollama pull gpt-oss:120b-cloud

# Verify Ollama is running on localhost:11434
ollama list
```

### 3. Chrome Extension

```bash
cd extension

# Install dependencies
npm install

# Build for production
npm run build
```

### 4. Load the Extension

1. Open Chrome → `chrome://extensions`
2. Enable **Developer mode** (top right corner)
3. Click **Load unpacked**
4. Select the `extension/dist` folder

### 5. Test Server (optional)

```bash
# To test PDFs without CORS issues
python serve_test_docs.py
# Opens http://localhost:8080
```

## Demonstration

### Scenario: Immigration Case Analysis

1. **Start the test server**: `python serve_test_docs.py`
2. **Open the legacy portal**: http://localhost:8080/legacy-portal.html
3. **Select a test case**: Sophie Martin (critical), Jean-Claude (compliant), etc.
4. **Activate OLI**: Click on the extension icon (🛡️)
5. **Scan the page**: Click "Analyze with AI"

### Available Test Cases

| Case | Status | Description |
|------|--------|-------------|
| Sophie Martin | 🔴 CRITICAL | Insufficient funds ($5k vs $20k), expired document |
| Jean-Claude Tremblay | 🟢 COMPLIANT | All criteria met |
| Marie Dubois | 🟡 WARNING | Funds at limit for 2 people |
| Ahmed Hassan | 🔴 CRITICAL | Multiple issues (funds, docs, delays) |

### Expected Results

The system will automatically detect with legal justification:
- ❌ **Insufficient Balance**: $5,000 < $20,635 (IRPR Section 4, R179)
- ⚠️ **Expired Document**: Submission date > 6 months (IRPR Section 44)
- ✅ **Proof of Funds**: Certified bank statement detected (IRPR Section 74)
- ✅ **Identity**: Complete information

## API Endpoints

### Analysis

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analyze` | POST | Rule-based analysis (fast) |
| `/analyze/llm` | POST | RAG + LLM analysis (comprehensive) |
| `/health` | GET | Server status + RAG + LLM |
| `/rules` | GET | List of compliance rules |

### RAG (Legal Search)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/rag/search` | POST | Semantic search in laws |
| `/rag/context` | POST | Legal context for a check type |
| `/rag/stats` | GET | Vector database statistics |

### LLM

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/llm/status` | GET | LLM status and active model |

### Anonymization (Microsoft Presidio)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/anonymize` | POST | Anonymize text (PII → tokens) |
| `/anonymize/detect` | POST | Detect PII without anonymizing |
| `/anonymize/status` | GET | Presidio status (NER or fallback) |

### LLM Request Example

```bash
curl -X POST http://localhost:8001/analyze/llm \
  -H "Content-Type: application/json" \
  -d '{"text": "Sophie Martin, Balance: $5,000, Date: 2024-01-01"}'
```

Response:
```json
{
  "overall_status": "CRITIQUE",
  "risk_score": 78,
  "analysis_mode": "llm",
  "checks": [
    {
      "name": "LICO Threshold",
      "status": "AVERTISSEMENT",
      "reference": "IRPR Section 4 & 74",
      "confidence": 0.85,
      "url": "http://laws-lois.justice.gc.ca/eng/regulations/SOR-2002-227/"
    }
  ],
  "sources": [
    {"title": "Immigration and Refugee Protection Regulations", "url": "..."}
  ]
}
```

## Tech Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **Backend**: Python 3.11+, FastAPI, Pydantic
- **RAG**: ChromaDB, Sentence-Transformers (paraphrase-multilingual-MiniLM-L12-v2)
- **LLM**: Ollama (configurable)
- **Anonymization**: Microsoft Presidio + spaCy NER (fr/en)
- **PDF**: PDF.js (pdfjs-dist)
- **Extension**: Manifest V3, Chrome Side Panel API
- **Data Source**: Justice.gc.ca XML API (76 immigration laws)

## G7 IAgouv Compliance

This project meets the G7 Grand Challenge IAgouv 2025 criteria:

1. ✅ **Social Impact** - Reduces cognitive load for agents
2. ✅ **Interoperability** - Works on any legacy system via DOM injection
3. ✅ **Explainability** - Clear justifications with legal references (RAG)
4. ✅ **Scalability** - Modular architecture, multilingual, swappable LLM

## Configuration

Environment variables (optional):

```bash
# Ollama model (default: qwen3:32b)
export OLLAMA_MODEL=qwen3:32b

# Ollama URL (default: http://localhost:11434)
export OLLAMA_BASE_URL=http://localhost:11434
```

## License

Project developed for the G7 IAgouv Grand Challenge 2025.

---

**🍁 Team G7 - OLI (Overlay Legal Intelligence)**
