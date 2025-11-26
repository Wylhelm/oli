# Instructions Détaillées pour le Développement de OLI (Overlay Legal Intelligence)

## 1. Vue d'Ensemble du Projet

OLI est une extension navigateur d'assistance décisionnelle qui fonctionne comme une "surcouche de réalité augmentée administrative", analysant en temps réel les documents et formulaires pour identifier les non-conformités réglementaires [1].

---

## 2. Architecture Technique Globale

### 2.1 Stack Technologique Recommandé

```
Frontend (Extension):
├── Framework: JavaScript/TypeScript vanilla ou React
├── Manifest: V3 (Chrome/Edge) + WebExtensions API (Firefox)
├── UI: CSS avec système de design modulaire
└── PDF Parser: PDF.js

Backend/Services:
├── Base vectorielle: Pinecone, Weaviate ou Azure Cognitive Search
├── LLM: Azure OpenAI (hébergé au Canada)
├── API: Node.js/Express ou Python/FastAPI
└── Base de données: PostgreSQL pour logs et traçabilité
```

---

## 3. Module F1 — Scanner d'Interface par Injection DOM

### 3.1 Structure de l'Extension Navigateur

```
extension/
├── manifest.json
├── background/
│   └── service-worker.js
├── content/
│   ├── content-script.js
│   ├── dom-scanner.js
│   ├── form-extractor.js
│   └── pdf-handler.js
├── popup/
│   ├── popup.html
│   ├── popup.js
│   └── popup.css
├── sidebar/
│   ├── sidebar.html
│   ├── sidebar.js
│   └── sidebar.css
├── styles/
│   └── overlay.css
└── utils/
    ├── anonymizer.js
    └── api-client.js
```

### 3.2 Manifest.json (Version 3)

```json
{
  "manifest_version": 3,
  "name": "OLI - Overlay Legal Intelligence",
  "version": "1.0.0",
  "description": "Assistant de conformité réglementaire en temps réel",
  "permissions": [
    "activeTab",
    "storage",
    "scripting",
    "sidePanel"
  ],
  "host_permissions": [
    "<all_urls>"
  ],
  "background": {
    "service_worker": "background/service-worker.js"
  },
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content/content-script.js"],
      "css": ["styles/overlay.css"],
      "run_at": "document_idle"
    }
  ],
  "action": {
    "default_popup": "popup/popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  "side_panel": {
    "default_path": "sidebar/sidebar.html"
  }
}
```

### 3.3 Scanner DOM (dom-scanner.js)

