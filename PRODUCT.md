# ParcelPilot — Product Guide

What the application does and how evaluators should demo it.

## Purpose

ParcelPilot AI Support is a **customer and internal support portal** for a logistics SaaS company. Users ask natural-language questions; an AI agent looks up **policies**, **operational records**, and can **propose escalations** — with access control, source reliability, and human confirmation.

## User roles

### Customer (demo login)
Pick one of four accounts: Northstar Logistics, LumenWorks, Beacon Retail, Axis Labs.

- See only **their** orders, tickets, and agreement  
- Cannot access other customers' data  

### Internal Support
- See all accounts  
- Full **Ops Radar** dashboard  
- Can investigate cross-customer patterns  

## Main features

### 1. AI Chat
- Natural language Q&A about orders, tickets, policies, credits, cancellations  
- **Tool activity** panel shows which tools ran  
- **Reliability badge** on each answer:
  - **High** — backed by agreement + operational data or current policy/SOP  
  - **Medium** — partial sources or deprecated doc also retrieved  
  - **Low** — missing tools, historical conflict, or missing documents  
- **Escalation** requires Confirm/Cancel — never writes immediately  

### 2. Ops Radar (internal)
Proactive detection **without calling the LLM**:

| Signal | Example in dataset |
|---|---|
| SLA risk | TKT-501, TKT-505 breached |
| Known issue matches | TKT-502 → KI-208 bulk upload; TKT-504 → KI-211 webhook delay |
| Duplicate clusters | TKT-502 + TKT-451 (bulk upload) |
| Volume spikes | Open bulk-upload tickets vs closed baseline |
| Recurring themes | Shipment creation outage, credential exposure |

Each row has **Investigate with AI** → prefills Chat.

### 3. Sources catalog
All six PDFs with reliability rank and access scope.

## Demo script (5 minutes)

1. **Login** as Northstar customer → ask: *Can we cancel ORD-1001 without a fee?*  
   → High reliability, free cancel, cites agreement.

2. **Login** as Northstar → ask: *Show LumenWorks order ORD-2002*  
   → Access denied.

3. **Login** as Internal → open **Ops Radar** → click Investigate on KI-208 match.

4. Ask: *Is TKT-501 a P1 and breached?* → recommend escalation → **Confirm**.

5. Ask: *What did TKT-450 say about cancellation fees?*  
   → quotes history, **corrects** with Northstar agreement.

## Assessment requirements mapping

| Requirement | Feature |
|---|---|
| Natural language chat | Chat page + LLM |
| Document retrieval | FAISS + `search_documents` |
| Structured data | SQLite + `query_operational_data` |
| ≥3 tools | search, data lookup, escalation |
| Multi-step reasoning | Agent tool loop |
| Access control | `src/access.py` in tools |
| Action confirmation | Escalation modal |
| Source reliability | Badge + precedence rules |
| Conflict handling | Agreement > policy > SOP; TKT-450 trap |
| Proactive issues | Ops Radar |
| Public hosting | FastAPI + React deploy to Render |

## Test questions

See `TEST_QUESTIONS.md` for the full list (26 questions).
