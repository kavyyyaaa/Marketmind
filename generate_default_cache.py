import os
import json
import pandas as pd
import numpy as np

# Import backend modules
from trend_analysis import analyze_all_trends
from risk_analysis import analyze_risk
from forecasting import forecast_with_prophet, forecast_with_xgboost, forecast_with_mlp
from ai_explanation import generate_ai_explanation

def serialize_df(df: pd.DataFrame) -> dict:
    df_temp = df.copy()
    if isinstance(df_temp.index, pd.DatetimeIndex):
        df_temp = df_temp.reset_index()
        df_temp[df_temp.columns[0]] = df_temp[df_temp.columns[0]].dt.strftime('%Y-%m-%d')
    return df_temp.to_dict(orient='split')

def generate_synthetic_data(symbol: str) -> pd.DataFrame:
    import hashlib
    seed_num = int(hashlib.md5(symbol.encode('utf-8')).hexdigest(), 16) % 10000
    np.random.seed(seed_num)
    
    base_price = 175.0
    volatility = 0.15
    drift = 0.0003
    
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)
    dates = pd.date_range(start=start_date, end=end_date, freq='B')
    
    n_days = len(dates)
    daily_vol = volatility / np.sqrt(252)
    daily_drift = drift - 0.5 * (daily_vol ** 2)
    
    shocks = np.random.normal(0, 1, n_days)
    price_paths = np.zeros(n_days)
    price_paths[0] = base_price
    
    for t in range(1, n_days):
        price_paths[t] = price_paths[t-1] * np.exp(daily_drift + daily_vol * shocks[t])
        
    df = pd.DataFrame(index=dates)
    df['Close'] = price_paths
    df['Open'] = df['Close'] * (1 + np.random.normal(0, 0.003, n_days))
    df['High'] = np.maximum(df['Open'], df['Close']) * (1 + np.random.uniform(0, 0.008, n_days))
    df['Low'] = np.minimum(df['Open'], df['Close']) * (1 - np.random.uniform(0, 0.008, n_days))
    df['Volume'] = np.random.randint(1000000, 10000000, n_days)
    df.index.name = "Date"
    return df

def main():
    print("Pre-calculating default cache for AAPL...")
    df = generate_synthetic_data("AAPL")
    
    print("Computing indicators & risk...")
    df_analyzed = analyze_all_trends(df)
    risk_metrics = analyze_risk(df)
    
    print("Fitting forecasting models (this takes a few seconds)...")
    prophet_fc = forecast_with_prophet(df, 30)
    xgb_fc, xgb_importance = forecast_with_xgboost(df, 30)
    mlp_fc = forecast_with_mlp(df, 30)
    
    current_price = float(df['Close'].iloc[-1])
    prev_price = float(df['Close'].iloc[-2])
    pct_change = ((current_price - prev_price) / prev_price) * 100.0
    
    # Compute Ensemble yhat for the AI prompt
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
    
    print("Generating fallback narrative report to avoid API calls on startup...")
    # Explicitly use the fast rule-based fallback report to bypass Gemini API quotas and load instantly
    from ai_explanation import get_rule_based_explanation
    rsi_status = "Overbought" if indicators_dict["RSI"] > 70 else ("Oversold" if indicators_dict["RSI"] < 30 else "Neutral")
    macd_status = "Bullish Crossover" if indicators_dict["MACD"] > indicators_dict["MACD_Signal"] else "Bearish Crossover"
    bb_status = "Trading within normal bands"
    
    ai_report_markdown = get_rule_based_explanation(
        symbol="AAPL",
        current_price=current_price,
        price_change=pct_change,
        forecast_price=forecast_price,
        expected_return=expected_return,
        horizon_days=30,
        rsi_val=indicators_dict["RSI"],
        rsi_status=rsi_status,
        macd_status=macd_status,
        bb_status=bb_status,
        risk_val=risk_metrics["risk_score"],
        risk_cat=risk_metrics["risk_category"],
        volatility=risk_metrics["volatility"],
        drawdown=risk_metrics["max_drawdown"],
        var_95=risk_metrics["var_95"],
        sharpe=risk_metrics["sharpe_ratio"],
        model_choice="Ensemble"
    )
    
    cache_payload = {
        "symbol": "AAPL",
        "df_dict": serialize_df(df),
        "df_analyzed_dict": serialize_df(df_analyzed),
        "prophet_fc_dict": serialize_df(prophet_fc),
        "xgb_fc_dict": serialize_df(xgb_fc),
        "mlp_fc_dict": serialize_df(mlp_fc),
        "xgb_importance": xgb_importance,
        "risk_metrics": risk_metrics,
        "ai_report_markdown": ai_report_markdown,
        "data_source": "demo"
    }
    
    os.makedirs("assets", exist_ok=True)
    cache_path = os.path.join("assets", "default_aapl_cache.json")
    with open(cache_path, "w") as f:
        json.dump(cache_payload, f, indent=2)
        
    print(f"Success! Default cache saved to {cache_path}")

if __name__ == "__main__":
    main()
