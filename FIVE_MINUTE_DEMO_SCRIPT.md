# PayPal SubWise AI — Five-Minute Hackathon Demonstration Script

**Target Time:** 5 Minutes (0:00 – 5:00)  
**Presenter Persona:** Lead FinTech Engineer / Co-Founder  
**Primary Demonstration Profile:** **DemoTech Solutions** (Stage 8.5 Isolated 6-Month Illustrative Dataset)  
**Secondary Verification:** Real PayPal Developer Sandbox (OAuth 2.0 & Orders API)

---

## Script Overview & Timeline

| Timestamp | Segment | Visual / Page | Key Message |
| :--- | :--- | :--- | :--- |
| **0:00 – 0:40** | **The SMB Problem** | Title Slide / Dashboard | Hidden SaaS sprawl & fluctuating cash-flow create surprise cash crunches. |
| **0:40 – 1:25** | **PayPal Integration & Ledger Ingestion** | Dashboard Stream Card | Direct PayPal OAuth connection, automated sync, non-operating transfer filtering. |
| **1:25 – 2:10** | **Hybrid Subscription Detection** | Subscriptions Page | Inter-arrival cadence analysis, price creep detection, confirmed vs potential tagging. |
| **2:10 – 2:55** | **Calendar Forecasting & Stress Simulation** | Forecast & Simulation | Exact renewal calendar (no artificial smoothing), 3 macro scenarios, shock testing. |
| **3:55 – 3:45** | **Purchase Affordability Simulator** | Recommendations / Simulator | Deterministic "Can I Afford This?" calculation without LLM math errors. |
| **3:45 – 4:30** | **Intelligent Financial Assistant** | Financial Assistant Page | Evidence-grounded conversational CFO; strict citations; deterministic fallback. |
| **4:30 – 5:00** | **Financial Reports & Business Impact** | Reports Page / Summary | OWASP-sanitized CSV, ReportLab PDF, and how PayPal becomes a strategic financial partner. |

---

## Detailed Minute-by-Minute Script

### [0:00 – 0:40] Segment 1: The Business Problem

**Action:** Open browser to `http://localhost:3000`. Dashboard is visible.  
**Presenter Speaks:**
> "Good morning, judges. Every small business owner shares the same nightmare: you check your bank balance on a Monday, and you're suddenly in the red because three software tools renewed on the exact same day.
>
> Today, the average 15-person software services firm manages 10 to 25 SaaS subscriptions—AWS, Slack, GitHub, Google Workspace, Adobe. Unlike payroll or rent, software subscriptions fluctuate: consumption billing creeps up, seats expand quietly, and annual licenses hit like surprise freight trains. Meanwhile, business revenue fluctuates week by week.
>
> Traditional accounting software only tells you what happened in the past. It doesn't forecast whether you can survive next month's renewals. That is why we built **PayPal SubWise AI**—a calendar-aware cash-flow intelligence and subscription guardian powered directly by PayPal."

---

### [0:40 – 1:25] Segment 2: PayPal Integration & Ledger Normalization

**Action:** Point to the top navigation badge and the **PayPal Stream Engine** card.  
**Presenter Speaks:**
> "SubWise AI connects directly to PayPal's Developer Sandbox and Production APIs via OAuth 2.0. 
> 
> Notice here on our navigation bar: we provide a strict, isolated dual-mode architecture. We have our live **PayPal Sandbox** integration with verified OAuth token exchanges and Orders v2 checkout, alongside **DemoTech Solutions**—an isolated 6-month illustrative dataset for reproducible demonstration.
>
> Let's look at the PayPal Stream Engine banner. When we ingest transactions from PayPal's Reporting API, raw merchant descriptors are messy: string noise like `AMZN*AWS CLOUD 102948-US` or `SLACK T1234 PRO MO`. 
>
> Our backend ingestion pipeline runs an automated normalization pass:
> 1. It normalizes descriptors into canonical merchants (`AWS`, `Slack`, `GitHub`).
> 2. It applies a **strict financial accuracy rule**: incoming sales, internal SubWise sandbox test orders, and account funding transfers like initial balance deposits are **never** counted as subscription expenses or operating revenue.
>
> Only completed operating transactions feed our downstream intelligence engines."

---

### [1:25 – 2:10] Segment 3: Hybrid Subscription Detection & Expense Intelligence

**Action:** Click **Subscriptions** in the sidebar (`/subscriptions`). Show the subscription summary metrics and list.  
**Presenter Speaks:**
> "Here on the Subscriptions page, you see our **Hybrid Subscription Detection Engine** in action. 
>
> Notice that we don't rely on simplistic keyword guesses. We use a two-pronged detection methodology:
> 1. **Canonical SaaS Registry Matching**: Recognizes 35+ known SaaS and cloud vendors immediately.
> 2. **Inter-Arrival Cadence Analysis**: We calculate the median and standard deviation of payment intervals. Intervals between 25 and 35 days confirm a monthly cadence; 80 to 100 days confirm quarterly; and 340 to 390 days confirm annual.
>
> Look at the classification tags:
> - **Confirmed Subscriptions**: 8 recurring contracts—such as AWS ($245.50/mo), Slack ($75.00/mo), and GitHub ($42.00/mo)—supported by steady historical cycles.
> - **Potential Subscriptions**: Look at *Linear* ($32.00/mo). Because Linear only has a single disbursement detected so far, SubWise refuses to fabricate certainty. It transparently classifies Linear as 'Potential' awaiting a second cycle.
> - **Price Creep Detection**: If a fixed-seat tool increases by more than 20%, SubWise flags it immediately with an `At-Risk` alert.
> - **Discretionary Tiering**: Tools are categorized into Tier 1 Core Infrastructure, Tier 2 Collaboration, and Tier 3 Discretionary."

