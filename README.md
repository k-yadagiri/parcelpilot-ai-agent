# 📦 ParcelPilot AI Agent

An AI-powered customer support and operations agent built for the **ParcelPilot B2B logistics platform** as part of the **CalQuity AI Engineer Assessment**.

The agent combines **Google Gemini, LangGraph, document retrieval, structured operational data, and controlled tools** to answer questions related to customer accounts, orders, tickets, cancellations, service credits, SLAs, and product issues.

## 🚀 Live Demo

**Streamlit App:**  
https://parcelpilot-ai-agent-4nkrirwyfnerrj2zlrj2jp.streamlit.app/

**GitHub Repository:**  
https://github.com/k-yadagiri/parcelpilot-ai-agent

---

## 🎯 What I Built

The goal was to build more than a simple chatbot. The system acts as a **tool-using support agent** that retrieves evidence from the supplied ParcelPilot data before answering.

For a typical support question, the agent can:

1. Identify the relevant customer/account.
2. Retrieve the required order or ticket information.
3. Search the relevant policy/SOP/agreement documents.
4. Check whether a customer-specific agreement overrides the general policy.
5. Perform required time/SLA calculations.
6. Combine the retrieved information.
7. Provide a concise, justified answer.
8. Escalate when the available information is insufficient or human judgment is required.

---

## 📚 Data Used

The application uses the complete assessment data pack:

### PDF Documents

- `01_Support_Policy_v3_CURRENT.pdf`
- `02_Support_Policy_v2_DEPRECATED.pdf`
- `03_Cancellation_and_Service_Credit_SOP_v4.pdf`
- `04_Product_Operations_Guide_and_Known_Issues.pdf`
- `05_Northstar_Logistics_Enterprise_Agreement.pdf`
- `06_LumenWorks_Service_Agreement.pdf`

### Structured Dataset

- `ParcelPilot_Assessment_Data.xlsx`

The structured dataset provides operational information such as **accounts, orders, and tickets**.

The application also uses the supplied dataset snapshot time:

`2026-08-16 11:00:00`

as the reference time for SLA and other time-based reasoning.

---

## 🧠 Core Agent Capabilities

### 1. Natural-Language Support

Users can ask normal support questions such as:

> Can Northstar cancel ORD-1001 without a cancellation fee?

The agent retrieves the relevant account, order, and policy information before responding.

### 2. Document Retrieval

The agent searches the supplied PDF documents rather than relying only on the LLM's general knowledge.

### 3. Structured Data Retrieval

The agent can retrieve operational information from the assessment dataset, including:

- Accounts
- Orders
- Tickets
- Status
- Timestamps
- Assignments
- SLA-related information

### 4. SLA / Time Reasoning

Time-sensitive questions use the fixed assessment snapshot time and the application's timing tools instead of relying on the server's current clock.

### 5. Source Conflict Resolution

The application assigns reliability metadata to documents and follows this precedence:

```text
Current Customer Agreement
          ↓
Current Company Policy / SOP
          ↓
Current Product Documentation
          ↓
Deprecated / Historical Information

🏗️ Architecture
================

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML                   `┌─────────────────────┐                     │    Streamlit UI     │                     └──────────┬──────────┘                                │                                ▼                     ┌─────────────────────┐                     │   LangGraph Agent   │                     │    Google Gemini    │                     └──────────┬──────────┘                                │               ┌────────────────┼────────────────┐               │                │                │               ▼                ▼                ▼        ┌────────────┐   ┌────────────┐   ┌────────────┐        │ Documents  │   │ Structured │   │   Action   │        │ Retrieval  │   │    Data    │   │   Tools    │        └─────┬──────┘   └─────┬──────┘   └─────┬──────┘              │                │                │              ▼                ▼                ▼          PDF Files        Excel/SQLite    Controlled                                             Actions               └────────────────┼────────────────┘                                ▼                      ┌───────────────────┐                      │   Final Answer    │                      └───────────────────┘`

Agent Flow

The main agent is implemented in:

app/agent.py

It uses:

*   ChatGoogleGenerativeAI
    
*   LangGraph
    
*   create\_react\_agent
    
*   MemorySaver
    
*   Custom ParcelPilot tools
    

The agent receives a UserContext, builds the appropriate tools, and uses Gemini to determine when those tools are required.

🛠️ Technology Stack
====================

Area Technology Language Python UIStreamlit LLM Google Gemini Agent Frame work LangGraphLLM Framework LangChainGemini Integration langchain-google-genaiPDF Processing PyPDFData Processing Pandas Excel OpenPyXLDatabase SQLiteML/Data Utilities Scikit-learn Configuration python-dotenv Testing PytestVersion ControlGit / GitHub Deployment Streamlit Community Cloud

📂 Project Structure
====================

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   parcelpilot-ai-agent/  │  ├── app/  │   ├── __init__.py  │   ├── agent.py  │   ├── analytics.py  │   ├── build_db.py  │   ├── config.py  │   ├── retriever.py  │   └── tools.py  │  ├── data/  │   ├── raw_pdfs/  │   │   ├── 01_Support_Policy_v3_CURRENT.pdf  │   │   ├── 02_Support_Policy_v2_DEPRECATED.pdf  │   │   ├── 03_Cancellation_and_Service_Credit_SOP_v4.pdf  │   │   ├── 04_Product_Operations_Guide_and_Known_Issues.pdf  │   │   ├── 05_Northstar_Logistics_Enterprise_Agreement.pdf  │   │   └── 06_LumenWorks_Service_Agreement.pdf  │   │  │   ├── ParcelPilot_Assessment_Data.xlsx  │   └── db/  │  ├── docs/  ├── tests/  │  ├── streamlit_app.py  ├── requirements.txt  ├── README.md  ├── .gitignore  └── .env.example   `

👤 Author

**Yadagiri**
