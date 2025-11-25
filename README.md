# OLI - Overlay Legal Intelligence

> 🛡️ **Overlay Legal Intelligence** - Surcouche d'intelligence légale pour les employés gouvernementaux

## Vue d'ensemble

OLI est une extension Chrome innovante qui agit comme une "surcouche de réalité augmentée administrative". Elle analyse en temps réel les documents et formulaires des systèmes gouvernementaux legacy pour identifier automatiquement les non-conformités réglementaires.

## Fonctionnalités

### 🔍 Analyse Multi-Règles
- **Vérification LICO** - Seuil de suffisance financière (R179(b))
- **Validité des documents** - Vérification de la fraîcheur des documents (R54)
- **Vérification d'identité** - Contrôle de complétude des informations (R52)
- **Preuve de fonds** - Validation du type de documentation (R76(1))

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
├── backend/              # Serveur FastAPI (Python)
│   ├── main.py          # API d'analyse de conformité
│   └── requirements.txt
├── extension/            # Extension Chrome (React/Vite)
│   ├── src/
│   │   ├── App.tsx      # Interface principale
│   │   └── lib/
│   │       ├── dom-scanner.ts   # Scanner DOM avec MutationObserver
│   │       ├── anonymizer.ts    # Anonymisation des données
│   │       └── utils.ts
│   ├── public/
│   │   ├── content.js   # Script d'injection DOM
│   │   ├── manifest.json
│   │   └── service-worker.js
│   └── dist/            # Build de production
└── legacy-portal.html    # Portail de test (simulation IRCC)
```

## Installation & Démarrage

### 1. Backend (API)

```bash
cd backend

# Créer un environnement virtuel (optionnel)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Lancer le serveur
python main.py
```

Le serveur démarre sur `http://localhost:8001`

### 2. Extension Chrome

```bash
cd extension

# Installer les dépendances
npm install

# Build pour production
npm run build
```

### 3. Charger l'Extension

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

Le système détectera automatiquement :
- ❌ **Solde insuffisant** : 5 000 $ < 20 635 $ (LICO)
- ⚠️ **Document périmé** : Date de soumission > 6 mois
- ✅ **Preuve de fonds** : Relevé bancaire certifié détecté
- ✅ **Identité** : Informations complètes

Sur la page, le montant "5 000 $" sera :
- Encadré en rouge
- Accompagné d'une icône d'alerte
- Enrichi d'un tooltip explicatif au survol

## API Endpoints

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/analyze` | POST | Analyse de conformité d'un texte |
| `/health` | GET | Vérification de l'état du serveur |
| `/rules` | GET | Liste des règles de conformité |

### Exemple de requête

```bash
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Sophie Martin, Solde: 5 000 $, Date: 2024-01-01"}'
```

## Stack Technique

- **Frontend** : React 18, TypeScript, Vite, Tailwind CSS
- **Backend** : Python 3.11+, FastAPI, Pydantic
- **Extension** : Manifest V3, Chrome Side Panel API
- **Design** : Plus Jakarta Sans, Glassmorphism, Animations CSS

## Conformité G7 IAgouv

Ce projet répond aux critères du Grand Défi IAgouv G7 2025 :

1. ✅ **Impact social** - Réduction de la charge cognitive des agents
2. ✅ **Interopérabilité** - Fonctionne sur tout système legacy via injection DOM
3. ✅ **Explicabilité** - Justifications claires avec références légales
4. ✅ **Évolutivité** - Architecture modulaire, multilingue

## Licence

Projet développé dans le cadre du Grand Défi IAgouv G7 2025.

---

**🍁 Équipe G7 - OLI (Overlay Legal Intelligence)**
