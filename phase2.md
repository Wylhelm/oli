# Phase 2 - OLI Implementation Plan
## Overlay Legal Intelligence - Fonctionnalités RAG, LLM & IA

**Version**: 2.0  
**Date**: November 2025  
**Statut**: À implémenter  

---

## 📊 Analyse de l'État Actuel (Phase 1 Complétée)

### ✅ Composants Implémentés

#### Extension Chrome (Frontend)
| Module | Fichier | Statut | Description |
|--------|---------|--------|-------------|
| UI Principale | `App.tsx` | ✅ Complet | Interface React avec scores, alertes, badges de statut |
| Anonymiseur Client | `anonymizer.ts` | ✅ Complet | Tokenization PII côté client (SIN, email, phone, etc.) |
| Scanner DOM | `dom-scanner.ts` | ✅ Complet | Extraction formulaires, tables, MutationObserver |
| Content Script | `content.js` | ✅ Complet | Surlignage, tooltips, indicateur flottant |
| Service Worker | `service-worker.js` | ✅ Minimal | Configuration side panel basique |
| Manifest V3 | `manifest.json` | ✅ Complet | Permissions, scripts, icons |

#### Backend (API)
| Module | Fichier | Statut | Description |
|--------|---------|--------|-------------|
| API FastAPI | `main.py` | ⚠️ MVP | Endpoints `/analyze`, `/health`, `/rules` |
| Règles LICO | `main.py` | ⚠️ Hardcodé | Seuils statiques, pas de RAG |
| Anonymisation | `main.py` | ⚠️ Basique | Regex simple, pas Presidio |

### ❌ Composants Manquants

| Fonctionnalité | Criticité | Effort |
|----------------|-----------|--------|
| RAG avec base vectorielle | 🔴 Critique | Élevé |
| Intégration LLM (Azure OpenAI) | 🔴 Critique | Moyen |
| Microsoft Presidio complet | 🟡 Important | Moyen |
| Extraction PDF (PDF.js) | 🟡 Important | Moyen |
| Base de données audit/logs | 🟡 Important | Moyen |
| Cache & Rate Limiting | 🟢 Optionnel | Faible |
| Détection langue FR/EN | 🟢 Optionnel | Faible |

---

## 🏗️ Architecture Phase 2

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         EXTENSION CHROME                                 │
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

## 📋 Plan d'Implémentation Détaillé

### Phase 2.1 — Système RAG (Retrieval-Augmented Generation)
**Durée estimée**: 3-4 jours  
**Priorité**: 🔴 Critique

#### 2.1.1 Configuration Base Vectorielle (ChromaDB)

```python
# backend/rag/vector_store.py

from chromadb import Client, Settings
from chromadb.utils import embedding_functions
import os

class LegalVectorStore:
    """
    Base vectorielle pour la législation canadienne
    Utilise ChromaDB (local) ou Pinecone (production)
    """
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.client = Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        # Embedding function (Azure OpenAI ou sentence-transformers)
        self.embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_type="azure",
            api_version="2024-02-01",
            model_name="text-embedding-3-small"
        )
        
        # Collections par domaine juridique
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
        Ajoute des documents à la collection
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
        Recherche sémantique dans la base vectorielle
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

#### 2.1.2 Pipeline d'Ingestion des Lois

```python
# backend/rag/ingestion.py

import re
from typing import Generator
from dataclasses import dataclass

@dataclass
class LegalChunk:
    id: str
    text: str
    metadata: dict

