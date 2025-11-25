Rôle : Tu es un Architecte Logiciel Senior et un Designer UI/UX expert, spécialisé dans les hackathons, les extensions navigateur et l'IA (RAG).
Objectif : Créer un MVP (Minimum Viable Product) fonctionnel pour OLI (Overlay Legal Intelligence). C'est une extension Chrome qui agit comme une surcouche d'intelligence légale pour les employés gouvernementaux.
Contexte Hackathon : Le code doit être propre, modulaire, mais surtout visuellement impressionnant ("Wow effect") et facile à déployer pour une démo.
1. Stack Technique (Obligatoire)
•	Frontend (Extension) : React, Vite, TypeScript, Tailwind CSS, Shadcn/UI (pour des composants magnifiques), Lucide React (icônes).
•	Architecture Extension : Manifest V3, Side Panel API.
•	Backend (API IA) : Python, FastAPI.
•	IA & Logic : LangChain (RAG simple), ChromaDB (Vector Store local), Microsoft Presidio (Simulation d'anonymisation).
•	Mocking : Créer une page HTML simple "Immigration Canada Legacy" pour tester l'extension.
________________________________________
2. Instructions Étape par Étape
Génère le projet en suivant ces étapes précises. Ne t'arrête pas tant que toutes les étapes ne sont pas couvertes.
ÉTAPE 1 : Le "Dummy" Legacy System (La Cible)
Crée un fichier legacy-portal.html simple mais d'apparence "vieux site gouvernemental".
•	Contenu : Un formulaire de demande d'immigration.
•	Données : Affiche un profil statique : "Demandeur : Sophie Martin", "Revenu : 5 000 $", "Date de la demande : 2024-01-01".
•	But : C'est la page que notre extension va scanner.
ÉTAPE 2 : Le Backend (Le Cerveau)
Crée un serveur FastAPI (server.py) avec un endpoint /analyze.
1.	Input : Reçoit du texte (JSON) extrait de la page web.
2.	Sécurité : Utilise une fonction simple anonymize_text(text) qui remplace les noms/dates par des placeholders (ex: <PERSON>).
3.	RAG (Retrieval) : Simule une base vectorielle. Hardcode un petit contexte légal : "Règlement R179(b) : Le seuil de suffisance financière (LICO) pour une personne seule est de 20 635 $. Si le revenu est inférieur, rejeter."
4.	Logique de décision : Compare le revenu reçu (5000) au seuil (20635).
5.	Output : Retourne un JSON structuré :
o	status: "CRITIQUE" (Rouge)
o	summary: "Solde insuffisant détecté."
o	reference: "Loi sur l'immigration, Article R179(b)"
o	url: "https://laws-lois.justice.gc.ca/"
o	recommendation: "Demander un co-signataire ou rejeter la demande."
ÉTAPE 3 : Le Frontend de l'Extension (L'Interface Magnifique)
C'est ici que tu dois exceller. L'UI doit être futuriste mais professionnelle.
•	Structure : Utilise chrome.sidePanel.
•	Design System : Fond blanc épuré, typographie Inter ou Roboto. Utilise des "Cards" avec des ombres douces.
•	Composant Principal (Dashboard) :
o	Header : Logo OLI, statut "Système actif".
o	Zone de Score : Un grand cercle ou une barre de progression montrant "Niveau de Risque".
o	Liste d'Alertes : Crée des composants "AlertCard" dynamiques.
	🟢 Vert : Conformité OK.
	🔴 Rouge : Alerte critique (ex: le problème de fonds financiers).
o	Bouton d'Action : "Générer Rapport" ou "Voir Source Légale".
•	Interaction : Ajoute un bouton dans le panneau "Scanner la page". Au clic, un script content.js lit le document.body.innerText du site legacy et l'envoie au backend.
ÉTAPE 4 : Injection DOM (Réalité Augmentée)
Dans le content.js :
•	Quand l'analyse revient du backend (ex: détection du revenu faible), cherche le texte "5 000 $" dans la page HTML.
•	Entoure ce texte d'une bordure rouge et d'une légère surbrillance rouge (highlight).
•	Ajoute une petite icône "⚠️" à côté du texte sur la page web.
________________________________________
3. Directives de Design (UI/UX)
•	Palette de couleurs :
o	Primaire : Bleu Royal Gouvernemental (#005696)
o	Alerte : Rouge Doux (#EF4444)
o	Succès : Émeraude (#10B981)
o	Fond : Blanc & Gris très clair (#F8FAFC)
•	Style : Utilise des bordures arrondies (rounded-xl), des effets de verre (backdrop-blur), et des animations fluides lors de l'apparition des résultats (fading in).
4. Commande de Génération
Commence par générer l'arborescence des fichiers, puis fournis le code complet pour :
1.	legacy-portal.html
2.	backend/main.py (FastAPI)
3.	extension/manifest.json
4.	extension/src/App.tsx (L'interface React magnifique)
5.	extension/src/content.js (Le script d'injection)
Assure-toi que le code est prêt à être copié et lancé avec npm run dev et uvicorn.
