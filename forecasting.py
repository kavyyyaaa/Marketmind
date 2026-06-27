import pandas as pd
import numpy as np
from prophet import Prophet
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from trend_analysis import analyze_all_trends

def forecast_with_prophet(df: pd.DataFrame, horizon_days: int) -> pd.DataFrame:
    """
    Fits a Prophet model and forecasts 'horizon_days' into the future.
    Returns a DataFrame containing historical and forecasted dates with 'yhat', 'yhat_lower', 'yhat_upper'.
    """
    # Prophet expects 'ds' (datestamp) and 'y' (target)
    prophet_df = pd.DataFrame()
    prophet_df['ds'] = pd.to_datetime(df.index).tz_localize(None)
    prophet_df['y'] = df['Close'].values
    
    # Instantiate and fit model with daily seasonality disabled if dataset is short, but standard settings are fine
    m = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=len(df) > 365,
        interval_width=0.95 # 95% confidence interval
    )
    m.fit(prophet_df)
    
    # Create future dates (include weekends for simplicity, yfinance can handle gaps or we can project daily)
    future = m.make_future_dataframe(periods=horizon_days, freq='D')
    forecast = m.predict(future)
    
    # Filter/Select output columns
    result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
    result.rename(columns={'ds': 'Date'}, inplace=True)
    result.set_index('Date', inplace=True)
    
    return result