class LegalDocumentIngester:
    """
    Ingestion et chunking des documents législatifs
    """
    
    CHUNK_SIZE = 1000  # caractères
    CHUNK_OVERLAP = 200
    
    def __init__(self, vector_store: LegalVectorStore):
        self.vector_store = vector_store
    
    def ingest_ripr(self, ripr_text: str) -> int:
        """
        Ingestion du Règlement sur l'immigration et la protection des réfugiés (RIPR)
        """
        chunks = list(self._chunk_legal_document(ripr_text, "RIPR"))
        
        documents = [
            {
                "id": chunk.id,
                "text": chunk.text,
                "metadata": chunk.metadata
            }
            for chunk in chunks
        ]
        
        self.vector_store.add_documents("immigration", documents)
        return len(documents)
    
    def ingest_lico_tables(self, lico_data: dict) -> int:
        """
        Ingestion des seuils LICO avec contexte
        """
        documents = []
        
        for year, thresholds in lico_data.items():
            for family_size, amount in thresholds.items():
                doc_id = f"LICO_{year}_{family_size}"
                text = f"""
                Low Income Cut-Off (LICO) - Seuil de faible revenu
                Année: {year}
                Taille de la famille: {family_size} personne(s)
                Montant minimum requis: {amount:,} $ CAD
                
                Référence légale: Règlement sur l'immigration R179(b)
                Source: Immigration, Réfugiés et Citoyenneté Canada (IRCC)
                
                Ce seuil représente le montant minimum de fonds qu'un demandeur 
                doit démontrer pour prouver sa capacité d'établissement au Canada.
                """
                
                documents.append({
                    "id": doc_id,
                    "text": text.strip(),
                    "metadata": {
                        "type": "LICO_threshold",
                        "year": year,
                        "family_size": family_size,
                        "amount": amount,
                        "rule": "R179(b)",
                        "url": "https://laws-lois.justice.gc.ca/fra/reglements/DORS-2002-227/page-22.html"
                    }
                })
        
        self.vector_store.add_documents("immigration", documents)
        return len(documents)
    
    def _chunk_legal_document(self, text: str, source: str) -> Generator[LegalChunk, None, None]:
        """
        Découpe un document légal en chunks avec overlap
        Préserve les références d'articles
        """
        # Pattern pour détecter les articles
        article_pattern = re.compile(r'(Article\s+\d+|R\d+|Section\s+\d+)', re.IGNORECASE)
        
        paragraphs = text.split('\n\n')
        current_chunk = ""
        current_article = "General"
        chunk_index = 0
        
        for para in paragraphs:
            # Détecter si c'est un nouvel article
            article_match = article_pattern.search(para)
            if article_match:
                current_article = article_match.group(1)
            
            # Ajouter au chunk courant
            if len(current_chunk) + len(para) < self.CHUNK_SIZE:
                current_chunk += para + "\n\n"
            else:
                # Émettre le chunk
                if current_chunk.strip():
                    yield LegalChunk(
                        id=f"{source}_{chunk_index}",
                        text=current_chunk.strip(),
                        metadata={
                            "source": source,
                            "article": current_article,
                            "chunk_index": chunk_index
                        }
                    )
                    chunk_index += 1
                
                # Commencer nouveau chunk avec overlap
                overlap_start = max(0, len(current_chunk) - self.CHUNK_OVERLAP)
                current_chunk = current_chunk[overlap_start:] + para + "\n\n"
        
        # Dernier chunk
        if current_chunk.strip():
            yield LegalChunk(
                id=f"{source}_{chunk_index}",
                text=current_chunk.strip(),
                metadata={
                    "source": source,
                    "article": current_article,
                    "chunk_index": chunk_index
                }
            )
```

#### 2.1.3 Retriever Contextuel

```python
# backend/rag/retriever.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class RetrievalResult:
    query: str
    documents: list[dict]
    context: str
    sources: list[str]

