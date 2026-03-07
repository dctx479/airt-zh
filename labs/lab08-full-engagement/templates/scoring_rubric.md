# Lab 08 - Full AI Red Team Engagement: Scoring Rubric

**Total Points: 100**

This rubric is used to evaluate the completeness and quality of the red team engagement. Each section is scored independently. Partial credit is awarded for incomplete but meaningful work.

---

## 1. Reconnaissance Completeness (10 points)

| Criteria | Points | Description |
|----------|--------|-------------|
| Service enumeration | 3 | Identified all 4 application services and their ports |
| Endpoint discovery | 3 | Mapped all API endpoints for each service (/, /chat, /query, /ingest, /documents, /memory, /execute, /status, /action, /health) |
| Technology identification | 2 | Identified tech stack: Flask, Ollama/Mistral, ChromaDB, Redis |
| Attack surface documentation | 2 | Created structured inventory of all entry points, trust boundaries, and data flows |

**Scoring Guide:**
- 10 pts: Complete enumeration of all services, endpoints, tech stack, and attack surface documented in structured format
- 7-9 pts: Most services and endpoints identified, minor gaps in documentation
- 4-6 pts: Partial enumeration, several services or endpoints missed
- 1-3 pts: Minimal reconnaissance, only obvious services identified
- 0 pts: No meaningful reconnaissance performed

---

## 2. Vulnerability Discovery (40 points)

### 2.1 Customer Chatbot Vulnerabilities (10 points)

| Criteria | Points | Description |
|----------|--------|-------------|
| System prompt extraction | 4 | Successfully extracted the full system prompt containing credentials via prompt injection |
| Credential discovery | 3 | Identified admin credentials, API keys, and internal URLs from the system prompt |
| FLAG capture | 2 | Retrieved FLAG{ch4tb0t_syst3m_pr0mpt_l3ak3d_2024} |
| RAG forwarding abuse | 1 | Discovered and exploited the use_rag parameter to query the internal RAG system through the chatbot |

### 2.2 Internal RAG System Vulnerabilities (10 points)

| Criteria | Points | Description |
|----------|--------|-------------|
| Unauthenticated access | 2 | Demonstrated that all endpoints are accessible without authentication |
| Confidential data extraction | 3 | Retrieved confidential documents (HR data, financial reports, infrastructure credentials) via /documents or /query |
| Document poisoning | 3 | Successfully injected a malicious document via /ingest that altered subsequent query responses (indirect prompt injection) |
| FLAG capture | 2 | Retrieved FLAG{r4g_kn0wl3dg3_b4s3_c0mpr0m1s3d} |

### 2.3 Agent System Vulnerabilities (10 points)

| Criteria | Points | Description |
|----------|--------|-------------|
| Memory exposure | 2 | Accessed all shared agent memory via /memory (credentials, SSH keys, config) |
| Memory poisoning | 2 | Wrote malicious data to shared memory via POST /memory to influence agent behavior |
| Agent impersonation / injection | 2 | Crafted messages that caused agents to perform unauthorized actions (refunds, escalations) |
| Command execution | 2 | Achieved arbitrary command execution via /execute endpoint or agent EXEC: action |
| FLAG capture | 2 | Retrieved FLAG{ag3nt_t00l_abus3_cmd_3x3c} |

### 2.4 Admin Portal Vulnerabilities (10 points)

| Criteria | Points | Description |
|----------|--------|-------------|
| Zero-auth access | 2 | Demonstrated that admin portal is accessible without any authentication |
| Service status information disclosure | 2 | Extracted detailed service information from /status endpoint including the admin flag |
| Cross-service action execution | 3 | Used /action endpoint to send commands to other services (chat, query, ingest, execute) |
| HTML source flag discovery | 1 | Found FLAG in HTML comments via view-source |
| FLAG capture | 2 | Retrieved FLAG{adm1n_p0rt4l_z3r0_auth_pwn3d} |

---

## 3. Attack Chain Construction (20 points)

### 3.1 Chain 1: Chatbot to RAG Poisoning to Data Exfiltration (7 points)

