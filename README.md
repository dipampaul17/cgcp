# 🛡️ Claude Governance Control Plane (CGCP)

<div align="center">
  <img src="https://img.shields.io/badge/Status-Production_Ready-green?style=for-the-badge" alt="Status">
  <img src="https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-purple?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/Framework-FastAPI-teal?style=for-the-badge&logo=fastapi" alt="FastAPI">
</div>

<br>

> **Production-ready implementation of Anthropic's Responsible Scaling Policy (RSP) as an operational governance system for Claude AI deployments.**

## 🎯 Overview

The Claude Governance Control Plane (CGCP) translates Anthropic's safety commitments into verifiable controls, providing enterprises with:

- 🔍 **Real-time Risk Detection** across CBRN, self-harm, jailbreak, and exploitation categories
- 🎚️ **Tiered Access Controls** (General, Enterprise, Research Sandbox)
- 📊 **ASL-3 Monitoring** with automatic escalation triggers
- 📜 **ISO 42001 Compliance** reporting and evidence generation
- 🔄 **Human-in-the-loop** policy review and threshold adjustment

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip
- 4GB RAM minimum

### Installation

```bash
# Clone the repository
git clone https://github.com/dipampaul17/cgcp.git
cd cgcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the System

#### Option 1: Quick Start (Recommended)
```bash
# One command to start everything
./start.sh
```

#### Option 2: Complete Demo with Fresh Data
```bash
# Reset database, generate data, and run full demo
python demo/run_complete_demo.py
```

#### Option 3: Manual Start
```bash
# Terminal 1 - Start API Backend
uvicorn backend.app:app --host 0.0.0.0 --port 8000

# Terminal 2 - Start Dashboard
streamlit run ui/dashboard.py

# Terminal 3 - Run Demo (optional)
python demo/production_demo.py
```

### First Time Setup

1. **Reset Database** (if needed)
```bash
python demo/reset_database.py
```

2. **Generate Test Data**
```bash
python data/synthetic_generator.py
```

3. **Ingest Data**
```bash
python demo/ingest_data.py
```

## ��️ Architecture

```