class ContextualRetriever:
    """
    Récupère le contexte légal pertinent pour une requête
    """
    
    def __init__(self, vector_store: LegalVectorStore):
        self.vector_store = vector_store
    
    def retrieve(self, query: str, domain: str = "immigration", 
                 top_k: int = 5, min_score: float = 0.7) -> RetrievalResult:
        """
        Récupère les documents les plus pertinents
        """
        results = self.vector_store.search(query, domain, top_k)
        
        # Filtrer par score minimum
        filtered = [r for r in results if r["score"] >= min_score]
        
        # Construire le contexte
        context_parts = []
        sources = []
        
        for doc in filtered:
            context_parts.append(f"[Source: {doc['metadata'].get('source', 'Unknown')}]\n{doc['text']}")
            if url := doc['metadata'].get('url'):
                sources.append(url)
        
        return RetrievalResult(
            query=query,
            documents=filtered,
            context="\n\n---\n\n".join(context_parts),
            sources=list(set(sources))
        )
    
    def retrieve_for_compliance_check(self, 
                                       document_text: str,
                                       check_type: str) -> RetrievalResult:
        """
        Récupère le contexte spécifique pour un type de vérification
        """
        # Requêtes spécialisées par type de vérification
        query_templates = {
            "LICO": "Quels sont les seuils LICO requis pour prouver la capacité financière d'établissement au Canada?",
            "DOCUMENT_VALIDITY": "Quelle est la durée de validité des documents requis pour une demande d'immigration?",
            "IDENTITY": "Quelles sont les exigences de vérification d'identité pour les demandeurs?",
            "PROOF_OF_FUNDS": "Quels types de preuves de fonds sont acceptés pour les demandes d'immigration?"
        }
        
        query = query_templates.get(check_type, document_text[:500])
        return self.retrieve(query, domain="immigration", top_k=3)
```

---

### Phase 2.2 — Intégration LLM (Azure OpenAI)
**Durée estimée**: 2-3 jours  
**Priorité**: 🔴 Critique

#### 2.2.1 Client Azure OpenAI

```python
# backend/llm/azure_client.py

from openai import AzureOpenAI
import os
from typing import AsyncGenerator
import json

class AzureLLMClient:
    """
    Client pour Azure OpenAI avec support streaming
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
        Analyse de conformité avec contexte RAG
        """
        if not system_prompt:
            system_prompt = self._get_compliance_system_prompt()
        
        user_message = f"""
## Document à analyser:
{document_text}

## Contexte légal pertinent:
{legal_context}

## Instructions:
Analysez le document ci-dessus en utilisant le contexte légal fourni.
Retournez une analyse structurée au format JSON.
"""
        
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1,  # Faible température pour cohérence
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def analyze_compliance_stream(self,
                                        document_text: str,
                                        legal_context: str) -> AsyncGenerator[str, None]:
        """
        Analyse avec streaming pour UX réactive
        """
        system_prompt = self._get_compliance_system_prompt()
        
        user_message = f"""
## Document:
{document_text}

## Contexte légal:
{legal_context}
"""
        
        stream = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def _get_compliance_system_prompt(self) -> str:
        return """Tu es OLI (Overlay Legal Intelligence), un assistant d'analyse de conformité réglementaire pour les agents de la fonction publique canadienne.

## Ton rôle:
- Analyser les documents soumis pour détecter les non-conformités
- Croiser les informations avec la législation canadienne applicable
- Fournir des recommandations claires et actionnables

## Format de réponse (JSON strict):
{
  "checks": [
    {
      "id": "CHECK_ID",
      "name": "Nom du contrôle",
      "status": "CONFORME|AVERTISSEMENT|CRITIQUE",
      "message": "Description du résultat",
      "reference": "Article de loi applicable",
      "url": "URL vers la source officielle",
      "recommendation": "Action recommandée",
      "highlight_text": "Texte à surligner dans le document (ou null)",
      "confidence": 0.95
    }
  ],
  "summary": "Résumé en une phrase",
  "risk_score": 0-100,
  "completeness_score": 0-100
}

## Règles:
1. Toujours citer les références légales exactes (R179, R52, etc.)
2. Fournir des URLs vers laws-lois.justice.gc.ca quand possible
3. Être précis sur les seuils numériques (LICO, délais, etc.)
4. Recommandations concrètes et actionnables
5. Niveau de confiance honnête"""
```

#### 2.2.2 Chain de Compliance

```python
# backend/llm/compliance_chain.py

from dataclasses import dataclass
from typing import Optional
from backend.rag.retriever import ContextualRetriever
from backend.llm.azure_client import AzureLLMClient

