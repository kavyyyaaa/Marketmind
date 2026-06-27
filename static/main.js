// ==========================================================================
// MARKETMIND - CORE FRONTEND CLIENT
// ==========================================================================

// Preset Ticker Options
const PRESET_TICKERS = [
    { label: "Apple Inc. (AAPL)", value: "AAPL" },
    { label: "Microsoft Corp. (MSFT)", value: "MSFT" },
    { label: "NVIDIA Corp. (NVDA)", value: "NVDA" },
    { label: "Alphabet Inc. (GOOGL)", value: "GOOGL" },
    { label: "Tesla Inc. (TSLA)", value: "TSLA" },
    { label: "S&P 500 ETF (SPY)", value: "SPY" },
    { label: "Bitcoin USD (BTC-USD)", value: "BTC-USD" }
];

// App Local States
let activePage = "dashboard";
let activeTheme = "dark";
let tickerMode = "preset"; // 'preset' or 'custom'
let selectedPresetTicker = "AAPL";
let customTickerValue = "";
let forecastHorizon = 30;
let forecastModel = "Ensemble";

// Analysis Data Cache Payload
let cachedPayload = null;

// Initialize Client on Load
document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initDropdown();
    initEventListeners();
    
    // Trigger initial AAPL analysis on load
    triggerAnalysis();
});

// ==========================================================================
// THEME MANAGER
// ==========================================================================
function initTheme() {
    const savedTheme = localStorage.getItem("theme") || "dark";
    setTheme(savedTheme);
}

function setTheme(theme) {
    activeTheme = theme;
    const root = document.getElementById("app-root");
    const toggleBtn = document.getElementById("theme-toggle-btn");
    const settingsDisplay = document.getElementById("settings-theme-display");
    
    if (theme === "light") {
        root.classList.add("light-theme");
        toggleBtn.textContent = "Dark Theme";
        if (settingsDisplay) settingsDisplay.textContent = "Active Theme: Light Theme";
    } else {
        root.classList.remove("light-theme");
        toggleBtn.textContent = "Light Theme";
        if (settingsDisplay) settingsDisplay.textContent = "Active Theme: Dark Theme";
    }
    
    localStorage.setItem("theme", theme);
    
    // Redraw Plotly charts to reflect theme swap
    if (cachedPayload) {
        renderAllCharts();
    }
}

function toggleTheme() {
    setTheme(activeTheme === "dark" ? "light" : "dark");
}

// Get Theme Colors for Plotly Charts
function getThemeChartColors() {
    const isLight = activeTheme === "light";
    return {
        paperBg: "rgba(0,0,0,0)",
        plotBg: "rgba(0,0,0,0)",
        textColor: isLight ? "#475569" : "#94a3b8",
        gridColor: isLight ? "rgba(15, 23, 42, 0.05)" : "rgba(255, 255, 255, 0.04)",
        zeroLineColor: isLight ? "rgba(15, 23, 42, 0.1)" : "rgba(255, 255, 255, 0.08)",
        cardBorder: isLight ? "#e2e8f0" : "rgba(255,255,255,0.06)"
    };
}

// ==========================================================================
// TICKER DROPDOWN ELEMENT CONTROL
// ==========================================================================
function initDropdown() {
    const optionsContainer = document.getElementById("dropdown-options-list");
    optionsContainer.innerHTML = "";
    
    PRESET_TICKERS.forEach(ticker => {
        const option = document.createElement("div");
        option.className = "dropdown-option";
        if (ticker.value === selectedPresetTicker) {
            option.classList.add("selected");
        }
        option.textContent = ticker.label;
        option.onclick = () => selectPresetOption(ticker);
        optionsContainer.appendChild(option);
    });
}

function toggleDropdown() {
    const wrapper = document.querySelector(".dropdown-wrapper");
    wrapper.classList.toggle("open");
}

function closeDropdown() {
    const wrapper = document.querySelector(".dropdown-wrapper");
    wrapper.classList.remove("open");
}

function selectPresetOption(ticker) {
    selectedPresetTicker = ticker.value;
    document.getElementById("selected-preset-label").textContent = ticker.label;
    
    // Mark active options
    const options = document.querySelectorAll(".dropdown-option");
    options.forEach(opt => {
        if (opt.textContent === ticker.label) {
            opt.classList.add("selected");
        } else {
            opt.classList.remove("selected");
        }
    });
    
    closeDropdown();
    triggerAnalysis();
}

