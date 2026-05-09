# 策略优化清单

## 📊 当前问题诊断

### 核心问题：策略准确率仅 16.7%

基于2026-04-07回测数据，当前策略过于保守，错失了多个盈利机会。

---

## 🔴 高优先级优化（核心策略逻辑）

### 1. RSI超卖信号误判 ❌

**当前逻辑** (`engine.py:1196-1205`)
```python
if rsi > 70:
    score -= 20  # 超买，扣分
elif rsi < 30:
    score += 20  # 超卖，加分 ✓
elif rsi > 50:
    score += 10  # 上涨动能
else:
    score -= 10  # 下跌动能
```

**问题**
- RSI < 30 只加20分，不足以反映买入机会
- RSI < 35（轻微超卖）完全被忽略
- 缺乏对超卖程度的细分（30 vs 20 vs 10）

**优化方案**
```python
# 分级超卖处理
if rsi < 20:
    score += 40  # 极度超卖，强买入信号
    signal = "STRONG_OVERSOLD"
elif rsi < 30:
    score += 30  # 深度超卖
    signal = "DEEP_OVERSOLD"
elif rsi < 35:
    score += 15  # 轻微超卖
    signal = "OVERSOLD"
elif rsi > 80:
    score -= 30  # 极度超买
    signal = "STRONG_OVERBOUGHT"
elif rsi > 70:
    score -= 20  # 超买
    signal = "OVERBOUGHT"
```

**预期效果**
- 准确识别超卖买入机会（BABA RSI=31.9 → 应为买入）
- 提升策略准确率至 50%+

---

### 2. 高波动率处理过于保守 ❌

**当前逻辑** (`engine.py:340-349`)
```python
if volatility > 0.50:  # 年化波动率 > 50%
    scores['volatility'] = 100  # 高风险
elif volatility > 0.30:
    scores['volatility'] = 80
elif volatility > 0.20:
    scores['volatility'] = 60
```

**问题**
- 高波动 = 高风险评分 → 降低总分数 → 建议 SELL/HOLD
- 忽略了高波动股票的收益潜力（COIN 73%波动 → +20.8%收益）
- 未与仓位管理结合（应该是降低仓位而非避免）

**优化方案**
```python
# 分离风险评分和机会评分
volatility_risk = calculate_volatility_risk(volatility)  # 用于风险警告
volatility_opportunity = calculate_volatility_opportunity(volatility)  # 用于收益预期

# 根据波动率调整仓位建议
def get_position_size_recommendation(volatility, base_position=0.10):
    """
    高波动股票：降低仓位而非回避
    - vol > 60%: max 5%仓位
    - vol 40-60%: max 8%仓位
    - vol < 40%: 标准仓位10-15%
    """
    if volatility > 0.60:
        return min(base_position, 0.05)
    elif volatility > 0.40:
        return min(base_position, 0.08)
    else:
        return base_position
```

**预期效果**
- COIN不会被标记为"高风险避免"，而是"高风险小仓位"
- 保留高波动股票的收益机会

---

### 3. 缺乏缺口分析（Support/Resistance）❌

**当前问题**
- 未计算关键支撑位和阻力位
- 未识别价格缺口（Gap）及其填充概率
- 无法提供精准的止损和目标价

**新增功能**
```python
def analyze_price_gaps(prices: List[float], lookback: int = 90) -> Dict:
    """
    分析价格缺口和支撑阻力位
    
    Returns:
        {
            'support_levels': [105.0, 110.0, 115.0],
            'resistance_levels': [130.0, 140.0, 150.0],
            'unfilled_gaps': [
                {'type': 'up', 'from': 115, 'to': 120, 'age': 14},
                {'type': 'down', 'from': 140, 'to': 135, 'age': 7}
            ],
            'nearest_support': 115.0,
            'nearest_resistance': 130.0,
            'gap_fill_probability': 0.75
        }
    """
    pass
```

**评分逻辑**
```python
# 价格接近支撑位 → 加分（买入机会）
distance_to_support = (current_price - nearest_support) / current_price
if distance_to_support < 0.05:  # 5%以内
    score += 15  # 接近支撑，买入机会

# 价格接近阻力位 → 扣分（获利了结）
distance_to_resistance = (nearest_resistance - current_price) / current_price
if distance_to_resistance < 0.05:
    score -= 10  # 接近阻力，考虑减仓
```

**预期效果**
- 提供精准的止损价位
- 提升目标价准确率

---

### 4. 缺乏趋势确认机制 ❌

**当前问题**
- RSI超卖 + 下跌趋势 = 抄底失败
- 未考虑价格与MA的关系
- 未结合成交量确认

