# Extended Technical Indicators Reference (技术指标扩展)

## Overview

Comprehensive technical analysis framework combining trend, momentum, volume, and volatility indicators.

---

## 📈 Trend Indicators

### 1. Moving Averages (移动平均线)

#### Simple Moving Average (SMA)
**Formula:**
```
SMA(n) = (P1 + P2 + ... + Pn) / n

Where:
P = Price (close, high, low, or typical)
n = Period (e.g., 20, 50, 200)
```

#### Exponential Moving Average (EMA)
**Formula:**
```
EMA_today = (Price_today × k) + (EMA_yesterday × (1 - k))

Where:
k = 2 / (n + 1)  # Smoothing factor
```

**Calculation:**
```python
def calculate_moving_averages(prices, periods=[20, 50, 200], ma_type='sma'):
    """
    Calculate moving averages
    
    Args:
        prices: List of closing prices
        periods: List of period lengths
        ma_type: 'sma' or 'ema'
    
    Returns:
        ma_dict: Dictionary of moving averages by period
    """
    import numpy as np
    
    ma_dict = {}
    
    for period in periods:
        if len(prices) < period:
            continue
        
        if ma_type == 'sma':
            # Simple Moving Average
            ma = []
            for i in range(len(prices)):
                if i < period - 1:
                    ma.append(None)
                else:
                    ma.append(np.mean(prices[i-period+1:i+1]))
        
        elif ma_type == 'ema':
            # Exponential Moving Average
            ma = []
            k = 2 / (period + 1)
            
            # First EMA is SMA
            first_sma = np.mean(prices[:period])
            ma.extend([None] * (period - 1))
            ma.append(first_sma)
            
            # Calculate subsequent EMAs
            for i in range(period, len(prices)):
                ema = prices[i] * k + ma[i-1] * (1 - k)
                ma.append(ema)
        
        ma_dict[period] = ma
    
    return ma_dict
```

**Trading Signals:**
- **Golden Cross:** 50-day EMA crosses above 200-day EMA (bullish)
- **Death Cross:** 50-day EMA crosses below 200-day EMA (bearish)
- **Price above MA:** Uptrend support
- **Price below MA:** Downtrend resistance

---

### 2. MACD (Moving Average Convergence Divergence)

**Formula:**
```
MACD = 12-day EMA - 26-day EMA
Signal Line = 9-day EMA of MACD
MACD Histogram = MACD - Signal Line
```

**Calculation:**
```python
def calculate_macd(prices, fast=12, slow=26, signal=9):
    """
    Calculate MACD indicator
    
    Args:
        prices: List of closing prices
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period
    
    Returns:
        macd_dict: Dictionary with MACD components
    """
    import numpy as np
    
    # Calculate EMAs
    ema_fast = calculate_moving_averages(prices, [fast], 'ema')[fast]
    ema_slow = calculate_moving_averages(prices, [slow], 'ema')[slow]
    
    # Calculate MACD line
    macd_line = []
    for i in range(len(prices)):
        if ema_fast[i] is None or ema_slow[i] is None:
            macd_line.append(None)
        else:
            macd_line.append(ema_fast[i] - ema_slow[i])
    
    # Calculate Signal line (EMA of MACD)
    signal_line = calculate_moving_averages(
        [x for x in macd_line if x is not None], 
        [signal], 
        'ema'
    )[signal]
    
    # Pad with None for alignment
    signal_line_padded = [None] * (len(prices) - len(signal_line)) + signal_line
    
    # Calculate Histogram
    histogram = []
    for i in range(len(prices)):
        if macd_line[i] is None or signal_line_padded[i] is None:
            histogram.append(None)
        else:
            histogram.append(macd_line[i] - signal_line_padded[i])
    
    return {
        'macd_line': macd_line,
        'signal_line': signal_line_padded,
        'histogram': histogram
    }
```

**Trading Signals:**
- **Bullish:** MACD crosses above signal line
- **Bearish:** MACD crosses below signal line
- **Divergence:** Price makes new high but MACD doesn't (potential reversal)

---

### 3. ADX (Average Directional Index)

**Formula:**
```
ADX = 14-day smoothed moving average of DX
DX = 100 × |(+DI - -DI)| / |(+DI + -DI)|
+DI = Positive Directional Indicator
-DI = Negative Directional Indicator
```