function setTickerMode(mode) {
    tickerMode = mode;
    const tabPreset = document.getElementById("tab-preset");
    const tabCustom = document.getElementById("tab-custom");
    const selectWrapper = document.getElementById("preset-select-wrapper");
    const customInput = document.getElementById("custom-ticker-input");
    
    if (mode === "preset") {
        tabPreset.classList.add("active");
        tabCustom.classList.remove("active");
        selectWrapper.style.display = "block";
        customInput.style.display = "none";
    } else {
        tabPreset.classList.remove("active");
        tabCustom.classList.add("active");
        selectWrapper.style.display = "none";
        customInput.style.display = "block";
        customInput.focus();
    }
}

function handleCustomInputKey(event) {
    if (event.key === "Enter") {
        triggerAnalysis();
    }
}

// Close Dropdown if click outside
window.addEventListener("click", (e) => {
    const trigger = document.getElementById("dropdown-select-trigger");
    if (trigger && !trigger.contains(e.target)) {
        closeDropdown();
    }
});

// ==========================================================================
// PAGE ROUTING & STATE EVENTS
// ==========================================================================
function initEventListeners() {
    document.getElementById("theme-toggle-btn").addEventListener("click", toggleTheme);
}

function switchPage(pageId) {
    activePage = pageId;
    
    // Toggle active nav links
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(item => {
        if (item.id === `nav-${pageId}`) {
            item.classList.add("active");
        } else {
            item.classList.remove("active");
        }
    });
    
    // Toggle active page section
    const sections = document.querySelectorAll(".page-section");
    sections.forEach(sec => {
        if (sec.id === `page-${pageId}`) {
            sec.classList.add("active");
        } else {
            sec.classList.remove("active");
        }
    });
    
    // Redraw charts on tab switch to fit grid boundaries correctly
    if (cachedPayload) {
        setTimeout(() => {
            renderAllCharts();
        }, 50);
    }
}

function updateHorizonDisplay(val) {
    document.getElementById("horizon-display-val").textContent = `${val} Days`;
}

function changeHorizon(val) {
    forecastHorizon = parseInt(val);
    triggerAnalysis();
}

function changeModel(val) {
    forecastModel = val;
    if (cachedPayload) {
        updateForecastDetails();
        renderForecastChart();
    }
}

// ==========================================================================
// REST API DATA INTEGRATION
// ==========================================================================
async function triggerAnalysis() {
    const errorContainer = document.getElementById("error-container");
    errorContainer.style.display = "none";
    errorContainer.innerHTML = "";
    
    // Get symbol value
    let symbol = selectedPresetTicker;
    if (tickerMode === "custom") {
        const inputVal = document.getElementById("custom-ticker-input").value.trim().toUpperCase();
        if (!inputVal) {
            errorContainer.innerHTML = `<div class="error-banner">Please enter a custom stock symbol.</div>`;
            errorContainer.style.display = "block";
            return;
        }
        symbol = inputVal;
    }
    
    // Start loader spinner animation
    document.getElementById("status-loading").style.display = "inline-block";
    document.getElementById("analyze-btn").disabled = true;
    
    try {
        const res = await fetch(`/api/analyze?preset_ticker=${selectedPresetTicker}&custom_ticker=${symbol}&ticker_mode=${tickerMode}&horizon=${forecastHorizon}`);
        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.error || "Analysis execution error.");
        }
        
        const data = await res.json();
        cachedPayload = data;
        
        // Render UI panels
        updateDashboardDetails();
        updateForecastDetails();
        updateRiskDetails();
        updateReportDetails();
        updateSettingsDetails();
        
        // Render Plotly graphs
        renderAllCharts();
        
    } catch (err) {
        console.error(err);
        errorContainer.innerHTML = `<div class="error-banner" style="background-color:rgba(244,63,94,0.08); border:1px solid rgba(244,63,94,0.2); color:var(--market-rose); padding:12px; border-radius:8px; margin-bottom:20px; font-size:13px;">Error: ${err.message}</div>`;
        errorContainer.style.display = "block";
    } finally {
        // Stop loader spinner
        document.getElementById("status-loading").style.display = "none";
        document.getElementById("analyze-btn").disabled = false;
    }
}

