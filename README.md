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


A current customer-specific agreement therefore takes precedence over a general policy when the agreement applies to that customer.

Deprecated documents are not treated as authoritative.

Historical ticket resolutions are treated as context and are verified against current documentation rather than being treated as current policy.

🔐 Access Control
=================

The application supports two user contexts:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   Customer  Internal Staff   `

### Customer Mode

Customer-facing users are restricted to their own account context.

For example, a Northstar customer operating under:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   ACCT-001   `

should not be able to access another customer's account information.

### Internal Staff Mode

Internal ParcelPilot staff have broader operational access for support and investigation.

### Tool-Level Enforcement

Access control is not intended to rely only on the LLM's system prompt.

The authenticated UserContext is passed into the tool layer, where the available data and actions are restricted according to the user's role/account.

⚙️ State-Changing Actions
=========================

The application separates **read-only operations** from **state-changing operations**.

### Read-only examples

*   Search documents
    
*   Retrieve an order
    
*   Retrieve a ticket
    
*   Check account information
    
*   Check SLA information
    

### State-changing examples

*   Escalation
    
*   Follow-up tasks
    
*   Service-credit actions
    
*   Other supported operational changes
    

State-changing operations require explicit confirmation.

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   User Request       ↓  Agent Investigation       ↓  Action Preview       ↓  User Confirmation       ↓  Action Execution   `

The agent must not claim that an action has been completed before the confirmation/execution step.

🔄 Multi-Step Tool Workflows
============================

The agent can combine multiple tools when a question requires information from different sources.

Example:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   User Question       ↓  Identify Account       ↓  Retrieve Order/Ticket       ↓  Search Relevant Documents       ↓  Check Customer Agreement       ↓  Calculate Timing if Required       ↓  Apply Source Precedence       ↓  Generate Answer   `

This allows the system to handle questions that cannot be answered from a single database record or document.

🏗️ Architecture
================

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML                   `┌─────────────────────┐                     │    Streamlit UI     │                     └──────────┬──────────┘                                │                                ▼                     ┌─────────────────────┐                     │   LangGraph Agent   │                     │    Google Gemini    │                     └──────────┬──────────┘                                │               ┌────────────────┼────────────────┐               │                │                │               ▼                ▼                ▼        ┌────────────┐   ┌────────────┐   ┌────────────┐        │ Documents  │   │ Structured │   │   Action   │        │ Retrieval  │   │    Data    │   │   Tools    │        └─────┬──────┘   └─────┬──────┘   └─────┬──────┘              │                │                │              ▼                ▼                ▼          PDF Files        Excel/SQLite    Controlled                                             Actions               └────────────────┼────────────────┘                                ▼                      ┌───────────────────┐                      │   Final Answer    │                      └───────────────────┘`

### Agent Flow

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

AreaTechnologyLanguagePythonUIStreamlitLLMGoogle GeminiAgent FrameworkLangGraphLLM FrameworkLangChainGemini Integrationlangchain-google-genaiPDF ProcessingPyPDFData ProcessingPandasExcelOpenPyXLDatabaseSQLiteML/Data UtilitiesScikit-learnConfigurationpython-dotenvTestingPytestVersion ControlGit / GitHubDeploymentStreamlit Community Cloud

📂 Project Structure
====================

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   parcelpilot-ai-agent/  │  ├── app/  │   ├── __init__.py  │   ├── agent.py  │   ├── analytics.py  │   ├── build_db.py  │   ├── config.py  │   ├── retriever.py  │   └── tools.py  │  ├── data/  │   ├── raw_pdfs/  │   │   ├── 01_Support_Policy_v3_CURRENT.pdf  │   │   ├── 02_Support_Policy_v2_DEPRECATED.pdf  │   │   ├── 03_Cancellation_and_Service_Credit_SOP_v4.pdf  │   │   ├── 04_Product_Operations_Guide_and_Known_Issues.pdf  │   │   ├── 05_Northstar_Logistics_Enterprise_Agreement.pdf  │   │   └── 06_LumenWorks_Service_Agreement.pdf  │   │  │   ├── ParcelPilot_Assessment_Data.xlsx  │   └── db/  │  ├── docs/  ├── tests/  │  ├── streamlit_app.py  ├── requirements.txt  ├── README.md  ├── .gitignore  └── .env.example   `

⚙️ Configuration
================

Central configuration is maintained in:

app/config.py

It contains:

*   Project/data paths
    
*   Database paths
    
*   Excel dataset path
    
*   Document index path
    
*   Dataset snapshot time
    
*   Gemini model configuration
    
*   Document reliability metadata
    
*   Source precedence rules
    

Default model:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   gemini-2.5-flash   `