**Interpretation:**
| ADX Value | Trend Strength | Action |
|-----------|----------------|--------|
| 0-25 | Weak or No Trend | Avoid trend-following strategies |
| 25-50 | Strong Trend | Favorable for trend-following |
| 50-75 | Very Strong Trend | Excellent trend conditions |
| 75-100 | Extremely Strong Trend | Rare, potential reversal |

**Calculation:**
```python
def calculate_adx(highs, lows, closes, period=14):
    """
    Calculate ADX indicator
    
    Args:
        highs: List of high prices
        lows: List of low prices
        closes: List of closing prices
        period: ADX period (default 14)
    
    Returns:
        adx_data: Dictionary with ADX components
    """
    import numpy as np
    
    n = len(highs)
    if n < period * 2:
        return None
    
    # Calculate True Range
    tr = []
    for i in range(1, n):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i-1])
        lc = abs(lows[i] - closes[i-1])
        tr.append(max(hl, hc, lc))
    
    # Calculate Directional Movement
    plus_dm = []
    minus_dm = []
    
    for i in range(1, n):
        up_move = highs[i] - highs[i-1]
        down_move = lows[i-1] - lows[i]
        
        if up_move > down_move and up_move > 0:
            plus_dm.append(up_move)
            minus_dm.append(0)
        elif down_move > up_move and down_move > 0:
            plus_dm.append(0)
            minus_dm.append(down_move)
        else:
            plus_dm.append(0)
            minus_dm.append(0)
    
    # Calculate smoothed values
    tr_smooth = []
    plus_dm_smooth = []
    minus_dm_smooth = []
    
    # Initial smoothing (simple average)
    tr_smooth.append(sum(tr[:period]) / period)
    plus_dm_smooth.append(sum(plus_dm[:period]) / period)
    minus_dm_smooth.append(sum(minus_dm[:period]) / period)
    
    # Wilder's smoothing
    for i in range(period, len(tr)):
        tr_smooth.append(tr_smooth[-1] - (tr_smooth[-1] / period) + tr[i])
        plus_dm_smooth.append(plus_dm_smooth[-1] - (plus_dm_smooth[-1] / period) + plus_dm[i])
        minus_dm_smooth.append(minus_dm_smooth[-1] - (minus_dm_smooth[-1] / period) + minus_dm[i])
    
    # Calculate +DI and -DI
    plus_di = []
    minus_di = []
    
    for i in range(len(tr_smooth)):
        if tr_smooth[i] != 0:
            plus_di.append(100 * plus_dm_smooth[i] / tr_smooth[i])
            minus_di.append(100 * minus_dm_smooth[i] / tr_smooth[i])
        else:
            plus_di.append(0)
            minus_di.append(0)
    
    # Calculate DX
    dx = []
    for i in range(len(plus_di)):
        if plus_di[i] + minus_di[i] != 0:
            dx.append(100 * abs(plus_di[i] - minus_di[i]) / (plus_di[i] + minus_di[i]))
        else:
            dx.append(0)
    
    # Calculate ADX (smoothed DX)
    adx = []
    adx.append(sum(dx[:period]) / period)
    
    for i in range(period, len(dx)):
        adx.append((adx[-1] * (period - 1) + dx[i]) / period)
    
    # Pad with None for alignment
    adx_padded = [None] * (n - len(adx)) + adx
    plus_di_padded = [None] * (n - len(plus_di)) + plus_di
    minus_di_padded = [None] * (n - len(minus_di)) + minus_di
    
    return {
        'adx': adx_padded,
        'plus_di': plus_di_padded,
        'minus_di': minus_di_padded,
        'trend_strength': interpret_adx(adx_padded[-1] if adx_padded[-1] else 0)
    }

def interpret_adx(adx_value):
    """Interpret ADX value"""
    if adx_value < 20:
        return 'NO_TREND'
    elif adx_value < 25:
        return 'WEAK_TREND'
    elif adx_value < 50:
        return 'STRONG_TREND'
    elif adx_value < 75:
        return 'VERY_STRONG_TREND'
    else:
        return 'EXTREME_TREND'
```

---

## 📊 Momentum Indicators

### 1. RSI (Relative Strength Index)

**Formula:**
```
RSI = 100 - (100 / (1 + RS))
RS = Average Gain / Average Loss over n periods
```

