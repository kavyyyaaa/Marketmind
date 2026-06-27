import os
import json
import io
import re
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory, render_template, make_response

# Import custom modules
from trend_analysis import analyze_all_trends
from risk_analysis import analyze_risk
from forecasting import forecast_with_prophet, forecast_with_xgboost, forecast_with_mlp
from ai_explanation import generate_ai_explanation
from report_generator import generate_pdf_report

app = Flask(__name__, static_folder="static", template_folder="templates")

# Global variable to cache Yahoo Finance connectivity status lazily
YFINANCE_STATUS = None

# Preset Tickers list
PRESET_TICKERS = [
    {"label": "Apple Inc. (AAPL)", "value": "AAPL"},
    {"label": "Microsoft Corp. (MSFT)", "value": "MSFT"},
    {"label": "NVIDIA Corp. (NVDA)", "value": "NVDA"},
    {"label": "Alphabet Inc. (GOOGL)", "value": "GOOGL"},
    {"label": "Tesla Inc. (TSLA)", "value": "TSLA"},
    {"label": "S&P 500 ETF (SPY)", "value": "SPY"},
    {"label": "Bitcoin USD (BTC-USD)", "value": "BTC-USD"}
]

# Offline Valid Symbols list to filter out invalid stock queries when API fails
OFFLINE_VALID_SYMBOLS = {
    "AAPL", "MSFT", "NVDA", "GOOGL", "GOOG", "TSLA", "SPY", "BTC-USD",
    "AMZN", "NFLX", "META", "AMD", "INTC", "MS", "GS", "JPM", "V", "MA",
    "DIS", "ADBE", "PYPL", "COIN", "ETH-USD", "USO", "GLD"
}

def generate_synthetic_data(symbol: str) -> pd.DataFrame:
    """Generates realistic synthetic historical stock data using a random walk with drift."""
    import hashlib
    # Seed based on symbol to get consistent data for the same symbol
    seed_num = int(hashlib.md5(symbol.encode('utf-8')).hexdigest(), 16) % 10000
    np.random.seed(seed_num)
    
    # Establish base price, volatility and drift based on known symbols or hashes
    base_prices = {
        "AAPL": 175.0,
        "MSFT": 400.0,
        "NVDA": 120.0,
        "GOOGL": 150.0,
        "TSLA": 180.0,
        "SPY": 500.0,
        "BTC-USD": 65000.0
    }
    
    base_price = base_prices.get(symbol, 100.0 + (seed_num % 400))
    volatility = 0.08 if symbol == "SPY" else (0.15 if symbol in ["MSFT", "AAPL", "GOOGL"] else (0.35 if symbol in ["TSLA", "NVDA"] else 0.55))
    drift = 0.0003 # Daily upward trend
    
    # Create daily dates for last 2 years (approx 500 trading days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)
    dates = pd.date_range(start=start_date, end=end_date, freq='B') # Business days
    
    # Geometric Brownian Motion simulation
    n_days = len(dates)
    daily_vol = volatility / np.sqrt(252)
    daily_drift = drift - 0.5 * (daily_vol ** 2)
    
    shocks = np.random.normal(0, 1, n_days)
    price_paths = np.zeros(n_days)
    price_paths[0] = base_price
    
    for t in range(1, n_days):
        price_paths[t] = price_paths[t-1] * np.exp(daily_drift + daily_vol * shocks[t])
        
    # Build dataframe
    df = pd.DataFrame(index=dates)
    df['Close'] = price_paths
    df['Open'] = df['Close'] * (1 + np.random.normal(0, 0.003, n_days))
    df['High'] = np.maximum(df['Open'], df['Close']) * (1 + np.random.uniform(0, 0.008, n_days))
    df['Low'] = np.minimum(df['Open'], df['Close']) * (1 - np.random.uniform(0, 0.008, n_days))
    df['Volume'] = np.random.randint(1000000, 10000000, n_days)
    df.index.name = "Date"
    return df

