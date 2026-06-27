import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load env variables (loads .env from parent folders or locally)
load_dotenv()

def generate_ai_explanation(
    symbol: str,
    current_price: float,
    price_change: float,
    forecast_price: float,
    expected_return: float,
    horizon_days: int,
    risk_metrics: dict,
    indicators: dict,
    model_choice: str
) -> str:
    """
    Generates a professional financial report using Gemini 1.5 Flash.
    Falls back to a structured rule-based report if the API fails or key is missing.
    """
    
    # Prepare data strings for the prompt
    rsi_val = indicators.get("RSI", 50.0)
    macd_val = indicators.get("MACD", 0.0)
    macd_signal = indicators.get("MACD_Signal", 0.0)
    close_price = current_price
    bb_upper = indicators.get("BB_Upper", close_price * 1.05)
    bb_lower = indicators.get("BB_Lower", close_price * 0.95)
    
    # Determine basic qualitative status
    rsi_status = "Overbought" if rsi_val > 70 else ("Oversold" if rsi_val < 30 else "Neutral")
    macd_status = "Bullish Crossover" if macd_val > macd_signal else "Bearish Crossover"
    
    bb_status = "Trading near Upper Band (Overextended)" if close_price >= bb_upper * 0.98 else (
        "Trading near Lower Band (Oversold/Undervalued)" if close_price <= bb_lower * 1.02 else "Trading within normal bands"
    )
    
    risk_val = risk_metrics.get("risk_score", 50.0)
    risk_cat = risk_metrics.get("risk_category", "Moderate")
    volatility = risk_metrics.get("volatility", 0.0) * 100.0
    drawdown = risk_metrics.get("max_drawdown", 0.0) * 100.0
    var_95 = risk_metrics.get("var_95", 0.0) * 100.0
    sharpe = risk_metrics.get("sharpe_ratio", 0.0)
    
    prompt = f"""
You are a Senior Financial Analyst and AI Quantitative Strategist.
Generate a comprehensive, executive-level Stock Forecast & Risk Analysis Report in Markdown format for the ticker symbol '{symbol.upper()}'.

Current Price: ${current_price:.2f} (Daily Change: {price_change:+.2f}%)
Forecast Horizon: {horizon_days} Days
Projected Price ({model_choice}): ${forecast_price:.2f} (Expected Return: {expected_return:+.2f}%)

Risk Assessment:
- Risk Score: {risk_val}/100 (Category: {risk_cat})
- Annualized Volatility: {volatility:.2f}%
- Maximum Drawdown: {drawdown:.2f}%
- 1-Day Value at Risk (95% VaR): {var_95:.2f}% of portfolio value
- Sharpe Ratio: {sharpe:.2f} (Annualized, risk-free rate = 2.0%)

Technical Indicators:
- RSI (14-day): {rsi_val:.1f} ({rsi_status})
- MACD Line: {macd_val:.4f}, Signal Line: {macd_signal:.4f} ({macd_status})
- Bollinger Bands: Close is at ${close_price:.2f} relative to Upper Band (${bb_upper:.2f}) and Lower Band (${bb_lower:.2f}) -> {bb_status}

Please construct a detailed analysis report using the following structure:
1. ## Executive Summary: A high-level overview of the asset's current state and forecast direction.
2. ## Forecasting Model Interpretation: Analyze the projected price. Discuss the implications of the expected return over the {horizon_days}-day horizon.
3. ## Risk Diagnostic & Exposure: Explain what the Volatility, Max Drawdown, and Value at Risk (VaR) mean for an investor. Interpret the Sharpe Ratio.
4. ## Technical Signal Synthesis: Synthesize the RSI, MACD, and Bollinger Bands indicators. What is the momentum showing?
5. ## Strategic Recommendations: Provide objective, data-driven suggestions for short-term and long-term positions based on the analysis.

Ensure the tone is highly professional, objective, and quantitative. Utilize markdown elements like tables, blockquotes, and highlights where appropriate. Do not include standard general investment disclosures (e.g. "this is not financial advice"). Make it read like a premium report.
"""
    
    # Try to load API key and run Gemini
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            if response.text and len(response.text.strip()) > 0:
                return response.text
        except Exception as e:
            # Fall back to rule-based report
            print(f"Gemini API execution failed: {e}. Falling back to rule-based report.")
            
    return get_rule_based_explanation(
        symbol=symbol,
        current_price=current_price,
        price_change=price_change,
        forecast_price=forecast_price,
        expected_return=expected_return,
        horizon_days=horizon_days,
        rsi_val=rsi_val,
        rsi_status=rsi_status,
        macd_status=macd_status,
        bb_status=bb_status,
        risk_val=risk_val,
        risk_cat=risk_cat,
        volatility=volatility,
        drawdown=drawdown,
        var_95=var_95,
        sharpe=sharpe,
        model_choice=model_choice
    )

