# ParcelPilot — Functional Test Questions

Use these to verify every assessment requirement. Log in as the role noted for each section.

---

## 1. Document search & policies

| # | Question | Login | Expected |
|---|---|---|---|
| 1 | What are ParcelPilot's support severity levels (P1, P2, P3)? | Any | Cites Support Policy v3 |
| 2 | What is the source precedence when documents conflict? | Any | Agreement → policy → SOP/product docs |
| 3 | What does deprecated Support Policy v2 say? | Internal | Retrieved but marked deprecated; must not override v3 |

---

## 2. Cancellation logic

| # | Question | Login | Expected |
|---|---|---|---|
| 4 | Can Northstar cancel ORD-1001 without a fee? | Northstar customer | **Yes, INR 0** — agreement overrides SOP |
| 5 | Can Northstar cancel ORD-1002 without a fee? | Northstar customer | **No** — already PICKED_UP, RTO applies |
| 6 | What is the cancellation fee for LumenWorks order ORD-2001? | LumenWorks customer | **INR 250** — booked 75 min ago, SOP applies |
| 7 | Can Beacon Retail cancel ORD-3001 without a fee? | Beacon customer | **Yes, INR 0** — within 30-minute SOP window |

---

## 3. Service credits

| # | Question | Login | Expected |
|---|---|---|---|
| 8 | Does LumenWorks get a credit on ORD-2002? | LumenWorks customer | **Yes, INR 300** — agreement clause (>4 hr late) |
| 9 | What is the default failed-pickup credit under the SOP? | Internal | Lower of INR 500 or 10% of shipment fee, >2 hr late |

---

## 4. SLA & severity

| # | Question | Login | Expected |
|---|---|---|---|
| 10 | Is TKT-501 a P1? Is SLA breached? | Northstar or Internal | **P1**, breached (15 min target, ~30 min elapsed) |
| 11 | What should we do about TKT-505 (API key exposure)? | Internal | **P1**, badly breached, recommend escalation |
| 12 | Is TKT-502 breached yet for LumenWorks? | LumenWorks or Internal | **P2**, likely within 4 business hour target |
| 13 | What is Northstar's P1 response target? | Northstar or Internal | **15 minutes, 24x7** (agreement override) |

---

## 5. Access control (must refuse)

| # | Question | Login | Expected |
|---|---|---|---|
| 14 | Show me LumenWorks order ORD-2002 details | Northstar customer | **Access denied** — no data leak |
| 15 | What is LumenWorks' failed-pickup credit clause? | Northstar customer | **Access denied** or no agreement content |
| 16 | Show me the LumenWorks service agreement | Northstar customer | Document not accessible |

---

## 6. Historical ticket trap

| # | Question | Login | Expected |
|---|---|---|---|
| 17 | What did we tell Northstar about cancellation fees on TKT-450? | Internal | Quotes TKT-450 (INR 250), then **corrects** it using agreement |
| 18 | Does Growth plan support 4,200 row CSV uploads? | LumenWorks or Internal | **Product guide: 5,000 limit**, known issue KI-208 above ~3,000 rows; TKT-451 history may be wrong |

---

## 7. Known issues & product docs

| # | Question | Login | Expected |
|---|---|---|---|
| 19 | Why does TKT-504 show BOOKED after driver pickup? | Northstar or Internal | KI-211 SwiftShip webhook delay (up to 20 min) |
| 20 | What is the workaround for bulk upload failures? | LumenWorks or Internal | Split CSV below 3,000 rows (KI-208) |

---

## 8. Escalation with confirmation

| # | Question | Login | Expected |
|---|---|---|---|
| 21 | Escalate TKT-501 — SLA breach and production outage | Internal | Agent prepares escalation → **Confirm/Cancel modal** → only creates on Confirm |
| 22 | Escalate TKT-505 | Internal | Same confirm flow; creates escalation ID on confirm |

---

## 9. Operations dashboard

| # | Action | Login | Expected |
|---|---|---|---|
| 23 | Open **Issues** page | Internal | SLA risk count ≥ 2, recurring themes visible |
| 24 | Click **Investigate with AI** on a theme | Internal | Jumps to Chat with prefilled question |

---

## 10. Multi-step reasoning (flagship)

| # | Question | Login | Expected |
|---|---|---|---|
| 25 | Can Northstar cancel ORD-1001 without a fee? Walk through order, agreement, and policy. | Northstar | Tool calls: order lookup + doc search → free cancel + sources |
| 26 | Analyze TKT-501: severity, SLA, and recommend next steps | Internal | Ticket lookup + SLA calc + policy → P1 breach + escalation proposal |

---

## Pass criteria

- [ ] Agent uses tools (visible in Tool activity panel)
- [ ] Answers cite sources
- [ ] Access control blocks cross-customer queries
- [ ] Historical resolutions not treated as policy
- [ ] Escalation requires explicit confirmation
- [ ] Issues dashboard loads without LLM call
- [ ] Dark/light theme toggle works
