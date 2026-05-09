# Risk Metrics Reference (风险指标分析)

## Overview

Comprehensive risk assessment framework for portfolio and individual stocks. This reference provides systematic calculation and interpretation of key risk metrics.

---

## 📊 Core Risk Metrics

### 1. Sharpe Ratio (夏普比率)

**Definition:** Risk-adjusted return measure comparing excess return per unit of risk (volatility).

**Formula:**
```
Sharpe Ratio = (Portfolio Return - Risk-Free Rate) / Portfolio Volatility

Where:
- Portfolio Return: Average daily/weekly/monthly return
- Risk-Free Rate: Typically 3-month Treasury yield (~0.02-0.05)
- Portfolio Volatility: Standard deviation of returns
```

**Calculation:**
```python
def calculate_sharpe_ratio(returns, risk_free_rate=0.03, periods_per_year=252):
    """
    Calculate Sharpe Ratio for given return series
    
    Args:
        returns: List/array of periodic returns (e.g., daily)
        risk_free_rate: Annual risk-free rate (default 3%)
        periods_per_year: Number of periods in a year (252 for daily)
    
    Returns:
        sharpe_ratio: Annualized Sharpe Ratio
    """
    import numpy as np
    
    if len(returns) < 2:
        return None
    
    returns = np.array(returns)
    
    # Calculate excess returns
    excess_returns = returns - (risk_free_rate / periods_per_year)
    
    # Calculate annualized Sharpe Ratio
    mean_excess_return = np.mean(excess_returns)
    std_excess_return = np.std(excess_returns)
    
    if std_excess_return == 0:
        return None
    
    # Annualize
    sharpe_ratio = (mean_excess_return / std_excess_return) * np.sqrt(periods_per_year)
    
    return sharpe_ratio
```

**Interpretation:**
| Sharpe Ratio | Risk-Adjusted Performance | Interpretation |
|--------------|---------------------------|----------------|
| > 2.0 | Excellent | Superior risk-adjusted returns |
| 1.0 - 2.0 | Good | Good risk-adjusted returns |
| 0.5 - 1.0 | Acceptable | Moderate risk-adjusted returns |
| 0.0 - 0.5 | Poor | Low risk-adjusted returns |
| < 0.0 | Bad | Negative risk-adjusted returns |

**Example Application:**
```python
# For a stock with daily returns
daily_returns = [0.01, -0.02, 0.03, 0.005, -0.01]  # 5 days of returns
sharpe = calculate_sharpe_ratio(daily_returns, risk_free_rate=0.03)
# Result: ~0.85 (Acceptable)
```

---

### 2. Maximum Drawdown (最大回撤)

**Definition:** Maximum peak-to-trough decline during a specific period.

**Formula:**
```
Maximum Drawdown = (Trough Value - Peak Value) / Peak Value

Where:
- Peak Value: Highest historical value
- Trough Value: Lowest value after the peak
```

**Calculation:**
```python
def calculate_max_drawdown(prices):
    """
    Calculate maximum drawdown from price series
    
    Args:
        prices: List/array of historical prices
    
    Returns:
        max_dd: Maximum drawdown (negative percentage)
        peak_idx: Index of peak before maximum drawdown
        trough_idx: Index of trough
    """
    import numpy as np
    
    if len(prices) < 2:
        return None, None, None
    
    prices = np.array(prices)
    
    # Calculate running maximum (peak)
    running_max = np.maximum.accumulate(prices)
    
    # Calculate drawdown series
    drawdown = (prices - running_max) / running_max
    
    # Find maximum drawdown
    max_dd_idx = np.argmin(drawdown)
    max_dd = drawdown[max_dd_idx]
    
    # Find peak before maximum drawdown
    peak_idx = np.argmax(prices[:max_dd_idx + 1])
    
    return max_dd, peak_idx, max_dd_idx
```

**Interpretation:**
| Maximum Drawdown | Risk Level | Interpretation |
|------------------|------------|----------------|
| < -10% | Low | Conservative risk profile |
| -10% to -20% | Moderate | Moderate risk profile |
| -20% to -30% | High | Aggressive risk profile |
| > -30% | Very High | Speculative risk profile |

