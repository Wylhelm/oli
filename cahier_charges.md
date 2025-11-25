# CAHIER DES CHARGES
OLI — Overlay Legal Intelligence
Solution d'assistance décisionnelle pour la conformité réglementaire
Défi Grand Défi IAgouv du G7 2025
Problématique Problématique 2 — Lois, politiques et réglementations
Équipe Équipe G7
Date limite 1er décembre 2025, 15h00 HE
Livrable final Vidéo de démonstration générée par IA (Google AI Studio)
 
1.	Contexte et énoncé de la problématique
1.1 Énoncé officiel (Statement 2)
« The public service works with many laws, policies, and regulations that are complex to navigate for clients and employees. Design a solution to streamline the interpretation and application of rules to increase consistency and compliance, and to reduce the cognitive load of employees. »
1.2 Analyse du problème
Les employés de la fonction publique font face quotidiennement à une charge cognitive excessive causée par la complexité des cadres légaux. Cette situation engendre plusieurs défis critiques :
• Fragmentation de l'information : lois, règlements et politiques dispersés dans de multiples sources
• Risque d'erreur humaine : interprétations incohérentes des règles applicables
• Temps de traitement prolongé : vérifications manuelles chronophages
• Manque de traçabilité : difficulté à justifier les décisions par des références légales précises
• Systèmes legacy : impossibilité de modifier les backends des applications gouvernementales existantes
2.	Présentation de la solution proposée
2.1 Vision globale
OLI (Overlay Legal Intelligence) est une solution d'assistance décisionnelle inspirée de Grammarly, conçue comme une surcouche de réalité augmentée administrative. OLI s'intègre directement dans le navigateur des employés sous forme d'extension et analyse en temps réel les documents et formulaires pour identifier automatiquement les non-conformités réglementaires.
2.2 Concept clé : l'approche « Man-in-the-Browser »
L'architecture repose sur une injection DOM non-invasive qui permet de moderniser instantanément les systèmes gouvernementaux existants (legacy) sans modifier une seule ligne de code backend. Cette approche garantit un déploiement rapide, universel et interopérable.
3.	Objectifs du projet
3.1 Objectif principal
Réduire la charge cognitive des employés de la fonction publique en automatisant l'identification des non-conformités et en fournissant des références légales contextuelles instantanées.
3.2 Objectifs spécifiques
4.	Augmenter la cohérence : standardiser l'interprétation des règles à travers tous les agents et départements
5.	Améliorer la conformité : réduire les erreurs de traitement par détection proactive des anomalies
6.	Accélérer le traitement : diminuer le temps de vérification manuelle de 40% minimum
7.	Assurer la traçabilité : lier chaque décision à sa source juridique officielle avec URL cliquable
8.	Protéger les données : garantir l'anonymisation complète avant tout traitement IA
 
9.	Fonctionnalités attendues
4.1 Fonctionnalités principales
F1 — Scanner d'interface par injection DOM
• Extension navigateur compatible Chrome/Edge/Firefox
• Lecture automatique des formulaires, champs et documents PDF ouverts
• Fonctionnement sur tout système legacy sans modification backend
F2 — Moteur de conformité RAG (Retrieval-Augmented Generation)
• Connexion à une base vectorielle contenant les lois canadiennes (ex: RIPR, LICO 2025)
• Analyse contextuelle via Azure OpenAI ou modèle IA équivalent hébergé au Canada
• Croisement en temps réel des données extraites avec les seuils et critères réglementaires
F3 — Système de code couleur (Zones de conformité)
Zone Signification Exemple
🟢 VERTE Conformité respectée Fonds suffisants, lettres conformes
🟡 JAUNE Avertissement Éléments manquants, incohérence de dates
🔴 ROUGE Risque critique Documents frauduleux, seuils non respectés
F4 — Panneau latéral d'analyse contextuelle
• Barre latérale flottante avec synthèse du dossier
• Affichage du pourcentage de complétude et niveau de risque
• Liste des points validés et anomalies détectées
• Recommandations IA avec actions suggérées (ex: « Demander co-signataire »)
F5 — Liens cliquables vers sources officielles
• Insertion automatique d'URLs vers Justice.gc.ca et sources légales officielles
• Citation de l'article ou règlement applicable (ex: « R179(b) »)
• Stockage des références dans la base vectorielle pour traçabilité
4.2 Fonctionnalités de sécurité
F6 — Anonymisation des données (Microsoft Presidio)
• Expurgation automatique des données personnelles avant traitement IA
• Remplacement par abstractions logiques (ex: « <ACCOUNT_ID> »)
• Conformité avec la Loi sur la protection des renseignements personnels
 
