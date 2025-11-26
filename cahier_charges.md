# SPECIFICATIONS
OLI — Overlay Legal Intelligence
Decision support solution for regulatory compliance
G7 Grand Challenge IAgouv 2025
Problem Statement Problem 2 — Laws, policies, and regulations
Team Team G7
Deadline December 1, 2025, 3:00 PM ET
Final Deliverable AI-generated demonstration video (Google AI Studio)
 
1. Context and Problem Statement
1.1 Official Statement (Statement 2)
"The public service works with many laws, policies, and regulations that are complex to navigate for clients and employees. Design a solution to streamline the interpretation and application of rules to increase consistency and compliance, and to reduce the cognitive load of employees."
1.2 Problem Analysis
Public servants face excessive cognitive load daily caused by the complexity of legal frameworks. This situation creates several critical challenges:
• Information fragmentation: laws, regulations, and policies scattered across multiple sources
• Human error risk: inconsistent rule interpretations
• Extended processing time: time-consuming manual verifications
• Lack of traceability: difficulty justifying decisions with precise legal references
• Legacy systems: inability to modify backends of existing government applications
2. Proposed Solution Overview
2.1 Global Vision
OLI (Overlay Legal Intelligence) is a decision support solution inspired by Grammarly, designed as an administrative augmented reality overlay. OLI integrates directly into employees' browsers as an extension and analyzes documents and forms in real-time to automatically identify regulatory non-compliance.
2.2 Key Concept: the "Man-in-the-Browser" Approach
The architecture relies on non-invasive DOM injection that allows instant modernization of existing government systems (legacy) without modifying a single line of backend code. This approach guarantees rapid, universal, and interoperable deployment.
3. Project Objectives
3.1 Main Objective
Reduce the cognitive load of public servants by automating non-compliance identification and providing instant contextual legal references.
3.2 Specific Objectives
4. Increase consistency: standardize rule interpretation across all agents and departments
5. Improve compliance: reduce processing errors through proactive anomaly detection
6. Accelerate processing: reduce manual verification time by at least 40%
7. Ensure traceability: link each decision to its official legal source with clickable URL
8. Protect data: guarantee complete anonymization before any AI processing
 
9. Expected Features
4.1 Main Features
F1 — Interface Scanner via DOM Injection
• Browser extension compatible with Chrome/Edge/Firefox
• Automatic reading of forms, fields, and open PDF documents
• Works on any legacy system without backend modification
F2 — RAG Compliance Engine (Retrieval-Augmented Generation)
• Connection to a vector database containing Canadian laws (e.g., IRPR, LICO 2025)
• Contextual analysis via Azure OpenAI or equivalent Canadian-hosted AI model
• Real-time cross-referencing of extracted data with regulatory thresholds and criteria
F3 — Color Code System (Compliance Zones)
Zone | Meaning | Example
🟢 GREEN | Compliance met | Sufficient funds, compliant letters
🟡 YELLOW | Warning | Missing elements, date inconsistency
🔴 RED | Critical risk | Fraudulent documents, thresholds not met
F4 — Contextual Analysis Side Panel
• Floating sidebar with case summary
• Completeness percentage and risk level display
• List of validated points and detected anomalies
• AI recommendations with suggested actions (e.g., "Request co-signer")
F5 — Clickable Links to Official Sources
• Automatic URL insertion to Justice.gc.ca and official legal sources
• Citation of applicable article or regulation (e.g., "R179(b)")
• Reference storage in vector database for traceability
4.2 Security Features
F6 — Data Anonymization (Microsoft Presidio)
• Automatic redaction of personal data before AI processing
• Replacement with logical abstractions (e.g., "<ACCOUNT_ID>")
• Compliance with the Privacy Act
 
5. Technical and Organizational Constraints
5.1 Technical Constraints
Constraint | Specification
Architecture | Browser extension (overlay) or integrated AI assistant — no backend access required
AI Hosting | Azure OpenAI (Canada region) or equivalent government infrastructure
Database | Vector database containing Canadian legislation (to build or existing)
Security | Mandatory anonymization via Microsoft Presidio before sending to LLM
Interoperability | Compatible with legacy systems via DOM injection (no API integration required)
Languages | Bilingual (French/English) — multilingual extension
5.2 Organizational Constraints
• Deadline: submission before December 1, 2025, 3:00 PM ET
• Team: maximum 4 members
• Submission format: Impact Canada portal + demonstration video
• Ethical compliance: G7 responsible AI principles (fairness, transparency, privacy)
• MVP video: demonstration generated by structured prompts on Google AI Studio (Gemini)
6. Target Users
6.1 Primary Users
• Public servants: processing applications subject to regulatory frameworks (immigration, taxation, health, vehicles, etc.)
• Supervisors: validating decisions and needing legal traceability
6.2 Secondary Users
• Citizens and businesses: via a public version of the overlay on government websites, helping them pre-validate their applications
• Government legal teams: for knowledge base updates
6.3 Illustrative Persona
Sophie, an immigration officer at IRCC, processes 40 files per day. She spends 30% of her time manually verifying LICO financial thresholds and document compliance. With OLI, the analysis is automatic: she opens the applicant's PDF bank statement, and the overlay instantly indicates that the average balance ($5,000) is below the required threshold ($20,635), with a clickable reference to article R179(b).
 
7. Success Criteria
The following criteria are aligned with the four official evaluation pillars of the G7 IAgouv Grand Challenge:
7.1 Impact and Social Good (G7 Criterion #1)
1. Measurable reduction of agent cognitive load (target: -40% verification time)
2. Improved decision consistency between agents handling similar cases
3. Compliance with responsible AI principles: fairness, privacy, accessibility
4. Citizen benefit via better quality and faster service
7.2 Interoperability (G7 Criterion #2)
5. Works on any existing system via DOM injection (no backend modification)
6. Transferable between ministries and departments (immigration, finance, health, etc.)
7. Applicable to other G7 countries with legislative database adaptation
8. Compatible with open data resources provided by the challenge
7.3 Explainability (G7 Criterion #3)
9. Each detection accompanied by a plain language justification
10. Precise legal reference with clickable official URL (Justice.gc.ca)
11. Intuitive color code system reducing ambiguity (green/yellow/red)
12. Complete decision traceability for audit and accountability
7.4 Scalability (G7 Criterion #4)
13. Modular architecture allowing addition of new laws and regulations
14. Extensible to other domains (taxation, health, environment, commerce)
15. Capacity to support growth in user volume and cases
16. Multilingual (French/English minimum, extensible to G7 languages)
17. Expected Deliverables
Deliverable | Description
Demonstration video | AI-generated video via Google AI Studio illustrating the scenario of an immigration agent using OLI to process Sophie Martin's case
Specifications | Present document detailing objectives, features, constraints, and success criteria
UI/UX Mockups | Screenshots of side panel, color system, and agent interface
Impact Canada Submission | Form completed on official portal before December 1, 2025
18. Appendices and References
9.1 Open Data Resources (Problem 2)
• Canada: House of Commons Debates, Open Data Portal
• United Kingdom: UK Legislation, UK Legal API, UK Parliament MCP Server
• European Union: EUR-Lex (legislation, case law)
• Germany: Bundestag, Federal Official Journal, AI Registry
• Italy: Active Laws Portal, Developers Italia
• Japan: Legal MCQ Dataset, e-Gov Data Portal
9.2 Official Links
• Impact Canada Portal: impact.canada.ca/en/challenges/g7-govAI
• Official Canada.ca Page: canada.ca/.../responsible-use-ai/ai-grand-challenge.html
• Contact: g7aichallenge-defiiag7@tbs-sct.gc.ca