**Example Application:**
```python
# Historical prices for a stock
prices = [100, 105, 110, 95, 100, 90, 85, 95, 100]
max_dd, peak_idx, trough_idx = calculate_max_drawdown(prices)
# Result: -22.7% (from 110 to 85)
```

---

### 3. Sortino Ratio (索提诺比率)

**Definition:** Risk-adjusted return measure using downside deviation instead of total volatility.

**Formula:**
```
Sortino Ratio = (Portfolio Return - Risk-Free Rate) / Downside Deviation

Where:
- Downside Deviation: Standard deviation of negative returns only
```

**Calculation:**
```python
def calculate_sortino_ratio(returns, risk_free_rate=0.03, periods_per_year=252):
    """
    Calculate Sortino Ratio for given return series
    
    Args:
        returns: List/array of periodic returns
        risk_free_rate: Annual risk-free rate
        periods_per_year: Number of periods in a year
    
    Returns:
        sortino_ratio: Annualized Sortino Ratio
    """
    import numpy as np
    
    if len(returns) < 2:
        return None
    
    returns = np.array(returns)
    
    # Calculate excess returns
    excess_returns = returns - (risk_free_rate / periods_per_year)
    
    # Calculate downside deviation (only negative excess returns)
    downside_returns = excess_returns[excess_returns < 0]
    
    if len(downside_returns) == 0:
        # No downside risk
        return np.inf if np.mean(excess_returns) > 0 else None
    
    downside_deviation = np.std(downside_returns)
    
    if downside_deviation == 0:
        return None
    
    # Annualize
    sortino_ratio = (np.mean(excess_returns) / downside_deviation) * np.sqrt(periods_per_year)
    
    return sortino_ratio
```

**Interpretation:**
| Sortino Ratio | Downside Risk Management | Interpretation |
|---------------|--------------------------|----------------|
| > 3.0 | Excellent | Superior downside protection |
| 2.0 - 3.0 | Good | Good downside protection |
| 1.0 - 2.0 | Acceptable | Moderate downside protection |
| < 1.0 | Poor | Weak downside protection |

---

### 4. Beta Coefficient (贝塔系数)

**Definition:** Measure of a stock's volatility relative to the market.

**Formula:**
```
Beta = Covariance(Stock Returns, Market Returns) / Variance(Market Returns)

Where:
- Covariance: How stock and market move together
- Variance: Market return variability
```

**Calculation:**
```python
def calculate_beta(stock_returns, market_returns):
    """
    Calculate beta coefficient for a stock
    
    Args:
        stock_returns: List/array of stock returns
        market_returns: List/array of market returns (e.g., S&P 500)
    
    Returns:
        beta: Beta coefficient
        r_squared: Goodness of fit
    """
    import numpy as np
    
    if len(stock_returns) != len(market_returns) or len(stock_returns) < 2:
        return None, None
    
    stock_returns = np.array(stock_returns)
    market_returns = np.array(market_returns)
    
    # Calculate covariance and variance
    covariance = np.cov(stock_returns, market_returns)[0, 1]
    market_variance = np.var(market_returns)
    
    if market_variance == 0:
        return None, None
    
    beta = covariance / market_variance
    
    # Calculate R-squared
    correlation = np.corrcoef(stock_returns, market_returns)[0, 1]
    r_squared = correlation ** 2
    
    return beta, r_squared
```

**Interpretation:**
| Beta | Market Sensitivity | Interpretation |
|------|-------------------|----------------|
| β < 0.8 | Defensive | Less volatile than market |
| 0.8 ≤ β ≤ 1.2 | Neutral | Similar volatility to market |
| β > 1.2 | Aggressive | More volatile than market |

**Example:**
- β = 0.5: Stock moves 0.5% for every 1% market move
- β = 1.5: Stock moves 1.5% for every 1% market move

---

### 5. Value at Risk (VaR) (风险价值)

**Definition:** Maximum expected loss over a given time period at a specified confidence level.

**Formula (Historical Method):**
```
VaR = Percentile(Portfolio Returns, Confidence Level)

Example: 95% VaR = 5th percentile of returns
```