5. Contraintes techniques et organisationnelles
5.1 Contraintes techniques
Contrainte Spécification
Architecture Extension navigateur (overlay) ou assistant IA intégré — aucun accès backend requis
Hébergement IA Azure OpenAI (région Canada) ou infrastructure gouvernementale équivalente
Base de données Base vectorielle contenant la législation canadienne (à construire ou existante)
Sécurité Anonymisation obligatoire via Microsoft Presidio avant envoi au LLM
Interopérabilité Compatible avec systèmes legacy via injection DOM (aucune intégration API requise)
Langues Bilingue (français/anglais) — multilingue en extension
5.2 Contraintes organisationnelles
• Délai : soumission avant le 1er décembre 2025, 15h00 HE
• Équipe : maximum 4 membres
• Format de soumission : portail Impact Canada + vidéo de démonstration
• Conformité éthique : principes d'IA responsable du G7 (équité, transparence, vie privée)
• MVP vidéo : démonstration générée par prompts structurés sur Google AI Studio (Gemini)
6. Utilisateurs visés
6.1 Utilisateurs primaires
• Agents de la fonction publique : traitant des demandes soumises à des cadres réglementaires (immigration, fiscalité, santé, véhicules, etc.)
• Superviseurs : validant les décisions et ayant besoin de traçabilité juridique
6.2 Utilisateurs secondaires
• Citoyens et entreprises : via une version publique de l'overlay sur les sites gouvernementaux, les aidant à pré-valider leurs demandes
• Équipes juridiques gouvernementales : pour mise à jour de la base de connaissances
6.3 Persona illustratif
Sophie, agente d'immigration à IRCC, traite 40 dossiers par jour. Elle passe 30% de son temps à vérifier manuellement les seuils financiers LICO et la conformité documentaire. Avec OLI, l'analyse est automatique : elle ouvre le relevé bancaire PDF du demandeur, et l'overlay lui indique instantanément que le solde moyen (5 000 $) est inférieur au seuil requis (20 635 $), avec référence à l'article R179(b) cliquable.
 
7. Critères de réussite
Les critères suivants sont alignés sur les quatre piliers d'évaluation officiels du Grand Défi IAgouv G7 :
7.1 Impact et bien social (Critère G7 #1)
1.	Réduction mesurable de la charge cognitive des agents (cible : -40% temps de vérification)
2.	Amélioration de la cohérence des décisions entre agents traitant des dossiers similaires
3.	Respect des principes d'IA responsable : équité, vie privée, accessibilité
4.	Bénéfice pour les citoyens via une meilleure qualité et rapidité de service
7.2 Interopérabilité (Critère G7 #2)
5.	Fonctionne sur tout système existant via injection DOM (aucune modification backend)
6.	Transférable entre ministères et départements (immigration, finances, santé, etc.)
7.	Applicable aux autres pays du G7 avec adaptation de la base législative
8.	Compatible avec les ressources de données ouvertes fournies par le défi
7.3 Explicabilité (Critère G7 #3)
9.	Chaque détection est accompagnée d'une justification en langage clair
10.	Référence juridique précise avec URL officielle cliquable (Justice.gc.ca)
11.	Système de code couleur intuitif réduisant l'ambiguïté (vert/jaune/rouge)
12.	Traçabilité complète des décisions pour audit et reddition de comptes
7.4 Évolutivité / Scalability (Critère G7 #4)
13.	Architecture modulaire permettant l'ajout de nouvelles lois et règlements
14.	Extensible à d'autres domaines (fiscalité, santé, environnement, commerce)
15.	Capacité à supporter une croissance du volume d'utilisateurs et de dossiers
16.	Multilingue (français/anglais minimum, extensible aux langues du G7)
17.	Livrables attendus
Livrable Description
Vidéo de démonstration Vidéo générée par IA via Google AI Studio illustrant le scénario d'un agent d'immigration utilisant OLI pour traiter le dossier de Sophie Martin
Cahier des charges Document présent détaillant objectifs, fonctionnalités, contraintes et critères de réussite
Maquettes UI/UX Captures d'écran du panneau latéral, système de couleurs et interface agent
Soumission Impact Canada Formulaire complété sur le portail officiel avant le 1er décembre 2025
18.	Annexes et références
9.1 Ressources de données ouvertes (Problématique 2)
• Canada : Délibérations de la Chambre des communes, Portail de données ouvertes
• Royaume-Uni : UK Legislation, UK Legal API, UK Parliament MCP Server
• Union européenne : EUR-Lex (législation, jurisprudence)
• Allemagne : Bundestag, Journal officiel fédéral, Registre IA
• Italie : Portail des lois actives, Developers Italia
• Japon : Ensemble de données juridiques MCQ, Portail e-Gov Data
9.2 Liens officiels
• Portail Impact Canada : impact.canada.ca/en/challenges/g7-govAI
• Page officielle Canada.ca : canada.ca/.../responsible-use-ai/ai-grand-challenge.html
• Contact : g7aichallenge-defiiag7@tbs-sct.gc.ca
