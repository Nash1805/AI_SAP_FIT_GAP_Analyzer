AI‑Generated Fit‑Gap Analysis
Paste workshop notes or requirements → get a complete Fit‑Gap breakdown.

🧩 Fit‑Gap Matrix
Classifies each process step as Fit or Gap

Maps to SAP Best Practice scope items

Identifies impacted SAP modules

🛠️ WRICEF Register
Automatically generates:

Workflow

Reports

Interfaces

Conversions

Enhancements

Forms
With complexity scoring and module assignment.

📋 Requirements Extraction
Clear, testable requirements generated from raw notes.

🧑‍💼 User Stories
Each story includes:

Role

Goal

Benefit

3–5 acceptance criteria

🔗 Integration Impacts
Identifies:

Impacted systems (Ariba, SF, Legacy, etc.)

Interface type (API, IDoc, BAPI, CPI/BTP)

📦 Data Migration Objects
Lists:

Objects

Required fields

Migration risks

⚠️ Risk Analysis
Impact, likelihood, and mitigation strategies.

📤 Export
PDF export

JSON export

Save & load analyses

🧠 Powered by Groq Llama 3.3‑70B
This app uses Groq’s ultra‑fast inference to generate structured SAP analysis from unstructured workshop notes.

📦 Installation
Clone the repository:

bash
git clone https://github.com/<your-username>/sap-fit-gap-analyzer.git
cd sap-fit-gap-analyzer
Install dependencies:

bash
pip install -r requirements.txt
Create a .env file:

Code
GROQ_API_KEY=your_key_here
Run the app:

bash
streamlit run app.py
📁 Project Structure
Code
sap-fit-gap-analyzer/
│
├── app.py
├── requirements.txt
├── README.md
├── .env.example
└── assets/
    ├── screenshot_overview.png
    ├── screenshot_fitgap.png
    └── screenshot_export.png