def check_yfinance_status() -> str:
    """Lazily checks Yahoo Finance API connectivity and caches the result."""
    global YFINANCE_STATUS
    if YFINANCE_STATUS is None:
        try:
            print("Checking Yahoo Finance API connectivity lazily...")
            test_df = yf.Ticker("AAPL").history(period="1d", timeout=1.0)
            if not test_df.empty:
                YFINANCE_STATUS = "ONLINE"
            else:
                YFINANCE_STATUS = "OFFLINE"
        except Exception:
            YFINANCE_STATUS = "OFFLINE"
        print(f"Yahoo Finance status determined: {YFINANCE_STATUS}")
    return YFINANCE_STATUS

# Load legacy default cache
DEFAULT_CACHE_PAYLOAD = None
DEFAULT_CACHE_FILE = os.path.join("assets", "default_aapl_cache.json")
if os.path.exists(DEFAULT_CACHE_FILE):
    print(f"Loading default AAPL cache from {DEFAULT_CACHE_FILE}...")
    try:
        with open(DEFAULT_CACHE_FILE, "r") as f:
            DEFAULT_CACHE_PAYLOAD = json.load(f)
        print("Default cache loaded successfully!")
    except Exception as e:
        print("Error loading default cache:", e)

def validate_ticker(symbol: str) -> bool:
    """Verifies format matches valid ticker expression."""
    return bool(re.match(r'^[A-Z0-9.\-]{1,10}$', symbol))

import math

def clean_nan(obj):
    """Recursively replaces float('nan'), float('inf'), and float('-inf') with None (JSON null)."""
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(x) for x in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    return obj

def deserialize_df(serialized):
    """Safely deserializes dataframes encoded in legacy JSON split format."""
    if not serialized:
        return None
    return pd.read_json(
        io.StringIO(serialized) if isinstance(serialized, str) else io.StringIO(json.dumps(serialized)),
        orient='split'
    )

def serialize_df_with_dates(df):
    """Safely resets index, handles date parsing, and formats as dictionary list."""
    df_reset = df.reset_index()
    # Detect date column
    date_col = None
    for col in ['Date', 'ds', 'index']:
        if col in df_reset.columns:
            date_col = col
            break
    if date_col is None:
        # Fallback to the first column if no named date column matches
        date_col = df_reset.columns[0]
        
    df_reset['Date'] = pd.to_datetime(df_reset[date_col]).dt.strftime('%Y-%m-%d')
    if date_col != 'Date':
        df_reset.drop(columns=[date_col], inplace=True)
        
    return df_reset.to_dict(orient='records')

def format_payload(cached_dict):
    """Converts a legacy Dash dict cache to the REST API JSON format."""
    if "historical" in cached_dict:
        return cached_dict
        
    symbol = cached_dict["symbol"]
    df = deserialize_df(cached_dict["df_dict"])
    df_analyzed = deserialize_df(cached_dict["df_analyzed_dict"])
    prophet_fc = deserialize_df(cached_dict["prophet_fc_dict"])
    xgb_fc = deserialize_df(cached_dict["xgb_fc_dict"])
    mlp_fc = deserialize_df(cached_dict["mlp_fc_dict"])
    xgb_importance = cached_dict["xgb_importance"]
    risk_metrics = cached_dict["risk_metrics"]
    ai_report_markdown = cached_dict["ai_report_markdown"]
    data_source = cached_dict["data_source"]
    
    # Precalculate SMA lines if not already present
    if 'SMA_20' not in df_analyzed.columns:
        df_analyzed['SMA_20'] = df_analyzed['Close'].rolling(window=20).mean()
    if 'SMA_50' not in df_analyzed.columns:
        df_analyzed['SMA_50'] = df_analyzed['Close'].rolling(window=50).mean()
        
    historical_list = serialize_df_with_dates(df_analyzed)
    
    # Format forecasts
    future_index = prophet_fc.index
    ensemble_fc = pd.DataFrame(index=future_index)
    ensemble_fc['yhat'] = (prophet_fc['yhat'] + xgb_fc['yhat'] + mlp_fc['yhat']) / 3.0
    ensemble_fc['yhat_lower'] = np.minimum(np.minimum(prophet_fc['yhat_lower'], xgb_fc['yhat_lower']), mlp_fc['yhat_lower'])
    ensemble_fc['yhat_upper'] = np.maximum(np.maximum(prophet_fc['yhat_upper'], xgb_fc['yhat_upper']), mlp_fc['yhat_upper'])
    
    forecasts = {}
    for name, fc_df in [("Prophet", prophet_fc), ("XGBoost", xgb_fc), ("MLP", mlp_fc), ("Ensemble", ensemble_fc)]:
        forecasts[name] = serialize_df_with_dates(fc_df)
        
    return clean_nan({
        "symbol": symbol,
        "historical": historical_list,
        "forecasts": forecasts,
        "xgb_importance": xgb_importance,
        "risk_metrics": risk_metrics,
        "ai_report_markdown": ai_report_markdown,
        "data_source": data_source
    })