// ==========================================================================
// UI COMPONENT DATA UPDATERS
// ==========================================================================
// Helper to get the last valid yhat forecast value from a forecast array
function getLastValidYhat(fcList, fallbackVal) {
    if (!fcList || fcList.length === 0) return fallbackVal;
    for (let i = fcList.length - 1; i >= 0; i--) {
        const val = fcList[i].yhat;
        if (val !== null && val !== undefined) {
            return val;
        }
    }
    return fallbackVal;
}

function updateDashboardDetails() {
    const ticker = cachedPayload.symbol;
    const hist = cachedPayload.historical;
    const lastRow = hist[hist.length - 1];
    const prevRow = hist[hist.length - 2];
    
    // Set headers
    document.getElementById("dash-overview-title").textContent = `${ticker} - Market Overview`;
    document.getElementById("forecast-title").textContent = `${ticker} - Predictive Forecast Models`;
    document.getElementById("technical-title").textContent = `${ticker} - Core Technical Indicator Suite`;
    document.getElementById("risk-title").textContent = `${ticker} - Quantitative Risk Audit Profile`;
    
    // Price details
    const lastClose = lastRow.Close;
    const priceChange = lastClose - prevRow.Close;
    const pctChange = (priceChange / prevRow.Close) * 100.0;
    
    document.getElementById("card-last-close").textContent = `$${lastClose.toFixed(2)}`;
    
    const changeCard = document.getElementById("card-price-change");
    changeCard.textContent = `${pctChange >= 0 ? "+" : ""}${pctChange.toFixed(2)}% (${priceChange >= 0 ? "+" : ""}${priceChange.toFixed(2)})`;
    if (pctChange >= 0) {
        changeCard.className = "digital-card-subvalue val-green";
    } else {
        changeCard.className = "digital-card-subvalue val-red";
    }
    
    // Forecast returns target details
    const fcData = cachedPayload.forecasts["Ensemble"];
    const targetVal = getLastValidYhat(fcData, lastClose);
    const returnPct = ((targetVal - lastClose) / lastClose) * 100.0;
    
    document.getElementById("card-forecast-target").textContent = `$${targetVal.toFixed(2)}`;
    const returnCard = document.getElementById("card-expected-return");
    returnCard.textContent = `${returnPct >= 0 ? "+" : ""}${returnPct.toFixed(2)}% expected return`;
    returnCard.className = returnPct >= 0 ? "digital-card-subvalue val-green" : "digital-card-subvalue val-red";
    
    // Risk index score
    const risk = cachedPayload.risk_metrics;
    const scoreVal = (risk && risk.risk_score !== null) ? Math.round(risk.risk_score) : 0;
    document.getElementById("card-risk-score").textContent = `${scoreVal}%`;
    document.getElementById("card-risk-progress").style.width = `${scoreVal}%`;
    document.getElementById("card-risk-label").textContent = risk.risk_category || "Low";
    
    // Dynamic recommendation badges
    const recBadge = document.getElementById("recommendation-badge");
    let rec = "HOLD";
    
    if (returnPct > 5 && scoreVal < 50) {
        rec = "BUY";
        recBadge.className = "recommendation-badge badge-buy";
    } else if (returnPct < -2) {
        rec = "SELL";
        recBadge.className = "recommendation-badge badge-sell";
    } else {
        recBadge.className = "recommendation-badge badge-hold";
    }
    recBadge.textContent = `RECOMMENDATION: ${rec}`;
    
    // Technical trend indicator
    const trendCard = document.getElementById("card-trend-align");
    const trendReason = document.getElementById("card-trend-reason");
    
    if (rec === "BUY") {
        trendCard.textContent = "BUY Alignment";
        trendCard.className = "digital-card-value val-green";
        trendReason.textContent = "Indicators signal strong bullish trend development with low volatility.";
    } else if (rec === "SELL") {
        trendCard.textContent = "SELL Alignment";
        trendCard.className = "digital-card-value val-red";
        trendReason.textContent = "High volatility combined with negative expected returns suggests downward trend.";
    } else {
        trendCard.textContent = "HOLD Alignment";
        trendCard.className = "digital-card-value val-gold";
        trendReason.textContent = "Indicators reflect consolidative sideways action with flat momentum oscillators.";
    }
    
    // Data Source Badge
    const sourceBadge = document.getElementById("data-status-badge");
    if (cachedPayload.data_source === "live") {
        sourceBadge.textContent = "Live Dataset Loaded";
        sourceBadge.className = "data-badge live";
    } else {
        sourceBadge.textContent = "Demo Dataset Loaded";
        sourceBadge.className = "data-badge demo";
    }
    
    // Executive Summary outline from AI Report
    const summaryText = document.getElementById("dashboard-outlook-text");
    if (cachedPayload.ai_report_markdown) {
        const sections = cachedPayload.ai_report_markdown.split("\n\n");
        // Pull the first paragraph or two as summary
        const executiveSummary = sections.find(s => s.trim().startsWith("## Executive Summary") || s.includes("Executive Summary")) || sections[1] || "Summary report loaded successfully.";
        summaryText.innerHTML = marked.parse(executiveSummary);
    } else {
        summaryText.innerHTML = "Analysis generation complete. Ready to review detailed sections.";
    }
}