@dataclass
class ComplianceAnalysis:
    overall_status: str
    risk_score: int
    completeness_score: int
    checks: list[dict]
    summary: str
    sources: list[str]
    anonymized_text: str

class ComplianceChain:
    """
    Pipeline complet: Anonymisation → RAG → LLM → Parsing
    """
    
    def __init__(self, 
                 retriever: ContextualRetriever,
                 llm_client: AzureLLMClient,
                 anonymizer):
        self.retriever = retriever
        self.llm = llm_client
        self.anonymizer = anonymizer
    
    async def analyze(self, document_text: str, 
                      url: Optional[str] = None) -> ComplianceAnalysis:
        """
        Exécute la chaîne complète d'analyse
        """
        # 1. Anonymisation
        anonymized = self.anonymizer.anonymize(document_text)
        
        # 2. Détection du type de document
        doc_type = self._detect_document_type(anonymized)
        
        # 3. Récupération du contexte légal
        retrieval = self.retriever.retrieve_for_compliance_check(
            anonymized, 
            doc_type
        )
        
        # 4. Analyse LLM
        llm_response = self.llm.analyze_compliance(
            anonymized,
            retrieval.context
        )
        
        # 5. Construction du résultat
        return ComplianceAnalysis(
            overall_status=self._determine_overall_status(llm_response["checks"]),
            risk_score=llm_response.get("risk_score", 0),
            completeness_score=llm_response.get("completeness_score", 0),
            checks=llm_response["checks"],
            summary=llm_response["summary"],
            sources=retrieval.sources,
            anonymized_text=anonymized
        )
    
    def _detect_document_type(self, text: str) -> str:
        """
        Détecte le type de document basé sur le contenu
        """
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in ["lico", "fonds", "solde", "bancaire"]):
            return "LICO"
        elif any(kw in text_lower for kw in ["passeport", "identité", "uci"]):
            return "IDENTITY"
        elif any(kw in text_lower for kw in ["relevé", "preuve de fonds"]):
            return "PROOF_OF_FUNDS"
        else:
            return "DOCUMENT_VALIDITY"
    
    def _determine_overall_status(self, checks: list[dict]) -> str:
        """
        Détermine le statut global basé sur les vérifications
        """
        statuses = [c["status"] for c in checks]
        
        if "CRITIQUE" in statuses:
            return "CRITIQUE"
        elif "AVERTISSEMENT" in statuses:
            return "AVERTISSEMENT"
        return "CONFORME"
```

---

### Phase 2.3 — Microsoft Presidio (Anonymisation Avancée)
**Durée estimée**: 1-2 jours  
**Priorité**: 🟡 Important

#### 2.3.1 Configuration Presidio

```python
# backend/anonymization/presidio_anonymizer.py

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from typing import Optional
import re