---

### [2:10 – 2:55] Segment 4: Calendar-Aware Forecasting & Stress Simulation

**Action:** Navigate to **Cash-Flow Forecast** (`/forecast`). Point to the payment calendar and scenario toggle.  
**Presenter Speaks:**
> "Now, here is our core algorithmic innovation: **Calendar-Aware Subscription Payment Scheduling**.
>
> Most financial forecasting tools make a dangerous error: they take annual expenses—like a $540 Figma annual subscription—and divide them by 12, pretending you pay $45 every month. But in reality, cash flow is not smooth. You pay $540 on a single day.
>
> SubWise maps every renewal to its exact forward calendar date across a 6-month horizon. 
>
> Look at December 2026: SubWise sounds a **Renewal Concentration Warning**! It flags that Figma's $540 annual license renews on December 15th, alongside AWS and GitHub, causing a 68% spike in software disbursements for that specific week.
>
> Next, toggle between our three macro scenarios:
> - **Baseline**: Historical average operating cash flow.
> - **Optimistic (+15% revenue growth)**: Runway expands to 18+ months.
> - **Conservative (-20% revenue dip)**: Notice that confirmed contractual commitments remain fixed because you cannot wish away your AWS or GitHub contracts during a sales slowdown. SubWise calculates your exact runway down to 4.2 months."

---

### [2:55 – 3:45] Segment 5: Purchase Affordability Simulator ("Can I Afford This?")

**Action:** Navigate to **Simulator** (`/simulator`). Enter a proposed subscription: Vendor = `Datadog APM`, Amount = `$350.00/month`, Category = `DevOps`. Click **Run Simulation**.  
**Presenter Speaks:**
> "Before a founder clicks 'Subscribe' on a new tool, they can run our **Purchase Affordability Simulator**.
>
> Let's test a realistic scenario: our engineering lead wants to add *Datadog APM* at $350 per month.
>
> Instead of giving a generic AI opinion, SubWise calculates the exact forward liquidity impact:
> 1. It subtracts $350 each month alongside existing contractual commitments.
> 2. It stress-tests cash reserves across our 12-month horizon.
> 3. It evaluates whether reserves breach the company's minimum safe runway threshold.
>
> Notice the result: SubWise issues a clear **Affordable with Caution** verdict. It shows that our closing cash reserves drop from $18,500 down to $12,800, shortening our buffer by 1.8 months, and recommends consolidating redundant observability tools first. All math is deterministic, verified, and completely transparent."

---

### [3:45 – 4:30] Segment 6: Evidence-Grounded AI Financial Assistant

**Action:** Navigate to **AI Assistant** (`/assistant`). Click the suggested prompt: *"What are my upcoming renewals in the next 30 days?"*.  
**Presenter Speaks:**
> "Now let's examine the **AI Financial Assistant**.
>
> In many hackathon projects, teams pass raw prompts into an LLM and let the model hallucinate numbers. In fintech, that is unacceptable.
>
> SubWise uses an **Evidence-First AI Architecture**:
> - The user asks a question in plain English.
> - Our query router resolves the exact backend calculations from `ForecastEngine`, `SubscriptionAnalyzer`, and `FinancialIntelligenceEngine`.
> - Google Gemini 1.5 Flash is used *solely* to interpret intent and articulate verified results in plain English.
>
> Look at the response: every number cited—Slack's $75 on November 12th, OpenAI's $85 on November 15th, Adobe's $59.99 on November 18th—is backed by an interactive **Supporting Evidence Card** citing the exact database ledger records.
>
> Even better: if the internet drops or the LLM provider hits rate limits, SubWise automatically falls back to our internal deterministic synthesis engine without crashing or degrading."

---

### [4:30 – 5:00] Segment 7: Professional Financial Reports & Closing

**Action:** Navigate to **Reports** (`/reports`). Click **Export PDF** (or preview the Comprehensive Intelligence Report).  
**Presenter Speaks:**
> "Finally, let's look at **Financial Reports & Export Intelligence**.
>
> Founders can select custom reporting periods and download board-ready deliverables:
> - **OWASP-Sanitized CSV Exports**: Fully protected against spreadsheet formula injection attacks.
> - **ReportLab Vector PDFs**: Complete with company branding, two-pass 'Page X of Y' numbering, 100-point Financial Health Index scoring, and statutory methodology disclosures.
>
> In summary: SubWise AI transforms PayPal from a silent payment rail into an proactive, intelligent financial co-pilot for SMBs. 
>
> All 9 stages are fully implemented with 103 passing backend tests, zero fabricated metrics, and complete PayPal Sandbox integration.
>
> Thank you, and we welcome your questions!"

---

## Quick Reference for Demo Transitions

- **Dashboard (`/`)**: Show PayPal Stream status card, runway metric, health score (78/100).
- **Subscriptions (`/subscriptions`)**: Highlight confirmed AWS vs potential Linear.
- **Forecast (`/forecast`)**: Point out December 15 Figma annual renewal spike.
- **Simulator (`/simulator`)**: Simulate $350 Datadog purchase; show runway reduction.
- **Assistant (`/assistant`)**: Ask *"What renewals are due in the next 30 days?"* and inspect evidence card.
- **Reports (`/reports`)**: Highlight OWASP formula sanitization and downloadable PDF.

