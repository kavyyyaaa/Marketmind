import sys
import pandas as pd
import yfinance as yf
from trend_analysis import analyze_all_trends
from risk_analysis import analyze_risk
from forecasting import forecast_with_prophet, forecast_with_xgboost
from ai_explanation import generate_ai_explanation

def run_verification():
    print("==================================================")
    print("MARKETMIND AI BACKEND VERIFICATION RUN")
    print("==================================================")
    
    symbol = "MSFT"
    print(f"\n1. Ingesting historical daily stock data for '{symbol}'...")
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y")
        print(f"   Success: Loaded {len(df)} days of historical data.")
        print(f"   Last close price: ${df['Close'].iloc[-1]:.2f}")
    except Exception as e:
        print(f"   ERROR: Failed to fetch data: {e}")
        sys.exit(1)
        
    print("\n2. Computing trend analysis and technical indicators...")
    try:
        df_analyzed = analyze_all_trends(df)
        print("   Success: Indicators calculated.")
        print(f"   Current RSI (14): {df_analyzed['RSI'].iloc[-1]:.2f}")
        print(f"   Current Bollinger Middle: ${df_analyzed['BB_Middle'].iloc[-1]:.2f}")
        print(f"   Current MACD: {df_analyzed['MACD'].iloc[-1]:.4f}")
    except Exception as e:
        print(f"   ERROR: Failed indicators calculation: {e}")
        sys.exit(1)
        
    print("\n3. Performing risk analysis audit...")
    try:
        risk_metrics = analyze_risk(df)
        print("   Success: Risk metrics compiled.")
        print(f"   Risk Score: {risk_metrics['risk_score']}/100")
        print(f"   Risk Category: {risk_metrics['risk_category']}")
        print(f"   Annualized Volatility: {risk_metrics['volatility']*100:.2f}%")
        print(f"   Sharpe Ratio: {risk_metrics['sharpe_ratio']:.2f}")
        print(f"   Maximum Drawdown: {risk_metrics['max_drawdown']*100:.2f}%")
        print(f"   95% Value at Risk (VaR): {risk_metrics['var_95']*100:.2f}%")
    except Exception as e:
        print(f"   ERROR: Failed risk analysis: {e}")
        sys.exit(1)
        
    horizon_days = 7
    print(f"\n4. Running 7-day forecast models (Prophet and XGBoost)...")
    try:
        print("   Fitting Prophet model...")
        prophet_fc = forecast_with_prophet(df, horizon_days)
        print(f"   Prophet forecast for t+7: ${prophet_fc['yhat'].iloc[-1]:.2f}")
        
        print("   Fitting XGBoost recursive model...")
        xgb_fc, xgb_importances = forecast_with_xgboost(df, horizon_days)
        print(f"   XGBoost forecast for t+7: ${xgb_fc['yhat'].iloc[-1]:.2f}")
    except Exception as e:
        print(f"   ERROR: Failed forecasting models: {e}")
        sys.exit(1)
        
    print("\n5. Testing AI explanation component...")
    try:
        # Prepare inputs
        current_price = float(df['Close'].iloc[-1])
        prev_price = float(df['Close'].iloc[-2])
        pct_change = ((current_price - prev_price) / prev_price) * 100.0
        
        forecast_price = float(prophet_fc['yhat'].iloc[-1])
        expected_return = ((forecast_price - current_price) / current_price) * 100.0
        
        indicators_dict = {
            "RSI": float(df_analyzed['RSI'].iloc[-1]),
            "MACD": float(df_analyzed['MACD'].iloc[-1]),
            "MACD_Signal": float(df_analyzed['MACD_Signal'].iloc[-1]),
            "BB_Upper": float(df_analyzed['BB_Upper'].iloc[-1]),
            "BB_Lower": float(df_analyzed['BB_Lower'].iloc[-1])
        }
        
        report = generate_ai_explanation(
            symbol=symbol,
            current_price=current_price,
            price_change=pct_change,
            forecast_price=forecast_price,
            expected_return=expected_return,
            horizon_days=horizon_days,
            risk_metrics=risk_metrics,
            indicators=indicators_dict,
            model_choice="Prophet"
        )
        print("   Success: Report generated.")
        print("\n=== SAMPLE REPORT PREVIEW (First 300 chars) ===")
        print(report[:300] + "...")
        print("===============================================")
    except Exception as e:
        print(f"   ERROR: Failed AI explanation: {e}")
        sys.exit(1)
        
    print("\n==================================================")
    print("VERIFICATION COMPLETED SUCCESSFULLY!")
    print("==================================================")
    
if __name__ == "__main__":
    run_verification()