def get_recommendation(expected_return: float, risk_metrics: dict, indicators: dict) -> tuple:
    """Calculates recommendation BUY/SELL/HOLD and detailed reason lists."""
    rsi_val = indicators.get("RSI", 50.0)
    macd_val = indicators.get("MACD", 0.0)
    macd_signal = indicators.get("MACD_Signal", 0.0)
    risk_score = risk_metrics.get("risk_score", 50.0)
    
    if expected_return > 8.0 and risk_score < 50.0:
        recommendation = "BUY"
    elif expected_return > 2.0 and risk_score < 70.0:
        recommendation = "BUY"
    elif expected_return < -5.0:
        recommendation = "SELL"
    elif expected_return < -2.0 and risk_score > 60.0:
        recommendation = "SELL"
    else:
        recommendation = "HOLD"
        
    reasons = []
    if expected_return > 0:
        reasons.append(f"Forecast model projects positive expected return of +{expected_return:.2f}% over the horizon.")
    else:
        reasons.append(f"Forecast model projects negative expected return of {expected_return:.2f}% over the horizon.")
        
    if rsi_val > 70:
        reasons.append(f"RSI indicator is at {rsi_val:.1f}, signaling overbought levels. Potential pullback risk.")
    elif rsi_val < 30:
        reasons.append(f"RSI indicator is at {rsi_val:.1f}, signaling oversold levels. Near-term price rebound possible.")
    else:
        reasons.append(f"RSI is neutral at {rsi_val:.1f}, suggesting stable momentum.")
        
    if macd_val > macd_signal:
        reasons.append("MACD indicator shows bullish crossover momentum (MACD line above Signal line).")
    else:
        reasons.append("MACD indicator shows bearish crossover momentum (MACD line below Signal line).")
        
    if risk_score > 60.0:
        reasons.append(f"Composite risk is elevated at {risk_score:.0f}/100. Size positions defensively.")
    else:
        reasons.append(f"Composite risk is comfortable at {risk_score:.0f}/100, supporting standard sizing.")
        
    return recommendation, reasons

def generate_csv_data(df_historical: pd.DataFrame, df_forecast: pd.DataFrame) -> str:
    """Compiles a unified CSV dataset of historical prices and forecasted bounds."""
    hist_df = pd.DataFrame(index=df_historical.index)
    hist_df['Type'] = 'Historical'
    hist_df['Price'] = df_historical['Close']
    hist_df['Confidence_Lower'] = np.nan
    hist_df['Confidence_Upper'] = np.nan
    
    fc_df = pd.DataFrame(index=df_forecast.index)
    fc_df['Type'] = 'Forecast'
    fc_df['Price'] = df_forecast['yhat']
    fc_df['Confidence_Lower'] = df_forecast['yhat_lower']
    fc_df['Confidence_Upper'] = df_forecast['yhat_upper']
    
    combined = pd.concat([hist_df, fc_df])
    combined.index.name = 'Date'
    combined_reset = combined.reset_index()
    combined_reset['Date'] = combined_reset['Date'].dt.strftime('%Y-%m-%d')
    return combined_reset.to_csv(index=False)