**Calculation:**
```python
def calculate_rsi(prices, period=14):
    """
    Calculate RSI indicator
    
    Args:
        prices: List of closing prices
        period: RSI period (default 14)
    
    Returns:
        rsi: List of RSI values
    """
    import numpy as np
    
    if len(prices) < period + 1:
        return None
    
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    
    rs = up / down if down != 0 else 0
    rsi = np.zeros_like(prices)
    rsi[:period] = 100.0 - 100.0 / (1.0 + rs)
    
    for i in range(period, len(prices)):
        delta = deltas[i-1]
        
        if delta > 0:
            up_val = delta
            down_val = 0.0
        else:
            up_val = 0.0
            down_val = -delta
        
        up = (up * (period - 1) + up_val) / period
        down = (down * (period - 1) + down_val) / period
        
        rs = up / down if down != 0 else 0
        rsi[i] = 100.0 - 100.0 / (1.0 + rs)
    
    return rsi.tolist()
```

**Interpretation:**
| RSI Level | Signal | Action |
|-----------|--------|--------|
| > 70 | Overbought | Consider selling/taking profits |
| 50 - 70 | Bullish | Uptrend, look for buying opportunities |
| 30 - 50 | Bearish | Downtrend, look for selling opportunities |
| < 30 | Oversold | Consider buying/bottom fishing |

**Divergence Analysis:**
- **Bullish Divergence:** Price makes lower low, RSI makes higher low
- **Bearish Divergence:** Price makes higher high, RSI makes lower high

---

### 2. Stochastic Oscillator

**Formula:**
```
%K = 100 × (Current Close - Lowest Low) / (Highest High - Lowest Low)
%D = 3-day SMA of %K

Period: Typically 14 days for %K, 3 days for %D
```

**Calculation:**
```python
def calculate_stochastic(highs, lows, closes, k_period=14, d_period=3):
    """
    Calculate Stochastic Oscillator
    
    Args:
        highs: List of high prices
        lows: List of low prices
        closes: List of closing prices
        k_period: %K period (default 14)
        d_period: %D period (default 3)
    
    Returns:
        stochastic_dict: Dictionary with %K and %D
    """
    import numpy as np
    
    n = len(closes)
    if n < k_period:
        return None
    
    # Calculate %K
    k_values = []
    for i in range(k_period - 1, n):
        high_max = max(highs[i-k_period+1:i+1])
        low_min = min(lows[i-k_period+1:i+1])
        
        if high_max - low_min != 0:
            k = 100 * (closes[i] - low_min) / (high_max - low_min)
        else:
            k = 0
        
        k_values.append(k)
    
    # Pad with None
    k_padded = [None] * (k_period - 1) + k_values
    
    # Calculate %D (SMA of %K)
    d_values = []
    for i in range(len(k_values)):
        if i >= d_period - 1:
            d = np.mean(k_values[i-d_period+1:i+1])
            d_values.append(d)
    
    # Pad with None
    d_padded = [None] * (k_period + d_period - 2) + d_values
    
    return {
        'percent_k': k_padded,
        'percent_d': d_padded
    }
```

**Trading Signals:**
- **Buy:** %K crosses above %D from oversold (<20)
- **Sell:** %K crosses below %D from overbought (>80)
- **Bullish Divergence:** Price lower lows, Stochastic higher lows
- **Bearish Divergence:** Price higher highs, Stochastic lower highs

---

### 3. Williams %R

**Formula:**
```
Williams %R = (Highest High - Current Close) / (Highest High - Lowest Low) × -100

Period: Typically 14 days
```

**Interpretation:**
- **-20 to 0:** Overbought
- **-80 to -100:** Oversold
- **-50:** Neutral

---

## 📉 Volatility Indicators

### 1. Bollinger Bands

**Formula:**
```
Middle Band = 20-day SMA
Upper Band = Middle Band + (2 × 20-day Standard Deviation)
Lower Band = Middle Band - (2 × 20-day Standard Deviation)
```

