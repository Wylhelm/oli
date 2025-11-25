# OLI - Overlay Legal Intelligence

> 🛡️ **Overlay Legal Intelligence** - Surcouche d'intelligence légale pour les employés gouvernementaux

## Vue d'ensemble

OLI est une extension Chrome innovante qui agit comme une "surcouche de réalité augmentée administrative". Elle analyse en temps réel les documents et formulaires des systèmes gouvernementaux legacy pour identifier automatiquement les non-conformités réglementaires.

**Nouveauté v2.0** : Intégration RAG + LLM pour une analyse intelligente basée sur la législation canadienne réelle.

## Fonctionnalités

### 🤖 Analyse IA avec RAG (Retrieval-Augmented Generation)
- **Base de connaissances légales** : 76 lois et règlements d'immigration (7 898 chunks indexés)
- **Recherche sémantique** : ChromaDB avec embeddings multilingues
- **LLM** : Ollama avec modèle `gpt-oss:120b-cloud` pour analyse contextuelle
- **Citations légales** : Références directes à Justice.gc.ca

### 🔍 Analyse Multi-Règles
- **Vérification LICO** - Seuil de suffisance financière (RIPR R179)
- **Validité des documents** - Vérification de la fraîcheur (RIPR R54)
- **Vérification d'identité** - Contrôle de complétude (RIPR R52)
- **Preuve de fonds** - Validation du type de documentation (RIPR R76)

### 📊 Tableau de Bord Intelligent
- Score de risque circulaire (0-100)
- Indicateur de complétude du dossier
- Code couleur intuitif : 🟢 Conforme | 🟡 Avertissement | 🔴 Critique
- Références légales cliquables vers Justice.gc.ca

### 🎯 Injection DOM Avancée
- Surlignage multi-couleurs sur les éléments à risque
- Tooltips interactifs avec détails de conformité
- Indicateur flottant de statut global
- Animations fluides et effets visuels

### 🔒 Sécurité & Confidentialité
- Anonymisation client-side des données personnelles
- Pattern matching pour : NAS, passeports, emails, téléphones, codes postaux
- Aucune donnée personnelle envoyée au backend

## Architecture

```
OLI/
├── backend/                    # Serveur FastAPI (Python)
│   ├── main.py                # API d'analyse de conformité
│   ├── requirements.txt
│   ├── rag/                   # Système RAG
│   │   ├── downloader.py      # Téléchargement lois depuis Justice.gc.ca
│   │   ├── vector_store.py    # ChromaDB + embeddings
│   │   └── retriever.py       # Récupération contexte légal
│   ├── llm/                   # Intégration LLM
│   │   ├── ollama_client.py   # Client Ollama API
│   │   ├── prompts.py         # Templates de prompts
│   │   └── compliance_chain.py # Pipeline complet RAG+LLM
│   └── data/
│       ├── laws/              # 76 documents légaux (JSON)
│       └── chroma_db/         # Base vectorielle
├── extension/                  # Extension Chrome (React/Vite)
│   ├── src/
│   │   ├── App.tsx            # Interface principale
│   │   └── lib/
│   │       ├── dom-scanner.ts # Scanner DOM avec MutationObserver
│   │       ├── anonymizer.ts  # Anonymisation des données
│   │       └── utils.ts
│   ├── public/
│   │   ├── content.js         # Script d'injection DOM
│   │   ├── manifest.json
│   │   └── service-worker.js
│   └── dist/                  # Build de production
└── legacy-portal.html          # Portail de test (simulation IRCC)
```

## Installation & Démarrage

### Prérequis
- Python 3.11+
- Node.js 18+
- Ollama (pour LLM local)
- Conda (recommandé)

### 1. Backend (API + RAG + LLM)

```bash
cd backend

# Créer environnement conda
conda create -n OLI python=3.11
conda activate OLI

# Installer les dépendances
pip install -r requirements.txt

# Télécharger les lois d'immigration (première fois uniquement)
python rag/downloader.py

# Ingérer dans la base vectorielle (première fois uniquement)
python rag/vector_store.py

# Lancer le serveur
uvicorn main:app --reload --port 8001
```

Le serveur démarre sur `http://localhost:8001`

