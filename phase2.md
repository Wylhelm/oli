# Phase 2 - OLI Implementation Plan
## Overlay Legal Intelligence - RAG, LLM & AI Features

**Version**: 2.0  
**Date**: November 2025  
**Status**: To implement  

---

## 📊 Current State Analysis (Phase 1 Completed)

### ✅ Implemented Components

#### Chrome Extension (Frontend)
| Module | File | Status | Description |
|--------|------|--------|-------------|
| Main UI | `App.tsx` | ✅ Complete | React interface with scores, alerts, status badges |
| Client Anonymizer | `anonymizer.ts` | ✅ Complete | Client-side PII tokenization (SIN, email, phone, etc.) |
| DOM Scanner | `dom-scanner.ts` | ✅ Complete | Form extraction, tables, MutationObserver |
| Content Script | `content.js` | ✅ Complete | Highlighting, tooltips, floating indicator |
| Service Worker | `service-worker.js` | ✅ Minimal | Basic side panel configuration |
| Manifest V3 | `manifest.json` | ✅ Complete | Permissions, scripts, icons |

#### Backend (API)
| Module | File | Status | Description |
|--------|------|--------|-------------|
| FastAPI API | `main.py` | ⚠️ MVP | `/analyze`, `/health`, `/rules` endpoints |
| LICO Rules | `main.py` | ⚠️ Hardcoded | Static thresholds, no RAG |
| Anonymization | `main.py` | ⚠️ Basic | Simple regex, no Presidio |

### ❌ Missing Components

| Feature | Criticality | Effort |
|---------|-------------|--------|
| RAG with vector database | 🔴 Critical | High |
| LLM Integration (Azure OpenAI) | 🔴 Critical | Medium |
| Microsoft Presidio complete | 🟡 Important | Medium |
| PDF Extraction (PDF.js) | 🟡 Important | Medium |
| Audit/logs database | 🟡 Important | Medium |
| Cache & Rate Limiting | 🟢 Optional | Low |
| Language detection FR/EN | 🟢 Optional | Low |

---

## 🏗️ Phase 2 Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CHROME EXTENSION                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │   App.tsx    │  │  PDF.js      │  │  Anonymizer  │  │ DOM Scanner │ │
│  │   (React)    │  │  Handler     │  │  (Presidio)  │  │             │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘ │
│         │                 │                 │                  │        │
│         └─────────────────┴─────────────────┴──────────────────┘        │
│                                    │                                     │
│                           ┌────────▼────────┐                           │
│                           │  API Client     │                           │
│                           │  (Streaming)    │                           │
│                           └────────┬────────┘                           │
└────────────────────────────────────┼────────────────────────────────────┘
                                     │ HTTPS
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           BACKEND API                                    │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐        │
│  │    FastAPI     │    │   Presidio     │    │   Rate Limit   │        │
│  │    Router      │────│   Anonymizer   │────│   & Cache      │        │
│  └───────┬────────┘    └────────────────┘    └────────────────┘        │
│          │                                                               │
│  ┌───────▼────────────────────────────────────────────────────────┐    │
│  │                    RAG PIPELINE                                  │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │    │
│  │  │   Embedder   │  │   Vector DB  │  │   Context Retriever  │  │    │
│  │  │(text-embed-3)│  │  (ChromaDB)  │  │   (Top-K Similarity) │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │    │
│  └───────┬────────────────────────────────────────────────────────┘    │
│          │                                                               │
│  ┌───────▼────────────────────────────────────────────────────────┐    │
│  │                    LLM CHAIN                                     │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │    │
│  │  │   Prompt     │  │ Azure OpenAI │  │  Response Parser     │  │    │
│  │  │   Template   │  │   GPT-4      │  │  (Structured Output) │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    PERSISTENCE                                     │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐    │  │
│  │  │  PostgreSQL  │  │  Redis Cache │  │   Audit Logs         │    │  │
│  │  │  (Metadata)  │  │  (Sessions)  │  │   (Compliance Trail) │    │  │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Detailed Implementation Plan