**Calculation:**
```python
def calculate_bollinger_bands(prices, period=20, num_std=2):
    """
    Calculate Bollinger Bands
    
    Args:
        prices: List of closing prices
        period: SMA period (default 20)
        num_std: Number of standard deviations (default 2)
    
    Returns:
        bb_dict: Dictionary with Bollinger Band components
    """
    import numpy as np
    
    if len(prices) < period:
        return None
    
    sma = calculate_moving_averages(prices, [period], 'sma')[period]
    
    upper_band = []
    lower_band = []
    bandwidth = []
    percent_b = []
    
    for i in range(len(prices)):
        if i < period - 1 or sma[i] is None:
            upper_band.append(None)
            lower_band.append(None)
            bandwidth.append(None)
            percent_b.append(None)
        else:
            # Calculate standard deviation
            start_idx = i - period + 1
            std = np.std(prices[start_idx:i+1])
            
            # Calculate bands
            ub = sma[i] + (num_std * std)
            lb = sma[i] - (num_std * std)
            
            upper_band.append(ub)
            lower_band.append(lb)
            
            # Calculate bandwidth (volatility measure)
            bandwidth.append((ub - lb) / sma[i])
            
            # Calculate %B (price position within bands)
            if ub - lb != 0:
                percent_b.append((prices[i] - lb) / (ub - lb))
            else:
                percent_b.append(0)
    
    return {
        'upper_band': upper_band,
        'middle_band': sma,
        'lower_band': lower_band,
        'bandwidth': bandwidth,
        'percent_b': percent_b
    }
```

**Trading Signals:**
- **Squeeze:** Low bandwidth (volatility) often precedes big move
- **Breakout:** Price breaks above upper band with volume
- **Reversion:** Price touches upper/lower band and reverses
- **Trend Confirmation:** Price riding upper band (bullish) or lower band (bearish)

---

### 2. Average True Range (ATR)

**Formula:**
```
True Range = max(High-Low, |High-Prev Close|, |Low-Prev Close|)
ATR = 14-day smoothed moving average of True Range
```

**Calculation:**
```python
def calculate_atr(highs, lows, closes, period=14):
    """
    Calculate Average True Range
    
    Args:
        highs: List of high prices
        lows: List of low prices
        closes: List of closing prices
        period: ATR period (default 14)
    
    Returns:
        atr: List of ATR values
    """
    import numpy as np
    
    n = len(highs)
    if n < period + 1:
        return None
    
    # Calculate True Range
    tr = []
    for i in range(1, n):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i-1])
        lc = abs(lows[i] - closes[i-1])
        tr.append(max(hl, hc, lc))
    
    # Calculate ATR (Wilder's smoothing)
    atr = []
    atr.append(sum(tr[:period]) / period)
    
    for i in range(period, len(tr)):
        atr.append((atr[-1] * (period - 1) + tr[i]) / period)
    
    # Pad with None for alignment
    atr_padded = [None] * (n - len(atr)) + atr
    
    return atr_padded
```

**Applications:**
- **Stop Loss Setting:** 2× ATR below entry for long, above entry for short
- **Position Sizing:** Higher ATR = smaller position size
- **Volatility Comparison:** Compare ATR across stocks/sectors

---

## 📊 Volume Indicators

### 1. On-Balance Volume (OBV)

**Formula:**
```
If Close > Previous Close: OBV = Previous OBV + Volume
If Close < Previous Close: OBV = Previous OBV - Volume
If Close = Previous Close: OBV = Previous OBV
```

**Calculation:**
```python
def calculate_obv(closes, volumes):
    """
    Calculate On-Balance Volume
    
    Args:
        closes: List of closing prices
        volumes: List of trading volumes
    
    Returns:
        obv: List of OBV values
    """
    if len(closes) != len(volumes):
        return None
    
    obv = [volumes[0]]  # Start with first day's volume
    
    for i in range(1, len(closes)):
        if closes[i] > closes[i-1]:
            obv.append(obv[-1] + volumes[i])
        elif closes[i] < closes[i-1]:
            obv.append(obv[-1] - volumes[i])
        else:
            obv.append(obv[-1])
    
    return obv
```

**Interpretation:**
- **Price-Volume Divergence:** Price up, OBV down = weak rally (bearish)
- **Price-Volume Confirmation:** Price up, OBV up = strong rally (bullish)
- **Breakouts:** OBV leading price = genuine breakout

---

### 2. Volume Weighted Average Price (VWAP)

**Formula:**
```
VWAP = ∑(Price × Volume) / ∑(Volume)

Typically calculated for intraday data
```