**新增逻辑**
```python
def confirm_trend(prices: List[float], indicators: Dict) -> Dict:
    """
    趋势确认
    
    Returns:
        {
            'trend': 'UP' | 'DOWN' | 'SIDEWAYS',
            'strength': 0.0-1.0,
            'confirmed': True/False
        }
    """
    # 1. MA趋势
    ma_50 = calculate_ma(prices, 50)
    ma_200 = calculate_ma(prices, 200)
    
    price_vs_ma50 = (current_price - ma_50) / ma_50
    price_vs_ma200 = (current_price - ma_200) / ma_200
    
    # 2. RSI趋势
    rsi_trend = indicators['rsi'][-5:]  # 最近5天RSI
    rsi_improving = all(rsi_trend[i] < rsi_trend[i+1] for i in range(len(rsi_trend)-1))
    
    # 3. 成交量确认
    volume_ratio = current_volume / avg_volume
    
    # 综合判断
    if price_vs_ma50 > 0.05 and rsi_improving and volume_ratio > 1.2:
        return {'trend': 'UP', 'strength': 0.8, 'confirmed': True}
    elif price_vs_ma50 < -0.05 and not rsi_improving and volume_ratio < 0.8:
        return {'trend': 'DOWN', 'strength': 0.8, 'confirmed': True}
    else:
        return {'trend': 'SIDEWAYS', 'strength': 0.3, 'confirmed': False}
```

**RSI超卖买入条件增强**
```python
# 只有在趋势确认后才买入超卖股票
if rsi < 30:
    if trend['trend'] != 'DOWN' or trend['strength'] < 0.5:
        score += 30  # 超卖 + 非强下跌趋势 = 买入
    else:
        score += 10  # 超卖但下跌趋势强 = 谨慎买入
```

**预期效果**
- 避免在强下跌趋势中抄底
- 提升买入信号准确率

---

## 🟡 中优先级优化（辅助功能）

### 5. 仓位管理过于保守 ❌

**当前问题**
- 统一建议仓位 10-20%
- 未根据股票特性调整

**优化方案**
```python
def calculate_position_size(
    volatility: float,
    beta: float,
    conviction_score: float,
    portfolio_risk_budget: float = 0.02
) -> float:
    """
    动态仓位管理
    
    Args:
        volatility: 年化波动率
        beta: 相对市场beta
        conviction_score: 信心分数 (0-100)
        portfolio_risk_budget: 组合风险预算 (默认2%)
    
    Returns:
        建议仓位比例 (0.0-1.0)
    """
    # Kelly Criterion简化版
    # 仓位 = 风险预算 / (波动率 * 调整系数)
    
    risk_adjustment = 1.0
    if volatility > 0.60:
        risk_adjustment = 2.0  # 高波动减半
    elif volatility < 0.20:
        risk_adjustment = 0.5  # 低波动加倍
    
    base_position = portfolio_risk_budget / (volatility * risk_adjustment)
    
    # 根据信心分数调整
    conviction_mult = conviction_score / 100.0
    final_position = base_position * conviction_mult
    
    # 限制范围
    return max(0.02, min(0.15, final_position))
```

**示例**
- COIN (vol=73%, score=45) → 仓位 5% (而非避免)
- BABA (vol=25%, score=75) → 仓位 12% (加仓)

---

### 6. 缺乏止损机制 ❌

**新增功能**
```python
def calculate_stop_loss(
    current_price: float,
    entry_price: float,
    volatility: float,
    support_level: float,
    position_type: str = 'LONG'
) -> Dict:
    """
    动态止损计算
    
    Returns:
        {
            'stop_loss_price': 115.0,
            'stop_loss_pct': 4.2,
            'trailing_stop': True,
            'risk_reward_ratio': 2.5
        }
    """
    # 基于ATR的止损
    atr = calculate_atr(prices, period=14)
    atr_stop = current_price - (2 * atr)
    
    # 基于支撑位的止损
    support_stop = support_level * 0.98  # 支撑位下方2%
    
    # 基于波动率的止损
    vol_stop = current_price * (1 - volatility * 0.5)
    
    # 选择最近的合理止损位
    stop_loss_price = max(atr_stop, support_stop, vol_stop)
    
    # 计算风险回报比
    target_price = calculate_target_price(current_price, volatility)
    risk = current_price - stop_loss_price
    reward = target_price - current_price
    risk_reward = reward / risk if risk > 0 else 0
    
    return {
        'stop_loss_price': round(stop_loss_price, 2),
        'stop_loss_pct': round((current_price - stop_loss_price) / current_price * 100, 2),
        'risk_reward_ratio': round(risk_reward, 2),
        'trailing_stop': True if position_type == 'LONG' else False
    }
```