function updateForecastDetails() {
    const hist = cachedPayload.historical;
    const lastClose = hist[hist.length - 1].Close;
    const fcData = cachedPayload.forecasts[forecastModel];
    const targetVal = getLastValidYhat(fcData, lastClose);
    const returnPct = ((targetVal - lastClose) / lastClose) * 100.0;
    
    document.getElementById("forecast-target-val").textContent = `$${targetVal.toFixed(2)}`;
    const returnValCard = document.getElementById("forecast-return-val");
    returnValCard.textContent = `${returnPct >= 0 ? "+" : ""}${returnPct.toFixed(2)}%`;
    returnValCard.className = returnPct >= 0 ? "banner-stat-value val-green" : "banner-stat-value val-red";
}

function updateRiskDetails() {
    const risk = cachedPayload.risk_metrics;
    
    // Annual Volatility
    const volVal = (risk && risk.volatility !== null && risk.volatility !== undefined) ? (risk.volatility * 100.0).toFixed(2) : "0.00";
    document.getElementById("risk-card-vol").textContent = `${volVal}%`;
    
    // Value at Risk (95%)
    const varVal = (risk && risk.var_95 !== null && risk.var_95 !== undefined) ? `-${(risk.var_95 * 100.0).toFixed(2)}%` : "0.00%";
    document.getElementById("risk-card-var").textContent = varVal;
    
    // Sharpe Ratio
    const sharpeVal = (risk && risk.sharpe_ratio !== null && risk.sharpe_ratio !== undefined) ? risk.sharpe_ratio.toFixed(2) : "0.00";
    document.getElementById("risk-card-sharpe").textContent = sharpeVal;
    
    // Max Drawdown
    const maxddVal = (risk && risk.max_drawdown !== null && risk.max_drawdown !== undefined) ? (risk.max_drawdown * 100.0).toFixed(2) : "0.00";
    document.getElementById("risk-card-maxdd").textContent = `${maxddVal}%`;
    
    // S&P 500 Beta (Calculated approximation: volatility relative to benchmark 18%)
    let betaApprox = 1.0;
    if (risk && risk.volatility !== null && risk.volatility !== undefined) {
        betaApprox = Math.min(2.0, Math.max(0.5, risk.volatility / 0.18));
    }
    document.getElementById("risk-card-beta").textContent = betaApprox.toFixed(2);
    
    // Risk Gauge and Narrative
    const scoreVal = (risk && risk.risk_score !== null) ? Math.round(risk.risk_score) : 0;
    document.getElementById("risk-gauge-score").textContent = `${scoreVal}%`;
    document.getElementById("risk-gauge-bar").style.width = `${scoreVal}%`;
    
    const categoryCard = document.getElementById("risk-gauge-category");
    const riskCat = (risk && risk.risk_category) ? risk.risk_category : "Low";
    categoryCard.textContent = riskCat;
    if (riskCat === "Low") {
        categoryCard.style.color = "var(--market-emerald)";
    } else if (riskCat === "Medium") {
        categoryCard.style.color = "var(--market-indigo)";
    } else {
        categoryCard.style.color = "var(--market-rose)";
    }
    
    // Narrative text builder
    const volPctText = (risk && risk.volatility !== null && risk.volatility !== undefined) ? (risk.volatility * 100.0).toFixed(1) : "0.0";
    const varPctText = (risk && risk.var_95 !== null && risk.var_95 !== undefined) ? (risk.var_95 * 100.0).toFixed(1) : "0.0";
    const maxddPctText = (risk && risk.max_drawdown !== null && risk.max_drawdown !== undefined) ? (risk.max_drawdown * 100.0).toFixed(1) : "0.0";
    const sharpeValText = (risk && risk.sharpe_ratio !== null && risk.sharpe_ratio !== undefined) ? risk.sharpe_ratio.toFixed(2) : "0.00";
    
    const narrativeText = document.getElementById("risk-narrative-text");
    narrativeText.innerHTML = `
        <p>A systematic audit of the historical returns indicates a <strong>${riskCat} Risk</strong> profile (score of ${scoreVal}/100) for this asset.</p>
        <p>The annual price volatility stands at ${volPctText}%. Under ordinary market conditions, the Value at Risk suggests that a single-day loss will exceed ${varPctText}% with only a 5% probability.</p>
        <p>The maximum peak-to-trough drawdown over the historical lookback period was ${maxddPctText}%. Combined with a Sharpe Ratio of ${sharpeValText}, the risk-adjusted return efficiency is considered ${risk && risk.sharpe_ratio > 1.0 ? 'strong' : (risk && risk.sharpe_ratio > 0.5 ? 'satisfactory' : 'moderate')}.</p>
    `;
}