**Calculation:**
```python
def calculate_vwap(intraday_data):
    """
    Calculate Volume Weighted Average Price
    
    Args:
        intraday_data: List of dicts with 'price', 'volume', 'timestamp'
    
    Returns:
        vwap: VWAP value
    """
    total_price_volume = 0
    total_volume = 0
    
    for data in intraday_data:
        price = data['price']
        volume = data['volume']
        
        total_price_volume += price * volume
        total_volume += volume
    
    if total_volume == 0:
        return None
    
    vwap = total_price_volume / total_volume
    return vwap
```

**Trading Applications:**
- **Trend Confirmation:** Price above VWAP = bullish, below = bearish
- **Support/Resistance:** VWAP often acts as dynamic support/resistance
- **Institutional Activity:** Large volume near VWAP suggests institutional interest

---

### 3. Money Flow Index (MFI)

**Formula:**
```
Typical Price = (High + Low + Close) / 3
Money Flow = Typical Price × Volume
Positive Money Flow = Sum of Money Flow on up days
Negative Money Flow = Sum of Money Flow on down days
Money Ratio = Positive Money Flow / Negative Money Flow
MFI = 100 - (100 / (1 + Money Ratio))
```

**Interpretation (similar to RSI but with volume):**
- **Overbought:** > 80
- **Oversold:** < 20
- **Bullish/Bearish Divergences:** Similar to RSI

---

## 🎯 Multi-Timeframe Analysis

### Framework for Multi-Timeframe Analysis

```python
def multi_timeframe_analysis(symbol, timeframes=['daily', 'weekly', 'monthly']):
    """
    Analyze technical indicators across multiple timeframes
    
    Args:
        symbol: Stock symbol
        timeframes: List of timeframes to analyze
    
    Returns:
        analysis: Dictionary with multi-timeframe insights
    """
    analysis = {}
    
    for tf in timeframes:
        # Get data for timeframe
        if tf == 'daily':
            period = 'day'
            days = 200
        elif tf == 'weekly':
            period = 'week'
            days = 365  # ~52 weeks
        elif tf == 'monthly':
            period = 'month'
            days = 1080  # ~36 months
        
        # Fetch data (pseudo-code)
        # kline_data = longbridge_kline(symbol, days=days, period=period)
        
        # Calculate indicators
        # analysis[tf] = calculate_all_indicators(kline_data)
        
        pass
    
    # Generate consensus
    analysis['consensus'] = generate_technical_consensus(analysis)
    
    return analysis

def generate_technical_consensus(multi_tf_analysis):
    """
    Generate consensus from multiple timeframes
    """
    consensus = {
        'trend': 'NEUTRAL',
        'momentum': 'NEUTRAL',
        'volatility': 'NORMAL',
        'volume': 'NEUTRAL',
        'signals': []
    }
    
    # Analyze each timeframe
    for tf, indicators in multi_tf_analysis.items():
        if tf == 'consensus':
            continue
        
        # Evaluate trend
        trend_score = evaluate_trend(indicators)
        
        # Evaluate momentum
        momentum_score = evaluate_momentum(indicators)
        
        # Add to consensus
        consensus['signals'].append({
            'timeframe': tf,
            'trend': trend_score,
            'momentum': momentum_score
        })
    
    return consensus
```

**Timeframe Hierarchy:**
1. **Monthly:** Primary trend (long-term investors)
2. **Weekly:** Intermediate trend (swing traders)
3. **Daily:** Short-term trend (day traders)

**Golden Rule:** Trade in direction of higher timeframe trend

---

## 📊 Technical Score System

### Comprehensive Technical Score