def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes indicators and lag features, and shifts all features by 1 day
    to prevent circular dependency and NaN inputs during recursive forecasting.
    """
    df_analyzed = analyze_all_trends(df)
    df_feat = pd.DataFrame(index=df.index)
    
    # Lags of the Close price
    df_feat['Lag_1'] = df['Close'].shift(1)
    df_feat['Lag_2'] = df['Close'].shift(2)
    df_feat['Lag_3'] = df['Close'].shift(3)
    df_feat['Lag_5'] = df['Close'].shift(5)
    df_feat['Lag_10'] = df['Close'].shift(10)
    
    # Rolling averages and standard deviations (shifted by 1)
    for window in [5, 10, 20]:
        df_feat[f'Roll_Mean_{window}'] = df['Close'].shift(1).rolling(window=window).mean()
        df_feat[f'Roll_Std_{window}'] = df['Close'].shift(1).rolling(window=window).std()
        
    # Technical indicators (shifted by 1)
    df_feat['RSI'] = df_analyzed['RSI'].shift(1)
    df_feat['MACD'] = df_analyzed['MACD'].shift(1)
    df_feat['MACD_Signal'] = df_analyzed['MACD_Signal'].shift(1)
    df_feat['MACD_Hist'] = df_analyzed['MACD_Hist'].shift(1)
    df_feat['BB_Middle'] = df_analyzed['BB_Middle'].shift(1)
    df_feat['BB_Upper'] = df_analyzed['BB_Upper'].shift(1)
    df_feat['BB_Lower'] = df_analyzed['BB_Lower'].shift(1)
    
    # Target close price
    df_feat['Close'] = df['Close']
    
    return df_feat

def forecast_with_xgboost(df: pd.DataFrame, horizon_days: int) -> tuple:
    """
    Fits an XGBoost Regressor on technical indicators and lags,
    and runs recursive multi-step forecasting for 'horizon_days'.
    Returns a tuple (xgb_forecast, importance_dict).
    """
    # 1. Generate features
    df_features = prepare_features(df)
    
    # Columns to use as features
    feature_cols = [
        'Lag_1', 'Lag_2', 'Lag_3', 'Lag_5', 'Lag_10',
        'Roll_Mean_5', 'Roll_Mean_10', 'Roll_Mean_20',
        'Roll_Std_5', 'Roll_Std_10', 'Roll_Std_20',
        'RSI', 'MACD', 'MACD_Signal', 'MACD_Hist',
        'BB_Middle', 'BB_Upper', 'BB_Lower'
    ]
    
    # Split into train sets (rows without NaNs)
    df_train = df_features.dropna(subset=feature_cols + ['Close'])
    
    X_train = df_train[feature_cols]
    y_train = df_train['Close']
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    # Fit XGBoost Regressor
    model = xgb.XGBRegressor(
        n_estimators=100,
        learning_rate=0.05,
        max_depth=5,
        random_state=42
    )
    model.fit(X_train_scaled, y_train)
    
    # Get feature importances
    importances = model.feature_importances_
    importance_dict = dict(zip(feature_cols, [float(val) for val in importances]))
    
    # 2. Recursive Multi-Step Forecasting
    hist_index = df.index
    last_date = hist_index[-1]
    
    # Create future dates
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=horizon_days, freq='D')
    
    # Initialize working DataFrame
    working_df = df.copy()
    
    # Fill in predictions step-by-step
    for date in future_dates:
        working_df.loc[date] = np.nan
        temp_features = prepare_features(working_df)
        x_pred = temp_features.loc[[date], feature_cols]
        x_pred_scaled = scaler.transform(x_pred)
        pred_close = float(model.predict(x_pred_scaled)[0])
        working_df.loc[date, 'Close'] = pred_close
        
    # Extract only the forecast rows
    xgb_forecast = pd.DataFrame(index=future_dates)
    xgb_forecast['yhat'] = working_df.loc[future_dates, 'Close'].values
    
    # Generate simple upper/lower bounds based on historical residuals
    residuals = y_train - model.predict(X_train_scaled)
    std_residual = residuals.std()
    
    xgb_forecast['yhat_lower'] = xgb_forecast['yhat'] - (1.96 * std_residual)
    xgb_forecast['yhat_upper'] = xgb_forecast['yhat'] + (1.96 * std_residual)
    
    return xgb_forecast, importance_dict

def forecast_with_mlp(df: pd.DataFrame, horizon_days: int) -> pd.DataFrame:
    """
    Fits a Scikit-Learn MLP Neural Network Regressor on technical indicators and lags,
    and runs recursive multi-step forecasting for 'horizon_days'.
    Returns a DataFrame of the forecast values.
    """
    # 1. Generate features
    df_features = prepare_features(df)
    
    # Columns to use as features
    feature_cols = [
        'Lag_1', 'Lag_2', 'Lag_3', 'Lag_5', 'Lag_10',
        'Roll_Mean_5', 'Roll_Mean_10', 'Roll_Mean_20',
        'Roll_Std_5', 'Roll_Std_10', 'Roll_Std_20',
        'RSI', 'MACD', 'MACD_Signal', 'MACD_Hist',
        'BB_Middle', 'BB_Upper', 'BB_Lower'
    ]
    
    # Split into train sets (rows without NaNs)
    df_train = df_features.dropna(subset=feature_cols + ['Close'])
    
    X_train = df_train[feature_cols]
    y_train = df_train['Close']
    
    # Scale features (MLPs are sensitive to feature scaling!)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    # Fit MLP Regressor (Neural Network) with L2 regularization
    model = MLPRegressor(
        hidden_layer_sizes=(32, 16),
        activation='relu',
        solver='adam',
        max_iter=500,
        alpha=1.0,
        random_state=42
    )
    model.fit(X_train_scaled, y_train)
    
    # 2. Recursive Multi-Step Forecasting
    hist_index = df.index
    last_date = hist_index[-1]
    
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=horizon_days, freq='D')
    working_df = df.copy()
    
    for date in future_dates:
        working_df.loc[date] = np.nan
        temp_features = prepare_features(working_df)
        x_pred = temp_features.loc[[date], feature_cols]
        x_pred_scaled = scaler.transform(x_pred)
        pred_close = float(model.predict(x_pred_scaled)[0])
        
        # Apply economic constraint: clip daily change to +/- 2.5% of previous day to avoid model explosion
        prev_idx = working_df.index.get_loc(date) - 1
        prev_close = float(working_df['Close'].iloc[prev_idx])
        pred_close = np.clip(pred_close, prev_close * 0.975, prev_close * 1.025)
        
        working_df.loc[date, 'Close'] = pred_close
        
    mlp_forecast = pd.DataFrame(index=future_dates)
    mlp_forecast['yhat'] = working_df.loc[future_dates, 'Close'].values
    
    # Generate simple upper/lower bounds based on historical residuals
    residuals = y_train - model.predict(X_train_scaled)
    std_residual = residuals.std()
    
    mlp_forecast['yhat_lower'] = mlp_forecast['yhat'] - (1.96 * std_residual)
    mlp_forecast['yhat_upper'] = mlp_forecast['yhat'] + (1.96 * std_residual)
    
    return mlp_forecast