function updateReportDetails() {
    const markdown = cachedPayload.ai_report_markdown || "# Narrative Report Unavailable\nPlease check internet connection.";
    document.getElementById("report-markdown-content").innerHTML = marked.parse(markdown);
}

function updateSettingsDetails() {
    const sourceStatus = document.getElementById("settings-source-status");
    if (cachedPayload.data_source === "live") {
        sourceStatus.textContent = "Live Yahoo Finance API Connection";
        sourceStatus.className = "status-value val-green";
    } else {
        sourceStatus.textContent = "Offline Demo Mode";
        sourceStatus.className = "status-value val-indigo";
    }
    
    // Sync diagnostics checklist yfinance status
    const yfCheck = document.getElementById("settings-check-yfinance");
    if (cachedPayload.data_source === "live") {
        yfCheck.textContent = "✔ yfinance API Status: ONLINE";
        yfCheck.className = "check-item val-green";
    } else {
        yfCheck.textContent = "✔ yfinance API Status: OFFLINE (Demo Fallback)";
        yfCheck.className = "check-item val-indigo";
    }
}

// ==========================================================================
// REPORT DOWNLOAD TRIGGER HANDLER
// ==========================================================================
async function downloadReport(format) {
    if (!cachedPayload) return;
    
    const url = format === "pdf" ? "/api/download_pdf" : "/api/download_csv";
    
    try {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(cachedPayload)
        });
        
        if (!response.ok) throw new Error("Export download failed.");
        
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = format === "pdf" ? `MarketMind_${cachedPayload.symbol}_Report.pdf` : `MarketMind_${cachedPayload.symbol}_Data.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(downloadUrl);
        
    } catch (err) {
        alert("Export download failed: " + err.message);
    }
}

// ==========================================================================
// PLOTLY CHART RENDER PIPELINE
// ==========================================================================
function renderAllCharts() {
    if (activePage === "forecast") {
        renderForecastChart();
    } else if (activePage === "technical") {
        renderTechnicalCharts();
    }
}

function renderForecastChart() {
    const isLight = activeTheme === "light";
    const colors = getThemeChartColors();
    const hist = cachedPayload.historical;
    const fc = cachedPayload.forecasts[forecastModel];
    
    // Limit historical timeline to last 90 business days to ensure details are clearly visible
    const sliceCount = Math.min(hist.length, 90);
    const histSlice = hist.slice(hist.length - sliceCount);
    
    const datesHist = histSlice.map(d => d.Date);
    const closeHist = histSlice.map(d => d.Close);
    
    const datesFc = fc.map(d => d.Date);
    const yhatFc = fc.map(d => d.yhat);
    const yhatLower = fc.map(d => d.yhat_lower);
    const yhatUpper = fc.map(d => d.yhat_upper);
    
    // Trace 1: Historical Prices
    const traceHist = {
        x: datesHist,
        y: closeHist,
        mode: 'lines',
        name: 'Historical Close',
        line: { color: '#6366f1', width: 2.5 }
    };
    
    // Trace 2: Predicted Price Curve
    const traceFc = {
        x: datesFc,
        y: yhatFc,
        mode: 'lines',
        name: `${forecastModel} Target`,
        line: { color: '#06b6d4', width: 2.5, dash: 'dash' }
    };
    
    // Trace 3: Shaded Confidence interval bounds
    const traceUpper = {
        x: datesFc,
        y: yhatUpper,
        mode: 'lines',
        line: { width: 0 },
        showlegend: false,
        hoverinfo: 'none'
    };
    
    const traceLower = {
        x: datesFc,
        y: yhatLower,
        mode: 'lines',
        fill: 'tonexty',
        fillcolor: isLight ? 'rgba(6, 182, 212, 0.08)' : 'rgba(6, 182, 212, 0.15)',
        line: { width: 0 },
        name: 'Confidence Boundary',
        hoverinfo: 'none'
    };
    
    const layout = {
        paper_bgcolor: colors.paperBg,
        plot_bgcolor: colors.plotBg,
        font: { family: 'Inter, sans-serif', color: colors.textColor, size: 11 },
        margin: { t: 30, b: 40, l: 50, r: 20 },
        legend: { orientation: 'h', x: 0.1, y: 1.1 },
        hovermode: 'x unified',
        xaxis: {
            gridcolor: colors.gridColor,
            zerolinecolor: colors.zeroLineColor,
            tickfont: { color: colors.textColor },
            rangeslider: { visible: false }
        },
        yaxis: {
            gridcolor: colors.gridColor,
            zerolinecolor: colors.zeroLineColor,
            tickfont: { color: colors.textColor },
            tickformat: '$d'
        }
    };
    
    Plotly.newPlot('forecast-chart', [traceHist, traceFc, traceUpper, traceLower], layout, { responsive: true, displayModeBar: false });
}

function renderTechnicalCharts() {
    const colors = getThemeChartColors();
    const hist = cachedPayload.historical;
    
    // Limit view window
    const sliceCount = Math.min(hist.length, 120);
    const histSlice = hist.slice(hist.length - sliceCount);
    
    const dates = histSlice.map(d => d.Date);
    const close = histSlice.map(d => d.Close);
    
    // 1. Chart: Price & SMA/BB
    const traceClose = { x: dates, y: close, name: 'Close', line: { color: '#6366f1', width: 2 } };
    const traceSma20 = { x: dates, y: histSlice.map(d => d.SMA_20), name: 'SMA 20', line: { color: '#f59e0b', width: 1.5 } };
    const traceSma50 = { x: dates, y: histSlice.map(d => d.SMA_50), name: 'SMA 50', line: { color: '#10b981', width: 1.5 } };
    
    const traceBBUpper = { x: dates, y: histSlice.map(d => d.BB_Upper), name: 'BB Upper', line: { color: 'rgba(255,255,255,0.15)', width: 1, dash: 'dot' } };
    const traceBBLower = { x: dates, y: histSlice.map(d => d.BB_Lower), name: 'BB Lower', line: { color: 'rgba(255,255,255,0.15)', width: 1, dash: 'dot' } };
    
    if (activeTheme === "light") {
        traceBBUpper.line.color = 'rgba(15,23,42,0.15)';
        traceBBLower.line.color = 'rgba(15,23,42,0.15)';
    }
    
    Plotly.newPlot('chart-price-sma', [traceClose, traceSma20, traceSma50, traceBBUpper, traceBBLower], {
        title: { text: 'Price, SMAs & Bollinger Bands', font: { family: 'Outfit, sans-serif', size: 14 } },
        paper_bgcolor: colors.paperBg, plot_bgcolor: colors.plotBg,
        font: { family: 'Inter', color: colors.textColor, size: 10 },
        margin: { t: 40, b: 30, l: 40, r: 10 },
        showlegend: false, hovermode: 'x unified',
        xaxis: { gridcolor: colors.gridColor, zerolinecolor: colors.zeroLineColor },
        yaxis: { gridcolor: colors.gridColor, zerolinecolor: colors.zeroLineColor, tickformat: '$d' }
    }, { responsive: true, displayModeBar: false });
    
    // 2. Chart: Volume bars
    const traceVol = {
        x: dates, y: histSlice.map(d => d.Volume), type: 'bar', name: 'Volume',
        marker: { color: histSlice.map((d, i) => {
            if (i === 0) return '#10b981';
            return d.Close >= histSlice[i-1].Close ? '#10b981' : '#f43f5e';
        }) }
    };
    
    Plotly.newPlot('chart-volume', [traceVol], {
        title: { text: 'Volume Transacted', font: { family: 'Outfit, sans-serif', size: 14 } },
        paper_bgcolor: colors.paperBg, plot_bgcolor: colors.plotBg,
        font: { family: 'Inter', color: colors.textColor, size: 10 },
        margin: { t: 40, b: 30, l: 40, r: 10 },
        showlegend: false, hovermode: 'x unified',
        xaxis: { gridcolor: colors.gridColor, zerolinecolor: colors.zeroLineColor },
        yaxis: { gridcolor: colors.gridColor, zerolinecolor: colors.zeroLineColor }
    }, { responsive: true, displayModeBar: false });
    
    // 3. Chart: RSI
    const rsiVals = histSlice.map(d => d.RSI);
    const traceRSI = { x: dates, y: rsiVals, name: 'RSI', line: { color: '#a855f7', width: 2 } };
    
    Plotly.newPlot('chart-rsi', [traceRSI], {
        title: { text: 'Relative Strength Index (RSI)', font: { family: 'Outfit, sans-serif', size: 14 } },
        paper_bgcolor: colors.paperBg, plot_bgcolor: colors.plotBg,
        font: { family: 'Inter', color: colors.textColor, size: 10 },
        margin: { t: 40, b: 30, l: 40, r: 10 },
        showlegend: false, hovermode: 'x unified',
        xaxis: { gridcolor: colors.gridColor, zerolinecolor: colors.zeroLineColor },
        yaxis: { gridcolor: colors.gridColor, zerolinecolor: colors.zeroLineColor, range: [10, 90] },
        shapes: [
            { type: 'line', y0: 30, y1: 30, x0: dates[0], x1: dates[dates.length-1], line: { color: '#f43f5e', width: 1, dash: 'dash' } },
            { type: 'line', y0: 70, y1: 70, x0: dates[0], x1: dates[dates.length-1], line: { color: '#f43f5e', width: 1, dash: 'dash' } }
        ]
    }, { responsive: true, displayModeBar: false });
    
    // 4. Chart: MACD
    const macdLine = histSlice.map(d => d.MACD);
    const signalLine = histSlice.map(d => d.MACD_Signal);
    const histLines = macdLine.map((m, i) => m - signalLine[i]);
    
    const traceMACD = { x: dates, y: macdLine, name: 'MACD', line: { color: '#3b82f6', width: 1.5 } };
    const traceSignal = { x: dates, y: signalLine, name: 'Signal', line: { color: '#ef4444', width: 1.5 } };
    const traceHistLine = {
        x: dates, y: histLines, type: 'bar', name: 'Histogram',
        marker: { color: histLines.map(h => h >= 0 ? 'rgba(16, 185, 129, 0.4)' : 'rgba(244, 63, 94, 0.4)') }
    };
    
    Plotly.newPlot('chart-macd', [traceMACD, traceSignal, traceHistLine], {
        title: { text: 'MACD Oscillator', font: { family: 'Outfit, sans-serif', size: 14 } },
        paper_bgcolor: colors.paperBg, plot_bgcolor: colors.plotBg,
        font: { family: 'Inter', color: colors.textColor, size: 10 },
        margin: { t: 40, b: 30, l: 40, r: 10 },
        showlegend: false, hovermode: 'x unified',
        xaxis: { gridcolor: colors.gridColor, zerolinecolor: colors.zeroLineColor },
        yaxis: { gridcolor: colors.gridColor, zerolinecolor: colors.zeroLineColor }
    }, { responsive: true, displayModeBar: false });
}