### Phase 2.1 — RAG System (Retrieval-Augmented Generation)
**Estimated Duration**: 3-4 days  
**Priority**: 🔴 Critical

#### 2.1.1 Vector Database Configuration (ChromaDB)

```python
# backend/rag/vector_store.py

from chromadb import Client, Settings
from chromadb.utils import embedding_functions
import os

class LegalVectorStore:
    """
    Vector database for Canadian legislation
    Uses ChromaDB (local) or Pinecone (production)
    """
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.client = Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        # Embedding function (Azure OpenAI or sentence-transformers)
        self.embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_type="azure",
            api_version="2024-02-01",
            model_name="text-embedding-3-small"
        )
        
        # Collections by legal domain
        self.collections = {
            "immigration": self._get_or_create_collection("immigration_laws"),
            "finance": self._get_or_create_collection("financial_regulations"),
            "identity": self._get_or_create_collection("identity_verification"),
        }
    
    def _get_or_create_collection(self, name: str):
        return self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(self, collection_name: str, documents: list[dict]):
        """
        Add documents to collection
        documents = [{"id": "...", "text": "...", "metadata": {...}}]
        """
        collection = self.collections[collection_name]
        collection.add(
            ids=[d["id"] for d in documents],
            documents=[d["text"] for d in documents],
            metadatas=[d["metadata"] for d in documents]
        )
    
    def search(self, query: str, collection_name: str = "immigration", 
               n_results: int = 5) -> list[dict]:
        """
        Semantic search in vector database
        """
        collection = self.collections.get(collection_name)
        if not collection:
            return []
        
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        return [
            {
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": 1 - results["distances"][0][i]  # Convert distance to similarity
            }
            for i in range(len(results["ids"][0]))
        ]
```

---

### Phase 2.2 — LLM Integration (Azure OpenAI)
**Estimated Duration**: 2-3 days  
**Priority**: 🔴 Critical

#### 2.2.1 Azure OpenAI Client

```python
# backend/llm/azure_client.py

from openai import AzureOpenAI
import os
from typing import AsyncGenerator
import json

class AzureLLMClient:
    """
    Azure OpenAI client with streaming support
    """
    
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-02-01",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
    
    def analyze_compliance(self, 
                           document_text: str,
                           legal_context: str,
                           system_prompt: str = None) -> dict:
        """
        Compliance analysis with RAG context
        """
        if not system_prompt:
            system_prompt = self._get_compliance_system_prompt()
        
        user_message = f"""
## Document to analyze:
{document_text}

## Relevant legal context:
{legal_context}

## Instructions:
Analyze the document above using the provided legal context.
Return a structured analysis in JSON format.
"""
        
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1,  # Low temperature for consistency
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
```

---

### Phase 2.3 — Microsoft Presidio (Advanced Anonymization)
**Estimated Duration**: 1-2 days  
**Priority**: 🟡 Important

#### 2.3.1 Presidio Configuration