```python
def calculate_technical_score(indicators, current_price):
    """
    Calculate comprehensive technical score (0-100)
    
    Args:
        indicators: Dictionary of calculated indicators
        current_price: Current stock price
    
    Returns:
        score: Technical score (0-100, higher = more bullish)
        breakdown: Score breakdown by component
    """
    scores = {}
    
    # 1. Trend Score (0-100)
    trend_score = evaluate_trend_score(indicators)
    scores['trend'] = trend_score
    
    # 2. Momentum Score (0-100)
    momentum_score = evaluate_momentum_score(indicators)
    scores['momentum'] = momentum_score
    
    # 3. Volume Score (0-100)
    volume_score = evaluate_volume_score(indicators)
    scores['volume'] = volume_score
    
    # 4. Volatility Score (0-100)
    volatility_score = evaluate_volatility_score(indicators)
    scores['volatility'] = volatility_score
    
    # 5. Support/Resistance Score (0-100)
    sr_score = evaluate_support_resistance_score(indicators, current_price)
    scores['support_resistance'] = sr_score
    
    # Calculate weighted average
    weights = {
        'trend': 0.30,
        'momentum': 0.25,
        'volume': 0.20,
        'volatility': 0.15,
        'support_resistance': 0.10
    }
    
    total_score = 0
    breakdown = {}
    
    for component, weight in weights.items():
        if component in scores:
            component_score = scores[component]
            contribution = component_score * weight
            total_score += contribution
            
            breakdown[component] = {
                'score': component_score,
                'weight': weight,
                'contribution': contribution
            }
    
    return total_score, breakdown

def evaluate_trend_score(indicators):
    """Evaluate trend strength and direction"""
    score = 50  # Neutral
    
    # Check moving averages
    if 'ma_50' in indicators and 'ma_200' in indicators:
        ma_50 = indicators['ma_50'][-1]
        ma_200 = indicators['ma_200'][-1]
        
        if ma_50 and ma_200:
            if ma_50 > ma_200:
                score += 20  # Bullish (Golden Cross)
            else:
                score -= 20  # Bearish (Death Cross)
    
    # Check ADX
    if 'adx' in indicators and indicators['adx'][-1]:
        adx_value = indicators['adx'][-1]
        if adx_value > 25:
            score += 10  # Strong trend
        elif adx_value < 20:
            score -= 10  # Weak/no trend
    
    return max(0, min(100, score))

def evaluate_momentum_score(indicators):
    """Evaluate momentum indicators"""
    score = 50
    
    # Check RSI
    if 'rsi' in indicators and indicators['rsi'][-1]:
        rsi = indicators['rsi'][-1]
        if rsi > 70:
            score -= 20  # Overbought
        elif rsi < 30:
            score += 20  # Oversold
        elif rsi > 50:
            score += 10  # Bullish momentum
        else:
            score -= 10  # Bearish momentum
    
    # Check MACD
    if 'macd_line' in indicators and 'signal_line' in indicators:
        macd = indicators['macd_line'][-1]
        signal = indicators['signal_line'][-1]
        
        if macd and signal:
            if macd > signal:
                score += 15  # Bullish MACD
            else:
                score -= 15  # Bearish MACD
    
    return max(0, min(100, score))

def evaluate_volume_score(indicators):
    """Evaluate volume indicators"""
    score = 50
    
    # Check volume vs average
    if 'volume' in indicators and 'volume_avg' in indicators:
        volume = indicators['volume'][-1]
        volume_avg = indicators['volume_avg']
        
        if volume and volume_avg:
            volume_ratio = volume / volume_avg
            if volume_ratio > 1.5:
                score += 20  # High volume (breakout potential)
            elif volume_ratio < 0.5:
                score -= 10  # Low volume (lack of interest)
    
    # Check OBV trend
    if 'obv' in indicators and len(indicators['obv']) > 10:
        obv_trend = analyze_obv_trend(indicators['obv'])
        if obv_trend == 'BULLISH':
            score += 15
        elif obv_trend == 'BEARISH':
            score -= 15
    
    return max(0, min(100, score))

def evaluate_volatility_score(indicators):
    """Evaluate volatility conditions"""
    score = 50
    
    # Check Bollinger Band width
    if 'bb_bandwidth' in indicators and indicators['bb_bandwidth'][-1]:
        bandwidth = indicators['bb_bandwidth'][-1]
        
        # Historical bandwidth percentile
        if bandwidth > 0.10:  # High volatility
            score += 15  # Breakout potential
        elif bandwidth < 0.03:  # Low volatility (squeeze)
            score += 10  # Potential big move coming
    
    # Check ATR
    if 'atr' in indicators and indicators['atr'][-1]:
        atr = indicators['atr'][-1]
        atr_percent = atr / indicators['price'][-1] if indicators['price'][-1] else 0
        
        if atr_percent > 0.03:  # >3% daily ATR
            score -= 10  # High risk
        elif atr_percent < 0.01:  # <1% daily ATR
            score += 10  # Low risk
    
    return max(0, min(100, score))

def evaluate_support_resistance_score(indicators, current_price):
    """Evaluate support/resistance levels"""
    score = 50
    
    # Check Bollinger Bands position
    if 'bb_upper' in indicators and 'bb_lower' in indicators:
        upper = indicators['bb_upper'][-1]
        lower = indicators['bb_lower'][-1]
        
        if upper and lower:
            if current_price > upper:
                score -= 20  # Overbought, near resistance
            elif current_price < lower:
                score += 20  # Oversold, near support
    
    # Check moving average support/resistance
    if 'ma_20' in indicators and indicators['ma_20'][-1]:
        ma_20 = indicators['ma_20'][-1]
        ma_distance = (current_price - ma_20) / ma_20
        
        if abs(ma_distance) < 0.02:  # Within 2% of MA
            if ma_distance > 0:
                score -= 10  # Near MA resistance
            else:
                score += 10  # Near MA support
    
    return max(0, min(100, score))
```