| Criteria | Points | Description |
|----------|--------|-------------|
| Initial access via chatbot | 2 | Used prompt injection on customer chatbot to discover internal RAG endpoint |
| Lateral movement to RAG | 2 | Pivoted from chatbot to directly query/poison the RAG system |
| Data exfiltration | 2 | Extracted confidential documents from RAG knowledge base |
| Chain documentation | 1 | Clearly documented the full chain with evidence at each step |

### 3.2 Chain 2: Agent Memory Poisoning to Command Execution (7 points)

| Criteria | Points | Description |
|----------|--------|-------------|
| Memory reconnaissance | 2 | Read agent shared memory to understand data structure and stored secrets |
| Memory poisoning | 2 | Injected malicious data into agent memory that influenced agent behavior |
| Tool abuse / command execution | 2 | Leveraged agent tools (EXEC, REFUND) to achieve unauthorized actions |
| Chain documentation | 1 | Clearly documented the full chain with evidence at each step |

### 3.3 Chain 3: Admin Portal to Full Compromise (6 points)

| Criteria | Points | Description |
|----------|--------|-------------|
| Admin portal access | 1 | Accessed admin portal without authentication |
| Cross-service manipulation | 2 | Used admin /action endpoint to control all three backend services |
| Full kill chain | 2 | Demonstrated complete compromise: poisoned RAG, wrote agent memory, executed commands, all via admin portal |
| Master FLAG | 1 | Discovered FLAG{full_k1ll_ch41n_c0mpl3t3_2024} |

---

## 4. Impact Demonstration (15 points)

| Criteria | Points | Description |
|----------|--------|-------------|
| Data confidentiality breach | 4 | Demonstrated extraction of confidential data (credentials, financial data, PII, SSH keys) from multiple services |
| Data integrity compromise | 4 | Demonstrated ability to modify system state: poisoned knowledge base, corrupted agent memory, processed unauthorized refunds |
| System compromise | 4 | Demonstrated command execution on agent system container, showing potential for further lateral movement |
| Business impact articulation | 3 | Clearly explained real-world impact: financial loss (unauthorized refunds), regulatory risk (PII exposure), operational risk (system compromise) |

**Scoring Guide:**
- 13-15 pts: Impact demonstrated across all three CIA pillars with clear business impact narrative
- 9-12 pts: Strong demonstration of 2-3 impact areas with adequate business context
- 5-8 pts: Some impact demonstrated but lacking depth or business context
- 1-4 pts: Minimal impact demonstration
- 0 pts: No impact analysis provided

---

## 5. Report Quality (15 points)

| Criteria | Points | Description |
|----------|--------|-------------|
| Structure and organization | 3 | Report follows professional template, clear sections, logical flow |
| Technical accuracy | 3 | Findings are technically correct, reproducible, with accurate severity ratings |
| Evidence quality | 3 | Includes exact commands, full request/response pairs, and clear proof of exploitation |
| MITRE ATLAS mapping | 2 | Findings correctly mapped to MITRE ATLAS techniques |
| Remediation quality | 2 | Remediation recommendations are specific, actionable, and prioritized (30/60/90 day plan) |
| Executive summary | 2 | Executive summary is concise, accurate, and communicates risk to non-technical stakeholders |

**Scoring Guide:**
- 13-15 pts: Professional-grade report suitable for executive and technical audiences
- 9-12 pts: Good report with minor gaps in evidence or recommendations
- 5-8 pts: Adequate report but missing several key elements
- 1-4 pts: Minimal or poorly organized report
- 0 pts: No report provided

---

## Grade Scale

| Score | Grade | Description |
|-------|-------|-------------|
| 90-100 | A | Exceptional - Complete engagement with professional reporting |
| 80-89 | B | Proficient - Strong engagement with minor gaps |
| 70-79 | C | Competent - Adequate engagement with some missing elements |
| 60-69 | D | Developing - Partial engagement with significant gaps |
| Below 60 | F | Incomplete - Major areas of the engagement not addressed |

---

## Bonus Points (up to 10 extra)

| Criteria | Points | Description |
|----------|--------|-------------|
| Novel attack technique | +3 | Discovered an attack vector not explicitly outlined in the lab instructions |
| Automation | +3 | Created scripts to automate parts of the attack chain |
| Defense recommendations beyond template | +2 | Provided novel or particularly insightful defense recommendations |
| MITRE ATLAS depth | +2 | Mapped findings to multiple ATLAS techniques with detailed justification |