**Calculation:**
```python
def calculate_var(returns, confidence_level=0.95, method='historical'):
    """
    Calculate Value at Risk
    
    Args:
        returns: List/array of returns
        confidence_level: Confidence level (e.g., 0.95 for 95%)
        method: 'historical' or 'parametric'
    
    Returns:
        var: Value at Risk (negative percentage)
    """
    import numpy as np
    
    if len(returns) < 10:
        return None
    
    returns = np.array(returns)
    
    if method == 'historical':
        # Historical VaR
        percentile = 1 - confidence_level
        var = np.percentile(returns, percentile * 100)
        
    elif method == 'parametric':
        # Parametric VaR (assuming normal distribution)
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        # Z-score for confidence level
        from scipy import stats
        z_score = stats.norm.ppf(1 - confidence_level)
        
        var = mean_return + z_score * std_return
    
    return var
```

**Interpretation:**
```
Example: 95% VaR = -2.5%
Interpretation: There's a 95% confidence that losses won't exceed 2.5% in one day.
```

---

## 📈 Volatility Metrics

### 1. Historical Volatility (历史波动率)

**Formula:**
```
Historical Volatility = Standard Deviation(Returns) × √(Periods per Year)
```

**Calculation:**
```python
def calculate_historical_volatility(returns, periods_per_year=252):
    """
    Calculate annualized historical volatility
    
    Args:
        returns: List/array of periodic returns
        periods_per_year: Trading periods per year
    
    Returns:
        volatility: Annualized volatility (percentage)
    """
    import numpy as np
    
    if len(returns) < 2:
        return None
    
    returns = np.array(returns)
    volatility = np.std(returns) * np.sqrt(periods_per_year)
    
    return volatility
```

**Interpretation:**
| Volatility | Risk Level | Typical Stocks |
|------------|------------|----------------|
| < 15% | Low | Utilities, Consumer Staples |
| 15% - 30% | Moderate | Large-cap Tech, Industrials |
| 30% - 50% | High | Small-cap, Biotech |
| > 50% | Very High | Speculative, Penny Stocks |

---

### 2. Rolling Volatility (滚动波动率)

**Calculation:**
```python
def calculate_rolling_volatility(returns, window=20, periods_per_year=252):
    """
    Calculate rolling volatility
    
    Args:
        returns: List/array of returns
        window: Rolling window size
        periods_per_year: Trading periods per year
    
    Returns:
        rolling_vol: List of rolling volatilities
    """
    import numpy as np
    import pandas as pd
    
    if len(returns) < window:
        return None
    
    # Convert to pandas Series for rolling calculations
    returns_series = pd.Series(returns)
    rolling_vol = returns_series.rolling(window=window).std() * np.sqrt(periods_per_year)
    
    return rolling_vol.tolist()
```

---

## 🎯 Risk-Adjusted Performance Metrics

### 1. Calmar Ratio (卡尔马比率)

**Definition:** Return per unit of maximum drawdown risk.

**Formula:**
```
Calmar Ratio = Annualized Return / Maximum Drawdown

Where Maximum Drawdown is expressed as positive number
```

**Calculation:**
```python
def calculate_calmar_ratio(returns, prices, periods_per_year=252):
    """
    Calculate Calmar Ratio
    
    Args:
        returns: List/array of returns
        prices: List/array of prices (for drawdown calculation)
        periods_per_year: Trading periods per year
    
    Returns:
        calmar_ratio: Calmar Ratio
    """
    import numpy as np
    
    if len(returns) < 2 or len(prices) < 2:
        return None
    
    # Calculate annualized return
    total_return = (prices[-1] / prices[0]) - 1
    annualized_return = (1 + total_return) ** (periods_per_year / len(returns)) - 1
    
    # Calculate maximum drawdown
    max_dd, _, _ = calculate_max_drawdown(prices)
    
    if max_dd == 0:
        return None
    
    calmar_ratio = annualized_return / abs(max_dd)
    
    return calmar_ratio
```

**Interpretation:**
| Calmar Ratio | Performance vs Drawdown | Interpretation |
|--------------|-------------------------|----------------|
| > 1.0 | Excellent | High returns relative to drawdown |
| 0.5 - 1.0 | Good | Good returns relative to drawdown |
| 0.0 - 0.5 | Poor | Low returns relative to drawdown |
| < 0.0 | Bad | Negative returns with drawdown |