def get_rule_based_explanation(
    symbol: str,
    current_price: float,
    price_change: float,
    forecast_price: float,
    expected_return: float,
    horizon_days: int,
    rsi_val: float,
    rsi_status: str,
    macd_status: str,
    bb_status: str,
    risk_val: float,
    risk_cat: str,
    volatility: float,
    drawdown: float,
    var_95: float,
    sharpe: float,
    model_choice: str
) -> str:
    """Generates a structured markdown financial report based on quantitative thresholds."""
    
    # 1. Executive Direction
    direction = "Bullish" if expected_return > 5.0 else ("Bearish" if expected_return < -5.0 else "Neutral/Consolidating")
    direction_color = "#10B981" if expected_return > 0 else "#EF4444"
    
    # 2. Risk interpretation
    if risk_cat == "Low":
        risk_desc = "displays low volatility and a protective risk profile. Suitable for capital preservation and defensive strategies."
    elif risk_cat == "Moderate":
        risk_desc = "exhibits standard market volatility. Suitable for core portfolio allocations seeking moderate growth."
    elif risk_cat == "High":
        risk_desc = "carries substantial volatility and drawdown risk. Investors should size positions carefully and prepare for swift price fluctuations."
    else:
        risk_desc = "exhibits extreme price swings, severe drawdown history, and highly elevated Value at Risk. Best suited for speculative capital and active risk management."

    # 3. Sharpe interpretation
    if sharpe > 2.0:
        sharpe_desc = "Outstanding risk-adjusted return ratio, indicating the historical performance has generated exceptional return relative to its volatility."
    elif sharpe > 1.0:
        sharpe_desc = "Adequate/Good risk-adjusted return, suggesting a favorable relationship between volatility and realized returns."
    elif sharpe > 0.0:
        sharpe_desc = "Sub-optimal risk-adjusted return. Returns are positive, but volatility is disproportionately high."
    else:
        sharpe_desc = "Negative risk-adjusted performance, indicating that the asset has underperformed a risk-free rate of return relative to its risk."

    # 4. Technical Indicator Synthesis
    tech_bullets = []
    if rsi_status == "Overbought":
        tech_bullets.append(f"- **RSI (14) is {rsi_val:.1f}**: The asset is in overbought territory, suggesting potential exhaustion of buyers and a pullback/reversion risk.")
    elif rsi_status == "Oversold":
        tech_bullets.append(f"- **RSI (14) is {rsi_val:.1f}**: The asset is oversold, indicating that it may be undervalued and due for a technical bounce.")
    else:
        tech_bullets.append(f"- **RSI (14) is {rsi_val:.1f}**: Momentum is in a neutral range, showing no immediate overbought or oversold conditions.")

    if "Bullish" in macd_status:
        tech_bullets.append("- **MACD Crossover**: The MACD line lies above the Signal line, indicating short-term momentum is rising faster than long-term trend, a bullish signal.")
    else:
        tech_bullets.append("- **MACD Crossover**: The MACD line is below the Signal line, showing bearish short-term pressure.")

    tech_bullets.append(f"- **Bollinger Bands**: {bb_status}.")

    # 5. Recommendation engine
    if expected_return > 8.0 and risk_cat in ["Low", "Moderate"]:
        rec = "Strong Buy / Accumulate. The forecast is positive with a favorable risk-reward profile."
    elif expected_return > 3.0:
        rec = "Moderate Buy. Favorable forecast, but volatile technical conditions suggest scaling into positions gradually."
    elif expected_return < -5.0:
        rec = "Reduce / Hedge. The model predicts price declines; consider profit-taking or writing protective call options."
    else:
        rec = "Hold / Monitor. The asset is projected to consolidate sideways. Ideal for range-bound trading or dividend/yield strategies."

    report = f"""# Quantitative Analytics Report: {symbol.upper()}
*Generated by MarketMind rule-based fallback engine.*

---

## Executive Summary
For Ticker **{symbol.upper()}**, the current market price is **${current_price:.2f}** with a daily change of **{price_change:+.2f}%**. The overall forecast direction is **<span style="color: {direction_color}">{direction}</span>**. Over the next **{horizon_days} days**, the {model_choice} model projects the asset to settle around **${forecast_price:.2f}**, representing an expected return of **{expected_return:+.2f}%**.

---

## Forecasting Model Interpretation
- **Model Selected**: {model_choice}
- **Projected Target**: ${forecast_price:.2f}
- **Expected Return**: {expected_return:+.2f}%

The {model_choice} forecast predicts that the price will move towards ${forecast_price:.2f} in the next {horizon_days} days. This movement represents a annualized expected return of approximately {(expected_return / horizon_days * 252):+.2f}%, indicating the forecast model sees a notable trend. 
> *Note: XGBoost captures short-term local structures and lag momentum, while Prophet models seasonal and weekly cycles. A combined forecast offers the highest reliability.*

---

## Risk Diagnostic & Exposure
The calculated **Risk Score is {risk_val}/100**, placing it in the **{risk_cat} Risk** category. 

- **Volatility ({volatility:.2f}%)**: This level of annualized volatility suggests that {symbol.upper()} {risk_desc}
- **Value at Risk ({var_95:.2f}%)**: The 95% 1-day VaR indicates a 5% probability that the asset will lose more than {var_95:.2f}% of its value in a single trading day, providing a key boundary for leverage and margin constraints.
- **Maximum Drawdown ({drawdown:.2f}%)**: This indicates the worst historical peak-to-trough drop over the period, showing the downside risk in a worst-case market event.
- **Sharpe Ratio ({sharpe:.2f})**: {sharpe_desc}

---

## Technical Signal Synthesis
Integrating technical indicators reveals the following details:
{chr(10).join(tech_bullets)}

Overall, technical momentum is currently aligned with the forecasting models, suggesting that near-term price actions are reacting to key support and resistance zones.

---

## Strategic Recommendations
- **Primary Stance**: `{rec}`
- **Risk Management**: Keep stop-loss bounds at approximately **${(current_price * (1 - var_95/100)):.2f}** (based on 1-day 95% VaR threshold).
- **Positioning**: For long-term investors, the Sharpe Ratio suggests it is {"favorable" if sharpe > 1.0 else "cautious"} to allocate capital. Short-term traders should trade the range defined by Bollinger Bands.
"""
    return report