class PresidioAnonymizer:
    """
    Anonymisation avancée avec Microsoft Presidio
    Supporte les entités canadiennes (SIN, codes postaux, etc.)
    """
    
    def __init__(self, language: str = "fr"):
        self.language = language
        
        # Configuration NLP
        nlp_config = {
            "nlp_engine_name": "spacy",
            "models": [
                {"lang_code": "fr", "model_name": "fr_core_news_lg"},
                {"lang_code": "en", "model_name": "en_core_web_lg"}
            ]
        }
        
        provider = NlpEngineProvider(nlp_configuration=nlp_config)
        nlp_engine = provider.create_engine()
        
        # Registre avec reconnaisseurs personnalisés
        registry = RecognizerRegistry()
        registry.load_predefined_recognizers(nlp_engine=nlp_engine)
        
        # Ajouter reconnaisseurs canadiens
        self._add_canadian_recognizers(registry)
        
        self.analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine,
            registry=registry
        )
        
        self.anonymizer = AnonymizerEngine()
        
        # Mapping de remplacement
        self.operators = {
            "PERSON": OperatorConfig("replace", {"new_value": "<PERSONNE>"}),
            "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "<TELEPHONE>"}),
            "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<COURRIEL>"}),
            "CA_SIN": OperatorConfig("replace", {"new_value": "<NAS>"}),
            "CA_POSTAL_CODE": OperatorConfig("replace", {"new_value": "<CODE_POSTAL>"}),
            "DATE_TIME": OperatorConfig("replace", {"new_value": "<DATE>"}),
            "CREDIT_CARD": OperatorConfig("replace", {"new_value": "<CARTE_CREDIT>"}),
            "IBAN_CODE": OperatorConfig("replace", {"new_value": "<COMPTE_BANCAIRE>"}),
            "CA_UCI": OperatorConfig("replace", {"new_value": "<UCI>"}),
        }
    
    def _add_canadian_recognizers(self, registry):
        """
        Ajoute des reconnaisseurs spécifiques au Canada
        """
        from presidio_analyzer import Pattern, PatternRecognizer
        
        # SIN canadien (NAS)
        sin_recognizer = PatternRecognizer(
            supported_entity="CA_SIN",
            patterns=[
                Pattern(
                    name="SIN",
                    regex=r"\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\b",
                    score=0.85
                )
            ]
        )
        
        # Code postal canadien
        postal_recognizer = PatternRecognizer(
            supported_entity="CA_POSTAL_CODE",
            patterns=[
                Pattern(
                    name="Postal Code",
                    regex=r"\b[A-Z]\d[A-Z][-\s]?\d[A-Z]\d\b",
                    score=0.9
                )
            ]
        )
        
        # UCI (Unique Client Identifier) - Immigration
        uci_recognizer = PatternRecognizer(
            supported_entity="CA_UCI",
            patterns=[
                Pattern(
                    name="UCI",
                    regex=r"\bUCI[-\s]?\d{8,10}\b",
                    score=0.95
                )
            ]
        )
        
        registry.add_recognizer(sin_recognizer)
        registry.add_recognizer(postal_recognizer)
        registry.add_recognizer(uci_recognizer)
    
    def anonymize(self, text: str, language: Optional[str] = None) -> str:
        """
        Anonymise le texte en remplaçant les PII
        """
        lang = language or self.language
        
        # Analyse
        analysis_results = self.analyzer.analyze(
            text=text,
            language=lang,
            entities=None  # Toutes les entités
        )
        
        # Anonymisation
        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analysis_results,
            operators=self.operators
        )
        
        return anonymized.text
    
    def get_entities(self, text: str, language: Optional[str] = None) -> list[dict]:
        """
        Retourne la liste des entités détectées (pour audit)
        """
        lang = language or self.language
        
        results = self.analyzer.analyze(
            text=text,
            language=lang
        )
        
        return [
            {
                "entity_type": r.entity_type,
                "start": r.start,
                "end": r.end,
                "score": r.score,
                "text": text[r.start:r.end]
            }
            for r in results
        ]
```

---

### Phase 2.4 — Extraction PDF
**Durée estimée**: 1-2 jours  
**Priorité**: 🟡 Important

#### 2.4.1 Handler PDF (Extension)

```typescript
// extension/src/lib/pdf-handler.ts

import * as pdfjsLib from 'pdfjs-dist';

// Configure worker
pdfjsLib.GlobalWorkerOptions.workerSrc = chrome.runtime.getURL('lib/pdf.worker.min.js');

export interface PDFExtractionResult {
  success: boolean;
  totalPages: number;
  content: PageContent[];
  formFields: FormField[];
  error?: string;
}

export interface PageContent {
  page: number;
  text: string;
}

export interface FormField {
  page: number;
  name: string;
  type: string;
  value: string | null;
  rect: number[];
}

export class PDFHandler {
  