---

### 2. Treynor Ratio (特雷诺比率)

**Definition:** Risk-adjusted return per unit of systematic risk (beta).

**Formula:**
```
Treynor Ratio = (Portfolio Return - Risk-Free Rate) / Beta
```

**Calculation:**
```python
def calculate_treynor_ratio(portfolio_return, risk_free_rate, beta):
    """
    Calculate Treynor Ratio
    
    Args:
        portfolio_return: Portfolio annualized return
        risk_free_rate: Annual risk-free rate
        beta: Portfolio beta
    
    Returns:
        treynor_ratio: Treynor Ratio
    """
    if beta == 0:
        return None
    
    treynor_ratio = (portfolio_return - risk_free_rate) / beta
    
    return treynor_ratio
```

---

## 📊 Portfolio-Level Risk Metrics

### 1. Portfolio Volatility (组合波动率)

**Formula:**
```
Portfolio Volatility = √(w' × Σ × w)

Where:
- w: Vector of portfolio weights
- Σ: Covariance matrix of asset returns
- w': Transpose of weight vector
```

**Calculation:**
```python
def calculate_portfolio_volatility(weights, covariance_matrix, periods_per_year=252):
    """
    Calculate portfolio volatility
    
    Args:
        weights: List of portfolio weights
        covariance_matrix: Covariance matrix of asset returns
        periods_per_year: Trading periods per year
    
    Returns:
        portfolio_vol: Portfolio volatility (annualized)
    """
    import numpy as np
    
    weights = np.array(weights)
    
    # Ensure weights sum to 1
    weights = weights / np.sum(weights)
    
    # Calculate portfolio variance
    portfolio_variance = np.dot(weights.T, np.dot(covariance_matrix, weights))
    
    # Annualize
    portfolio_vol = np.sqrt(portfolio_variance * periods_per_year)
    
    return portfolio_vol
```

---

### 2. Correlation Matrix Analysis (相关性矩阵分析)

**Importance:**
- Diversification benefits
- Risk concentration
- Sector exposure

**Calculation:**
```python
def analyze_correlation_matrix(returns_data):
    """
    Analyze correlation matrix for risk concentration
    
    Args:
        returns_data: DataFrame or dict of asset returns
    
    Returns:
        analysis: Dictionary with correlation insights
    """
    import numpy as np
    import pandas as pd
    
    # Calculate correlation matrix
    if isinstance(returns_data, dict):
        df = pd.DataFrame(returns_data)
    else:
        df = returns_data
    
    corr_matrix = df.corr()
    
    # Find high correlations (> 0.7)
    high_corr_pairs = []
    n_assets = corr_matrix.shape[0]
    
    for i in range(n_assets):
        for j in range(i + 1, n_assets):
            corr = corr_matrix.iloc[i, j]
            if abs(corr) > 0.7:
                high_corr_pairs.append({
                    'asset1': corr_matrix.index[i],
                    'asset2': corr_matrix.columns[j],
                    'correlation': corr
                })
    
    # Calculate average correlation
    upper_triangle = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    avg_correlation = upper_triangle.stack().mean()
    
    return {
        'correlation_matrix': corr_matrix,
        'high_correlation_pairs': high_corr_pairs,
        'average_correlation': avg_correlation,
        'diversification_score': 1 - abs(avg_correlation)  # Higher = better diversification
    }
```

---

## 🎯 Risk Assessment Framework

### Comprehensive Risk Score