🔑 API Key & Security
=====================

The current implementation uses the **Google Gemini API**.

The API key is **not stored in the GitHub repository**.

For Streamlit Cloud, the key is configured through **Streamlit Secrets**.

Example:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   GOOGLE_API_KEY = "your-gemini-api-key"  GEMINI_MODEL = "gemini-2.5-flash"   `

The repository contains only placeholder configuration.

**Never commit a real API key to GitHub.**

🚀 Local Setup
==============

Clone the repository:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   git clone https://github.com/k-yadagiri/parcelpilot-ai-agent.git  cd parcelpilot-ai-agent   `

Install dependencies:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   pip install -r requirements.txt   `

Configure the Gemini API key using environment variables or local secrets.

Run the application:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   streamlit run streamlit_app.py   `

☁️ Deployment
=============

The application is deployed directly from GitHub using Streamlit Community Cloud.

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   GitHub Repository         ↓  main branch         ↓  Streamlit Cloud         ↓  Install requirements.txt         ↓  Load Secrets         ↓  Run streamlit_app.py         ↓  Live Application   `

### Repository

[https://github.com/k-yadagiri/parcelpilot-ai-agent](https://github.com/k-yadagiri/parcelpilot-ai-agent?utm_source=chatgpt.com)

### Live Application

[https://parcelpilot-ai-agent-4nkrirwyfnerrj2zlrj2jp.streamlit.app/](https://parcelpilot-ai-agent-4nkrirwyfnerrj2zlrj2jp.streamlit.app/)

💬 Example
==========

### User

> Can Northstar cancel ORD-1001 without a cancellation fee?

### Agent

The agent:

1.  Identifies Northstar Logistics.
    
2.  Retrieves account ACCT-001.
    
3.  Retrieves order ORD-1001.
    
4.  Checks the order status.
    
5.  Retrieves the general cancellation SOP.
    
6.  Retrieves the Northstar customer agreement.
    
7.  Applies the source-precedence rule.
    
8.  Produces the final answer using the retrieved evidence.
    

This demonstrates the intended **multi-step, tool-using agent workflow**.

🚨 Escalation & Reliability
===========================

The agent should not guess when important information is missing or conflicting.

Situations that may require escalation include:

*   P1 incidents
    
*   Complete outages
    
*   Suspected security incidents
    
*   Unresolved policy conflicts
    
*   Unsupported exceptions
    
*   SLA breaches requiring intervention
    
*   Requests requiring human judgment
    

The system prioritizes **evidence and source authority over confident speculation**.

📈 Proactive Support / Operations
=================================

The project also includes support/operations analysis capabilities for identifying issues such as:

*   High-severity tickets
    
*   SLA risks
    
*   Recurring support problems
    
*   Product-related issues
    
*   Operational patterns
    

The objective is to move beyond a purely reactive chatbot and help support teams identify issues that may require attention.

🧠 Design Decisions
===================

### Why Gemini?

Gemini provides the natural-language reasoning and tool-selection layer while application code remains responsible for business data and operational controls.

### Why LangGraph?

The problem requires multi-step tool workflows. LangGraph provides a structured way for the agent to reason, call tools, observe results, and continue until it has enough information to answer.

### Why Tool-Based Data Access?

Business-critical information should come from the supplied documents and operational dataset rather than from the LLM's general knowledge.

### Why Source Precedence?

The assessment contains documents with different authority levels, including customer-specific agreements and deprecated policies. Explicit precedence prevents the agent from treating all sources equally.

### Why Confirmation?

Operational actions can have real consequences. Separating action preview from execution reduces the risk of unintended changes.

### Why Fixed Dataset Time?

Using the supplied snapshot time makes SLA and time-based reasoning reproducible instead of depending on the server's current clock.

⚖️ Technical Trade-offs
=======================

DecisionBenefitTrade-offGeminiStrong reasoning/tool useRequires API keyLangGraphStructured multi-step workflowsAdditional complexitySQLiteSimple and lightweightNot ideal for production scaleStreamlitFast development/deploymentLimited compared with a production frontendFixed dataset timeReproducible resultsNot live operational dataMock authenticationSimple assessment demonstrationRequires production authentication for real deployment

⚠️ Known Limitations
====================

This is an assessment/demo implementation rather than a production enterprise system.

Current limitations include:

*   Mock authentication
    
*   Assessment-sized dataset
    
*   Streamlit-based UI
    
*   Limited production monitoring
    
*   No enterprise SSO
    
*   No production-grade audit system
    
*   SQLite is not intended for high-scale production workloads
    
*   Gemini API dependency
    
*   Limited automated evaluation coverage
    
*   State-changing actions operate within the assessment environment rather than a real ParcelPilot backend
    

🔮 Future Improvements
======================

For a production version, I would add:

*   SSO/OAuth authentication
    
*   Production RBAC
    
*   PostgreSQL or another production database
    
*   Persistent audit logs
    
*   Hybrid/semantic retrieval with reranking
    
*   Automated evaluation and regression tests
    
*   Production monitoring and observability
    
*   User feedback loops
    
*   Better source citations
    
*   Integration with real ParcelPilot operational systems
    

📊 Evaluation Metric
====================

A primary metric for the agent would be:

### Correct Resolution Rate

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   Correctly resolved eligible requests  --------------------------------------  Total eligible requests   `

