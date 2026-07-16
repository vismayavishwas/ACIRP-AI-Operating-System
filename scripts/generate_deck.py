import os
from fpdf import FPDF

class PitchDeck(FPDF):
    def header_slide(self, title):
        # Draw background color
        self.set_fill_color(11, 15, 25)
        self.rect(0, 0, 297, 210, "F")
        
        # Header bar accent
        self.set_fill_color(66, 133, 244)
        self.rect(0, 0, 297, 3, "F")
        
        # Title text
        self.set_font("Arial", "B", 18)
        self.set_text_color(66, 133, 244)
        self.text(15, 20, title)
        
        # Subtitle
        self.set_font("Arial", "", 9)
        self.set_text_color(156, 163, 175)
        self.text(15, 25, "ACIRP | Autonomous Civic Incident Platform")
        
        # Page count
        self.set_font("Arial", "B", 18)
        self.set_text_color(156, 163, 175)
        self.text(270, 20, f"0{self.page_no()}")

# Initialize PDF
pdf = PitchDeck(orientation="landscape", unit="mm", format="A4")
pdf.set_margins(15, 35, 15)

# ==============================================================
# SLIDE 1: Cover Slide
# ==============================================================
pdf.add_page()
# Draw Background
pdf.set_fill_color(11, 15, 25)
pdf.rect(0, 0, 297, 210, "F")

# Visual line
pdf.set_fill_color(66, 133, 244)
pdf.rect(15, 100, 267, 2, "F")

# Main Title (Enlarged)
pdf.set_font("Arial", "B", 60)
pdf.set_text_color(255, 255, 255)
pdf.text(15, 75, "ACIRP")

# Subtitle & Tagline
pdf.set_font("Arial", "", 18)
pdf.set_text_color(156, 163, 175)
pdf.text(15, 90, "Autonomous Civic Incident Platform")

pdf.set_font("Arial", "I", 12)
pdf.set_text_color(66, 133, 244)
pdf.text(15, 115, "Ensuring safe streets through agentic civic action.")

# Details Card
pdf.set_fill_color(20, 29, 47)
pdf.rect(15, 140, 150, 45, "F")
pdf.set_font("Arial", "B", 10)
pdf.set_text_color(255, 255, 255)
pdf.text(20, 150, "Team Leader: Vismaya Vishwas")
pdf.set_font("Arial", "", 9)
pdf.set_text_color(156, 163, 175)
pdf.text(20, 160, "Email: vismayavishwas11@gmail.com")
pdf.set_text_color(251, 188, 5) # Yellow
pdf.text(20, 170, "Integrations: Gemini 2.5, Firebase, Google Cloud, Mem0, Keploy")

# ==============================================================
# SLIDE 2: Problem & Solution (Constructive / Narrative)
# ==============================================================
pdf.add_page()
pdf.header_slide("Problem & Solution")

# Left Card: Problem
pdf.set_fill_color(20, 29, 47)
pdf.rect(15, 45, 125, 145, "F")
pdf.set_fill_color(219, 68, 85) # Red
pdf.rect(15, 45, 125, 2, "F")
pdf.set_font("Arial", "B", 14)
pdf.set_text_color(219, 68, 85)
pdf.text(25, 58, "THE CIVIC CHALLENGE")

# Context Quote
pdf.set_font("Arial", "I", 9.5)
pdf.set_text_color(156, 163, 175)
pdf.set_xy(25, 68)
pdf.multi_cell(105, 5, '"Urban India records millions of civic complaints annually, yet delayed routing and lack of verification leave many hazards unresolved."', 0, "L")

# Bullets
pdf.set_font("Arial", "", 9.5)
pdf.set_text_color(255, 255, 255)
y = 100
problems = [
    "Municipal departments are overwhelmed by duplicate, un-prioritized reports.",
    "Database outages or portal timeouts disconnect citizens from municipal cells.",
    "Lack of automated validation makes verification of field resolution expensive."
]
for p in problems:
    pdf.set_xy(25, y)
    pdf.multi_cell(105, 5, f"- {p}", 0, "L")
    y += 28

# Right Card: Solution
pdf.set_fill_color(20, 29, 47)
pdf.rect(157, 45, 125, 145, "F")
pdf.set_fill_color(52, 168, 83) # Green
pdf.rect(157, 45, 125, 2, "F")
pdf.set_font("Arial", "B", 14)
pdf.set_text_color(52, 168, 83)
pdf.text(167, 58, "HOW ACIRP HELPS")

pdf.set_font("Arial", "", 9.5)
pdf.set_text_color(255, 255, 255)
y = 75
solutions = [
    "Perception Agent: Structuring photos into prioritized complaints.",
    "Generates structured complaint reports and escalation petitions with human-in-the-loop review.",
    "Resilience Engine: Gracefully escalates to safety dispatchers on server outage.",
    "Resolution Proof: Automates audit verification via visual comparison."
]
for s in solutions:
    pdf.set_xy(167, y)
    pdf.multi_cell(105, 5, f"- {s}", 0, "L")
    y += 26

# ==============================================================
# SLIDE 3: System Architecture & Workflow (Flowchart)
# ==============================================================
pdf.add_page()
pdf.header_slide("System Workflow & Architecture")

# Draw Flowchart Row
steps = [
    ("Citizen Report", 15),
    ("Gemini Vision", 62),
    ("Routing Agent", 109),
    ("Firestore DB", 156),
    ("Verification", 203),
    ("Case Resolved", 250)
]