```javascript
class DOMScanner {
  constructor() {
    this.observerConfig = {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['value', 'src', 'data-*']
    };
    this.scanResults = [];
    this.mutationObserver = null;
  }

  // Initialiser l'observation du DOM
  init() {
    this.scanCurrentPage();
    this.setupMutationObserver();
    this.setupFormListeners();
  }

  // Scanner tous les éléments pertinents de la page
  scanCurrentPage() {
    const elements = {
      forms: this.extractForms(),
      inputs: this.extractInputFields(),
      tables: this.extractDataTables(),
      pdfs: this.detectEmbeddedPDFs(),
      textBlocks: this.extractRelevantText()
    };
    return elements;
  }

  // Extraire les formulaires
  extractForms() {
    const forms = document.querySelectorAll('form');
    return Array.from(forms).map(form => ({
      id: form.id || this.generateUniqueId(),
      action: form.action,
      method: form.method,
      fields: this.extractFormFields(form),
      element: form
    }));
  }

  // Extraire les champs de formulaire
  extractFormFields(form) {
    const fields = form.querySelectorAll('input, select, textarea');
    return Array.from(fields).map(field => ({
      name: field.name || field.id,
      type: field.type || field.tagName.toLowerCase(),
      value: field.value,
      label: this.findLabelForField(field),
      required: field.required,
      element: field
    }));
  }

  // Trouver le label associé à un champ
  findLabelForField(field) {
    // Par attribut for
    if (field.id) {
      const label = document.querySelector(`label[for="${field.id}"]`);
      if (label) return label.textContent.trim();
    }
    // Par parent label
    const parentLabel = field.closest('label');
    if (parentLabel) return parentLabel.textContent.trim();
    // Par aria-label
    return field.getAttribute('aria-label') || '';
  }

  // Extraire les tableaux de données
  extractDataTables() {
    const tables = document.querySelectorAll('table');
    return Array.from(tables).map(table => ({
      id: table.id || this.generateUniqueId(),
      headers: this.extractTableHeaders(table),
      rows: this.extractTableRows(table),
      element: table
    }));
  }

  extractTableHeaders(table) {
    const headers = table.querySelectorAll('th');
    return Array.from(headers).map(th => th.textContent.trim());
  }

  extractTableRows(table) {
    const rows = table.querySelectorAll('tbody tr');
    return Array.from(rows).map(row => {
      const cells = row.querySelectorAll('td');
      return Array.from(cells).map(cell => cell.textContent.trim());
    });
  }

  // Détecter les PDFs intégrés
  detectEmbeddedPDFs() {
    const pdfElements = [
      ...document.querySelectorAll('embed[type="application/pdf"]'),
      ...document.querySelectorAll('iframe[src*=".pdf"]'),
      ...document.querySelectorAll('object[data*=".pdf"]')
    ];
    return pdfElements.map(el => ({
      src: el.src || el.data,
      element: el
    }));
  }

  // Observer les mutations du DOM
  setupMutationObserver() {
    this.mutationObserver = new MutationObserver((mutations) => {
      mutations.forEach(mutation => {
        if (this.isRelevantMutation(mutation)) {
          this.handleDOMChange(mutation);
        }
      });
    });
    this.mutationObserver.observe(document.body, this.observerConfig);
  }

  isRelevantMutation(mutation) {
    // Filtrer les mutations pertinentes
    const relevantTags = ['INPUT', 'SELECT', 'TEXTAREA', 'FORM', 'TABLE'];
    if (mutation.type === 'childList') {
      return Array.from(mutation.addedNodes).some(
        node => node.nodeType === 1 && relevantTags.includes(node.tagName)
      );
    }
    return mutation.type === 'attributes';
  }

  handleDOMChange(mutation) {
    // Émettre un événement pour déclencher une nouvelle analyse
    const event = new CustomEvent('oli-dom-change', {
      detail: { mutation, timestamp: Date.now() }
    });
    document.dispatchEvent(event);
  }

  // Écouter les changements de formulaires
  setupFormListeners() {
    document.addEventListener('input', this.debounce((e) => {
      if (this.isFormElement(e.target)) {
        this.onFieldChange(e.target);
      }
    }, 500));

    document.addEventListener('change', (e) => {
      if (this.isFormElement(e.target)) {
        this.onFieldChange(e.target);
      }
    });
  }

  isFormElement(element) {
    return ['INPUT', 'SELECT', 'TEXTAREA'].includes(element.tagName);
  }

  onFieldChange(field) {
    const event = new CustomEvent('oli-field-change', {
      detail: {
        field: {
          name: field.name || field.id,
          value: field.value,
          type: field.type
        },
        timestamp: Date.now()
      }
    });
    document.dispatchEvent(event);
  }

  generateUniqueId() {
    return `oli-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  destroy() {
    if (this.mutationObserver) {
      this.mutationObserver.disconnect();
    }
  }
}

export default DOMScanner;
```

### 3.4 Gestionnaire PDF (pdf-handler.js)

```javascript
class PDFHandler {
  constructor() {
    this.pdfjsLib = null;
  }

  async init() {
    // Charger PDF.js dynamiquement
    if (!this.pdfjsLib) {
      this.pdfjsLib = await import('pdfjs-dist');
      this.pdfjsLib.GlobalWorkerOptions.workerSrc = 
        chrome.runtime.getURL('lib/pdf.worker.min.js');
    }
  }