Additional safety metrics:

*   Incorrect answer rate
    
*   Unsafe action rate
    
*   Unnecessary escalation rate
    
*   Tool failure rate
    
*   Response latency
    

For an operational AI agent, accuracy should be measured together with safety and reliability.

🤖 AI-Assisted Development
==========================

AI coding tools were used during development to assist with:

*   Understanding assessment requirements
    
*   Project scaffolding
    
*   Code generation
    
*   Debugging
    
*   Refactoring
    
*   Dependency configuration
    
*   Streamlit deployment troubleshooting
    
*   Documentation
    

The implementation, configuration, integration, and final deployment were reviewed and assembled into the submitted GitHub project.

🎥 Submission Video
===================

The walkthrough video will demonstrate:

1.  Project overview
    
2.  Architecture
    
3.  Live Streamlit application
    
4.  Customer/internal user context
    
5.  Natural-language support query
    
6.  Tool-based workflow
    
7.  Document/source precedence
    
8.  Structured data usage
    
9.  Access control
    
10.  Confirmation-gated actions
    
11.  Technical decisions
    
12.  Product improvements
    

📋 Assessment Submission
========================

### GitHub Repository

[https://github.com/k-yadagiri/parcelpilot-ai-agent](https://github.com/k-yadagiri/parcelpilot-ai-agent?utm_source=chatgpt.com)

### Live Agent

[https://parcelpilot-ai-agent-4nkrirwyfnerrj2zlrj2jp.streamlit.app/](https://parcelpilot-ai-agent-4nkrirwyfnerrj2zlrj2jp.streamlit.app/)

### Demo Video

_Add Loom / Google Drive / YouTube link here._

### LinkedIn

_Add LinkedIn profile link here._

👤 Author
=========

**Yadagiri**

B.Tech – Computer Science & Engineering (AI & Data Science)

GitHub:[https://github.com/k-yadagiri](https://github.com/k-yadagiri)

LinkedIn:_Add LinkedIn profile here._
