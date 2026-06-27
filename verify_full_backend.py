import sys
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# Import backend modules
from trend_analysis import analyze_all_trends
from risk_analysis import analyze_risk
from forecasting import forecast_with_prophet, forecast_with_xgboost, forecast_with_mlp
from ai_explanation import generate_ai_explanation
from report_generator import generate_pdf_report

def get_recommendation(expected_return: float, risk_metrics: dict, indicators: dict) -> tuple:
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

def test_backend():
    print("==================================================")
    print("VERIFYING ALL MARKETMIND AI BACKEND COMPONENTS")
    print("==================================================")
    
    # Generate simulated data to guarantee successful runs without yfinance API blocks
    from app import generate_synthetic_data
    symbol = "MSFT"
    print(f"\n1. Ingesting daily stock data for '{symbol}'...")
    df = generate_synthetic_data(symbol)
    print(f"   Loaded {len(df)} days of historical data.")
    print(f"   Last close price: ${df['Close'].iloc[-1]:.2f}")
    
    print("\n2. Computing indicators & risk...")
    df_analyzed = analyze_all_trends(df)
    risk_metrics = analyze_risk(df)
    print(f"   RSI: {df_analyzed['RSI'].iloc[-1]:.2f}")
    print(f"   Risk Score: {risk_metrics['risk_score']}/100")
    
    horizon_days = 14
    print(f"\n3. Fitting 3 models (Prophet, XGBoost, MLP) for {horizon_days}-day horizon...")
    
    # Prophet
    print("   Running Prophet...")
    prophet_fc = forecast_with_prophet(df, horizon_days)
    print(f"   Prophet Forecast t+14: ${prophet_fc['yhat'].iloc[-1]:.2f}")
    
    # XGBoost
    print("   Running XGBoost...")
    xgb_fc, xgb_importances = forecast_with_xgboost(df, horizon_days)
    print(f"   XGBoost Forecast t+14: ${xgb_fc['yhat'].iloc[-1]:.2f}")
    print(f"   Top XGBoost Feature: {max(xgb_importances, key=xgb_importances.get)} ({max(xgb_importances.values())*100:.1f}%)")
    
    # MLP
    print("   Running MLP Neural Network...")
    mlp_fc = forecast_with_mlp(df, horizon_days)
    print(f"   MLP Forecast t+14: ${mlp_fc['yhat'].iloc[-1]:.2f}")
    
    # Ensemble
    future_index = prophet_fc.index[-horizon_days:]
    ensemble_yhat = (prophet_fc.loc[future_index, 'yhat'] + xgb_fc.loc[future_index, 'yhat'] + mlp_fc.loc[future_index, 'yhat']) / 3.0
    print(f"   Ensemble Forecast t+14: ${ensemble_yhat.iloc[-1]:.2f}")
    
    # Recommendation
    current_price = float(df['Close'].iloc[-1])
    expected_return = ((ensemble_yhat.iloc[-1] - current_price) / current_price) * 100.0
    indicators_dict = {
        "RSI": float(df_analyzed['RSI'].iloc[-1]),
        "MACD": float(df_analyzed['MACD'].iloc[-1]),
        "MACD_Signal": float(df_analyzed['MACD_Signal'].iloc[-1]),
        "BB_Upper": float(df_analyzed['BB_Upper'].iloc[-1]),
        "BB_Lower": float(df_analyzed['BB_Lower'].iloc[-1])
    }
    recommendation, reasons = get_recommendation(expected_return, risk_metrics, indicators_dict)
    print(f"\n4. Quantitative Recommendation: {recommendation}")
    for reason in reasons:
        print(f"   - {reason}")
        
    print("\n5. Generating AI Explanation (Fallback check)...")
    ai_report = generate_ai_explanation(
        symbol=symbol,
        current_price=current_price,
        price_change=-0.5,
        forecast_price=float(ensemble_yhat.iloc[-1]),
        expected_return=expected_return,
        horizon_days=horizon_days,
        risk_metrics=risk_metrics,
        indicators=indicators_dict,
        model_choice="Ensemble"
    )
    print("   AI Report successfully generated.")
    
    print("\n6. Compiling PDF Report via fpdf2...")
    model_comparison = {
        "Prophet": float(prophet_fc['yhat'].iloc[-1]),
        "XGBoost": float(xgb_fc['yhat'].iloc[-1]),
        "MLP Neural Network": float(mlp_fc['yhat'].iloc[-1]),
        "Ensemble Blend": float(ensemble_yhat.iloc[-1])
    }
    pdf_bytes = generate_pdf_report(
        symbol=symbol,
        current_price=current_price,
        price_change=-0.5,
        forecast_price=float(ensemble_yhat.iloc[-1]),
        expected_return=expected_return,
        horizon_days=horizon_days,
        risk_metrics=risk_metrics,
        recommendation=recommendation,
        reasons=reasons,
        model_comparison=model_comparison,
        ai_report=ai_report
    )
    
    print(f"   PDF generated successfully. Byte size: {len(pdf_bytes)} bytes")
    
    with open("test_report.pdf", "wb") as f:
        f.write(pdf_bytes)
    print("   Saved test_report.pdf to disk.")
    
    print("\n==================================================")
    print("ALL BACKEND CHECKS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    test_backend()