```python
def calculate_comprehensive_risk_score(risk_metrics, weights=None):
    """
    Calculate comprehensive risk score (0-100, higher = riskier)
    
    Args:
        risk_metrics: Dictionary of calculated risk metrics
        weights: Optional weights for each metric
    
    Returns:
        risk_score: Comprehensive risk score
        breakdown: Score breakdown by component
    """
    # Default weights
    if weights is None:
        weights = {
            'max_drawdown': 0.30,
            'volatility': 0.25,
            'beta': 0.20,
            'var': 0.15,
            'correlation': 0.10
        }
    
    scores = {}
    
    # 1. Maximum Drawdown Score (0-100)
    max_dd = abs(risk_metrics.get('max_drawdown', 0))
    if max_dd > 0.50:  # >50% drawdown
        scores['max_drawdown'] = 100
    elif max_dd > 0.30:
        scores['max_drawdown'] = 80
    elif max_dd > 0.20:
        scores['max_drawdown'] = 60
    elif max_dd > 0.10:
        scores['max_drawdown'] = 40
    else:
        scores['max_drawdown'] = 20
    
    # 2. Volatility Score (0-100)
    volatility = risk_metrics.get('volatility', 0)
    if volatility > 0.50:  # >50% annual volatility
        scores['volatility'] = 100
    elif volatility > 0.30:
        scores['volatility'] = 80
    elif volatility > 0.20:
        scores['volatility'] = 60
    elif volatility > 0.15:
        scores['volatility'] = 40
    else:
        scores['volatility'] = 20
    
    # 3. Beta Score (0-100)
    beta = abs(risk_metrics.get('beta', 1.0))
    if beta > 1.5:
        scores['beta'] = 100
    elif beta > 1.2:
        scores['beta'] = 80
    elif beta > 0.8:
        scores['beta'] = 40
    else:
        scores['beta'] = 20
    
    # 4. VaR Score (0-100)
    var = abs(risk_metrics.get('var_95', 0))
    if var > 0.05:  # >5% daily VaR
        scores['var'] = 100
    elif var > 0.03:
        scores['var'] = 80
    elif var > 0.02:
        scores['var'] = 60
    elif var > 0.01:
        scores['var'] = 40
    else:
        scores['var'] = 20
    
    # 5. Correlation Score (0-100)
    avg_corr = abs(risk_metrics.get('avg_correlation', 0))
    scores['correlation'] = avg_corr * 100  # Higher correlation = higher risk
    
    # Calculate weighted risk score
    risk_score = 0
    breakdown = {}
    
    for metric, weight in weights.items():
        metric_score = scores.get(metric, 50)
        contribution = metric_score * weight
        risk_score += contribution
        breakdown[metric] = {
            'score': metric_score,
            'weight': weight,
            'contribution': contribution
        }
    
    return min(100, risk_score), breakdown
```

---

## 📋 Implementation in Stock Analysis Workflow

### Integration Steps:

1. **Data Collection:**
   ```bash
   # Get historical price data for risk calculations
   longbridge kline history SYMBOL.US --start $(date -v-365d +%Y-%m-%d) --end $(date +%Y-%m-%d) --period day --format json
   ```

2. **Calculate Returns:**
   ```python
   # Convert prices to returns
   prices = [candle['close'] for candle in kline_data]
   returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
   ```

3. **Compute Risk Metrics:**
   ```python
   risk_metrics = {
       'sharpe_ratio': calculate_sharpe_ratio(returns),
       'max_drawdown': calculate_max_drawdown(prices)[0],
       'volatility': calculate_historical_volatility(returns),
       'beta': calculate_beta(stock_returns, market_returns)[0],
       'var_95': calculate_var(returns, confidence_level=0.95)
   }
   ```

4. **Generate Risk Report:**
   ```markdown
   ## Risk Assessment
   
   ### Risk Metrics:
   - Sharpe Ratio: 1.2 (Good)
   - Maximum Drawdown: -18.5% (Moderate)
   - Annual Volatility: 28.3% (High)
   - Beta: 1.35 (Aggressive)
   - 95% VaR: -2.8% (Daily)
   
   ### Risk Score: 68/100 (Moderate-High Risk)
   
   ### Recommendations:
   - Consider reducing position size due to high volatility
   - Add defensive stocks to lower portfolio beta
   - Set stop-loss at -15% to manage drawdown risk
   ```

---

## 🎯 Key Takeaways

1. **Sharpe Ratio** - Best for comparing different investments
2. **Maximum Drawdown** - Most intuitive for risk tolerance assessment  
3. **Beta** - Essential for understanding market sensitivity
4. **VaR** - Useful for setting risk limits
5. **Correlation** - Critical for portfolio diversification

**Always consider:**
- Time period for calculations (at least 1 year recommended)
- Market conditions (volatility regimes)
- Investment horizon (short-term vs long-term risk)
- Personal risk tolerance