  async extractTextFromPDF(pdfSource) {
    await this.init();
    
    try {
      const pdf = await this.pdfjsLib.getDocument(pdfSource).promise;
      const textContent = [];

      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const text = await page.getTextContent();
        const pageText = text.items.map(item => item.str).join(' ');
        textContent.push({
          page: i,
          text: pageText
        });
      }

      return {
        success: true,
        totalPages: pdf.numPages,
        content: textContent
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async extractFormFieldsFromPDF(pdfSource) {
    await this.init();
    
    try {
      const pdf = await this.pdfjsLib.getDocument(pdfSource).promise;
      const fields = [];

      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const annotations = await page.getAnnotations();
        
        annotations.forEach(annotation => {
          if (annotation.subtype === 'Widget') {
            fields.push({
              page: i,
              name: annotation.fieldName,
              type: annotation.fieldType,
              value: annotation.fieldValue,
              rect: annotation.rect
            });
          }
        });
      }

      return { success: true, fields };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
}

export default PDFHandler;
```

### 3.5 Anonymiseur de Données (anonymizer.js)

L'anonymisation complète est requise avant tout traitement IA [1].

```javascript
class DataAnonymizer {
  constructor() {
    this.patterns = {
      // Numéro d'assurance sociale canadien
      sin: /\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\b/g,
      // Numéro de passeport
      passport: /\b[A-Z]{2}\d{6}\b/g,
      // Email
      email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
      // Téléphone canadien
      phone: /\b(\+1[-\s]?)?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b/g,
      // Code postal canadien
      postalCode: /\b[A-Z]\d[A-Z][-\s]?\d[A-Z]\d\b/gi,
      // Numéro de carte de crédit
      creditCard: /\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b/g,
      // Date de naissance (formats variés)
      dob: /\b\d{4}[-/]\d{2}[-/]\d{2}\b|\b\d{2}[-/]\d{2}[-/]\d{4}\b/g,
      // Numéro de permis de conduire
      driversLicense: /\b[A-Z]\d{4}[-\s]?\d{5}[-\s]?\d{5}\b/g,
      // Adresse IP
      ip: /\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g
    };

    this.tokenMap = new Map();
    this.reverseMap = new Map();
  }

  anonymize(data) {
    if (typeof data === 'string') {
      return this.anonymizeString(data);
    } else if (typeof data === 'object') {
      return this.anonymizeObject(data);
    }
    return data;
  }

  anonymizeString(text) {
    let anonymized = text;
    
    for (const [type, pattern] of Object.entries(this.patterns)) {
      anonymized = anonymized.replace(pattern, (match) => {
        return this.createToken(match, type);
      });
    }

    // Anonymiser les noms propres (heuristique)
    anonymized = this.anonymizeProperNouns(anonymized);
    
    return anonymized;
  }

  anonymizeObject(obj) {
    const sensitiveFields = [
      'name', 'nom', 'prenom', 'firstName', 'lastName',
      'email', 'courriel', 'phone', 'telephone',
      'address', 'adresse', 'sin', 'nas',
      'passport', 'passeport', 'dob', 'dateOfBirth',
      'dateNaissance', 'creditCard', 'carte'
    ];

    const anonymized = {};
    
    for (const [key, value] of Object.entries(obj)) {
      const lowerKey = key.toLowerCase();
      const isSensitive = sensitiveFields.some(f => lowerKey.includes(f));
      
      if (isSensitive && typeof value === 'string') {
        anonymized[key] = this.createToken(value, 'field_' + key);
      } else if (typeof value === 'object' && value !== null) {
        anonymized[key] = this.anonymizeObject(value);
      } else if (typeof value === 'string') {
        anonymized[key] = this.anonymizeString(value);
      } else {
        anonymized[key] = value;
      }
    }

    return anonym