### 2. Ollama (LLM)

```bash
# Installer le modèle
ollama pull gpt-oss:120b-cloud

# Vérifier que Ollama tourne sur localhost:11434
ollama list
```

### 3. Extension Chrome

```bash
cd extension

# Installer les dépendances
npm install

# Build pour production
npm run build
```

### 4. Charger l'Extension

1. Ouvrir Chrome → `chrome://extensions`
2. Activer le **Mode développeur** (coin supérieur droit)
3. Cliquer **Charger l'extension non empaquetée**
4. Sélectionner le dossier `extension/dist`

## Démonstration

### Scénario : Analyse d'un dossier d'immigration

1. **Ouvrir le portail legacy** : Double-cliquer sur `legacy-portal.html`
2. **Activer OLI** : Cliquer sur l'icône de l'extension (🛡️)
3. **Scanner la page** : Cliquer sur "Scanner la page"

### Résultats attendus

Le système détectera automatiquement avec justification légale :
- ❌ **Solde insuffisant** : 5 000 $ < 20 635 $ (RIPR Section 4, R179)
- ⚠️ **Document périmé** : Date de soumission > 6 mois (RIPR Section 44)
- ✅ **Preuve de fonds** : Relevé bancaire certifié détecté (RIPR Section 74)
- ✅ **Identité** : Informations complètes

## API Endpoints

### Analyse

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/analyze` | POST | Analyse règle-based (rapide) |
| `/analyze/llm` | POST | Analyse RAG + LLM (complète) |
| `/health` | GET | État du serveur + RAG + LLM |
| `/rules` | GET | Liste des règles de conformité |

### RAG (Recherche légale)

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/rag/search` | POST | Recherche sémantique dans les lois |
| `/rag/context` | POST | Contexte légal pour un type de vérification |
| `/rag/stats` | GET | Statistiques de la base vectorielle |

### LLM

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/llm/status` | GET | État du LLM et modèle actif |

### Exemple de requête LLM

```bash
curl -X POST http://localhost:8001/analyze/llm \
  -H "Content-Type: application/json" \
  -d '{"text": "Sophie Martin, Solde: 5 000 $, Date: 2024-01-01"}'
```

Réponse :
```json
{
  "overall_status": "CRITIQUE",
  "risk_score": 78,
  "analysis_mode": "llm",
  "checks": [
    {
      "name": "Seuil LICO",
      "status": "AVERTISSEMENT",
      "reference": "IRPR Section 4 & 74",
      "url": "http://laws-lois.justice.gc.ca/eng/regulations/SOR-2002-227/"
    }
  ],
  "sources": [
    {"title": "Immigration and Refugee Protection Regulations", "url": "..."}
  ]
}
```

## Stack Technique

- **Frontend** : React 18, TypeScript, Vite, Tailwind CSS
- **Backend** : Python 3.11+, FastAPI, Pydantic
- **RAG** : ChromaDB, Sentence-Transformers (paraphrase-multilingual-MiniLM-L12-v2)
- **LLM** : Ollama (gpt-oss:120b-cloud)
- **Extension** : Manifest V3, Chrome Side Panel API
- **Data Source** : Justice.gc.ca XML API (76 lois d'immigration)

## Conformité G7 IAgouv

Ce projet répond aux critères du Grand Défi IAgouv G7 2025 :

1. ✅ **Impact social** - Réduction de la charge cognitive des agents
2. ✅ **Interopérabilité** - Fonctionne sur tout système legacy via injection DOM
3. ✅ **Explicabilité** - Justifications claires avec références légales (RAG)
4. ✅ **Évolutivité** - Architecture modulaire, multilingue, LLM interchangeable

## Configuration

Variables d'environnement (optionnel) :

```bash
# Modèle Ollama (défaut: gpt-oss:120b-cloud)
export OLLAMA_MODEL=gpt-oss:120b-cloud

# URL Ollama (défaut: http://localhost:11434)
export OLLAMA_BASE_URL=http://localhost:11434
```

## Licence

Projet développé dans le cadre du Grand Défi IAgouv G7 2025.

---

**🍁 Équipe G7 - OLI (Overlay Legal Intelligence)**