---

### 7. 缺乏市场环境评估 ❌

**当前问题**
- 未考虑大盘趋势（S&P 500, NASDAQ）
- 未考虑市场情绪指标（VIX, Put/Call Ratio）

**新增功能**
```python
def assess_market_environment() -> Dict:
    """
    市场环境评估
    
    Returns:
        {
            'market_trend': 'BULL' | 'BEAR' | 'NEUTRAL',
            'volatility_regime': 'HIGH' | 'NORMAL' | 'LOW',
            'risk_on_off': 'RISK_ON' | 'RISK_OFF',
            'sector_rotation': 'TECH_LEAD' | 'VALUE_LEAD',
            'recommendation': {
                'aggressive_positions': True/False,
                'sector_focus': ['TECH', 'FINANCE']
            }
        }
    """
    # VIX水平
    vix = get_vix()
    
    # 市场宽度（涨跌比）
    market_breadth = calculate_market_breadth()
    
    # 板块轮动
    sector_momentum = get_sector_momentum()
    
    # 综合判断
    if vix < 20 and market_breadth > 0.6:
        return {
            'market_trend': 'BULL',
            'risk_on_off': 'RISK_ON',
            'recommendation': {
                'aggressive_positions': True,
                'sector_focus': ['TECH', 'GROWTH']
            }
        }
```

**调整策略**
```python
# 在牛市环境中，提高风险容忍度
if market_env['market_trend'] == 'BULL':
    score_threshold_for_buy = 55  # 降低买入门槛
else:
    score_threshold_for_buy = 65  # 提高买入门槛
```

---

## 🟢 低优先级优化（体验提升）

### 8. 缺乏历史准确率跟踪 ❌

**新增功能**
```python
def track_prediction_accuracy(
    predictions: List[Dict],
    actual_results: List[Dict],
    time_horizon: int = 14
) -> Dict:
    """
    跟踪预测准确率
    
    Returns:
        {
            'overall_accuracy': 0.65,
            'by_strategy': {
                'rsi_oversold': {'accuracy': 0.75, 'samples': 20},
                'breakout': {'accuracy': 0.60, 'samples': 15}
            },
            'by_timeframe': {
                '3_day': 0.70,
                '7_day': 0.68,
                '14_day': 0.65
            },
            'improvement_trend': 'IMPROVING' | 'DECLINING' | 'STABLE'
        }
    """
    pass
```

---

### 9. 缺乏情景分析 ❌

**新增功能**
```python
def scenario_analysis(
    current_price: float,
    volatility: float,
    days: int = 14
) -> Dict:
    """
    情景分析：最好/最差/预期情况
    
    Returns:
        {
            'bull_case': {'price': 145.0, 'probability': 0.25, 'return': 0.20},
            'base_case': {'price': 128.0, 'probability': 0.50, 'return': 0.06},
            'bear_case': {'price': 110.0, 'probability': 0.25, 'return': -0.09},
            'expected_return': 0.058,
            'var_95': -0.12
        }
    """
    # 蒙特卡洛模拟
    simulated_prices = monte_carlo_simulation(current_price, volatility, days, n_sims=10000)
    
    # 计算分布
    p5 = np.percentile(simulated_prices, 5)
    p50 = np.percentile(simulated_prices, 50)
    p95 = np.percentile(simulated_prices, 95)
    
    return {
        'bull_case': {'price': p95, 'probability': 0.25},
        'base_case': {'price': p50, 'probability': 0.50},
        'bear_case': {'price': p5, 'probability': 0.25}
    }
```

---

## 📋 实施计划

### Phase 1: 核心策略修复（1-2天）
- [x] 修复RSI超卖逻辑
- [x] 调整波动率处理
- [ ] 添加缺口分析
- [ ] 添加趋势确认

### Phase 2: 风险管理增强（2-3天）
- [ ] 实现动态仓位管理
- [ ] 实现止损机制
- [ ] 添加市场环境评估

### Phase 3: 监控与优化（持续）
- [ ] 实现预测准确率跟踪
- [ ] 添加情景分析
- [ ] 建立策略迭代机制

---

## 🎯 预期效果

### 策略准确率提升路径
```
当前: 16.7% → Phase 1后: 45-55% → Phase 2后: 60-70%
```

### 具体改进
- **RSI超卖**：从错过机会 → 准确识别买入点
- **高波动股票**：从回避 → 小仓位参与
- **缺口分析**：提升目标价准确率 +30%
- **趋势确认**：避免抄底失败，提升胜率 +15%
- **仓位管理**：最大化风险调整后收益

---

**创建时间**: 2026-04-21  
**状态**: 待实施  
**优先级**: 高
