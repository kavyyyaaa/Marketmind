import io
from datetime import datetime
from fpdf import FPDF

class CustomPDF(FPDF):
    def header(self):
        # Header banner
        self.set_fill_color(15, 23, 42) # Slate-900 (Dark background)
        self.rect(0, 0, 210, 32, 'F')
        
        self.set_text_color(255, 255, 255)
        self.set_font("helvetica", "B", 18)
        self.cell(0, 8, "MARKETMIND", align="L", ln=True)
        self.set_font("helvetica", "I", 10)
        self.cell(0, 4, "Advanced Quantitative Stock Forecast & Risk Report", align="L", ln=True)
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(148, 163, 184) # Slate-400
        self.cell(0, 10, f"Page {self.page_no()} // MarketMind Analytics Suite", align="R")

def generate_pdf_report(
    symbol: str,
    current_price: float,
    price_change: float,
    forecast_price: float,
    expected_return: float,
    horizon_days: int,
    risk_metrics: dict,
    recommendation: str,
    reasons: list,
    model_comparison: dict,
    ai_report: str
) -> bytes:
    """Generates a beautiful executive-level PDF report as bytes."""
    pdf = CustomPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Report Metadata
    pdf.set_text_color(15, 23, 42) # Dark Slate
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, f"EQUITY RESEARCH REPORT: {symbol.upper()}", ln=True)
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(100, 116, 139) # Gray
    pdf.cell(0, 5, f"Date: {datetime.now().strftime('%B %d, %Y')} // Horizon: {horizon_days} Days // Status: QUANT CORE CONVERGED", ln=True)
    pdf.ln(5)
    
    # Draw a line
    pdf.set_draw_color(226, 232, 240)
    pdf.line(10, 48, 200, 48)
    pdf.ln(4)
    
    # 1. Executive Summary Table
    pdf.set_text_color(15, 23, 42)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 6, "1. Executive Summary", ln=True)
    pdf.ln(2)
    
    pdf.set_font("helvetica", "", 10)
    # Print metrics in a grid
    pdf.set_fill_color(248, 250, 252) # Light background
    
    # Row 1
    pdf.cell(45, 8, " Last Market Close:", border=1, fill=True)
    pdf.cell(50, 8, f" ${current_price:.2f} ({price_change:+.2f}%)", border=1)
    pdf.cell(45, 8, " Expected Price Target:", border=1, fill=True)
    pdf.cell(50, 8, f" ${forecast_price:.2f} ({expected_return:+.2f}%)", border=1)
    pdf.ln(8)
    
    # Row 2
    pdf.cell(45, 8, " Composite Risk Index:", border=1, fill=True)
    pdf.cell(50, 8, f" {risk_metrics.get('risk_score', 0.0)}/100 ({risk_metrics.get('risk_category', 'Unknown')})", border=1)
    pdf.cell(45, 8, " Recommendation:", border=1, fill=True)
    pdf.cell(50, 8, f" {recommendation}", border=1)
    pdf.ln(12)
    
    # 2. Risk Profile
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 6, "2. Quantitative Risk Audit", ln=True)
    pdf.ln(2)
    
    pdf.set_font("helvetica", "", 10)
    pdf.cell(45, 8, " Annual Volatility:", border=1, fill=True)
    pdf.cell(50, 8, f" {risk_metrics.get('volatility', 0.0)*100:.2f}%", border=1)
    pdf.cell(45, 8, " Sharpe Ratio (Ann.):", border=1, fill=True)
    pdf.cell(50, 8, f" {risk_metrics.get('sharpe_ratio', 0.0):.2f}", border=1)
    pdf.ln(8)
    
    pdf.cell(45, 8, " Maximum Drawdown:", border=1, fill=True)
    pdf.cell(50, 8, f" {risk_metrics.get('max_drawdown', 0.0)*100:.2f}%", border=1)
    pdf.cell(45, 8, " 95% 1-Day VaR:", border=1, fill=True)
    pdf.cell(50, 8, f" {risk_metrics.get('var_95', 0.0)*100:.2f}%", border=1)
    pdf.ln(12)
    
    # 3. Model Comparison
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 6, "3. Forecasting Model Comparison", ln=True)
    pdf.ln(2)
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(65, 8, " Model Name", border=1, fill=True)
    pdf.cell(65, 8, " Projected Target Price", border=1, fill=True, align="R")
    pdf.cell(60, 8, " Expected Directional Return", border=1, fill=True, align="R")
    pdf.ln(8)
    
    pdf.set_font("helvetica", "", 10)
    for model_name, pred_price in model_comparison.items():
        ret = ((pred_price - current_price) / current_price) * 100.0
        pdf.cell(65, 8, f" {model_name}", border=1)
        pdf.cell(65, 8, f"${pred_price:.2f} ", border=1, align="R")
        pdf.cell(60, 8, f"{ret:+.2f}% ", border=1, align="R")
        pdf.ln(8)
        
    pdf.ln(4)
    
    # 4. Recommendation Rationale
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 6, "4. Qualitative Recommendation Rationale", ln=True)
    pdf.ln(2)
    pdf.set_font("helvetica", "", 10)
    for reason in reasons:
        pdf.cell(0, 6, f"- {reason}", ln=True)
        
    pdf.ln(6)
    
    # 5. AI Analyst Insights
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 6, "5. AI Analyst Narrative Insights", ln=True)
    pdf.ln(2)
    
    pdf.set_font("helvetica", "", 9.5)
    # Strip markdown headers to keep PDF reading clean
    clean_ai = ai_report.replace("# ", "").replace("## ", "").replace("### ", "").replace("**", "")
    pdf.multi_cell(0, 5, clean_ai)
    
    return bytes(pdf.output())