# Flask Routing Definition
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/analyze")
def analyze():
    preset_ticker = request.args.get("preset_ticker", "AAPL")
    custom_ticker = request.args.get("custom_ticker", "")
    ticker_mode = request.args.get("ticker_mode", "preset")
    horizon_days = int(request.args.get("horizon", "30"))
    
    if ticker_mode == "custom":
        symbol = custom_ticker.strip().upper() if custom_ticker and len(custom_ticker.strip()) > 0 else None
    else:
        symbol = preset_ticker
        
    if not symbol:
        symbol = "AAPL"
        
    if not validate_ticker(symbol):
        return jsonify({"error": f"Invalid stock symbol format: '{symbol}'"}), 400
        
    # Check if we should load the default Apple dataset from cache
    if (ticker_mode == "preset") and (symbol == "AAPL") and DEFAULT_CACHE_PAYLOAD:
        return jsonify(format_payload(DEFAULT_CACHE_PAYLOAD))
        
    # Ingest stock data from yfinance or generate synthetic mock data
    status = check_yfinance_status()
    if status == "OFFLINE":
        is_preset = any(p["value"] == symbol for p in PRESET_TICKERS)
        is_known = symbol in OFFLINE_VALID_SYMBOLS
        if not (is_preset or is_known):
            return jsonify({"error": f"Ticker '{symbol}' not found offline. Connect to the internet."}), 404
        df = generate_synthetic_data(symbol)
        data_source = "demo"
    else:
        try:
            print(f"Fetching stock data for {symbol}...")
            ticker_obj = yf.Ticker(symbol)
            df = ticker_obj.history(period="2y", timeout=5.0)
            if df.empty or len(df) < 30:
                df = generate_synthetic_data(symbol)
                data_source = "demo"
            else:
                data_source = "live"
                df.index.name = "Date"
        except Exception:
            is_preset = any(p["value"] == symbol for p in PRESET_TICKERS)
            is_known = symbol in OFFLINE_VALID_SYMBOLS
            if not (is_preset or is_known):
                return jsonify({"error": f"Error fetching ticker '{symbol}'. Check connection."}), 500
            df = generate_synthetic_data(symbol)
            data_source = "demo"
            global YFINANCE_STATUS
            YFINANCE_STATUS = "OFFLINE"
            
    # Calculate indicators
    df_analyzed = analyze_all_trends(df)
    risk_metrics = analyze_risk(df)
    
    # Fit forecasting models
    prophet_fc = forecast_with_prophet(df, horizon_days)
    xgb_fc, xgb_importance = forecast_with_xgboost(df, horizon_days)
    mlp_fc = forecast_with_mlp(df, horizon_days)
    
    current_price = float(df['Close'].iloc[-1])
    prev_price = float(df['Close'].iloc[-2])
    pct_change = ((current_price - prev_price) / prev_price) * 100.0
    
    future_index = prophet_fc.index
    ensemble_fc_yhat = (prophet_fc['yhat'] + xgb_fc['yhat'] + mlp_fc['yhat']) / 3.0
    forecast_price = float(ensemble_fc_yhat.iloc[-1])
    expected_return = ((forecast_price - current_price) / current_price) * 100.0
    
    indicators_dict = {
        "RSI": float(df_analyzed['RSI'].iloc[-1]),
        "MACD": float(df_analyzed['MACD'].iloc[-1]),
        "MACD_Signal": float(df_analyzed['MACD_Signal'].iloc[-1]),
        "BB_Upper": float(df_analyzed['BB_Upper'].iloc[-1]),
        "BB_Lower": float(df_analyzed['BB_Lower'].iloc[-1])
    }
    
    ai_report_markdown = generate_ai_explanation(
        symbol=symbol,
        current_price=current_price,
        price_change=pct_change,
        forecast_price=forecast_price,
        expected_return=expected_return,
        horizon_days=horizon_days,
        risk_metrics=risk_metrics,
        indicators=indicators_dict,
        model_choice="Ensemble"
    )
    
    # Precalculate SMA lines if not already present
    if 'SMA_20' not in df_analyzed.columns:
        df_analyzed['SMA_20'] = df_analyzed['Close'].rolling(window=20).mean()
    if 'SMA_50' not in df_analyzed.columns:
        df_analyzed['SMA_50'] = df_analyzed['Close'].rolling(window=50).mean()
        
    historical_list = serialize_df_with_dates(df_analyzed)
    
    # Format forecasts
    ensemble_fc = pd.DataFrame(index=future_index)
    ensemble_fc['yhat'] = ensemble_fc_yhat
    ensemble_fc['yhat_lower'] = np.minimum(np.minimum(prophet_fc['yhat_lower'], xgb_fc['yhat_lower']), mlp_fc['yhat_lower'])
    ensemble_fc['yhat_upper'] = np.maximum(np.maximum(prophet_fc['yhat_upper'], xgb_fc['yhat_upper']), mlp_fc['yhat_upper'])
    
    forecasts = {}
    for name, fc_df in [("Prophet", prophet_fc), ("XGBoost", xgb_fc), ("MLP", mlp_fc), ("Ensemble", ensemble_fc)]:
        forecasts[name] = serialize_df_with_dates(fc_df)
        
    return jsonify(clean_nan({
        "symbol": symbol,
        "historical": historical_list,
        "forecasts": forecasts,
        "xgb_importance": xgb_importance,
        "risk_metrics": risk_metrics,
        "ai_report_markdown": ai_report_markdown,
        "data_source": data_source
    }))

