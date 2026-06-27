# MarketMind: Advanced Stock Forecasting & Risk Audit Suite

MarketMind is an ultra-premium, responsive quantitative stock analytics platform. It combines business-grade visual excellence with modern machine learning ensembles to provide investors, analysts, and recruiters with instant price projections, technical indicators, and systematic risk profiling.

---

## Key Features

- **🏠 Executive Dashboard Overview**: Real-time ticker summary containing last market close, projected target price, composite risk allocation progress bar, and unified recommendation strategy (`BUY` / `HOLD` / `SELL`).
- **📈 Predictive Forecast Curves**: Shaded confidence boundary intervals comparing the forecasts of three distinct algorithms and a unified Ensemble Blend:
  - *Facebook Prophet*: Core seasonality, trend drift, and business cycle modeling.
  - *Extreme Gradient Boosting (XGBoost)*: Short-term local lag momentum regression.
  - *Multilayer Perceptron (MLP)*: Multi-layered feedforward neural network trend fitting.
  - *Ensemble Blend*: An equally-weighted blend of all three models.
- **📊 Core Technical Indicators**: A beautiful, responsive 2x2 Plotly grid mapping:
  - Price, Simple Moving Averages (SMA 20/50), and Bollinger Bands.
  - Volume transaction delta colors (gains vs. losses).
  - Relative Strength Index (RSI 14) with overbought/oversold boundaries.
  - Moving Average Convergence Divergence (MACD) line crossovers and histogram.
- **⚠️ Quantitative Risk Audit Profile**: KPI dashboard tracking annualized price volatility, 95% 1-day Value at Risk (VaR), Sharpe Ratio (Rf=2.0%), Maximum peak-to-trough Drawdown, and S&P 500 Beta exposure, accompanied by a detailed risk audit narrative.
- **🤖 Bloomberg-Style Executive Report**: Real-time intelligence report detailing qualitative strategic recommendations and exposure assessments, powered by the Google Gemini API (with an offline rule-based fallback). Supports direct Morningstar-style PDF report downloads and CSV data spreadsheet exports.
- **⚙️ Diagnostics & Cache Control**: Local storage synchronization, API connectivity indicators, and diagnostic logs.

---

## Technology Stack

- **Backend**: Python 3.12, Flask, yfinance, Pandas, NumPy, Scikit-Learn, XGBoost, CmdStanPy (Prophet), FPDF.
- **Frontend**: HTML5, Vanilla CSS3 (Custom Glassmorphism, CSS Theme Variables), Vanilla ES6 JavaScript, Plotly.js (CDN), Marked.js (CDN).

---

## Quick Start & Installation

### Prerequisites
- Python 3.12+
- `uv` (recommended fast Python package manager) or standard `pip`

### Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone https://github.com/<your-username>/marketmind.git
   cd marketmind
   ```

2. **Initialize and Activate Virtual Environment**
   Using `uv` (recommended):
   ```powershell
   uv venv --python 3.12
   .venv\Scripts\activate
   ```
   Or using standard `venv`:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   uv pip install -r requirements.txt
   ```
   Or:
   ```bash
   pip install -r requirements.txt
   ```

4. **Add Environment Variables (Optional)**
   Create a `.env` file in the root folder to load your Gemini API Key:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
   *(If no key is provided, the platform will seamlessly switch to the rule-based quantitative intelligence report generator).*

5. **Launch Application**
   Simply double-click `run_marketmind.bat` or run:
   ```powershell
   .\run_marketmind.bat
   ```
   The dashboard will automatically open in your default browser at: **http://127.0.0.1:8050/**

---

## Git Deployment Guide

Since Git is not globally registered on this local environment, follow these simple steps to push this project to your GitHub repository:

1. **Open Git Bash / Command Prompt** (make sure Git is installed on your system).
2. **Initialize Git & Add Files**:
   ```bash
   git init
   git add .
   ```
3. **Configure Git Ignore** (make sure large directories like virtual environments are ignored):
   Create a `.gitignore` file:
   ```env
   .venv/
   __pycache__/
   *.pyc
   .env
   test_report.pdf
   ```
4. **Commit the Codebase**:
   ```bash
   git commit -m "feat: migrate to Flask REST API + premium HTML/CSS/JS frontend"
   ```
5. **Push to GitHub**:
   Create a new blank repository on GitHub, then link and push:
   ```bash
   git remote add origin https://github.com/<your-username>/marketmind.git
   git branch -M main
   git push -u origin main
   ```