**Interpretation:**
| Technical Score | Market Condition | Action |
|-----------------|------------------|--------|
| 80-100 | Strongly Bullish | Buy/Add to position |
| 60-80 | Bullish | Look for buying opportunities |
| 40-60 | Neutral | Hold/Wait for confirmation |
| 20-40 | Bearish | Look for selling opportunities |
| 0-20 | Strongly Bearish | Sell/Reduce position |

---

## 🎯 Integration with Existing Framework

### Enhanced Technical Analysis Workflow

1. **Data Collection:**
   ```bash
   # Get extended historical data for technical indicators
   longbridge kline history SYMBOL.US --start $(date -v-200d +%Y-%m-%d) --end $(date +%Y-%m-%d) --period day --format json
   ```

2. **Indicator Calculation:**
   ```python
   technical_indicators = {
       'trend': {
           'sma_20': calculate_moving_averages(prices, [20], 'sma')[20],
           'sma_50': calculate_moving_averages(prices, [50], 'sma')[50],
           'sma_200': calculate_moving_averages(prices, [200], 'sma')[200],
           'ema_12': calculate_moving_averages(prices, [12], 'ema')[12],
           'ema_26': calculate_moving_averages(prices, [26], 'ema')[26],
           'adx': calculate_adx(highs, lows, closes)
       },
       'momentum': {
           'rsi': calculate_rsi(prices),
           'macd': calculate_macd(prices),
           'stochastic': calculate_stochastic(highs, lows, closes)
       },
       'volatility': {
           'bollinger_bands': calculate_bollinger_bands(prices),
           'atr': calculate_atr(highs, lows, closes)
       },
       'volume': {
           'obv': calculate_obv(closes, volumes),
           'volume_sma': calculate_moving_averages(volumes, [20], 'sma')[20]
       }
   }
   ```

3. **Generate Technical Report:**
   ```markdown
   ## Technical Analysis
   
   ### Trend Analysis:
   - Primary Trend: Bullish (Price above 200-day SMA)
   - ADX: 32 (Strong trend)
   - Golden Cross: 50-day EMA above 200-day EMA ✅
   
   ### Momentum:
   - RSI: 58 (Bullish momentum)
   - MACD: Bullish crossover confirmed
   - Stochastic: %K 65, %D 62 (Bullish)
   
   ### Volatility:
   - Bollinger Bands: Price in upper half of bands
   - Bandwidth: 0.08 (Moderate volatility)
   - ATR: 2.3% (Average daily range)
   
   ### Volume:
   - OBV: Rising trend confirms price advance
   - Volume: 25% above 20-day average
   
   ### Technical Score: 72/100 (Bullish)
   
   ### Key Levels:
   - Support: $105 (50-day SMA), $100 (200-day SMA)
   - Resistance: $120 (Previous high), $125 (Upper Bollinger Band)
   
   ### Recommendation:
   - Technicals support continued uptrend
   - Buy on pullback to $105-110 support zone
   - Stop loss: $95 (below 200-day SMA)
   - Target: $120-125 resistance zone
   ```

---

## 🎖️ Best Practices

1. **Multiple Confirmation:** Never rely on single indicator
2. **Context Matters:** Consider market environment and sector
3. **Timeframe Alignment:** Higher timeframe > lower timeframe
4. **Risk Management:** Use ATR for stop loss placement
5. **Volume Confirmation:** Price moves without volume are suspect
6. **Divergence Hunting:** Look for divergences for early reversal signals
7. **Backtesting:** Test strategies on historical data
8. **Continuous Learning:** Markets evolve, stay updated