@app.route("/api/download_pdf", methods=["POST"])
def download_pdf():
    payload = request.json
    symbol = payload.get("symbol", "AAPL")
    
    historical = payload.get("historical", [])
    forecasts = payload.get("forecasts", {})
    risk_metrics = payload.get("risk_metrics", {})
    ai_report_markdown = payload.get("ai_report_markdown", "")
    
    current_price = historical[-1]["Close"]
    prev_price = historical[-2]["Close"]
    pct_change = ((current_price - prev_price) / prev_price) * 100.0
    
    def get_last_valid_yhat(model_name):
        model_fc = forecasts.get(model_name, [])
        for fc_point in reversed(model_fc):
            yhat = fc_point.get("yhat")
            if yhat is not None:
                return yhat
        return current_price

    forecast_price = get_last_valid_yhat("Ensemble")
    expected_return = ((forecast_price - current_price) / current_price) * 100.0
    horizon_days = len(forecasts.get("Ensemble", []))
    
    last_rsi = historical[-1].get("RSI", 50.0)
    last_macd = historical[-1].get("MACD", 0.0)
    last_macd_sig = historical[-1].get("MACD_Signal", 0.0)
    indicators_dict = {
        "RSI": last_rsi,
        "MACD": last_macd,
        "MACD_Signal": last_macd_sig,
        "BB_Upper": historical[-1].get("BB_Upper", current_price),
        "BB_Lower": historical[-1].get("BB_Lower", current_price)
    }
    
    recommendation, reasons = get_recommendation(expected_return, risk_metrics, indicators_dict)
    
    model_comparison = {
        "Prophet": get_last_valid_yhat("Prophet"),
        "XGBoost": get_last_valid_yhat("XGBoost"),
        "MLP Neural Network": get_last_valid_yhat("MLP"),
        "Ensemble Blend": forecast_price
    }
    
    pdf_bytes = generate_pdf_report(
        symbol=symbol,
        current_price=current_price,
        price_change=pct_change,
        forecast_price=forecast_price,
        expected_return=expected_return,
        horizon_days=horizon_days,
        risk_metrics=risk_metrics,
        recommendation=recommendation,
        reasons=reasons,
        model_comparison=model_comparison,
        ai_report=ai_report_markdown
    )
    
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=MarketMind_{symbol}_Report.pdf'
    return response

@app.route("/api/download_csv", methods=["POST"])
def download_csv():
    payload = request.json
    symbol = payload.get("symbol", "AAPL")
    
    historical = payload.get("historical", [])
    forecasts = payload.get("forecasts", {})
    
    df_hist = pd.DataFrame(historical)
    df_hist.set_index(pd.to_datetime(df_hist['Date']), inplace=True)
    
    ensemble = forecasts.get("Ensemble", [])
    df_fc = pd.DataFrame(ensemble)
    df_fc.set_index(pd.to_datetime(df_fc['Date']), inplace=True)
    
    csv_str = generate_csv_data(df_hist, df_fc)
    
    response = make_response(csv_str)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=MarketMind_{symbol}_Data.csv'
    return response

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8050, debug=True)
