import pandas as pd
import numpy as np

def analyze_risk(df: pd.DataFrame, risk_free_rate: float = 0.02) -> dict:
    """
    Computes key risk metrics and returns a consolidated risk analysis dictionary.
    
    Metrics:
    - Volatility (Annualized Std Dev of daily returns)
    - Max Drawdown (Peak to trough max loss)
    - Value at Risk (95% 1-day historical VaR)
    - Sharpe Ratio (Risk-adjusted return ratio)
    - Risk Score (A weighted index from 0 to 100)
    """
    if len(df) < 5:
        return {
            "volatility": 0.0,
            "max_drawdown": 0.0,
            "var_95": 0.0,
            "sharpe_ratio": 0.0,
            "risk_score": 0.0,
            "risk_category": "Insufficient Data"
        }
        
    df = df.copy()
    
    # Calculate daily returns
    df['Returns'] = df['Close'].pct_change()
    returns = df['Returns'].dropna()
    
    if len(returns) == 0:
        return {
            "volatility": 0.0,
            "max_drawdown": 0.0,
            "var_95": 0.0,
            "sharpe_ratio": 0.0,
            "risk_score": 0.0,
            "risk_category": "Insufficient Data"
        }

    # 1. Annualized Volatility
    daily_vol = returns.std()
    ann_vol = daily_vol * np.sqrt(252)
    
    # 2. Maximum Drawdown
    rolling_max = df['Close'].cummax()
    drawdowns = (df['Close'] - rolling_max) / rolling_max
    max_drawdown = drawdowns.min()
    
    # 3. 95% 1-day Value at Risk (VaR)
    # Using historical simulation method
    var_95_daily = -np.percentile(returns, 5) if len(returns) >= 10 else 0.0
    
    # 4. Sharpe Ratio
    # Annualized return
    total_return = (df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1
    n_years = len(df) / 252.0
    ann_return = (1 + total_return) ** (1 / n_years) - 1 if n_years > 0 else 0.0
    
    # Excess return over risk-free rate
    excess_return = ann_return - risk_free_rate
    sharpe_ratio = excess_return / ann_vol if ann_vol > 0 else 0.0
    
    # 5. Composite Risk Score (0-100)
    # Normalize components based on typical extreme limits
    # Volatility limit: 80% (0.80)
    vol_component = min(ann_vol / 0.80, 1.0) * 100
    
    # Max Drawdown limit: 70% (0.70)
    drawdown_component = min(abs(max_drawdown) / 0.70, 1.0) * 100
    
    # Daily VaR limit: 8% (0.08)
    var_component = min(var_95_daily / 0.08, 1.0) * 100
    
    # Weight: 40% Volatility, 30% Max Drawdown, 30% VaR
    risk_score = (0.4 * vol_component) + (0.3 * drawdown_component) + (0.3 * var_component)
    risk_score = round(max(0.0, min(100.0, risk_score)), 1)
    
    # Determine Category
    if risk_score < 25.0:
        risk_category = "Low"
    elif risk_score < 50.0:
        risk_category = "Moderate"
    elif risk_score < 75.0:
        risk_category = "High"
    else:
        risk_category = "Extreme"
        
    return {
        "volatility": float(ann_vol),
        "max_drawdown": float(max_drawdown),
        "var_95": float(var_95_daily),
        "sharpe_ratio": float(sharpe_ratio),
        "risk_score": float(risk_score),
        "risk_category": risk_category
    }