```python
# backend/anonymization/presidio_anonymizer.py

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from typing import Optional

class PresidioAnonymizer:
    """
    Advanced anonymization with Microsoft Presidio
    Supports Canadian entities (SIN, postal codes, etc.)
    """
    
    def __init__(self, language: str = "en"):
        self.language = language
        
        # NLP configuration
        nlp_config = {
            "nlp_engine_name": "spacy",
            "models": [
                {"lang_code": "fr", "model_name": "fr_core_news_lg"},
                {"lang_code": "en", "model_name": "en_core_web_lg"}
            ]
        }
        
        provider = NlpEngineProvider(nlp_configuration=nlp_config)
        nlp_engine = provider.create_engine()
        
        # Registry with custom recognizers
        registry = RecognizerRegistry()
        registry.load_predefined_recognizers(nlp_engine=nlp_engine)
        
        # Add Canadian recognizers
        self._add_canadian_recognizers(registry)
        
        self.analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine,
            registry=registry
        )
        
        self.anonymizer = AnonymizerEngine()
        
        # Replacement mapping
        self.operators = {
            "PERSON": OperatorConfig("replace", {"new_value": "<PERSON>"}),
            "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "<PHONE>"}),
            "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL>"}),
            "CA_SIN": OperatorConfig("replace", {"new_value": "<SIN>"}),
            "CA_POSTAL_CODE": OperatorConfig("replace", {"new_value": "<POSTAL_CODE>"}),
            "DATE_TIME": OperatorConfig("replace", {"new_value": "<DATE>"}),
            "CREDIT_CARD": OperatorConfig("replace", {"new_value": "<CREDIT_CARD>"}),
            "IBAN_CODE": OperatorConfig("replace", {"new_value": "<BANK_ACCOUNT>"}),
            "CA_UCI": OperatorConfig("replace", {"new_value": "<UCI>"}),
        }
```

---

## 📊 Legal Data to Ingest

### Priority Sources

| Source | URL | Format | Priority |
|--------|-----|--------|----------|
| IRPR (Immigration Regulations) | laws-lois.justice.gc.ca | HTML/PDF | 🔴 |
| LICO Thresholds 2024-2025 | ircc.canada.ca | Table | 🔴 |
| PIPEDA (Privacy) | laws-lois.justice.gc.ca | HTML | 🟡 |
| IRCC Operational Guide | canada.ca | PDF | 🟡 |

### LICO Structure to Ingest

```json
{
  "2024": {
    "1": 28185,
    "2": 35091,
    "3": 43145,
    "4": 52399,
    "5": 59423,
    "6": 67044,
    "7": 74665
  },
  "2025": {
    "1": 29185,
    "2": 36091,
    "3": 44145,
    "4": 53399,
    "5": 60423,
    "6": 68044,
    "7": 75665
  }
}
```

---

## 📅 Estimated Timeline

| Phase | Description | Duration | Dependencies |
|-------|-------------|----------|--------------|
| 2.1 | RAG System (ChromaDB + Ingestion) | 3-4 days | - |
| 2.2 | LLM Integration (Azure OpenAI) | 2-3 days | 2.1 |
| 2.3 | Microsoft Presidio | 1-2 days | - |
| 2.4 | PDF Extraction (PDF.js) | 1-2 days | - |
| 2.5 | Backend Refactoring | 2-3 days | 2.1, 2.2, 2.3 |
| 2.6 | API Endpoints Updates | 1-2 days | 2.5 |
| 2.7 | Testing & Documentation | 2 days | All |

**Total Estimated Duration**: 12-18 development days

---

## 🔐 Required Environment Variables

```env
# .env

# Azure OpenAI
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/oli

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Logging
LOG_LEVEL=INFO
```

---

## 🚀 Startup Commands (Phase 2)

```bash
# 1. Install dependencies
cd backend
pip install -r requirements.txt

# 2. Download SpaCy models
python -m spacy download fr_core_news_lg
python -m spacy download en_core_web_lg

# 3. Ingest legal data
python -m backend.rag.ingestion --source laws/ripr.txt

# 4. Start backend
uvicorn backend.main:app --reload --port 8001

# 5. Build extension
cd ../extension
npm run build
```

---

## 📝 Migration Notes

### From Phase 1 to Phase 2

1. **Backend `main.py`**: Functions `check_financial_threshold`, `check_document_validity`, etc. will be replaced by `ComplianceChain` using RAG and LLM.

2. **Anonymization**: Migrate from simple regex to full Presidio while maintaining backward compatibility.

3. **Database**: Add PostgreSQL for audit logs without impacting real-time analysis.

4. **Extension**: Few changes - mainly add PDF.js and streaming support.

---

*Document prepared for Team G7 - IAgouv Challenge 2025*