  /**
   * Extrait le texte d'un PDF à partir de son URL
   */
  async extractFromUrl(pdfUrl: string): Promise<PDFExtractionResult> {
    try {
      const pdf = await pdfjsLib.getDocument(pdfUrl).promise;
      return this.extractFromDocument(pdf);
    } catch (error) {
      return {
        success: false,
        totalPages: 0,
        content: [],
        formFields: [],
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
  
  /**
   * Extrait le texte d'un PDF à partir d'un ArrayBuffer
   */
  async extractFromBuffer(buffer: ArrayBuffer): Promise<PDFExtractionResult> {
    try {
      const pdf = await pdfjsLib.getDocument({ data: buffer }).promise;
      return this.extractFromDocument(pdf);
    } catch (error) {
      return {
        success: false,
        totalPages: 0,
        content: [],
        formFields: [],
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
  
  private async extractFromDocument(pdf: pdfjsLib.PDFDocumentProxy): Promise<PDFExtractionResult> {
    const content: PageContent[] = [];
    const formFields: FormField[] = [];
    
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      
      // Extract text
      const textContent = await page.getTextContent();
      const pageText = textContent.items
        .map((item: any) => item.str)
        .join(' ');
      
      content.push({ page: i, text: pageText });
      
      // Extract form fields
      const annotations = await page.getAnnotations();
      for (const annotation of annotations) {
        if (annotation.subtype === 'Widget') {
          formFields.push({
            page: i,
            name: annotation.fieldName || '',
            type: annotation.fieldType || '',
            value: annotation.fieldValue || null,
            rect: annotation.rect
          });
        }
      }
    }
    
    return {
      success: true,
      totalPages: pdf.numPages,
      content,
      formFields
    };
  }
  
  /**
   * Détecte les PDFs embarqués dans la page
   */
  detectEmbeddedPDFs(): string[] {
    const pdfUrls: string[] = [];
    
    // Check embed elements
    document.querySelectorAll('embed[type="application/pdf"]').forEach(el => {
      const src = (el as HTMLEmbedElement).src;
      if (src) pdfUrls.push(src);
    });
    
    // Check iframes with PDF
    document.querySelectorAll('iframe').forEach(el => {
      const src = el.src;
      if (src && src.includes('.pdf')) pdfUrls.push(src);
    });
    
    // Check object elements
    document.querySelectorAll('object[data*=".pdf"]').forEach(el => {
      const data = (el as HTMLObjectElement).data;
      if (data) pdfUrls.push(data);
    });
    
    return pdfUrls;
  }
}

export default new PDFHandler();
```

---

### Phase 2.5 — Backend Amélioré
**Durée estimée**: 2-3 jours  
**Priorité**: 🟡 Important

#### 2.5.1 Structure Backend Refactorisée

```
backend/
├── main.py                    # Point d'entrée FastAPI
├── config.py                  # Configuration centralisée
├── requirements.txt           # Dépendances
│
├── api/
│   ├── __init__.py
│   ├── routes/
│   │   ├── analyze.py         # /analyze endpoint
│   │   ├── rules.py           # /rules endpoint
│   │   └── health.py          # /health endpoint
│   └── dependencies.py        # Injection de dépendances
│
├── rag/
│   ├── __init__.py
│   ├── vector_store.py        # ChromaDB wrapper
│   ├── ingestion.py           # Document ingestion
│   └── retriever.py           # Context retrieval
│
├── llm/
│   ├── __init__.py
│   ├── azure_client.py        # Azure OpenAI client
│   ├── prompts.py             # Prompt templates
│   └── compliance_chain.py    # Analysis chain
│
├── anonymization/
│   ├── __init__.py
│   └── presidio_anonymizer.py # Presidio wrapper
│
├── db/
│   ├── __init__.py
│   ├── models.py              # SQLAlchemy models
│   ├── session.py             # DB session
│   └── audit.py               # Audit logging
│
├── data/
│   ├── laws/                  # Source legislation files
│   │   ├── ripr.txt
│   │   └── lico_tables.json
│   └── chroma_db/             # Vector DB persistence
│
└── tests/
    ├── test_rag.py
    ├── test_llm.py
    └── test_anonymization.py
```

#### 2.5.2 Nouvelle Configuration

```python
# backend/config.py

from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # API
    app_name: str = "OLI Backend"
    debug: bool = False
    
    # Azure OpenAI
    azure_openai_api_key: str
    azure_openai_endpoint: str
    azure_openai_deployment: str = "gpt-4"
    azure_openai_embedding_deployment: str = "text-embedding-3-small"
    
    # Vector DB
    chroma_persist_dir: str = "./data/chroma_db"
    
    # Database
    database_url: str = "postgresql://user:pass@localhost/oli"
    
    # Redis Cache
    redis_url: str = "redis://localhost:6379"
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

#### 2.5.3 Requirements Mis à Jour

```txt
# backend/requirements.txt

# API Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Validation
pydantic==2.5.3
pydantic-settings==2.1.0

# LLM
openai==1.10.0
langchain==0.1.5
langchain-openai==0.0.5

# Vector Store
chromadb==0.4.22

# Anonymization
presidio-analyzer==2.2.351
presidio-anonymizer==2.2.351
spacy==3.7.2

# NLP Models (run separately)
# python -m spacy download fr_core_news_lg
# python -m spacy download en_core_web_lg

# Database
sqlalchemy==2.0.25
asyncpg==0.29.0
alembic==1.13.1

# Caching
redis==5.0.1
aioredis==2.0.1

# Utils
python-dotenv==1.0.0
httpx==0.26.0

# PDF Processing (optional, for server-side)
pypdf==3.17.4

# Testing
pytest==8.0.0
pytest-asyncio==0.23.3
httpx==0.26.0
```

---

### Phase 2.6 — Endpoints API Améliorés
**Durée estimée**: 1-2 jours  
**Priorité**: 🟡 Important

#### 2.6.1 Nouveau Endpoint /analyze

```python
# backend/api/routes/analyze.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json

from backend.api.dependencies import (
    get_compliance_chain,
    get_audit_logger
)
from backend.llm.compliance_chain import ComplianceChain

router = APIRouter(prefix="/analyze", tags=["Analysis"])

class AnalyzeRequest(BaseModel):
    text: str
    url: Optional[str] = None
    language: Optional[str] = "fr"
    stream: bool = False

class AnalyzeResponse(BaseModel):
    overall_status: str
    risk_score: int
    completeness_score: int
    checks: list[dict]
    summary: str
    sources: list[str]
    anonymized_text: str

@router.post("", response_model=AnalyzeResponse)
async def analyze_document(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    chain: ComplianceChain = Depends(get_compliance_chain),
    audit = Depends(get_audit_logger)
):
    """
    Analyse un document pour la conformité réglementaire.
    
    Utilise RAG pour récupérer le contexte légal pertinent,
    puis LLM pour l'analyse intelligente.
    """
    try:
        result = await chain.analyze(
            document_text=request.text,
            url=request.url
        )
        
        # Log pour audit (background)
        background_tasks.add_task(
            audit.log_analysis,
            url=request.url,
            status=result.overall_status,
            risk_score=result.risk_score
        )
        
        return AnalyzeResponse(
            overall_status=result.overall_status,
            risk_score=result.risk_score,
            completeness_score=result.completeness_score,
            checks=result.checks,
            summary=result.summary,
            sources=result.sources,
            anonymized_text=result.anonymized_text
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream")
async def analyze_document_stream(
    request: AnalyzeRequest,
    chain: ComplianceChain = Depends(get_compliance_chain)
):
    """
    Analyse avec streaming pour UX réactive
    """
    async def generate():
        async for chunk in chain.analyze_stream(request.text):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

---

## 📊 Données Législatives à Ingérer

### Sources Prioritaires

| Source | URL | Format | Priorité |
|--------|-----|--------|----------|
| RIPR (Règlement immigration) | laws-lois.justice.gc.ca | HTML/PDF | 🔴 |
| Seuils LICO 2024-2025 | ircc.canada.ca | Table | 🔴 |
| LPRPDE (Vie privée) | laws-lois.justice.gc.ca | HTML | 🟡 |
| Guide opérationnel IRCC | canada.ca | PDF | 🟡 |

### Structure LICO à Ingérer

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

## 🧪 Plan de Tests

### Tests Unitaires

```python
# backend/tests/test_rag.py

import pytest
from backend.rag.vector_store import LegalVectorStore
from backend.rag.retriever import ContextualRetriever

@pytest.fixture
def vector_store():
    return LegalVectorStore(persist_directory="./test_chroma")

def test_lico_retrieval(vector_store):
    """Test que les seuils LICO sont correctement récupérés"""
    retriever = ContextualRetriever(vector_store)
    
    result = retriever.retrieve(
        "Quel est le seuil LICO pour une personne seule?",
        domain="immigration"
    )
    
    assert len(result.documents) > 0
    assert "LICO" in result.context
    assert "20635" in result.context or "28185" in result.context

def test_anonymization_preserves_amounts():
    """Test que les montants financiers ne sont pas anonymisés"""
    from backend.anonymization.presidio_anonymizer import PresidioAnonymizer
    
    anonymizer = PresidioAnonymizer()
    text = "Sophie Martin a un solde de 5 000 $"
    
    result = anonymizer.anonymize(text)
    
    assert "5 000 $" in result  # Montant préservé
    assert "Sophie Martin" not in result  # Nom anonymisé
```

### Tests d'Intégration

```python
# backend/tests/test_integration.py

import pytest
from httpx import AsyncClient
from backend.main import app

@pytest.mark.asyncio
async def test_full_analysis_pipeline():
    """Test du pipeline complet: Extension → Backend → RAG → LLM"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/analyze", json={
            "text": """
            Demandeur: Sophie Martin
            UCI: UCI-99887766
            Solde moyen: 5 000 $
            Date du relevé: 2024-01-01
            """,
            "url": "http://legacy-portal.gov.ca"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["overall_status"] == "CRITIQUE"
        assert data["risk_score"] >= 40
        assert any(c["id"] == "LICO_001" for c in data["checks"])
```

---

## 📅 Timeline Estimée

| Phase | Description | Durée | Dépendances |
|-------|-------------|-------|-------------|
| 2.1 | RAG System (ChromaDB + Ingestion) | 3-4 jours | - |
| 2.2 | LLM Integration (Azure OpenAI) | 2-3 jours | 2.1 |
| 2.3 | Microsoft Presidio | 1-2 jours | - |
| 2.4 | PDF Extraction (PDF.js) | 1-2 jours | - |
| 2.5 | Backend Refactoring | 2-3 jours | 2.1, 2.2, 2.3 |
| 2.6 | API Endpoints Updates | 1-2 jours | 2.5 |
| 2.7 | Testing & Documentation | 2 jours | Tout |

**Durée totale estimée**: 12-18 jours de développement

---

## 🔐 Variables d'Environnement Requises

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

## 🚀 Commandes de Démarrage (Phase 2)

```bash
# 1. Installer les dépendances
cd backend
pip install -r requirements.txt

# 2. Télécharger les modèles SpaCy
python -m spacy download fr_core_news_lg
python -m spacy download en_core_web_lg

# 3. Ingérer les données légales
python -m backend.rag.ingestion --source laws/ripr.txt

# 4. Démarrer le backend
uvicorn backend.main:app --reload --port 8001

# 5. Builder l'extension
cd ../extension
npm run build
```

---

## 📝 Notes de Migration

### De Phase 1 à Phase 2

1. **Backend `main.py`**: Les fonctions `check_financial_threshold`, `check_document_validity`, etc. seront remplacées par le `ComplianceChain` qui utilise le RAG et LLM.

2. **Anonymisation**: Migrer de regex simple vers Presidio complet tout en maintenant la rétrocompatibilité.

3. **Base de données**: Ajouter PostgreSQL pour les logs d'audit sans impacter l'analyse temps réel.

4. **Extension**: Peu de changements - principalement ajouter le support PDF.js et streaming.

---

*Document préparé pour l'équipe G7 - Défi IAgouv 2025*

