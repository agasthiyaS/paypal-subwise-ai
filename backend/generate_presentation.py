"""
Generate Professional Hackathon Presentation for PayPal SubWise AI.
Slide Dimensions: 16:9 Widescreen (13.333 x 7.5 inches)
Palette:
- PayPal Deep Navy: #003087 (0, 48, 135)
- PayPal Classic Blue: #0070BA (0, 112, 186)
- PayPal Light Cyan: #00CFE8 (0, 207, 232)
- Slate Dark / Text: #0F172A (15, 23, 42)
- Text Body / Slate: #334155 (51, 65, 85)
- Text Muted: #64748B (100, 116, 139)
- Card Background: #F8FAFC (248, 250, 252)
- Card Border: #E2E8F0 (226, 232, 240)
- White: #FFFFFF (255, 255, 255)
- Emerald: #059669 (5, 150, 105)
- Emerald Light: #ECFDF5 (236, 253, 245)
- Amber: #D97706 (217, 119, 6)
- Amber Light: #FFFBEB (255, 251, 235)
- Purple / Violet: #6D28D9 (109, 40, 217)
- Purple Light: #F5F3FF (245, 243, 255)
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# Initialize 16:9 widescreen presentation
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# Color Constants
C_NAVY = RGBColor(0, 48, 135)
C_BLUE = RGBColor(0, 112, 186)
C_CYAN = RGBColor(0, 207, 232)
C_DARK = RGBColor(15, 23, 42)
C_BODY = RGBColor(51, 65, 85)
C_MUTED = RGBColor(100, 116, 139)
C_BG_CARD = RGBColor(248, 250, 252)
C_BORDER = RGBColor(226, 232, 240)
C_WHITE = RGBColor(255, 255, 255)
C_EMERALD = RGBColor(5, 150, 105)
C_EMERALD_BG = RGBColor(236, 253, 245)
C_AMBER = RGBColor(217, 119, 6)
C_AMBER_BG = RGBColor(255, 251, 235)
C_PURPLE = RGBColor(109, 40, 217)
C_PURPLE_BG = RGBColor(245, 243, 255)

FONT_HEADING = "Segoe UI"
FONT_BODY = "Segoe UI"

blank_layout = prs.slide_layouts[6]

def set_slide_background(slide, color=C_WHITE):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_header(slide, title_text, category_text="PAYPAL SUBWISE AI — FINTECH INTELLIGENCE"):
    # Category tag
    tag_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
    tf_tag = tag_box.text_frame
    tf_tag.word_wrap = True
    tf_tag.margin_left = tf_tag.margin_top = tf_tag.margin_right = tf_tag.margin_bottom = 0
    p_tag = tf_tag.paragraphs[0]
    p_tag.text = category_text.upper()
    p_tag.font.name = FONT_HEADING
    p_tag.font.size = Pt(10)
    p_tag.font.bold = True
    p_tag.font.color.rgb = C_BLUE

    # Title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(11.7), Inches(0.7))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    p_title.text = title_text
    p_title.font.name = FONT_HEADING
    p_title.font.size = Pt(24)
    p_title.font.bold = True
    p_title.font.color.rgb = C_NAVY

    # Subtle divider rule
    line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0.8), Inches(1.48), Inches(11.733), Inches(0.02)
    )
    line.fill.solid()
    line.fill.fore_color.rgb = C_BORDER
    line.line.color.rgb = C_BORDER

def add_card(slide, left, top, width, height, bg_color=C_BG_CARD, border_color=C_BORDER):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        left, top, width, height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    shape.line.color.rgb = border_color
    shape.line.width = Pt(1.2)
    return shape

# ==============================================================================
# SLIDE 1: Title Slide (Fintech Cover)
# ==============================================================================
s1 = prs.slides.add_slide(blank_layout)
set_slide_background(s1, C_WHITE)

# Left decorative bar
bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.35), Inches(7.5))
bar.fill.solid()
bar.fill.fore_color.rgb = C_NAVY
bar.line.fill.background()

# Top Tag
tag_box = s1.shapes.add_textbox(Inches(1.2), Inches(1.3), Inches(10.5), Inches(0.4))
tf = tag_box.text_frame
p = tf.paragraphs[0]
p.text = "PAYPAL DEVELOPER HACKATHON 2026  ·  FINTECH & COMMERCE TRACK"
p.font.name = FONT_HEADING
p.font.size = Pt(12)
p.font.bold = True
p.font.color.rgb = C_BLUE

# Title & Subtitle
title_box = s1.shapes.add_textbox(Inches(1.2), Inches(1.8), Inches(10.8), Inches(2.2))
tf = title_box.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "PayPal SubWise AI"
p.font.name = FONT_HEADING
p.font.size = Pt(46)
p.font.bold = True
p.font.color.rgb = C_NAVY

p2 = tf.add_paragraph()
p2.text = "Calendar-Aware Cash-Flow Forecasting & Subscription Intelligence for SMBs"
p2.font.name = FONT_HEADING
p2.font.size = Pt(20)
p2.font.bold = False
p2.font.color.rgb = C_BODY
p2.space_before = Pt(10)

# 3 Feature Pills
pills = [
    ("Real-Time PayPal API Streams", "OAuth 2.0 & Orders v2 Integration"),
    ("Deterministic Cash-Flow Math", "Zero LLM Math Hallucination"),
    ("Calendar-Aware Payment Schedule", "Exact Forward Renewal Mapping")
]
pill_width = Inches(3.45)
pill_gap = Inches(0.4)
pill_start_left = Inches(1.2)
pill_top = Inches(4.3)

for i, (pill_title, pill_sub) in enumerate(pills):
    p_left = pill_start_left + i * (pill_width + pill_gap)
    card = add_card(s1, p_left, pill_top, pill_width, Inches(1.4), C_BG_CARD, C_BORDER)
    tb = s1.shapes.add_textbox(p_left + Inches(0.2), pill_top + Inches(0.2), pill_width - Inches(0.4), Inches(1.0))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = pill_title
    p.font.name = FONT_HEADING
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_NAVY
    p_sub = tf.add_paragraph()
    p_sub.text = pill_sub
    p_sub.font.name = FONT_BODY
    p_sub.font.size = Pt(11)
    p_sub.font.color.rgb = C_MUTED
    p_sub.space_before = Pt(4)

# Footer metadata
ft_box = s1.shapes.add_textbox(Inches(1.2), Inches(6.3), Inches(10.8), Inches(0.5))
tf = ft_box.text_frame
p = tf.paragraphs[0]
p.text = "Full-Stack System: FastAPI  ·  React 18  ·  PostgreSQL  ·  PayPal REST APIs  ·  Google Gemini 1.5 Flash  ·  101 Tests Passed"
p.font.name = FONT_BODY
p.font.size = Pt(11)
p.font.color.rgb = C_MUTED


# ==============================================================================
# SLIDE 2: Problem Statement
# ==============================================================================
s2 = prs.slides.add_slide(blank_layout)
set_slide_background(s2, C_WHITE)
add_header(s2, "Problem Statement: The SMB Subscription Blindspot")

prob_cards = [
    ("Hidden Recurring Drag",
     "The average 15-person software services firm manages 15–25 SaaS subscriptions (AWS, GitHub, Slack, Zoom, Adobe). Costs creep up through unmonitored seat expansion and consumption billing without centralized visibility.",
     C_AMBER, C_AMBER_BG),
    ("Revenue Volatility vs Fixed Commitments",
     "Small business revenue fluctuates significantly month to month with client payment delays. Meanwhile, contractual software disbursements are strictly non-negotiable—creating acute, unanticipated cash crunches.",
     C_NAVY, C_BG_CARD),
    ("Lump-Sum Renewal Surprises",
     "Annual subscriptions hit bank accounts like unexpected freight trains. Standard accounting tools smooth annual expenses over 12 months, blinding founders to multi-thousand-dollar cash depletion events.",
     C_PURPLE, C_PURPLE_BG)
]

for i, (title, desc, accent_color, bg_col) in enumerate(prob_cards):
    c_left = Inches(0.8) + i * Inches(3.95)
    card = add_card(s2, c_left, Inches(1.8), Inches(3.75), Inches(4.8), bg_col, C_BORDER)
    
    # Top accent bar
    top_bar = s2.shapes.add_shape(MSO_SHAPE.RECTANGLE, c_left + Inches(0.25), Inches(2.1), Inches(0.7), Inches(0.08))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = accent_color
    top_bar.line.fill.background()

    tb = s2.shapes.add_textbox(c_left + Inches(0.25), Inches(2.35), Inches(3.25), Inches(4.0))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.name = FONT_HEADING
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = C_DARK
    
    p2 = tf.add_paragraph()
    p2.text = desc
    p2.font.name = FONT_BODY
    p2.font.size = Pt(13)
    p2.font.color.rgb = C_BODY
    p2.space_before = Pt(12)


# ==============================================================================
# SLIDE 3: Challenges Faced by Small Businesses
# ==============================================================================
s3 = prs.slides.add_slide(blank_layout)
set_slide_background(s3, C_WHITE)
add_header(s3, "Why Traditional Accounting Fails Modern Software-Driven SMBs")

challenges = [
    ("Backward-Looking P&L Reporting",
     "Traditional tools (QuickBooks, Xero) report what happened 30 days ago for tax compliance. SMB founders need forward-looking liquidity intelligence to make payroll next month."),
    ("Dangerous Straight-Line Smoothing",
     "Dividing an annual $1,200 Figma contract by 12 hides reality. Cash flow is not smooth—the entire $1,200 is debited on a single Tuesday, depleting working reserves."),
    ("No Pre-Purchase Decision Support",
     "Founders ask: 'Can we afford an additional $350/mo APM tool right now?' Traditional accounting software provides zero forward impact simulation before clicking Subscribe."),
    ("Disconnected Merchant Feeds",
     "Standard bank statement descriptors (e.g., DEBIT-102948-US) are unreadable. Founders lack automated cadence detection, seat tracking, and duplicate redundancy discovery.")
]

for i, (title, desc) in enumerate(challenges):
    row = i // 2
    col = i % 2
    c_left = Inches(0.8) + col * Inches(5.95)
    c_top = Inches(1.8) + row * Inches(2.5)
    
    card = add_card(s3, c_left, c_top, Inches(5.75), Inches(2.25), C_BG_CARD, C_BORDER)
    
    tb = s3.shapes.add_textbox(c_left + Inches(0.3), c_top + Inches(0.25), Inches(5.15), Inches(1.75))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = f"{i+1}.  {title}"
    p.font.name = FONT_HEADING
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_NAVY
    
    p2 = tf.add_paragraph()
    p2.text = desc
    p2.font.name = FONT_BODY
    p2.font.size = Pt(12)
    p2.font.color.rgb = C_BODY
    p2.space_before = Pt(6)


# ==============================================================================
# SLIDE 4: Proposed Solution
# ==============================================================================
s4 = prs.slides.add_slide(blank_layout)
set_slide_background(s4, C_WHITE)
add_header(s4, "Proposed Solution: PayPal SubWise AI")

solution_cols = [
    ("Automated PayPal Ingestion",
     "Direct OAuth 2.0 connection to PayPal Reporting API. Normalizes messy merchant strings and filters non-operating capital transfers.",
     "STREAM INGESTION"),
    ("Hybrid Recurrence Engine",
     "Statistical inter-arrival time deltas + 35+ SaaS merchant dictionary. Classifies confirmed vs potential commitments with price-creep alerts.",
     "DETECTION ENGINE"),
    ("Calendar-Aware Forecasting",
     "Maps exact forward renewal dates across 6 months. Multi-scenario stress tests (Optimistic, Baseline, Conservative) with concentration warnings.",
     "CASH-FLOW FORECAST"),
    ("Grounded Financial Assistant",
     "Evidence-first conversational CFO powered by Google Gemini 1.5 Flash. 100% deterministic financial math with zero hallucination risk.",
     "AI ADVISOR")
]

for i, (title, desc, badge) in enumerate(solution_cols):
    c_left = Inches(0.8) + i * Inches(2.95)
    card = add_card(s4, c_left, Inches(1.8), Inches(2.8), Inches(4.8), C_BG_CARD, C_BORDER)
    
    # Badge
    b_box = s4.shapes.add_textbox(c_left + Inches(0.2), Inches(2.1), Inches(2.4), Inches(0.3))
    tf = b_box.text_frame
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = badge
    p.font.name = FONT_HEADING
    p.font.size = Pt(9)
    p.font.bold = True
    p.font.color.rgb = C_BLUE

    tb = s4.shapes.add_textbox(c_left + Inches(0.2), Inches(2.5), Inches(2.4), Inches(3.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.name = FONT_HEADING
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_DARK
    
    p2 = tf.add_paragraph()
    p2.text = desc
    p2.font.name = FONT_BODY
    p2.font.size = Pt(12)
    p2.font.color.rgb = C_BODY
    p2.space_before = Pt(8)


# ==============================================================================
# SLIDE 5: How PayPal Powers SubWise AI
# ==============================================================================
s5 = prs.slides.add_slide(blank_layout)
set_slide_background(s5, C_WHITE)
add_header(s5, "How PayPal Powers SubWise AI")

pp_features = [
    ("PayPal OAuth 2.0 Security Rail",
     "Secure client-credentials authorization exchange. Client secrets remain strictly server-side; frontend receives only masked previews. Full separation of Sandbox and Live environments.",
     "AUTHENTICATION"),
    ("PayPal Transaction Search API",
     "Queries /v1/reporting/transactions across historical timeframes. Ingests counterparty names, currency codes, gross amounts, fee breakdowns, and completion statuses with zero manual data entry.",
     "REPORTING API"),
    ("PayPal Orders v2 API Checkout",
     "Live sandbox payment creation and capture via /v2/checkout/orders. Enables instant verification of transaction flows and payment status lifecycle in developer environments.",
     "CHECKOUT ORDERS"),
    ("Strategic Partner Synergy",
     "Transforms PayPal from a passive transaction rail into an indispensable financial advisor for SMB merchants. Increases merchant retention and boosts PayPal wallet share for business spend.",
     "VALUE CREATION")
]

for i, (title, desc, badge) in enumerate(pp_features):
    row = i // 2
    col = i % 2
    c_left = Inches(0.8) + col * Inches(5.95)
    c_top = Inches(1.8) + row * Inches(2.5)
    
    card = add_card(s5, c_left, c_top, Inches(5.75), Inches(2.25), C_BG_CARD, C_BORDER)
    
    # Left accent indicator
    ind = s5.shapes.add_shape(MSO_SHAPE.RECTANGLE, c_left, c_top, Inches(0.1), Inches(2.25))
    ind.fill.solid()
    ind.fill.fore_color.rgb = C_BLUE
    ind.line.fill.background()

    tb = s5.shapes.add_textbox(c_left + Inches(0.3), c_top + Inches(0.25), Inches(5.15), Inches(1.75))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = badge + "  ·  " + title
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_NAVY
    
    p2 = tf.add_paragraph()
    p2.text = desc
    p2.font.name = FONT_BODY
    p2.font.size = Pt(12)
    p2.font.color.rgb = C_BODY
    p2.space_before = Pt(6)


# ==============================================================================
# SLIDE 6: System Architecture
# ==============================================================================
s6 = prs.slides.add_slide(blank_layout)
set_slide_background(s6, C_WHITE)
add_header(s6, "Full-Stack System Architecture & Information Flow")

arch_tiers = [
    ("Presentation Layer", "React 18 · Vite 5 · React Router 6",
     "Component-driven fintech SPA. Real-time SVG chart visualizations, calendar heatmaps, interactive purchase simulator, and responsive evidence cards."),
    ("API & Routing Layer", "FastAPI · Pydantic v2 · Python 3.10",
     "Asynchronous REST endpoints, Passlib bcrypt auth, HMAC-SHA256 JWT tokens. Request interceptors dynamically enforce business-profile isolation."),
    ("Deterministic Engines", "Python 3.10 Mathematical Modules",
     "Core intelligence services: TransactionNormalizer, SubscriptionDetector, ForecastEngine, CashFlowSimulator, FinancialIntelligenceEngine, ReportEngine."),
    ("Database & External APIs", "PostgreSQL 15 · PayPal · Gemini",
     "Relational PostgreSQL with composite constraints. Direct PayPal Reporting and Orders APIs. Google Gemini 1.5 Flash for natural language explanation.")
]

for i, (layer, tech, detail) in enumerate(arch_tiers):
    c_left = Inches(0.8) + i * Inches(2.95)
    card = add_card(s6, c_left, Inches(1.8), Inches(2.8), Inches(4.8), C_BG_CARD, C_BORDER)
    
    tb = s6.shapes.add_textbox(c_left + Inches(0.2), Inches(2.1), Inches(2.4), Inches(4.2))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = f"Tier {i+1}"
    p.font.name = FONT_HEADING
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = C_BLUE
    
    p_title = tf.add_paragraph()
    p_title.text = layer
    p_title.font.name = FONT_HEADING
    p_title.font.size = Pt(16)
    p_title.font.bold = True
    p_title.font.color.rgb = C_NAVY
    p_title.space_before = Pt(4)

    p_tech = tf.add_paragraph()
    p_tech.text = tech
    p_tech.font.name = FONT_HEADING
    p_tech.font.size = Pt(10)
    p_tech.font.bold = True
    p_tech.font.color.rgb = C_MUTED
    p_tech.space_before = Pt(2)

    p_body = tf.add_paragraph()
    p_body.text = detail
    p_body.font.name = FONT_BODY
    p_body.font.size = Pt(12)
    p_body.font.color.rgb = C_BODY
    p_body.space_before = Pt(10)


# ==============================================================================
# SLIDE 7: Subscription Detection & Expense Intelligence
# ==============================================================================
s7 = prs.slides.add_slide(blank_layout)
set_slide_background(s7, C_WHITE)
add_header(s7, "Hybrid Subscription Detection & Expense Intelligence")

# Left Column: Mathematical Methodology
card_l = add_card(s7, Inches(0.8), Inches(1.8), Inches(5.75), Inches(4.8), C_BG_CARD, C_BORDER)
tb_l = s7.shapes.add_textbox(Inches(1.1), Inches(2.1), Inches(5.15), Inches(4.2))
tf_l = tb_l.text_frame
tf_l.word_wrap = True
p = tf_l.paragraphs[0]
p.text = "Mathematical Detection Pipeline"
p.font.name = FONT_HEADING
p.font.size = Pt(18)
p.font.bold = True
p.font.color.rgb = C_NAVY

steps = [
    ("Descriptor Normalization: ", "Strips merchant noise; maps strings to 35+ canonical SaaS vendor profiles in MERCHANT_REGISTRY."),
    ("Non-Operating Filtering: ", "Excludes account deposits, wallet funding, and customer sales from subscription classification."),
    ("Cadence Inter-Arrival Math: ", "Calculates median intervals (weekly 5-9d, monthly 25-35d, quarterly 80-100d, annual 340-390d)."),
    ("Confidence & Variance: ", "Confidence score scaled inversely with standard deviation: max(0.60, min(0.99, 1.0 - (std/15.0)))."),
    ("Classification Tagging: ", "Separates Confirmed recurring commitments from Potential cold-starts awaiting cycle 2.")
]
for title_sub, desc_sub in steps:
    p_step = tf_l.add_paragraph()
    p_step.text = "•  " + title_sub + desc_sub
    p_step.font.name = FONT_BODY
    p_step.font.size = Pt(12)
    p_step.font.color.rgb = C_BODY
    p_step.space_before = Pt(8)

# Right Column: Verified DemoTech Metrics
card_r = add_card(s7, Inches(6.8), Inches(1.8), Inches(5.75), Inches(4.8), C_WHITE, C_BORDER)
tb_r = s7.shapes.add_textbox(Inches(7.1), Inches(2.1), Inches(5.15), Inches(4.2))
tf_r = tb_r.text_frame
tf_r.word_wrap = True
p = tf_r.paragraphs[0]
p.text = "Demonstrated Ingestion (DemoTech Solutions)"
p.font.name = FONT_HEADING
p.font.size = Pt(18)
p.font.bold = True
p.font.color.rgb = C_NAVY

demo_items = [
    ("Confirmed Monthly Commitments: ", "$563.48 / month ($7,301.76 / year run-rate) across 8 verified SaaS vendors."),
    ("Core Software Stack: ", "AWS ($245.50), GitHub ($42.00), Slack ($75.00), OpenAI ($85.00), Adobe ($59.99), Zoom ($19.99), Google ($36.00)."),
    ("Annual Renewal Mapping: ", "Figma Organization ($540.00/yr) mapped to December 15, 2026 renewal date."),
    ("Potential Cold-Start Detection: ", "Linear ($32.00/mo) classified as Potential awaiting second billing cycle confirmation."),
    ("Price Creep Monitoring: ", "Flags fixed-seat tools that increase by >15% over historical billing history.")
]
for title_sub, desc_sub in demo_items:
    p_item = tf_r.add_paragraph()
    p_item.text = "✔  " + title_sub + desc_sub
    p_item.font.name = FONT_BODY
    p_item.font.size = Pt(12)
    p_item.font.color.rgb = C_BODY
    p_item.space_before = Pt(8)


# ==============================================================================
# SLIDE 8: Cash Flow Forecasting & Scenario Simulation
# ==============================================================================
s8 = prs.slides.add_slide(blank_layout)
set_slide_background(s8, C_WHITE)
add_header(s8, "Calendar-Aware Cash Flow Forecasting & Scenario Simulation")

fore_cards = [
    ("Exact Renewal Calendar",
     "Schedules disbursements on their exact calendar dates over 6 months rather than artificial straight-line smoothing. Accurately reveals week-level liquidity dips.",
     "CALENDAR ENGINE"),
    ("Renewal Concentration Warnings",
     "Monitors forward 7-day windows. Automatically sounds an alert if scheduled commitments exceed 35% of total monthly overhead (e.g. Dec 15 Figma renewal spike).",
     "LIQUIDITY ALERTS"),
    ("3 Macro Scenarios",
     "• Optimistic: +15% revenue growth\n• Baseline: Historical average\n• Conservative: -20% sales dip\nContractual commitments remain invariant across all scenarios.",
     "MACRO STRESS TESTING"),
    ("Closing Cash Projection",
     "Cash_m = Cash_{m-1} + Rev_m - (NonSub_m + ScheduledSubs_m). Derives verified runway depletion horizons without hardcoded financial fallbacks.",
     "RUNWAY DEPLETION")
]

for i, (title, desc, badge) in enumerate(fore_cards):
    c_left = Inches(0.8) + i * Inches(2.95)
    card = add_card(s8, c_left, Inches(1.8), Inches(2.8), Inches(4.8), C_BG_CARD, C_BORDER)
    
    b_box = s8.shapes.add_textbox(c_left + Inches(0.2), Inches(2.1), Inches(2.4), Inches(0.3))
    tf = b_box.text_frame
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = badge
    p.font.name = FONT_HEADING
    p.font.size = Pt(9)
    p.font.bold = True
    p.font.color.rgb = C_BLUE

    tb = s8.shapes.add_textbox(c_left + Inches(0.2), Inches(2.5), Inches(2.4), Inches(3.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.name = FONT_HEADING
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_DARK
    
    p2 = tf.add_paragraph()
    p2.text = desc
    p2.font.name = FONT_BODY
    p2.font.size = Pt(12)
    p2.font.color.rgb = C_BODY
    p2.space_before = Pt(8)


# ==============================================================================
# SLIDE 9: AI Recommendations & Financial Assistant
# ==============================================================================
s9 = prs.slides.add_slide(blank_layout)
set_slide_background(s9, C_WHITE)
add_header(s9, "AI Financial Assistant & Purchase Affordability Simulator")

card_l9 = add_card(s9, Inches(0.8), Inches(1.8), Inches(5.75), Inches(4.8), C_BG_CARD, C_BORDER)
tb_l9 = s9.shapes.add_textbox(Inches(1.1), Inches(2.1), Inches(5.15), Inches(4.2))
tf_l9 = tb_l9.text_frame
tf_l9.word_wrap = True
p = tf_l9.paragraphs[0]
p.text = "Evidence-Grounded AI Assistant"
p.font.name = FONT_HEADING
p.font.size = Pt(18)
p.font.bold = True
p.font.color.rgb = C_NAVY

ai_bullets = [
    ("Google Gemini 1.5 Flash Integration: ", "Interprets natural language queries and synthesizes executive briefings from verified backend calculations."),
    ("Strict Deterministic Math Guardrail: ", "AI is strictly forbidden from calculating math independently. 100% of figures come from verified ledger queries."),
    ("Interactive Evidence Cards: ", "Responses return structured citation cards with exact transaction dates, amounts, and vendor names."),
    ("Automated Offline Fallback: ", "If Gemini API key is missing or quota is exhausted (HTTP 429), the engine automatically falls back to deterministic rule synthesis with zero downtime.")
]
for title_sub, desc_sub in ai_bullets:
    p_step = tf_l9.add_paragraph()
    p_step.text = "•  " + title_sub + desc_sub
    p_step.font.name = FONT_BODY
    p_step.font.size = Pt(12)
    p_step.font.color.rgb = C_BODY
    p_step.space_before = Pt(8)

card_r9 = add_card(s9, Inches(6.8), Inches(1.8), Inches(5.75), Inches(4.8), C_WHITE, C_BORDER)
tb_r9 = s9.shapes.add_textbox(Inches(7.1), Inches(2.1), Inches(5.15), Inches(4.2))
tf_r9 = tb_r9.text_frame
tf_r9.word_wrap = True
p = tf_r9.paragraphs[0]
p.text = "Purchase Affordability Simulator"
p.font.name = FONT_HEADING
p.font.size = Pt(18)
p.font.bold = True
p.font.color.rgb = C_NAVY

sim_bullets = [
    ("Pre-Purchase Stress Test: ", "Simulates proposed software purchases (e.g. Datadog APM at $350/mo) against forward cash-flow commitments."),
    ("Runway Buffer Analysis: ", "Evaluates whether cash reserves remain above the target 6-month safety runway buffer."),
    ("Objective Decision Verdicts: ", "Produces deterministic recommendations: 'Affordable', 'Affordable with Caution', or 'Postpone / Not Recommended'."),
    ("Actionable Optimization: ", "Scans for redundant tools (e.g. multiple messaging or design tools) and high-cost zombie subscriptions.")
]
for title_sub, desc_sub in sim_bullets:
    p_item = tf_r9.add_paragraph()
    p_item.text = "✔  " + title_sub + desc_sub
    p_item.font.name = FONT_BODY
    p_item.font.size = Pt(12)
    p_item.font.color.rgb = C_BODY
    p_item.space_before = Pt(8)


# ==============================================================================
# SLIDE 10: Financial Reports & Business Insights
# ==============================================================================
s10 = prs.slides.add_slide(blank_layout)
set_slide_background(s10, C_WHITE)
add_header(s10, "Financial Reports, 100-Point Health Index & Export Security")

rep_cols = [
    ("100-Point Financial Health Index",
     "Audited scoring across 5 deterministic pillars:\n• Subscription Burden Ratio (30 pts)\n• Net Cash Flow Positive (25 pts)\n• Runway Adequacy (25 pts)\n• Renewal Concentration (10 pts)\n• Data Sufficiency (10 pts)\nScore withheld if data < 60 days.",
     "HEALTH INDEX"),
    ("OWASP-Sanitized CSV Exports",
     "Protects accountants from spreadsheet formula injection attacks. Formulas starting with =, +, -, @, \\t, \\r are safely escaped with leading single quotes before export.",
     "EXPORT SECURITY"),
    ("ReportLab Vector PDF Reports",
     "Generates board-ready executive PDFs in pure Python. Features corporate branding, dynamic two-pass 'Page X of Y' numbering, and statutory methodology disclosures.",
     "PDF COMPILATION"),
    ("Data Sufficiency Transparency",
     "Zero hallucination for cold-start businesses. Clearly explains why historical data is insufficient rather than fabricating optimistic projections.",
     "ACCOUNTING INTEGRITY")
]

for i, (title, desc, badge) in enumerate(rep_cols):
    c_left = Inches(0.8) + i * Inches(2.95)
    card = add_card(s10, c_left, Inches(1.8), Inches(2.8), Inches(4.8), C_BG_CARD, C_BORDER)
    
    b_box = s10.shapes.add_textbox(c_left + Inches(0.2), Inches(2.1), Inches(2.4), Inches(0.3))
    tf = b_box.text_frame
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = badge
    p.font.name = FONT_HEADING
    p.font.size = Pt(9)
    p.font.bold = True
    p.font.color.rgb = C_BLUE

    tb = s10.shapes.add_textbox(c_left + Inches(0.2), Inches(2.5), Inches(2.4), Inches(3.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.name = FONT_HEADING
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_DARK
    
    p2 = tf.add_paragraph()
    p2.text = desc
    p2.font.name = FONT_BODY
    p2.font.size = Pt(12)
    p2.font.color.rgb = C_BODY
    p2.space_before = Pt(8)


# ==============================================================================
# SLIDE 11: Technology Stack
# ==============================================================================
s11 = prs.slides.add_slide(blank_layout)
set_slide_background(s11, C_WHITE)
add_header(s11, "Modern, Type-Safe, High-Performance Technology Stack")

tech_cards = [
    ("Frontend Client", "React 18 · Vite 5 · CSS Variables",
     "• Vite 5 fast build (11.9s production bundle)\n• React Router 6 SPA navigation\n• Pure CSS design system with custom properties\n• Lucide React visual iconography\n• Modular SVG financial charts"),
    ("Backend API Gateway", "FastAPI · Pydantic v2 · Python 3.10",
     "• High-throughput asynchronous routing\n• Pydantic v2 strict schema validation\n• Passlib bcrypt password hashing\n• PyJWT OAuth2 authentication tokens\n• Multi-tenant profile switching middleware"),
    ("Database & ORM", "PostgreSQL 15 · SQLAlchemy 2.0",
     "• Relational integrity with cascade deletions\n• Composite unique constraints: (user_id, is_demo)\n• Alembic versioned schema migrations\n• In-memory SQLite for rapid automated test runs\n• Indexed transaction and vendor search"),
    ("Fintech & AI Services", "PayPal APIs · Gemini 1.5 Flash",
     "• PayPal OAuth 2.0 client credentials\n• PayPal Reporting API (/v1/reporting)\n• PayPal Orders v2 API (/v2/checkout/orders)\n• ReportLab pure-Python vector PDF engine\n• Google Gemini 1.5 Flash + fallback")
]

for i, (title, subtitle, desc) in enumerate(tech_cards):
    row = i // 2
    col = i % 2
    c_left = Inches(0.8) + col * Inches(5.95)
    c_top = Inches(1.8) + row * Inches(2.5)
    
    card = add_card(s11, c_left, c_top, Inches(5.75), Inches(2.25), C_BG_CARD, C_BORDER)
    
    tb = s11.shapes.add_textbox(c_left + Inches(0.3), c_top + Inches(0.2), Inches(5.15), Inches(1.85))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.name = FONT_HEADING
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_NAVY
    
    p_sub = tf.add_paragraph()
    p_sub.text = subtitle
    p_sub.font.name = FONT_HEADING
    p_sub.font.size = Pt(11)
    p_sub.font.bold = True
    p_sub.font.color.rgb = C_BLUE
    p_sub.space_before = Pt(2)

    p_body = tf.add_paragraph()
    p_body.text = desc
    p_body.font.name = FONT_BODY
    p_body.font.size = Pt(11)
    p_body.font.color.rgb = C_BODY
    p_body.space_before = Pt(4)


# ==============================================================================
# SLIDE 12: Innovation & Competitive Advantages
# ==============================================================================
s12 = prs.slides.add_slide(blank_layout)
set_slide_background(s12, C_WHITE)
add_header(s12, "Innovation & Competitive Advantages")

# Comparison Table
t_left = Inches(0.8)
t_top = Inches(1.8)
t_width = Inches(11.733)
t_height = Inches(4.8)

table_shape = s12.shapes.add_table(6, 5, t_left, t_top, t_width, t_height)
tbl = table_shape.table

# Column widths
tbl.columns[0].width = Inches(3.2)
tbl.columns[1].width = Inches(2.2)
tbl.columns[2].width = Inches(2.1)
tbl.columns[3].width = Inches(2.1)
tbl.columns[4].width = Inches(2.133)

headers = ["Capability / Feature", "PayPal SubWise AI", "QuickBooks / Xero", "Torii / Zylo", "Manual Spreadsheets"]
for j, h in enumerate(headers):
    cell = tbl.cell(0, j)
    cell.fill.solid()
    cell.fill.fore_color.rgb = C_NAVY if j == 1 else C_DARK
    p = cell.text_frame.paragraphs[0]
    p.text = h
    p.font.name = FONT_HEADING
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = C_WHITE
    p.alignment = PP_ALIGN.CENTER if j > 0 else PP_ALIGN.LEFT

matrix_data = [
    ("Forward Renewal Calendar", "✔ Exact Day Mapping", "✖ Amortized (/12)", "✔ SSO Only", "✖ Outdated / Manual"),
    ("Pre-Purchase Stress Simulator", "✔ Deterministic Verdict", "✖ No Capability", "✖ No Capability", "✖ Static Formulas"),
    ("Setup Complexity for SMBs", "✔ Zero IT (PayPal OAuth)", "✔ Manual Bank Feed", "✖ 6-Mo Enterprise SAML", "✖ High Maintenance"),
    ("Conversational CFO Grounding", "✔ Evidence Cards (0-Hallucination)", "✖ Basic Chatbot", "✖ Keyword Search", "✖ None"),
    ("Data Sufficiency Protection", "✔ Transparent Withholding", "✖ Misleading Zeroes", "✖ Incomplete Scans", "✖ Formula Errors")
]

for i, row in enumerate(matrix_data):
    for j, val in enumerate(row):
        cell = tbl.cell(i + 1, j)
        cell.fill.solid()
        if j == 1:
            cell.fill.fore_color.rgb = C_EMERALD_BG
        else:
            cell.fill.fore_color.rgb = C_WHITE if (i % 2 == 0) else C_BG_CARD
        p = cell.text_frame.paragraphs[0]
        p.text = val
        p.font.name = FONT_BODY
        p.font.size = Pt(11)
        p.font.bold = (j == 1)
        p.font.color.rgb = C_EMERALD if (j == 1) else (C_DARK if j == 0 else C_BODY)
        p.alignment = PP_ALIGN.CENTER if j > 0 else PP_ALIGN.LEFT


# ==============================================================================
# SLIDE 13: Limitations & Future Scope
# ==============================================================================
s13 = prs.slides.add_slide(blank_layout)
set_slide_background(s13, C_WHITE)
add_header(s13, "Engineering Transparency & Growth Roadmap")

card_l13 = add_card(s13, Inches(0.8), Inches(1.8), Inches(5.75), Inches(4.8), C_BG_CARD, C_BORDER)
tb_l13 = s13.shapes.add_textbox(Inches(1.1), Inches(2.1), Inches(5.15), Inches(4.2))
tf_l13 = tb_l13.text_frame
tf_l13.word_wrap = True
p = tf_l13.paragraphs[0]
p.text = "Current Technical Limitations"
p.font.name = FONT_HEADING
p.font.size = Pt(18)
p.font.bold = True
p.font.color.rgb = C_NAVY

limits = [
    ("PayPal Stream Scope: ", "Tracks disbursements settled across PayPal rails. Does not yet ingest non-PayPal ACH or direct debit bank accounts."),
    ("Automated Cancellation: ", "Provides step-by-step negotiation and downgrade workflows; direct 1-click webhook cancellation planned for Stage 10."),
    ("Multi-Currency Normalization: ", "All amounts normalized to USD. Dynamic foreign exchange rate volatility tracking is in active development."),
    ("Cold-Start Data Dependency: ", "Requires at least 60 days of transaction history to compute statistically reliable Health Index scores.")
]
for title_sub, desc_sub in limits:
    p_step = tf_l13.add_paragraph()
    p_step.text = "•  " + title_sub + desc_sub
    p_step.font.name = FONT_BODY
    p_step.font.size = Pt(12)
    p_step.font.color.rgb = C_BODY
    p_step.space_before = Pt(8)

card_r13 = add_card(s13, Inches(6.8), Inches(1.8), Inches(5.75), Inches(4.8), C_WHITE, C_BORDER)
tb_r13 = s13.shapes.add_textbox(Inches(7.1), Inches(2.1), Inches(5.15), Inches(4.2))
tf_r13 = tb_r13.text_frame
tf_r13.word_wrap = True
p = tf_r9.paragraphs[0]
p.text = "Strategic Roadmap (Stage 10+)"
p.font.name = FONT_HEADING
p.font.size = Pt(18)
p.font.bold = True
p.font.color.rgb = C_NAVY

roadmap = [
    ("1-Click PayPal Webhook Cancellation: ", "Integrate PayPal Billing Agreements API to enable instant contract cancellations inside SubWise."),
    ("Plaid / Open Banking Integration: ", "Aggregate complementary checking accounts for holistic multi-bank liquidity views alongside PayPal."),
    ("Native PayPal App Marketplace: ", "Package SubWise AI as a verified, one-click installed app in the PayPal Commerce Platform."),
    ("Predictive Seat Right-Sizing: ", "Automated detection of inactive team seats through Google Workspace and GitHub API integrations.")
]
for title_sub, desc_sub in roadmap:
    p_item = tf_r13.add_paragraph()
    p_item.text = "🚀  " + title_sub + desc_sub
    p_item.font.name = FONT_BODY
    p_item.font.size = Pt(12)
    p_item.font.color.rgb = C_BODY
    p_item.space_before = Pt(8)


# ==============================================================================
# SLIDE 14: Conclusion & Key Takeaways
# ==============================================================================
s14 = prs.slides.add_slide(blank_layout)
set_slide_background(s14, C_WHITE)

# Left decorative bar
bar14 = s14.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.35), Inches(7.5))
bar14.fill.solid()
bar14.fill.fore_color.rgb = C_NAVY
bar14.line.fill.background()

# Title
add_header(s14, "SubWise AI: Transforming PayPal into a Proactive Financial Partner", "SUMMARY & CONCLUSION")

concl_cards = [
    ("101 Passing Tests",
     "100% verified test coverage across 8.5 stages. Zero regressions, complete PayPal Sandbox OAuth and Orders integration.",
     C_EMERALD, C_EMERALD_BG),
    ("Strict Accounting Rigor",
     "Zero funding contamination, zero double-counting, exact calendar payment scheduling without false smoothing.",
     C_NAVY, C_BG_CARD),
    ("Grounded AI Assistant",
     "Google Gemini 1.5 Flash with deterministic mathematical guardrails and automatic offline synthesis fallback.",
     C_PURPLE, C_PURPLE_BG)
]

for i, (title, desc, accent_color, bg_col) in enumerate(concl_cards):
    c_left = Inches(0.8) + i * Inches(3.95)
    card = add_card(s14, c_left, Inches(1.8), Inches(3.75), Inches(3.2), bg_col, C_BORDER)
    
    # Top accent bar
    top_bar = s14.shapes.add_shape(MSO_SHAPE.RECTANGLE, c_left + Inches(0.25), Inches(2.1), Inches(0.7), Inches(0.08))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = accent_color
    top_bar.line.fill.background()

    tb = s14.shapes.add_textbox(c_left + Inches(0.25), Inches(2.35), Inches(3.25), Inches(2.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.name = FONT_HEADING
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = C_DARK
    
    p2 = tf.add_paragraph()
    p2.text = desc
    p2.font.name = FONT_BODY
    p2.font.size = Pt(12)
    p2.font.color.rgb = C_BODY
    p2.space_before = Pt(8)

# Call to Action / Pitch Summary Box
cta_card = add_card(s14, Inches(0.8), Inches(5.3), Inches(11.733), Inches(1.5), C_NAVY, C_NAVY)
tb_cta = s14.shapes.add_textbox(Inches(1.1), Inches(5.45), Inches(11.133), Inches(1.2))
tf_cta = tb_cta.text_frame
tf_cta.word_wrap = True
p_cta1 = tf_cta.paragraphs[0]
p_cta1.text = "Ready for Production & Merchant Deployment"
p_cta1.font.name = FONT_HEADING
p_cta1.font.size = Pt(18)
p_cta1.font.bold = True
p_cta1.font.color.rgb = C_CYAN

p_cta2 = tf_cta.add_paragraph()
p_cta2.text = "SubWise AI delivers high-impact, calendar-aware cash flow protection for PayPal's millions of SMB merchants—preventing cash crunches before they happen. Thank you!"
p_cta2.font.name = FONT_BODY
p_cta2.font.size = Pt(13)
p_cta2.font.color.rgb = C_WHITE
p_cta2.space_before = Pt(4)

# Save file to project root
output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "PAYPAL_SUBWISE_AI_HACKATHON_PRESENTATION.pptx"))
prs.save(output_path)
print(f"Successfully generated {output_path} with {len(prs.slides)} professional slides.")

