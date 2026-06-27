import pandas as pd
import numpy as np

def compute_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """Computes Simple and Exponential Moving Averages."""
    df = df.copy()
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    return df

def compute_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Computes the Relative Strength Index (RSI)."""
    df = df.copy()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    # Avoid division by zero
    rs = gain / np.where(loss == 0, 1e-9, loss)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Fill leading NaNs with a neutral 50
    df['RSI'] = df['RSI'].fillna(50)
    return df

def compute_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """Computes MACD, Signal line, and Histogram."""
    df = df.copy()
    ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()
    df['MACD'] = ema_fast - ema_slow
    df['MACD_Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    return df

def compute_bollinger_bands(df: pd.DataFrame, period: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """Computes Bollinger Bands (Middle, Upper, Lower bands)."""
    df = df.copy()
    df['BB_Middle'] = df['Close'].rolling(window=period).mean()
    std = df['Close'].rolling(window=period).std()
    df['BB_Upper'] = df['BB_Middle'] + (num_std * std)
    df['BB_Lower'] = df['BB_Middle'] - (num_std * std)
    return df

def analyze_all_trends(df: pd.DataFrame) -> pd.DataFrame:
    """Runs all trend analysis functions sequentially."""
    df = compute_moving_averages(df)
    df = compute_rsi(df)
    df = compute_macd(df)
    df = compute_bollinger_bands(df)
    return df