for name, x in steps:
    # Card box
    pdf.set_fill_color(20, 29, 47)
    pdf.rect(x, 45, 32, 20, "F")
    
    # Title Text
    pdf.set_font("Arial", "B", 8.5)
    pdf.set_text_color(255, 255, 255)
    # Centering text inside the box
    pdf.set_xy(x, 52)
    pdf.multi_cell(32, 4, name, 0, "C")
    
    # Draw arrow to next box if not the last one
    if x < 250:
        pdf.set_draw_color(66, 133, 244)
        pdf.set_line_width(1)
        # Line from end of current box to start of next box
        pdf.line(x + 32, 55, x + 47, 55)
        # Draw arrow tip
        pdf.line(x + 44, 53, x + 47, 55)
        pdf.line(x + 44, 57, x + 47, 55)

# Split Bottom Area into Why AI? and Technology Stack
# Bottom Left: Why AI?
pdf.set_fill_color(20, 29, 47)
pdf.rect(15, 80, 125, 110, "F")
pdf.set_fill_color(66, 133, 244)
pdf.rect(15, 80, 125, 2, "F")
pdf.set_font("Arial", "B", 13)
pdf.set_text_color(66, 133, 244)
pdf.text(25, 92, "WHY AGENTIC AI?")

pdf.set_font("Arial", "", 9.5)
pdf.set_text_color(255, 255, 255)
why_ai = [
    ("Vision-Based Recognition", "Structures raw incident photos into categorised details automatically."),
    ("Autonomous Context Routing", "Dynamically routes files to target helplines based on location/type."),
    ("Resolution Verification", "Analyzes before/after visual proof to ensure roads/bins are clear.")
]
y = 102
for title, desc in why_ai:
    pdf.set_font("Arial", "B", 9.5)
    pdf.text(25, y, f"* {title}:")
    pdf.set_font("Arial", "", 9)
    pdf.set_xy(25, y + 2)
    pdf.multi_cell(105, 4, desc, 0, "L")
    y += 28

# Bottom Right: Technology Stack
pdf.set_fill_color(20, 29, 47)
pdf.rect(157, 80, 125, 110, "F")
pdf.set_fill_color(52, 168, 83)
pdf.rect(157, 80, 125, 2, "F")
pdf.set_font("Arial", "B", 13)
pdf.set_text_color(52, 168, 83)
pdf.text(167, 92, "CORE TECHNOLOGY STACK")

pdf.set_font("Arial", "", 9.5)
pdf.set_text_color(255, 255, 255)
tech_stack = [
    ("AI Models & SDK:", "Gemini 2.5 Flash, Google GenAI SDK (Google AI Studio)"),
    ("Primary Database:", "Real-time incident database (Google Cloud Firestore)"),
    ("Asset Hosting:", "Firebase Storage (visual proofs) and Firebase Hosting CDN")
]
y = 102
for label, value in tech_stack:
    pdf.set_font("Arial", "B", 9.5)
    pdf.text(167, y, label)
    pdf.set_font("Arial", "", 9.5)
    pdf.set_xy(167, y + 2)
    pdf.multi_cell(105, 4, value, 0, "L")
    y += 28

# ==============================================================
# SLIDE 4: Partner Integrations & Market
# ==============================================================
pdf.add_page()
pdf.header_slide("Partner Integrations & Market")

# Mem0 Integration
pdf.set_fill_color(20, 29, 47)
pdf.rect(15, 45, 125, 68, "F")
pdf.set_fill_color(66, 133, 244)
pdf.rect(15, 45, 125, 2, "F")
pdf.set_font("Arial", "B", 12)
pdf.set_text_color(66, 133, 244)
pdf.text(20, 56, "Mem0 (Agent Memory Integration)")
pdf.set_font("Arial", "", 9.5)
pdf.set_text_color(255, 255, 255)
pdf.text(20, 68, "- Remembers complainant profiles across sessions.")
pdf.text(20, 78, "- Identifies local ward hazard repeating histories.")
pdf.text(20, 88, "- Real-time 'Memory Context' timelines generated automatically.")

# Keploy Integration
pdf.set_fill_color(20, 29, 47)
pdf.rect(15, 122, 125, 68, "F")
pdf.set_fill_color(251, 188, 5)
pdf.rect(15, 122, 125, 2, "F")
pdf.set_font("Arial", "B", 12)
pdf.set_text_color(251, 188, 5)
pdf.text(20, 133, "Keploy (API Test Mocking)")
pdf.set_font("Arial", "", 9.5)
pdf.set_text_color(255, 255, 255)
pdf.text(20, 145, "- Records real API calls and generates mocks automatically.")
pdf.text(20, 155, "- Tracks custom headers (x-competition) for route routing.")
pdf.text(20, 165, "- Ignores timestamps to prevent fake testing regression checks.")

# Market Opportunity
pdf.set_fill_color(20, 29, 47)
pdf.rect(157, 45, 125, 145, "F")
pdf.set_fill_color(52, 168, 83)
pdf.rect(157, 45, 125, 2, "F")
pdf.set_font("Arial", "B", 12)
pdf.set_text_color(52, 168, 83)
pdf.text(167, 56, "Market Impact & Operational Value")
pdf.set_font("Arial", "", 9.5)
pdf.set_text_color(255, 255, 255)
y = 70
points = [
    "Helps municipal officials, currently drowning in duplicate complaints, organize their work systematically.",
    "Improves transparency through automated tracking and visual verification.",
    "Allows ward representatives to view structured reports with human-in-the-loop approval.",
    "Reduces auditing costs and manual field inspection cycles.",
    "Highly scalable architecture: applicable to any municipality globally."
]
for p in points:
    pdf.set_xy(167, y)
    pdf.multi_cell(105, 4.5, f"- {p}", 0, "L")
    y += 24.5

# Save PDF
output_pdf_path = os.path.join(os.path.dirname(__file__), "ACIRP_MVP_Pitch_Deck.pdf")
pdf.output(output_pdf_path)
print(f"Generated Vector PDF successfully at: {output_pdf_path}")
