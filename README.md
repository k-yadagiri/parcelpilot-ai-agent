# 📦 ParcelPilot AI Agent

An AI-powered customer support and operations assistant for ParcelPilot, a B2B logistics platform.

The system combines a conversational AI agent with document retrieval, structured operational data, and controlled state-changing actions to answer customer-support questions about orders, tickets, contracts, cancellations, service credits, SLAs, and product issues.

## 🚀 Live Application

**Try the deployed application:**

https://parcelpilot-ai-agent-4nkrirwyfnerrj2zlrj2jp.streamlit.app/

The application is deployed using Streamlit and provides a simple conversational interface for interacting with the ParcelPilot support agent.

---

## 📌 Project Overview

ParcelPilot support teams need to answer questions by checking multiple sources:

- Customer agreements
- Current support policies
- Cancellation and service-credit SOPs
- Product documentation
- Historical support tickets
- Account, order, and ticket data

These sources are not equally reliable. A customer-specific agreement may override a general company policy, while deprecated documents and historical ticket resolutions may contain outdated or incorrect information.

This project builds an AI support agent that combines these sources and applies source-precedence rules when answering questions.

---

## 🎯 Assessment Goals Addressed

The implementation is designed around the major requirements of the ParcelPilot AI Agent assessment:

- Natural-language support chatbot
- Document search and retrieval
- Structured account/order/ticket lookup
- Multi-step tool usage
- Access-controlled customer context
- State-changing actions
- Confirmation before state-changing actions
- Source reliability and conflict handling
- SLA and time-based reasoning
- Product issue investigation
- Streamlit-based chat interface
- Hosted application
- Proactive support/operations analysis

---

# ✨ Key Features

## 1. Natural-Language Support Chat

Users can ask questions such as:

> Can Northstar cancel ORD-1001 without a cancellation fee?

The agent identifies the relevant account, order information, and applicable policy/agreement before producing an answer.

---

## 2. Document Retrieval

The application searches the supplied ParcelPilot documents to retrieve relevant information from:

- Support Policy v3
- Support Policy v2 (deprecated)
- Cancellation & Service Credit SOP
- Product Operations Guide & Known Issues
- Northstar Logistics Enterprise Agreement
- LumenWorks Service Agreement

The system does not rely only on the LLM's general knowledge for policy-sensitive questions.

---

## 3. Structured Operational Data

The application works with the supplied ParcelPilot assessment dataset containing account, order, and ticket information.

Structured data is used for questions involving:

- Accounts
- Orders
- Tickets
- Ticket status
- Order status
- SLA calculations
- Operational investigation

---

## 4. Source Precedence & Reliability

Different sources have different authority levels.

The application follows this precedence:

```text
1. Current signed customer agreement
                ↓
2. Current company-wide policy / SOP
                ↓
3. Current product documentation
                ↓
4. Deprecated documents / historical ticket information
