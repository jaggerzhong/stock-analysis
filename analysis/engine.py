#!/usr/bin/env python3
"""
Stock Analysis Engine - Comprehensive analysis module integrating risk metrics,
valuation metrics, technical indicators, and multi-factor models.

This module implements the algorithms from the reference documents:
- references/risk-metrics.md
- references/valuation-metrics.md  
- references/technical-indicators.md
- references/multi-factor-model.md
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Union, Any
from dataclasses import dataclass
import json
from datetime import datetime, timedelta
import statistics
import math
from pathlib import Path

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class ConfigLoader:
    """Load and cache configuration from YAML file."""
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> Dict:
        if cls._config is not None:
            return cls._config
        
        if config_path is None:
            config_path = Path(__file__).parent / 'config.yaml'
        
        cls._config = cls._load_yaml(config_path)
        return cls._config
    
    @classmethod
    def _load_yaml(cls, path: Path) -> Dict:
        if not YAML_AVAILABLE or not path.exists():
            return cls._default_config()
        
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return cls._default_config()
    
    @classmethod
    def _default_config(cls) -> Dict:
        return {
            'risk': {'weights': {'max_drawdown': 0.30, 'volatility': 0.25, 'beta': 0.20, 'var': 0.15, 'correlation': 0.10}},
            'valuation': {'weights': {'pe': 0.20, 'peg': 0.25, 'p_fcf': 0.20, 'ev_ebitda': 0.20, 'dcf': 0.15}},
            'technical': {
                'weights': {'trend': 0.30, 'momentum': 0.25, 'volume': 0.20, 'volatility': 0.15, 'support_resistance': 0.10},
                'gap': {'threshold_pct': 1.0},
            },
            'factors': {'strategies': {'balanced': {'quality': 0.25, 'value': 0.25, 'growth': 0.20, 'momentum': 0.20, 'low_volatility': 0.10}}},
            'moat': {
                'sector_gross_margins': {'Technology': 0.55, 'Healthcare': 0.60, 'Financials': 0.70},
                'sector_op_margins': {'Technology': 0.20, 'Healthcare': 0.18, 'Financials': 0.25},
            },
            'overall': {
                'weights': {'risk': 0.10, 'valuation': 0.35, 'technical': 0.30, 'factor': 0.25},
                'recommendation_thresholds': {'strong_buy': 75, 'buy': 65, 'hold': 55, 'weak_hold': 45, 'sell': 35},
            },
        }
    
    @classmethod
    def get(cls, *keys, default=None):
        config = cls.load()
        for key in keys:
            if isinstance(config, dict) and key in config:
                config = config[key]
            else:
                return default
        return config


def get_config(*keys, default=None):
    """Convenience function to get config values."""
    return ConfigLoader.get(*keys, default=default)


_SECTOR_PE_BENCHMARKS = None

def _get_sector_pe_benchmarks():
    global _SECTOR_PE_BENCHMARKS
    if _SECTOR_PE_BENCHMARKS is not None:
        return _SECTOR_PE_BENCHMARKS
    raw = get_config('valuation', 'sector_pe_benchmarks')
    if raw:
        _SECTOR_PE_BENCHMARKS = {}
        for sector, data in raw.items():
            norm = sector.replace('_', ' ')
            _SECTOR_PE_BENCHMARKS[norm] = {
                'median': data.get('median', 15),
                'range': tuple(data.get('range', [10, 25])),
                'cheap': data.get('range', [10, 25])[0],
                'expensive': data.get('range', [10, 25])[1],
            }
    else:
        _SECTOR_PE_BENCHMARKS = {
            'Technology': {'median': 22, 'range': (15, 35), 'cheap': 15, 'expensive': 35},
            'Healthcare': {'median': 18, 'range': (12, 30), 'cheap': 12, 'expensive': 30},
            'Financials': {'median': 12, 'range': (8, 18), 'cheap': 8, 'expensive': 18},
            'Consumer Staples': {'median': 16, 'range': (12, 22), 'cheap': 12, 'expensive': 22},
            'Utilities': {'median': 14, 'range': (10, 18), 'cheap': 10, 'expensive': 18},
            'Industrials': {'median': 15, 'range': (10, 22), 'cheap': 10, 'expensive': 22},
            'Energy': {'median': 10, 'range': (6, 15), 'cheap': 6, 'expensive': 15},
            'Consumer Discretionary': {'median': 18, 'range': (12, 28), 'cheap': 12, 'expensive': 28},
        }
    return _SECTOR_PE_BENCHMARKS


_SECTOR_EV_EBITDA_BENCHMARKS = None

def _get_sector_ev_ebitda_benchmarks():
    global _SECTOR_EV_EBITDA_BENCHMARKS
    if _SECTOR_EV_EBITDA_BENCHMARKS is not None:
        return _SECTOR_EV_EBITDA_BENCHMARKS
    raw = get_config('valuation', 'sector_ev_ebitda_benchmarks')
    if raw:
        _SECTOR_EV_EBITDA_BENCHMARKS = {}
        for sector, data in raw.items():
            norm = sector.replace('_', ' ')
            _SECTOR_EV_EBITDA_BENCHMARKS[norm] = {
                'cheap': data.get('range', [6, 15])[0],
                'expensive': data.get('range', [6, 15])[1],
            }
    else:
        _SECTOR_EV_EBITDA_BENCHMARKS = {
            'Technology': {'cheap': 8, 'expensive': 20},
            'Healthcare': {'cheap': 8, 'expensive': 20},
            'Financials': {'cheap': 5, 'expensive': 12},
            'Utilities': {'cheap': 5, 'expensive': 12},
            'Industrials': {'cheap': 6, 'expensive': 15},
            'Energy': {'cheap': 4, 'expensive': 10},
            'Consumer Staples': {'cheap': 6, 'expensive': 15},
            'Consumer Discretionary': {'cheap': 6, 'expensive': 15},
        }
    return _SECTOR_EV_EBITDA_BENCHMARKS
    raw = get_config('valuation', 'sector_pe_benchmarks')
    if raw:
        _SECTOR_PE_BENCHMARKS = {}
        for sector, data in raw.items():
            norm = sector.replace('_', ' ')
            _SECTOR_PE_BENCHMARKS[norm] = {
                'median': data.get('median', 15),
                'range': tuple(data.get('range', [10, 25])),
                'cheap': data.get('range', [10, 25])[0],
                'expensive': data.get('range', [10, 25])[1],
            }
    else:
        _SECTOR_PE_BENCHMARKS = {
            'Technology': {'median': 22, 'range': (15, 35), 'cheap': 15, 'expensive': 35},
            'Healthcare': {'median': 18, 'range': (12, 30), 'cheap': 12, 'expensive': 30},
            'Financials': {'median': 12, 'range': (8, 18), 'cheap': 8, 'expensive': 18},
            'Consumer Staples': {'median': 16, 'range': (12, 22), 'cheap': 12, 'expensive': 22},
            'Utilities': {'median': 14, 'range': (10, 18), 'cheap': 10, 'expensive': 18},
            'Industrials': {'median': 15, 'range': (10, 22), 'cheap': 10, 'expensive': 22},
            'Energy': {'median': 10, 'range': (6, 15), 'cheap': 6, 'expensive': 15},
            'Consumer Discretionary': {'median': 18, 'range': (12, 28), 'cheap': 12, 'expensive': 28},
        }
    return _SECTOR_PE_BENCHMARKS


def comprehensive_score_to_position(comprehensive_score: float) -> float:
    """
    Map 5-dimension comprehensive score to base target position %.
    This is the single source of truth for score→position mapping.
    Reads from config.yaml under overall.score_to_position.
    """
    score_map = get_config('overall', 'score_to_position', default=None)
    if score_map:
        for regime_name, params in sorted(
            score_map.items(),
            key=lambda x: x[1].get('min', 0),
            reverse=True
        ):
            if comprehensive_score >= params.get('min', 0):
                return params.get('position', 57.5)
    
    # Fallback hardcoded (matches config)
    if comprehensive_score >= 80:
        return 17.5
    elif comprehensive_score >= 70:
        return 32.5
    elif comprehensive_score >= 60:
        return 47.5
    elif comprehensive_score >= 40:
        return 57.5
    elif comprehensive_score >= 30:
        return 72.5
    else:
        return 87.5


@dataclass
class StockData:
    """Container for stock data needed for analysis"""
    symbol: str
    prices: List[float]  # Historical closing prices (most recent last)
    volumes: Optional[List[float]] = None  # Historical volumes
    highs: Optional[List[float]] = None  # Historical high prices
    lows: Optional[List[float]] = None  # Historical low prices
    opens: Optional[List[float]] = None  # Historical open prices
    current_price: Optional[float] = None  # Current price
    market_cap: Optional[float] = None  # Market capitalization
    sector: Optional[str] = None  # Industry sector
    
    # Financial metrics
    eps: Optional[float] = None  # Earnings per share
    revenue: Optional[float] = None  # Total revenue
    ebitda: Optional[float] = None  # EBITDA
    net_income: Optional[float] = None  # Net income
    shareholders_equity: Optional[float] = None  # Shareholders' equity
    total_debt: Optional[float] = None  # Total debt
    cash: Optional[float] = None  # Cash and equivalents
    free_cash_flow: Optional[float] = None  # Free cash flow
    dividend_per_share: Optional[float] = None  # Dividend per share
    recurring_revenue_pct: Optional[float] = None  # Recurring revenue percentage (0-1)
    
    # Metadata
    _price_source: Optional[str] = None  # 'live_quote', 'kline_close_stale', or 'unavailable'
    
    # Growth metrics
    revenue_growth: Optional[float] = None  # Revenue growth rate
    eps_growth: Optional[float] = None  # EPS growth rate
    estimated_growth: Optional[float] = None  # Estimated future growth
    
    # Valuation metrics
    book_value_per_share: Optional[float] = None  # Book value per share
    
    def __post_init__(self):
        """Validate and set defaults"""
        if self.current_price is None and self.prices:
            self.current_price = self.prices[-1] if self.prices else None


@dataclass
class OptionPosition:
    """Container for an option position"""
    symbol: str
    underlying: str
    option_type: str  # 'call' or 'put'
    direction: str    # 'long' or 'short'
    strike: float
    expiry: str       # ISO date string e.g. '2027-01-15'
    quantity: float    # positive=long, negative=short (matches positions API)
    cost_price: float  # average cost per contract
    current_price: Optional[float] = None  # current premium
    multiplier: int = 100  # US options contract multiplier
    underlying_price: Optional[float] = None
    implied_volatility: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None

    @property
    def is_short(self) -> bool:
        return self.quantity < 0 or self.direction == 'short'

    @property
    def abs_quantity(self) -> float:
        return abs(self.quantity)

    @property
    def market_value(self) -> float:
        if self.current_price is None:
            return 0.0
        return self.current_price * self.abs_quantity * self.multiplier * (-1 if self.is_short else 1)

    @property
    def cost_basis(self) -> float:
        return self.cost_price * self.abs_quantity * self.multiplier

    @property
    def pnl(self) -> Optional[float]:
        if self.current_price is None:
            return None
        if self.is_short:
            return (self.cost_price - self.current_price) * self.abs_quantity * self.multiplier
        return (self.current_price - self.cost_price) * self.abs_quantity * self.multiplier

    @property
    def pnl_pct(self) -> Optional[float]:
        if self.pnl is None or self.cost_basis == 0:
            return None
        return (self.pnl / self.cost_basis) * 100

    @property
    def days_to_expiry(self) -> Optional[int]:
        try:
            expiry_date = datetime.strptime(self.expiry, '%Y-%m-%d')
            return (expiry_date - datetime.now()).days
        except (ValueError, TypeError):
            return None

    @property
    def is_itm(self) -> Optional[bool]:
        """Check if option is in-the-money. Requires underlying_price to be set, otherwise returns None."""
        if self.underlying_price is not None:
            return self.is_itm_with_price(self.underlying_price)
        return None

    def is_itm_with_price(self, underlying_price: float) -> bool:
        if self.option_type == 'put':
            return underlying_price < self.strike
        return underlying_price > self.strike

    @staticmethod
    def parse_symbol(symbol: str) -> Optional['OptionPosition']:
        """Parse an option symbol like BABA270115P120000.US into an OptionPosition.

        Pattern: {UNDERLYING}{YYMMDD}{C/P}{STRIKE*1000}.US
        e.g. BABA270115P120000.US -> underlying=BABA, expiry=2027-01-15, put, strike=120
        """
        import re
        base = symbol.replace('.US', '')
        m = re.match(r'^([A-Z]+)(\d{6})([CP])(\d+)$', base)
        if not m:
            return None
        underlying = m.group(1)
        date_str = m.group(2)
        opt_type = 'put' if m.group(3) == 'P' else 'call'
        strike_raw = m.group(4)
        strike = float(strike_raw) / 1000.0
        try:
            expiry = datetime.strptime(date_str, '%y%m%d').strftime('%Y-%m-%d')
        except ValueError:
            return None
        return OptionPosition(
            symbol=symbol,
            underlying=underlying,
            option_type=opt_type,
            direction='long',
            strike=strike,
            expiry=expiry,
            quantity=0,
            cost_price=0.0,
        )


class OptionAnalyzer:
    """Analyze option positions within a portfolio.

    Provides:
    - Position parsing from longbridge positions API
    - Greeks estimation (simplified BSM)
    - Risk metrics (max loss, break-even, probability of profit)
    - Integration with underlying stock analysis
    - Strategy identification (covered call, cash-secured put, etc.)
    """

    @staticmethod
    def parse_positions(positions: List[Dict]) -> List[OptionPosition]:
        """Parse raw positions list, separating options from stocks.

        Returns list of OptionPosition for option-type positions.
        """
        options = []
        for pos in positions:
            symbol = pos.get('symbol', '')
            parsed = OptionPosition.parse_symbol(symbol)
            if parsed is None:
                continue
            parsed.quantity = float(pos.get('quantity', 0))
            parsed.direction = 'short' if parsed.quantity < 0 else 'long'
            parsed.cost_price = float(pos.get('cost_price', 0))
            options.append(parsed)
        return options

    @staticmethod
    def estimate_greeks(
        option: OptionPosition,
        underlying_price: float,
        risk_free_rate: float = 0.04,
        implied_vol: Optional[float] = None,
    ) -> OptionPosition:
        """Estimate option Greeks using simplified Black-Scholes-Merton.

        If implied_vol is not provided, uses a heuristic based on moneyness and DTE.
        Returns the same OptionPosition with Greeks populated.
        """
        T = (option.days_to_expiry or 30) / 365.0
        if T <= 0:
            T = 1 / 365.0
        K = option.strike
        S = underlying_price
        r = risk_free_rate
        sigma = implied_vol or OptionAnalyzer._estimate_iv(option, S)

        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        from scipy.stats import norm as _norm

        if option.option_type == 'call':
            delta = _norm.cdf(d1)
        else:
            delta = _norm.cdf(d1) - 1

        gamma = _norm.pdf(d1) / (S * sigma * np.sqrt(T))
        theta = (-(S * _norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
                 - r * K * np.exp(-r * T) * _norm.cdf(d2 if option.option_type == 'call' else -d2))
        theta /= 365.0
        vega = S * _norm.pdf(d1) * np.sqrt(T) / 100

        if option.is_short:
            delta = -delta
            gamma = -gamma
            theta = -theta
            vega = -vega

        option.delta = round(delta, 4)
        option.gamma = round(gamma, 4)
        option.theta = round(theta, 4)
        option.vega = round(vega, 4)
        option.implied_volatility = sigma
        return option

    @staticmethod
    def _estimate_iv(option: OptionPosition, underlying_price: float) -> float:
        """Rough IV estimate based on moneyness and DTE for when no market IV is available."""
        moneyness = abs(underlying_price - option.strike) / option.strike
        dte = option.days_to_expiry or 30
        base = 0.35
        if dte < 30:
            base = 0.45
        elif dte > 180:
            base = 0.30
        if moneyness > 0.15:
            base += 0.05
        if moneyness > 0.30:
            base += 0.08
        return min(base, 1.0)

    @staticmethod
    def estimate_premium_bsm(
        option: OptionPosition,
        underlying_price: float,
        risk_free_rate: float = 0.04,
        implied_vol: Optional[float] = None,
    ) -> float:
        """Estimate option premium using BSM model."""
        T = max((option.days_to_expiry or 30) / 365.0, 1 / 365.0)
        K = option.strike
        S = underlying_price
        r = risk_free_rate
        sigma = implied_vol or OptionAnalyzer._estimate_iv(option, S)

        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        from scipy.stats import norm as _norm

        if option.option_type == 'call':
            premium = S * _norm.cdf(d1) - K * np.exp(-r * T) * _norm.cdf(d2)
        else:
            premium = K * np.exp(-r * T) * _norm.cdf(-d2) - S * _norm.cdf(-d1)
        return max(premium, 0.0)

    @staticmethod
    def analyze_option(option: OptionPosition, underlying_price: float) -> Dict:
        """Full analysis of a single option position.

        Returns dict with:
        - position_summary
        - risk_metrics (max_loss, break_even, prob_of_profit)
        - greeks
        - strategy_interpretation
        - recommendation
        """
        # Set underlying_price so that option.is_itm property works correctly
        option.underlying_price = underlying_price
        
        try:
            option = OptionAnalyzer.estimate_greeks(option, underlying_price)
        except ImportError:
            pass

        itm = option.is_itm_with_price(underlying_price)
        dte = option.days_to_expiry
        premium_est = OptionAnalyzer.estimate_premium_bsm(option, underlying_price)
        if option.current_price is None:
            option.current_price = round(premium_est, 2)

        moneyness = (underlying_price - option.strike) / option.strike
        if option.option_type == 'put':
            moneyness = -moneyness

        if option.is_short and option.option_type == 'put':
            max_loss = (option.strike - 0) * option.abs_quantity * option.multiplier - option.cost_basis
            break_even = option.strike - option.cost_price
            prob_profit = 1.0 - OptionAnalyzer._prob_short_put_itm(underlying_price, option.strike, dte or 30)
        elif option.is_short and option.option_type == 'call':
            max_loss = float('inf')
            break_even = option.strike + option.cost_price
            prob_profit = 1.0 - OptionAnalyzer._prob_short_call_itm(underlying_price, option.strike, dte or 30)
        elif not option.is_short and option.option_type == 'put':
            max_loss = option.strike * option.abs_quantity * option.multiplier - option.cost_basis
            break_even = option.strike - option.cost_price
            prob_profit = 1.0 - OptionAnalyzer._prob_short_put_itm(underlying_price, option.strike, dte or 30)
        else:
            max_loss = option.cost_basis
            break_even = option.strike + option.cost_price
            prob_profit = 1.0 - OptionAnalyzer._prob_short_call_itm(underlying_price, option.strike, dte or 30)

        strategy = OptionAnalyzer._identify_strategy(option)
        time_warning = OptionAnalyzer._time_decay_warning(option)

        recommendation = OptionAnalyzer._recommend_option(
            option, underlying_price, itm, prob_profit, dte
        )

        return {
            'symbol': option.symbol,
            'underlying': option.underlying,
            'option_type': option.option_type,
            'direction': option.direction,
            'strike': option.strike,
            'expiry': option.expiry,
            'days_to_expiry': dte,
            'quantity': option.quantity,
            'cost_price': option.cost_price,
            'current_price': option.current_price,
            'underlying_price': underlying_price,
            'is_itm': itm,
            'moneyness': round(moneyness, 4),
            'premium_estimated': round(premium_est, 2),
            'market_value': option.market_value,
            'cost_basis': option.cost_basis,
            'pnl': option.pnl,
            'pnl_pct': option.pnl_pct,
            'risk_metrics': {
                'max_loss': max_loss,
                'break_even': break_even,
                'prob_of_profit': round(prob_profit, 4),
            },
            'greeks': {
                'delta': option.delta,
                'gamma': option.gamma,
                'theta': option.theta,
                'vega': option.vega,
                'implied_volatility': option.implied_volatility,
            },
            'strategy': strategy,
            'time_decay_warning': time_warning,
            'recommendation': recommendation,
        }

    @staticmethod
    def _prob_short_put_itm(spot: float, strike: float, dte: int, iv: float = 0.35) -> float:
        """Approximate probability that spot < strike at expiry (put finishes ITM)."""
        try:
            from scipy.stats import norm
            T = dte / 365.0
            if T <= 0:
                return 1.0 if spot < strike else 0.0
            d2 = (np.log(spot / strike) + (0.04 - 0.5 * iv ** 2) * T) / (iv * np.sqrt(T))
            return norm.cdf(-d2)
        except ImportError:
            if spot > strike * 1.1:
                return 0.15
            elif spot > strike:
                return 0.35
            return 0.55

    @staticmethod
    def _prob_short_call_itm(spot: float, strike: float, dte: int, iv: float = 0.35) -> float:
        try:
            from scipy.stats import norm
            T = dte / 365.0
            if T <= 0:
                return 1.0 if spot > strike else 0.0
            d2 = (np.log(spot / strike) + (0.04 - 0.5 * iv ** 2) * T) / (iv * np.sqrt(T))
            return norm.cdf(d2)
        except ImportError:
            if spot < strike * 0.9:
                return 0.15
            elif spot < strike:
                return 0.35
            return 0.55

    @staticmethod
    def _identify_strategy(option: OptionPosition) -> Dict:
        """Identify the option strategy and explain it."""
        if option.is_short and option.option_type == 'put':
            return {
                'name': 'Cash-Secured Put (卖出看跌期权)',
                'description': f'卖出{option.underlying}的看跌期权，行权价${option.strike:.0f}，到期日{option.expiry}',
                'intent': '收取权利金，愿意在行权价买入正股',
                'ideal_outcome': '正股保持高于行权价，权利金全部收入',
                'risk_outcome': f'正股跌破${option.strike:.0f}，需以行权价买入100股/合约，最大亏损=行权价×数量',
                'bullish_or_bearish': '看涨/中性',
            }
        elif option.is_short and option.option_type == 'call':
            return {
                'name': 'Covered Call (备兑看涨期权)',
                'description': f'卖出{option.underlying}的看涨期权，行权价${option.strike:.0f}',
                'intent': '收取权利金增厚收益，限制上行空间',
                'ideal_outcome': '正股小幅上涨但不超行权价，权利金+正股收益',
                'risk_outcome': '正股大涨，需以行权价卖出正股，错失上行收益',
                'bullish_or_bearish': '中性/微看涨',
            }
        elif not option.is_short and option.option_type == 'call':
            return {
                'name': 'Long Call (买入看涨期权)',
                'description': f'买入{option.underlying}的看涨期权，行权价${option.strike:.0f}',
                'intent': '以有限风险博取正股上涨收益',
                'ideal_outcome': '正股大幅上涨，杠杆收益',
                'risk_outcome': '权利金全部损失',
                'bullish_or_bearish': '看涨',
            }
        else:
            return {
                'name': 'Long Put (买入看跌期权)',
                'description': f'买入{option.underlying}的看跌期权，行权价${option.strike:.0f}',
                'intent': '对冲下行风险或投机下跌',
                'ideal_outcome': '正股大幅下跌，杠杆收益',
                'risk_outcome': '权利金全部损失',
                'bullish_or_bearish': '看跌',
            }

    @staticmethod
    def _time_decay_warning(option: OptionPosition) -> Optional[str]:
        """Generate time decay warning if applicable."""
        dte = option.days_to_expiry
        if dte is None:
            return None
        if dte <= 0:
            return "EXPIRED - 期权已到期"
        if option.is_short:
            if dte <= 7:
                return f"⏰ 到期倒计时{dte}天 - 时间价值加速衰减，权利金收入已基本锁定"
            if dte <= 21:
                return f"⏰ 到期倒计时{dte}天 - theta衰减加快，卖方有利"
            return None
        else:
            if dte <= 7:
                return f"⚠️ 到期倒计时{dte}天 - 时间价值极速衰减，买方不利"
            if dte <= 21:
                return f"⚠️ 到期倒计时{dte}天 - theta衰减加速，考虑平仓或展期"
            return None

    @staticmethod
    def _recommend_option(
        option: OptionPosition,
        underlying_price: float,
        is_itm: bool,
        prob_profit: float,
        dte: Optional[int],
    ) -> Dict:
        """Generate recommendation for option position."""
        action = 'HOLD'
        urgency = 'LOW'
        reasons = []

        if option.is_short and option.option_type == 'put':
            distance_to_strike = (underlying_price - option.strike) / underlying_price

            if prob_profit > 0.75:
                action = 'HOLD'
                reasons.append(f'盈利概率{prob_profit:.0%}，继续持有收取权利金')
            elif prob_profit > 0.50:
                action = 'HOLD'
                urgency = 'MEDIUM'
                reasons.append(f'盈利概率{prob_profit:.0%}，尚可但需关注正股走势')
            else:
                action = 'CLOSE'
                urgency = 'HIGH'
                reasons.append(f'盈利概率仅{prob_profit:.0%}，建议提前平仓止损')

            if distance_to_strike < 0.05:
                urgency = 'HIGH'
                reasons.append(f'正股距行权价仅{distance_to_strike:.1%}，被行权风险高')

            if dte is not None and dte <= 14 and prob_profit > 0.6:
                reasons.append(f'剩余{dte}天到期，时间价值加速归零对卖方有利')

            if not is_itm and prob_profit > 0.60:
                reasons.append('当前OTM，正股需跌至行权价才会被行权，安全边际充足')

        elif not option.is_short:
            if is_itm and option.pnl is not None and option.pnl > 0:
                action = 'TAKE_PROFIT'
                reasons.append('当前ITM且有浮盈，考虑止盈')
            elif dte is not None and dte <= 14 and not is_itm:
                action = 'CLOSE'
                urgency = 'HIGH'
                reasons.append(f'剩余{dte}天到期且OTM，时间价值将归零')

        return {
            'action': action,
            'urgency': urgency,
            'reasons': reasons,
        }

    @staticmethod
    def generate_option_report(analysis: Dict) -> str:
        """Generate markdown report for a single option analysis."""
        a = analysis
        lines = []
        lines.append(f"### {a['symbol']} — {a['strategy']['name']}")
        lines.append('')
        lines.append(f"**方向:** {a['direction']} | **类型:** {a['option_type']} | **行权价:** ${a['strike']:.0f} | **到期日:** {a['expiry']}")
        lines.append(f"**正股价格:** ${a['underlying_price']:.2f} | **ITM:** {'是' if a['is_itm'] else '否'} | **距到期:** {a['days_to_expiry']}天")
        lines.append('')
        lines.append(f"**数量:** {a['quantity']} | **成本:** ${a['cost_price']:.2f}/合约 | **现价:** ${a['current_price']:.2f}/合约")
        lines.append(f"**市值:** ${a['market_value']:.2f} | **成本基数:** ${a['cost_basis']:.2f} | **盈亏:** ${a['pnl']:.2f} ({a['pnl_pct']:.1f}%)" if a['pnl'] is not None else f"**市值:** ${a['market_value']:.2f} | **成本基数:** ${a['cost_basis']:.2f}")
        lines.append('')

        lines.append('**风险指标:**')
        risk = a['risk_metrics']
        max_loss_str = f"${risk['max_loss']:,.0f}" if risk['max_loss'] != float('inf') else '无限'
        lines.append(f"- 最大亏损: {max_loss_str}")
        lines.append(f"- 盈亏平衡: ${risk['break_even']:.2f}")
        lines.append(f"- 盈利概率: {risk['prob_of_profit']:.1%}")
        lines.append('')

        greeks = a['greeks']
        if greeks.get('delta') is not None:
            lines.append('**Greeks:**')
            lines.append(f"- Delta: {greeks['delta']} | Gamma: {greeks['gamma']} | Theta: {greeks['theta']} | Vega: {greeks['vega']}")
            lines.append(f"- 隐含波动率: {greeks['implied_volatility']:.1%}" if greeks.get('implied_volatility') else '')
            lines.append('')

        strat = a['strategy']
        lines.append('**策略解读:**')
        lines.append(f"- {strat['intent']}")
        lines.append(f"- 最佳结果: {strat['ideal_outcome']}")
        lines.append(f"- 最差结果: {strat['risk_outcome']}")
        lines.append(f"- 方向: {strat['bullish_or_bearish']}")
        lines.append('')

        if a.get('time_decay_warning'):
            lines.append(f"**时间衰减:** {a['time_decay_warning']}")
            lines.append('')

        rec = a['recommendation']
        lines.append(f"**建议: {rec['action']}** (紧迫度: {rec['urgency']})")
        for r in rec['reasons']:
            lines.append(f"- {r}")
        lines.append('')

        return '\n'.join(lines)


class RiskMetricsCalculator:
    """Calculate risk metrics for stocks and portfolios"""
    
    @staticmethod
    def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.03, 
                              periods_per_year: int = 252) -> Optional[float]:
        """
        Calculate Sharpe Ratio for given return series
        
        Args:
            returns: List of periodic returns (e.g., daily)
            risk_free_rate: Annual risk-free rate (default 3%)
            periods_per_year: Number of periods in a year (252 for daily)
        
        Returns:
            sharpe_ratio: Annualized Sharpe Ratio
        """
        if len(returns) < 2:
            return None
        
        returns_array = np.array(returns)
        
        # Calculate excess returns
        excess_returns = returns_array - (risk_free_rate / periods_per_year)
        
        # Calculate annualized Sharpe Ratio
        mean_excess_return = np.mean(excess_returns)
        std_excess_return = np.std(excess_returns)
        
        if std_excess_return == 0:
            return None
        
        # Annualize
        sharpe_ratio = (mean_excess_return / std_excess_return) * np.sqrt(periods_per_year)
        
        return sharpe_ratio
    
    @staticmethod
    def calculate_max_drawdown(prices: List[float]) -> Tuple[Optional[float], Optional[int], Optional[int]]:
        """
        Calculate maximum drawdown from price series
        
        Args:
            prices: List/array of historical prices
        
        Returns:
            max_dd: Maximum drawdown (negative percentage)
            peak_idx: Index of peak before maximum drawdown
            trough_idx: Index of trough
        """
        if len(prices) < 2:
            return None, None, None
        
        prices_array = np.array(prices)
        
        # Calculate running maximum (peak)
        running_max = np.maximum.accumulate(prices_array)
        
        # Calculate drawdown series
        drawdown = (prices_array - running_max) / running_max
        
        # Find maximum drawdown
        max_dd_idx = np.argmin(drawdown)
        max_dd = drawdown[max_dd_idx]
        
        # Find peak before maximum drawdown
        peak_idx = np.argmax(prices_array[:max_dd_idx + 1])
        
        return max_dd, peak_idx, max_dd_idx
    
    @staticmethod
    def calculate_sortino_ratio(returns: List[float], risk_free_rate: float = 0.03,
                               periods_per_year: int = 252) -> Optional[float]:
        """
        Calculate Sortino Ratio for given return series
        
        Args:
            returns: List of periodic returns
            risk_free_rate: Annual risk-free rate
            periods_per_year: Number of periods in a year
        
        Returns:
            sortino_ratio: Annualized Sortino Ratio
        """
        if len(returns) < 2:
            return None
        
        returns_array = np.array(returns)
        
        # Calculate excess returns
        excess_returns = returns_array - (risk_free_rate / periods_per_year)
        
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
    
    @staticmethod
    def calculate_beta(stock_returns: List[float], market_returns: List[float]) -> Tuple[Optional[float], Optional[float]]:
        """
        Calculate beta coefficient for a stock
        
        Args:
            stock_returns: List of stock returns
            market_returns: List of market returns (e.g., S&P 500)
        
        Returns:
            beta: Beta coefficient
            r_squared: Goodness of fit
        """
        if len(stock_returns) != len(market_returns) or len(stock_returns) < 2:
            return None, None
        
        stock_returns_array = np.array(stock_returns)
        market_returns_array = np.array(market_returns)
        
        # Calculate covariance and variance
        covariance = np.cov(stock_returns_array, market_returns_array)[0, 1]
        market_variance = np.var(market_returns_array)
        
        if market_variance == 0:
            return None, None
        
        beta = covariance / market_variance
        
        # Calculate R-squared
        correlation = np.corrcoef(stock_returns_array, market_returns_array)[0, 1]
        r_squared = correlation ** 2
        
        return beta, r_squared
    
    @staticmethod
    def calculate_var(returns: List[float], confidence_level: float = 0.95, 
                     method: str = 'historical') -> Optional[float]:
        """
        Calculate Value at Risk
        
        Args:
            returns: List of returns
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            method: 'historical' or 'parametric'
        
        Returns:
            var: Value at Risk (negative percentage)
        """
        if len(returns) < 10:
            return None
        
        returns_array = np.array(returns)
        
        if method == 'historical':
            # Historical VaR
            percentile = 1 - confidence_level
            var = np.percentile(returns_array, percentile * 100)
            
        elif method == 'parametric':
            # Parametric VaR (assuming normal distribution)
            mean_return = np.mean(returns_array)
            std_return = np.std(returns_array)
            
            # Z-score for confidence level
            try:
                from scipy import stats
                z_score = stats.norm.ppf(1 - confidence_level)
            except ImportError:
                # Fallback approximation for common confidence levels
                z_scores = {0.90: -1.282, 0.95: -1.645, 0.99: -2.326}
                z_score = z_scores.get(confidence_level, -1.645)
            
            var = mean_return + z_score * std_return
        else:
            raise ValueError("Method must be 'historical' or 'parametric'")
        
        return var
    
    @staticmethod
    def calculate_historical_volatility(returns: List[float], periods_per_year: int = 252) -> Optional[float]:
        """
        Calculate annualized historical volatility
        
        Args:
            returns: List of periodic returns
            periods_per_year: Trading periods per year
        
        Returns:
            volatility: Annualized volatility (percentage)
        """
        if len(returns) < 2:
            return None
        
        returns_array = np.array(returns)
        volatility = np.std(returns_array) * np.sqrt(periods_per_year)
        
        return volatility
    
    @staticmethod
    def calculate_calmar_ratio(returns: List[float], prices: List[float], 
                              periods_per_year: int = 252) -> Optional[float]:
        """
        Calculate Calmar Ratio
        
        Args:
            returns: List of returns
            prices: List of prices (for drawdown calculation)
            periods_per_year: Trading periods per year
        
        Returns:
            calmar_ratio: Calmar Ratio
        """
        if len(returns) < 2 or len(prices) < 2:
            return None
        
        # Calculate annualized return
        total_return = (prices[-1] / prices[0]) - 1
        annualized_return = (1 + total_return) ** (periods_per_year / len(returns)) - 1
        
        # Calculate maximum drawdown
        max_dd, _, _ = RiskMetricsCalculator.calculate_max_drawdown(prices)
        
        if max_dd == 0:
            return None
        
        calmar_ratio = annualized_return / abs(max_dd)
        
        return calmar_ratio
    
    @staticmethod
    def calculate_comprehensive_risk_score(risk_metrics: Dict[str, float], 
                                         weights: Optional[Dict[str, float]] = None) -> Tuple[float, Dict]:
        """
        Calculate comprehensive risk score (0-100, higher = riskier)
        
        Args:
            risk_metrics: Dictionary of calculated risk metrics
            weights: Optional weights for each metric
        
        Returns:
            risk_score: Comprehensive risk score
            breakdown: Score breakdown by component
        """
        if weights is None:
            weights = get_config('risk', 'weights', default={
                'max_drawdown': 0.30,
                'volatility': 0.25,
                'beta': 0.20,
                'var': 0.15,
                'correlation': 0.10
            })
        
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
    
    @staticmethod
    def get_volatility_position_recommendation(volatility: float, base_position: float = None) -> Dict:
        """
        Get position size recommendation based on volatility.
        
        High volatility should lead to smaller position sizes, not avoidance.
        This allows participation in high-volatility opportunities while managing risk.
        
        Args:
            volatility: Annual volatility (e.g., 0.73 for 73%)
            base_position: Base position size (default from config, fallback 10%)
        
        Returns:
            {
                'recommended_position_size': float (0.0-1.0),
                'volatility_tier': 'VERY_HIGH' | 'HIGH' | 'MODERATE' | 'LOW',
                'risk_note': str,
                'stop_loss_recommendation': str,
                'expected_move_range': str
            }
        """
        if base_position is None:
            base_position = get_config('overall', 'position_sizing', 'base_position', default=0.10)
        max_pos = get_config('overall', 'position_sizing', 'max_position', default=0.15)
        min_pos = get_config('overall', 'position_sizing', 'min_position', default=0.02)
        tiers_config = get_config('overall', 'position_sizing', 'volatility_tiers', default={
            'very_high': 0.60, 'high': 0.40, 'moderate': 0.25, 'low': 0.25
        })
        if volatility > 0.60:  # >60% annual volatility
            tier = 'VERY_HIGH'
            position_mult = 0.5  # Reduce to 50% of base
            risk_note = 'Extremely volatile. Consider tight stop-losses and smaller position sizing.'
            stop_loss_pct = 8.0
            expected_move = '±10-15% typical daily moves possible'
        elif volatility > 0.40:  # 40-60%
            tier = 'HIGH'
            position_mult = 0.7  # Reduce to 70% of base
            risk_note = 'High volatility. Use position sizing and stop-losses to manage risk.'
            stop_loss_pct = 10.0
            expected_move = '±7-10% daily moves common'
        elif volatility > 0.25:  # 25-40%
            tier = 'MODERATE'
            position_mult = 1.0  # Normal position
            risk_note = 'Moderate volatility. Standard position sizing appropriate.'
            stop_loss_pct = 12.0
            expected_move = '±4-6% typical daily range'
        else:  # <25%
            tier = 'LOW'
            position_mult = 1.2  # Can increase position slightly
            risk_note = 'Low volatility. May consider larger position if conviction is high.'
            stop_loss_pct = 15.0
            expected_move = '±2-4% daily range'
        
        recommended_position = base_position * position_mult
        recommended_position = max(0.02, min(0.15, recommended_position))  # Clamp to 2-15%
        
        return {
            'recommended_position_size': round(recommended_position, 3),
            'volatility_tier': tier,
            'risk_note': risk_note,
            'stop_loss_recommendation': f'{stop_loss_pct:.1f}% stop-loss recommended',
            'expected_move_range': expected_move,
            'position_multiplier': position_mult
        }
    
    @staticmethod
    def analyze_stock_risk(stock_data: StockData, market_returns: Optional[List[float]] = None) -> Dict:
        """
        Comprehensive risk analysis for a stock
        
        Args:
            stock_data: StockData object with price history
            market_returns: Optional market returns for beta calculation
        
        Returns:
            risk_analysis: Dictionary with all risk metrics
        """
        # Calculate returns from prices
        if len(stock_data.prices) < 2:
            return {"error": "Insufficient price data"}
        
        returns = []
        for i in range(1, len(stock_data.prices)):
            daily_return = (stock_data.prices[i] - stock_data.prices[i-1]) / stock_data.prices[i-1]
            returns.append(daily_return)
        
        # Calculate risk metrics
        sharpe_ratio = RiskMetricsCalculator.calculate_sharpe_ratio(returns)
        max_drawdown, peak_idx, trough_idx = RiskMetricsCalculator.calculate_max_drawdown(stock_data.prices)
        sortino_ratio = RiskMetricsCalculator.calculate_sortino_ratio(returns)
        historical_vol = RiskMetricsCalculator.calculate_historical_volatility(returns)
        var_95 = RiskMetricsCalculator.calculate_var(returns, confidence_level=0.95)
        calmar_ratio = RiskMetricsCalculator.calculate_calmar_ratio(returns, stock_data.prices)
        
        # Calculate beta if market returns provided
        beta = r_squared = None
        if market_returns and len(market_returns) == len(returns):
            beta, r_squared = RiskMetricsCalculator.calculate_beta(returns, market_returns)
        
        # Prepare metrics for risk score calculation
        risk_metrics_dict = {
            'max_drawdown': abs(max_drawdown) if max_drawdown else 0,
            'volatility': historical_vol if historical_vol else 0,
            'beta': beta if beta else 1.0,
            'var_95': abs(var_95) if var_95 else 0,
            'avg_correlation': 0.5  # Default, should be calculated from portfolio context
        }
        
        risk_score, risk_breakdown = RiskMetricsCalculator.calculate_comprehensive_risk_score(risk_metrics_dict)
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'max_drawdown_peak_idx': peak_idx,
            'max_drawdown_trough_idx': trough_idx,
            'sortino_ratio': sortino_ratio,
            'beta': beta,
            'r_squared': r_squared,
            'var_95': var_95,
            'historical_volatility': historical_vol,
            'calmar_ratio': calmar_ratio,
            'risk_score': risk_score,
            'risk_breakdown': risk_breakdown,
            'returns_volatility': np.std(returns) if returns else None,
            'returns_mean': np.mean(returns) if returns else None
        }


class ValuationMetricsCalculator:
    """Calculate valuation metrics for stocks"""
    
    @staticmethod
    def calculate_pe_ratio(price: float, eps: float, sector: Optional[str] = None) -> Tuple[Optional[float], Optional[str]]:
        """
        Calculate P/E ratio with sector context
        
        Args:
            price: Current stock price
            eps: Earnings per share (trailing or forward)
            sector: Industry sector for comparison
        
        Returns:
            pe_ratio: P/E ratio
            percentile: Percentile vs sector ('Low', 'Average', 'High')
        """
        if eps <= 0:
            return None, None
        
        pe_ratio = price / eps
        
        sector_benchmarks = _get_sector_pe_benchmarks()
        
        percentile = None
        if pe_ratio and sector and sector in sector_benchmarks:
            bench = sector_benchmarks[sector]
            if pe_ratio < bench['range'][0]:
                percentile = 'Low'
            elif pe_ratio > bench['range'][1]:
                percentile = 'High'
            else:
                percentile = 'Average'
        
        return pe_ratio, percentile
    
    @staticmethod
    def calculate_ev_ebitda(market_cap: float, debt: float, cash: float, ebitda: float) -> Optional[float]:
        """
        Calculate EV/EBITDA ratio
        
        Args:
            market_cap: Market capitalization
            debt: Total debt
            cash: Cash and equivalents
            ebitda: EBITDA
        
        Returns:
            ev_ebitda: EV/EBITDA ratio
        """
        enterprise_value = market_cap + debt - cash
        
        if ebitda <= 0:
            return None
        
        ev_ebitda = enterprise_value / ebitda
        return ev_ebitda
    
    @staticmethod
    def calculate_peg_ratio(pe_ratio: float, growth_rate: float) -> Optional[float]:
        """
        Calculate PEG ratio
        
        Args:
            pe_ratio: Current P/E ratio
            growth_rate: Expected annual earnings growth rate (decimal)
        
        Returns:
            peg_ratio: PEG ratio
        """
        if growth_rate <= 0:
            return None
        
        peg_ratio = pe_ratio / (growth_rate * 100)  # Convert growth to percentage
        return peg_ratio
    
    @staticmethod
    def calculate_fcf_yield(free_cash_flow: float, market_cap: float) -> Optional[float]:
        """
        Calculate Free Cash Flow Yield
        
        Args:
            free_cash_flow: Free cash flow
            market_cap: Market capitalization
        
        Returns:
            fcf_yield: FCF Yield (percentage)
        """
        if market_cap <= 0:
            return None
        
        fcf_yield = free_cash_flow / market_cap
        return fcf_yield
    
    @staticmethod
    def calculate_graham_intrinsic_value(eps: float, growth_rate: float, bond_yield: float) -> Optional[float]:
        """
        Calculate Graham intrinsic value
        
        Args:
            eps: Earnings per share
            growth_rate: Expected growth rate (decimal)
            bond_yield: Current AAA corporate bond yield (decimal)
        
        Returns:
            intrinsic_value: Graham intrinsic value
        """
        if bond_yield <= 0:
            return None
        
        # Original formula
        base_value = eps * (8.5 + 2 * growth_rate * 100)  # Convert growth to percentage
        
        # Adjust for bond yield
        intrinsic_value = (base_value * 4.4) / (bond_yield * 100)
        
        return intrinsic_value
    
    @staticmethod
    def calculate_valuation_score(valuation_metrics: Dict[str, float], sector: Optional[str] = None) -> Tuple[float, Dict]:
        """
        Calculate comprehensive valuation score (0-100, lower = more undervalued)
        
        Sector-adjusted: AI/tech stocks have naturally higher PE ratios.
        Uses sector-specific thresholds when sector is provided.

        Args:
            valuation_metrics: Dictionary of valuation metrics
            sector: Industry sector for context

        Returns:
            score: Valuation score (0-100)
            breakdown: Score breakdown by metric
        """
        scores = {}
        is_tech = sector and sector.lower() in ('technology', 'ai', 'semiconductor', 'software', 'internet')
        
        pe_thresholds = [
            (10, 20), (15, 40), (25, 60), (40, 80)
        ] if is_tech else [
            (10, 20), (15, 40), (20, 60), (30, 80)
        ]
        
        pe_ratio = valuation_metrics.get('pe_ratio')
        if pe_ratio:
            if pe_ratio < 0:
                scores['pe'] = 80
            else:
                score_val = 100
                for threshold, score in pe_thresholds:
                    if pe_ratio < threshold:
                        score_val = score
                        break
                scores['pe'] = score_val
        
        peg_ratio = valuation_metrics.get('peg_ratio')
        if peg_ratio:
            if peg_ratio < 0.5:
                scores['peg'] = 20
            elif peg_ratio < 1.0:
                scores['peg'] = 40
            elif peg_ratio < 1.5:
                scores['peg'] = 60
            elif peg_ratio < 2.0:
                scores['peg'] = 80
            else:
                scores['peg'] = 100
        
        p_fcf = valuation_metrics.get('p_fcf_ratio')
        if p_fcf:
            if p_fcf < 10:
                scores['p_fcf'] = 20
            elif p_fcf < 15:
                scores['p_fcf'] = 40
            elif p_fcf < 20:
                scores['p_fcf'] = 60
            elif p_fcf < 25:
                scores['p_fcf'] = 80
            else:
                scores['p_fcf'] = 100
        
        ev_ebitda = valuation_metrics.get('ev_ebitda_ratio')
        if ev_ebitda:
            if ev_ebitda < 6:
                scores['ev_ebitda'] = 20
            elif ev_ebitda < 10:
                scores['ev_ebitda'] = 40
            elif ev_ebitda < 15:
                scores['ev_ebitda'] = 60
            elif ev_ebitda < 20:
                scores['ev_ebitda'] = 80
            else:
                scores['ev_ebitda'] = 100
        
        # 5. DCF Margin of Safety (0-100)
        dcf_mos = valuation_metrics.get('dcf_margin_of_safety')
        if dcf_mos:
            if dcf_mos > 0.30:  # >30% discount to DCF
                scores['dcf'] = 20
            elif dcf_mos > 0.15:  # 15-30% discount
                scores['dcf'] = 40
            elif dcf_mos > -0.10:  # -10% to +15%
                scores['dcf'] = 60
            elif dcf_mos > -0.25:  # -25% to -10%
                scores['dcf'] = 80
            else:  # >25% premium
                scores['dcf'] = 100
        
        # Calculate weighted average score
        weights = get_config('valuation', 'weights', default={
            'pe': 0.20,
            'peg': 0.25,
            'p_fcf': 0.20,
            'ev_ebitda': 0.20,
            'dcf': 0.15
        })
        
        total_score = 0
        total_weight = 0
        breakdown = {}
        
        for metric, weight in weights.items():
            if metric in scores:
                total_score += scores[metric] * weight
                total_weight += weight
                breakdown[metric] = {
                    'score': scores[metric],
                    'weight': weight,
                    'contribution': scores[metric] * weight
                }
        
        if total_weight > 0:
            final_score = total_score / total_weight
        else:
            final_score = 50  # Neutral if no metrics available
        
        return final_score, breakdown
    
    @staticmethod
    def analyze_stock_valuation(stock_data: StockData, bond_yield: float = 0.04) -> Dict:
        """
        Comprehensive valuation analysis for a stock
        
        Args:
            stock_data: StockData object with financial metrics
            bond_yield: Current AAA corporate bond yield (default 4%)
        
        Returns:
            valuation_analysis: Dictionary with all valuation metrics
        """
        if stock_data.current_price is None:
            return {"error": "Current price required"}
        
        analysis = {}
        
        # Calculate P/E ratio
        if stock_data.eps and stock_data.eps > 0:
            pe_ratio, pe_percentile = ValuationMetricsCalculator.calculate_pe_ratio(
                stock_data.current_price, stock_data.eps, stock_data.sector
            )
            analysis['pe_ratio'] = pe_ratio
            analysis['pe_percentile'] = pe_percentile
        
        # Calculate EV/EBITDA
        if all([stock_data.market_cap is not None, stock_data.total_debt is not None, 
                stock_data.cash is not None, stock_data.ebitda is not None]):
            ev_ebitda = ValuationMetricsCalculator.calculate_ev_ebitda(
                stock_data.market_cap, stock_data.total_debt, stock_data.cash, stock_data.ebitda
            )
            analysis['ev_ebitda_ratio'] = ev_ebitda
        
        # Calculate PEG ratio
        if 'pe_ratio' in analysis and stock_data.estimated_growth:
            peg_ratio = ValuationMetricsCalculator.calculate_peg_ratio(
                analysis['pe_ratio'], stock_data.estimated_growth
            )
            analysis['peg_ratio'] = peg_ratio
        
        # Calculate P/FCF ratio
        if stock_data.market_cap and stock_data.free_cash_flow and stock_data.free_cash_flow > 0:
            p_fcf_ratio = stock_data.market_cap / stock_data.free_cash_flow
            analysis['p_fcf_ratio'] = p_fcf_ratio
        
        # Calculate FCF Yield
        if stock_data.market_cap and stock_data.free_cash_flow:
            fcf_yield = ValuationMetricsCalculator.calculate_fcf_yield(
                stock_data.free_cash_flow, stock_data.market_cap
            )
            analysis['fcf_yield'] = fcf_yield
        
        # Calculate Graham intrinsic value
        if stock_data.eps and stock_data.estimated_growth:
            graham_value = ValuationMetricsCalculator.calculate_graham_intrinsic_value(
                stock_data.eps, stock_data.estimated_growth, bond_yield
            )
            analysis['graham_intrinsic_value'] = graham_value
            
            if graham_value and stock_data.current_price:
                graham_mos = (graham_value - stock_data.current_price) / graham_value
                analysis['graham_margin_of_safety'] = graham_mos
        
        # Calculate P/B ratio
        if stock_data.current_price and stock_data.shareholders_equity:
            # Need shares outstanding for book value per share
            # For now, use market cap / shareholders equity
            if stock_data.market_cap:
                p_b_ratio = stock_data.market_cap / stock_data.shareholders_equity
                analysis['p_b_ratio'] = p_b_ratio
        
        # Calculate dividend yield
        if stock_data.dividend_per_share and stock_data.current_price:
            dividend_yield = stock_data.dividend_per_share / stock_data.current_price
            analysis['dividend_yield'] = dividend_yield
        
        # Calculate valuation score
        valuation_score, score_breakdown = ValuationMetricsCalculator.calculate_valuation_score(
            analysis, stock_data.sector
        )
        analysis['valuation_score'] = valuation_score
        analysis['valuation_breakdown'] = score_breakdown
        
        # Determine valuation attractiveness
        if valuation_score <= 30:
            analysis['valuation_attractiveness'] = 'Significantly Undervalued'
        elif valuation_score <= 50:
            analysis['valuation_attractiveness'] = 'Undervalued'
        elif valuation_score <= 70:
            analysis['valuation_attractiveness'] = 'Fairly Valued'
        elif valuation_score <= 90:
            analysis['valuation_attractiveness'] = 'Overvalued'
        else:
            analysis['valuation_attractiveness'] = 'Significantly Overvalued'
        
        return analysis


class TechnicalIndicatorsCalculator:
    """Calculate technical indicators for stocks"""
    
    @staticmethod
    def calculate_moving_averages(prices: List[float], periods: List[int] = [20, 50, 200], 
                                 ma_type: str = 'sma') -> Dict[int, List[Optional[float]]]:
        """
        Calculate moving averages
        
        Args:
            prices: List of closing prices
            periods: List of period lengths
            ma_type: 'sma' or 'ema'
        
        Returns:
            ma_dict: Dictionary of moving averages by period
        """
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
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> Optional[List[float]]:
        """
        Calculate RSI indicator
        
        Args:
            prices: List of closing prices
            period: RSI period (default 14)
        
        Returns:
            rsi: List of RSI values
        """
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
    
    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
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
        # Calculate EMAs
        ema_fast_dict = TechnicalIndicatorsCalculator.calculate_moving_averages(prices, [fast], 'ema')
        ema_slow_dict = TechnicalIndicatorsCalculator.calculate_moving_averages(prices, [slow], 'ema')
        
        if fast not in ema_fast_dict or slow not in ema_slow_dict:
            return {}
        
        ema_fast = ema_fast_dict[fast]
        ema_slow = ema_slow_dict[slow]
        
        # Calculate MACD line
        macd_line = []
        for i in range(len(prices)):
            if ema_fast[i] is None or ema_slow[i] is None:
                macd_line.append(None)
            else:
                macd_line.append(ema_fast[i] - ema_slow[i])
        
        # Calculate Signal line (EMA of MACD)
        # Filter out None values for calculation
        macd_line_valid = [x for x in macd_line if x is not None]
        if not macd_line_valid:
            return {}
        
        signal_line_dict = TechnicalIndicatorsCalculator.calculate_moving_averages(
            macd_line_valid, [signal], 'ema'
        )
        
        if signal not in signal_line_dict:
            return {}
        
        signal_line = signal_line_dict[signal]
        
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
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, num_std: float = 2) -> Dict:
        """
        Calculate Bollinger Bands
        
        Args:
            prices: List of closing prices
            period: SMA period (default 20)
            num_std: Number of standard deviations (default 2)
        
        Returns:
            bb_dict: Dictionary with Bollinger Band components
        """
        if len(prices) < period:
            return {}
        
        sma_dict = TechnicalIndicatorsCalculator.calculate_moving_averages(prices, [period], 'sma')
        if period not in sma_dict:
            return {}
        
        sma = sma_dict[period]
        
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
    
    @staticmethod
    def calculate_stochastic(highs: List[float], lows: List[float], closes: List[float], 
                            k_period: int = 14, d_period: int = 3) -> Optional[Dict]:
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
    
    @staticmethod
    def calculate_atr(highs: List[float], lows: List[float], closes: List[float], 
                     period: int = 14) -> Optional[List[Optional[float]]]:
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
    
    @staticmethod
    def calculate_technical_score(indicators: Dict, current_price: float) -> Tuple[float, Dict]:
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
        trend_score = TechnicalIndicatorsCalculator._evaluate_trend_score(indicators)
        scores['trend'] = trend_score
        
        # 2. Momentum Score (0-100)
        momentum_score = TechnicalIndicatorsCalculator._evaluate_momentum_score(indicators)
        scores['momentum'] = momentum_score
        
        # 3. Volume Score (0-100)
        volume_score = TechnicalIndicatorsCalculator._evaluate_volume_score(indicators)
        scores['volume'] = volume_score
        
        # 4. Volatility Score (0-100)
        volatility_score = TechnicalIndicatorsCalculator._evaluate_volatility_score(indicators)
        scores['volatility'] = volatility_score
        
        # 5. Support/Resistance Score (0-100)
        sr_score = TechnicalIndicatorsCalculator._evaluate_support_resistance_score(indicators, current_price)
        scores['support_resistance'] = sr_score
        
        # Calculate weighted average
        weights = get_config('technical', 'weights', default={
            'trend': 0.30,
            'momentum': 0.25,
            'volume': 0.20,
            'volatility': 0.15,
            'support_resistance': 0.10
        })
        
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
    
    @staticmethod
    def _evaluate_trend_score(indicators: Dict) -> float:
        """Evaluate trend strength and direction"""
        score = 50  # Neutral
        
        # Check moving averages
        ma_keys = [key for key in indicators.keys() if key.startswith('ma_')]
        
        if 'ma_50' in indicators and 'ma_200' in indicators:
            ma_50 = indicators['ma_50'][-1] if indicators['ma_50'] else None
            ma_200 = indicators['ma_200'][-1] if indicators['ma_200'] else None
            
            if ma_50 and ma_200:
                if ma_50 > ma_200:
                    score += 20  # Bullish (Golden Cross)
                else:
                    score -= 20  # Bearish (Death Cross)
        
        return max(0, min(100, score))
    
    @staticmethod
    def calculate_price_roc(prices: List[float], periods: List[int] = [5, 10, 21]) -> Dict[int, float]:
        """Calculate price Rate of Change (RoC) over multiple periods. Returns {period: roc_pct}."""
        result = {}
        for period in periods:
            if len(prices) > period and prices[-period - 1] != 0:
                roc = (prices[-1] - prices[-period - 1]) / prices[-period - 1] * 100
                result[period] = roc
            else:
                result[period] = None
        return result
    
    @staticmethod
    def calculate_trend_strength(prices: List[float], period: int = 14) -> float:
        """Calculate directional trend strength (0-100). Uses simplified ADX-like approach."""
        if len(prices) < period + 1:
            return 50.0
        ups = []
        downs = []
        for i in range(-period, 0):
            change = prices[i] - prices[i-1] if i > -len(prices) else 0
            ups.append(max(change, 0))
            downs.append(max(-change, 0))
        avg_up = sum(ups) / period
        avg_down = sum(downs) / period
        if avg_up + avg_down == 0:
            return 50.0
        di_plus = (avg_up / (avg_up + avg_down)) * 100
        return min(100, di_plus)
    
    @staticmethod
    def _evaluate_momentum_score(indicators: Dict) -> float:
        """
        Evaluate momentum indicators with enhanced RSI oversold handling.
        
        RSI Scoring Logic:
        - Extreme oversold (RSI < 20): +40 (strong buy signal)
        - Deep oversold (RSI 20-30): +30 (buy signal)
        - Oversold (RSI 30-35): +15 (potential opportunity)
        - Neutral (RSI 35-65): momentum enhancement applied (NEW)
        - Overbought (RSI 65-70): -10
        - Overbought (RSI 70-80): -20
        - Extreme overbought (RSI > 80): -30 (strong sell signal)
        
        NEW: When RSI is neutral (35-65), apply price momentum and trend
        strength bonuses to distinguish stocks poised to rally vs. decline.
        This fixes the COIN.US misjudgment where neutral RSI missed a +20.8% rally.
        """
        score = 50
        momentum_bonus = 0
        
        rsi = None
        if 'rsi' in indicators and indicators['rsi'] and indicators['rsi'][-1]:
            rsi = indicators['rsi'][-1]
            
            if rsi < 20:
                score += 40  # Extreme oversold - strong buy signal
            elif rsi < 30:
                score += 30  # Deep oversold - buy signal
            elif rsi < 35:
                score += 15  # Oversold - potential opportunity
            elif rsi < 65:
                pass  # Neutral range - momentum enhancement below
            elif rsi < 70:
                score -= 10  # Approaching overbought
            elif rsi < 80:
                score -= 20  # Overbought
            else:
                score -= 30  # Extreme overbought - strong sell signal
        
        # NEW: Momentum enhancement for neutral RSI zone (35-65)
        # This is the fix for COIN.US misjudgment - neutral RSI doesn't mean no momentum
        if rsi is not None and 35 <= rsi <= 65:
            roc = indicators.get('_price_roc', {})
            trend_strength = indicators.get('_trend_strength', 50.0)
            
            # Price rate of change signals
            roc_5 = roc.get(5)
            roc_10 = roc.get(10)
            roc_21 = roc.get(21)
            
            if roc_5 is not None:
                if roc_5 > 5:
                    momentum_bonus += 10  # Strong short-term momentum
                elif roc_5 > 2:
                    momentum_bonus += 5
                elif roc_5 < -5:
                    momentum_bonus -= 10
                elif roc_5 < -2:
                    momentum_bonus -= 5
            
            if roc_10 is not None:
                if roc_10 > 8:
                    momentum_bonus += 8  # Strong medium-term trend
                elif roc_10 > 4:
                    momentum_bonus += 4
                elif roc_10 < -8:
                    momentum_bonus -= 8
                elif roc_10 < -4:
                    momentum_bonus -= 4
            
            if roc_21 is not None:
                if roc_21 > 12:
                    momentum_bonus += 5  # Sustained uptrend
                elif roc_21 < -12:
                    momentum_bonus -= 5
            
            # Trend strength: strong trends get bonus in their direction
            if trend_strength > 70:
                momentum_bonus += 6  # Strong bullish directional movement
            elif trend_strength > 60:
                momentum_bonus += 3
            elif trend_strength < 30:
                momentum_bonus -= 6  # Strong bearish directional movement
            elif trend_strength < 40:
                momentum_bonus -= 3
        
        score += momentum_bonus
        
        if 'macd_line' in indicators and 'signal_line' in indicators:
            macd = indicators['macd_line'][-1] if indicators['macd_line'] else None
            signal = indicators['signal_line'][-1] if indicators['signal_line'] else None
            
            if macd and signal:
                if macd > signal:
                    score += 15
                else:
                    score -= 15
        
        return max(0, min(100, score))
    
    @staticmethod
    def get_rsi_signal(rsi: float) -> Dict[str, any]:
        """
        Get detailed RSI signal information.
        
        Args:
            rsi: RSI value (0-100)
        
        Returns:
            {
                'signal': 'STRONG_BUY' | 'BUY' | 'OPPORTUNITY' | 'NEUTRAL' | 'CAUTION' | 'SELL' | 'STRONG_SELL',
                'label': 'EXTREME OVERSOLD' | 'DEEP OVERSOLD' | ...,
                'score_adjustment': +40 | +30 | +15 | 0 | -10 | -20 | -30,
                'confidence': 'HIGH' | 'MEDIUM' | 'LOW'
            }
        """
        if rsi < 20:
            return {
                'signal': 'STRONG_BUY',
                'label': 'EXTREME OVERSOLD',
                'score_adjustment': 40,
                'confidence': 'HIGH'
            }
        elif rsi < 30:
            return {
                'signal': 'BUY',
                'label': 'DEEP OVERSOLD',
                'score_adjustment': 30,
                'confidence': 'HIGH'
            }
        elif rsi < 35:
            return {
                'signal': 'OPPORTUNITY',
                'label': 'OVERSOLD',
                'score_adjustment': 15,
                'confidence': 'MEDIUM'
            }
        elif rsi > 80:
            return {
                'signal': 'STRONG_SELL',
                'label': 'EXTREME OVERBOUGHT',
                'score_adjustment': -30,
                'confidence': 'HIGH'
            }
        elif rsi > 70:
            return {
                'signal': 'SELL',
                'label': 'OVERBOUGHT',
                'score_adjustment': -20,
                'confidence': 'HIGH'
            }
        elif rsi > 65:
            return {
                'signal': 'CAUTION',
                'label': 'APPROACHING OVERBOUGHT',
                'score_adjustment': -10,
                'confidence': 'MEDIUM'
            }
        else:
            return {
                'signal': 'NEUTRAL',
                'label': 'NEUTRAL',
                'score_adjustment': 0,
                'confidence': 'LOW'
            }
    
    @staticmethod
    def _evaluate_volume_score(indicators: Dict) -> float:
        """Evaluate volume indicators"""
        score = 50
        
        # Check volume vs average
        if 'volume' in indicators and 'volume_avg' in indicators:
            volume = indicators['volume'][-1] if indicators['volume'] else None
            volume_avg = indicators['volume_avg']
            
            if volume and volume_avg:
                volume_ratio = volume / volume_avg
                if volume_ratio > 1.5:
                    score += 20  # High volume (breakout potential)
                elif volume_ratio < 0.5:
                    score -= 10  # Low volume (lack of interest)
        
        return max(0, min(100, score))
    
    @staticmethod
    def _evaluate_volatility_score(indicators: Dict) -> float:
        """Evaluate volatility conditions"""
        score = 50
        
        # Check Bollinger Band width
        if 'bb_bandwidth' in indicators and indicators['bb_bandwidth'] and indicators['bb_bandwidth'][-1]:
            bandwidth = indicators['bb_bandwidth'][-1]
            
            # Historical bandwidth percentile
            if bandwidth > 0.10:  # High volatility
                score += 15  # Breakout potential
            elif bandwidth < 0.03:  # Low volatility (squeeze)
                score += 10  # Potential big move coming
        
        return max(0, min(100, score))
    
    @staticmethod
    def identify_support_resistance(highs: List[float], lows: List[float], closes: List[float],
                                     lookback: int = 90, min_touches: int = 2) -> Dict:
        """
        Identify key support and resistance levels using swing points and pivot points.
        
        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of closing prices
            lookback: Number of days to analyze (default 90)
            min_touches: Minimum touches to confirm level (default 2)
        
        Returns:
            {
                'support_levels': [{'price': 115.0, 'strength': 3, 'touches': 4}, ...],
                'resistance_levels': [{'price': 130.0, 'strength': 4, 'touches': 5}, ...],
                'nearest_support': {'price': 115.0, 'distance_pct': 3.2},
                'nearest_resistance': {'price': 130.0, 'distance_pct': 8.5},
                'price_gaps': [
                    {'type': 'up', 'from': 115, 'to': 120, 'age': 14, 'filled': False},
                    ...
                ]
            }
        """
        if len(closes) < lookback:
            lookback = len(closes)
        
        recent_highs = highs[-lookback:]
        recent_lows = lows[-lookback:]
        recent_closes = closes[-lookback:]
        current_price = recent_closes[-1]
        
        # Find swing highs and lows
        swing_highs = []
        swing_lows = []
        
        for i in range(2, len(recent_highs) - 2):
            # Swing high: high is higher than 2 bars on each side
            if (recent_highs[i] > recent_highs[i-1] and recent_highs[i] > recent_highs[i-2] and
                recent_highs[i] > recent_highs[i+1] and recent_highs[i] > recent_highs[i+2]):
                swing_highs.append(recent_highs[i])
            
            # Swing low: low is lower than 2 bars on each side
            if (recent_lows[i] < recent_lows[i-1] and recent_lows[i] < recent_lows[i-2] and
                recent_lows[i] < recent_lows[i+1] and recent_lows[i] < recent_lows[i+2]):
                swing_lows.append(recent_lows[i])
        
        # Cluster similar price levels
        def cluster_levels(levels, tolerance=0.02):
            """Group similar price levels"""
            if not levels:
                return []
            
            sorted_levels = sorted(levels)
            clusters = []
            current_cluster = [sorted_levels[0]]
            
            for level in sorted_levels[1:]:
                if abs(level - current_cluster[0]) / current_cluster[0] <= tolerance:
                    current_cluster.append(level)
                else:
                    # Calculate average and count touches
                    avg_price = sum(current_cluster) / len(current_cluster)
                    clusters.append({
                        'price': round(avg_price, 2),
                        'touches': len(current_cluster),
                        'strength': min(5, len(current_cluster))
                    })
                    current_cluster = [level]
            
            # Add last cluster
            if current_cluster:
                avg_price = sum(current_cluster) / len(current_cluster)
                clusters.append({
                    'price': round(avg_price, 2),
                    'touches': len(current_cluster),
                    'strength': min(5, len(current_cluster))
                })
            
            return clusters
        
        support_levels = cluster_levels(swing_lows, tolerance=get_config('technical', 'support_resistance', 'cluster_tolerance', default=0.015))
        resistance_levels = cluster_levels(swing_highs, tolerance=get_config('technical', 'support_resistance', 'cluster_tolerance', default=0.015))
        
        # Sort by strength
        support_levels = sorted(support_levels, key=lambda x: x['strength'], reverse=True)[:5]
        resistance_levels = sorted(resistance_levels, key=lambda x: x['strength'], reverse=True)[:5]
        
        # Find nearest support and resistance
        nearest_support = None
        nearest_resistance = None
        
        for level in sorted(support_levels, key=lambda x: x['price'], reverse=True):
            if level['price'] < current_price:
                distance_pct = ((current_price - level['price']) / current_price) * 100
                nearest_support = {
                    'price': level['price'],
                    'distance_pct': round(distance_pct, 2),
                    'strength': level['strength']
                }
                break
        
        for level in sorted(resistance_levels, key=lambda x: x['price']):
            if level['price'] > current_price:
                distance_pct = ((level['price'] - current_price) / current_price) * 100
                nearest_resistance = {
                    'price': level['price'],
                    'distance_pct': round(distance_pct, 2),
                    'strength': level['strength']
                }
                break
        
        # Identify price gaps
        price_gaps = []
        for i in range(1, min(30, len(recent_closes))):
            prev_low = recent_lows[i-1]
            prev_high = recent_highs[i-1]
            curr_low = recent_lows[i]
            curr_high = recent_highs[i]
            
            # Up gap: current low > previous high
            if curr_low > prev_high:
                gap_pct = ((curr_low - prev_high) / prev_high) * 100
                gap_threshold = get_config('technical', 'gap', 'threshold_pct', default=1.0)
                if gap_pct > gap_threshold:
                    price_gaps.append({
                        'type': 'up',
                        'from': round(prev_high, 2),
                        'to': round(curr_low, 2),
                        'age': i,
                        'filled': False,
                        'gap_pct': round(gap_pct, 2)
                    })
            
            # Down gap: current high < previous low
            elif curr_high < prev_low:
                gap_pct = ((prev_low - curr_high) / prev_low) * 100
                gap_threshold = get_config('technical', 'gap', 'threshold_pct', default=1.0)
                if gap_pct > gap_threshold:
                    price_gaps.append({
                        'type': 'down',
                        'from': round(prev_low, 2),
                        'to': round(curr_high, 2),
                        'age': i,
                        'filled': False,
                        'gap_pct': round(gap_pct, 2)
                    })
        
        return {
            'support_levels': support_levels,
            'resistance_levels': resistance_levels,
            'nearest_support': nearest_support,
            'nearest_resistance': nearest_resistance,
            'price_gaps': price_gaps,
            'current_price': round(current_price, 2)
        }
    
    @staticmethod
    def _evaluate_support_resistance_score(indicators: Dict, current_price: float) -> float:
        """Evaluate support/resistance levels"""
        score = 50
        
        # Check Bollinger Bands position
        if 'bb_upper' in indicators and 'bb_lower' in indicators:
            upper = indicators['bb_upper'][-1] if indicators['bb_upper'] else None
            lower = indicators['bb_lower'][-1] if indicators['bb_lower'] else None
            
            if upper and lower:
                if current_price > upper:
                    score -= 20  # Overbought, near resistance
                elif current_price < lower:
                    score += 20  # Oversold, near support
        
        # Check moving average support/resistance
        if 'ma_20' in indicators and indicators['ma_20'] and indicators['ma_20'][-1]:
            ma_20 = indicators['ma_20'][-1]
            ma_distance = (current_price - ma_20) / ma_20
            
            if abs(ma_distance) < 0.02:  # Within 2% of MA
                if ma_distance > 0:
                    score -= 10  # Near MA resistance
                else:
                    score += 10  # Near MA support
        
        return max(0, min(100, score))


class MultiFactorCalculator:
    """Calculate multi-factor model scores"""
    
    @staticmethod
    def calculate_quality_score(financials: Dict) -> float:
        """
        Calculate quality factor score
        
        Args:
            financials: Dictionary of financial metrics
        
        Returns:
            quality_score: Quality score (0-100)
        """
        components = []
        weights = []
        
        # ROE component (30%)
        roe = financials.get('roe')
        if roe:
            components.append(MultiFactorCalculator._calculate_roe_score(roe))
            weights.append(0.30)
        
        # Gross Margin component (25%)
        gross_margin = financials.get('gross_margin')
        if gross_margin is not None:
            components.append(MultiFactorCalculator._calculate_margin_score(gross_margin))
            weights.append(0.25)
        
        # Earnings Stability (25%)
        stability = financials.get('earnings_stability_score')
        if stability is not None:
            components.append(stability)
            weights.append(0.25)
        
        # Debt/Equity (20%)
        debt_eq = financials.get('debt_to_equity')
        if debt_eq:
            components.append(MultiFactorCalculator._calculate_debt_score(debt_eq))
            weights.append(0.20)
        
        # Calculate weighted average
        if not components:
            return 50
        
        total_score = 0
        total_weight = 0
        
        for score, weight in zip(components, weights):
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight
    
    @staticmethod
    def calculate_value_score(financials: Dict, current_price: float, sector: Optional[str] = None) -> float:
        """
        Calculate value factor score
        
        Args:
            financials: Dictionary of financial metrics
            current_price: Current stock price
            sector: Industry sector
        
        Returns:
            value_score: Value score (0-100)
        """
        components = []
        weights = []
        
        # P/E component (30%)
        pe_ratio = financials.get('pe_ratio')
        if pe_ratio:
            components.append(MultiFactorCalculator._calculate_pe_score(pe_ratio, sector))
            weights.append(0.30)
        
        # EV/EBITDA component (30%)
        ev_ebitda = financials.get('ev_ebitda')
        if ev_ebitda:
            components.append(MultiFactorCalculator._calculate_ev_ebitda_score(ev_ebitda, sector))
            weights.append(0.30)
        
        # FCF Yield component (25%)
        fcf_yield = financials.get('fcf_yield')
        if fcf_yield:
            components.append(MultiFactorCalculator._calculate_fcf_yield_score(fcf_yield))
            weights.append(0.25)
        
        # Dividend Yield component (15%)
        div_yield = financials.get('dividend_yield')
        if div_yield:
            components.append(MultiFactorCalculator._calculate_dividend_score(div_yield))
            weights.append(0.15)
        
        # Calculate weighted average
        if not components:
            return 50
        
        total_score = 0
        total_weight = 0
        
        for score, weight in zip(components, weights):
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight
    
    @staticmethod
    def calculate_growth_score(financials: Dict) -> float:
        """
        Calculate growth factor score
        
        Args:
            financials: Dictionary of growth metrics
        
        Returns:
            growth_score: Growth score (0-100)
        """
        components = []
        weights = []
        
        # Revenue growth (40%)
        revenue_growth = financials.get('revenue_growth')
        if revenue_growth:
            components.append(MultiFactorCalculator._calculate_growth_component_score(revenue_growth))
            weights.append(0.40)
        
        # EPS growth (40%)
        eps_growth = financials.get('eps_growth')
        if eps_growth:
            components.append(MultiFactorCalculator._calculate_growth_component_score(eps_growth))
            weights.append(0.40)
        
        # Future growth estimates (20%)
        future_growth = financials.get('estimated_growth')
        if future_growth:
            components.append(MultiFactorCalculator._calculate_future_growth_score(future_growth))
            weights.append(0.20)
        
        # Calculate weighted average
        if not components:
            return 50
        
        total_score = 0
        total_weight = 0
        
        for score, weight in zip(components, weights):
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight
    
    @staticmethod
    def calculate_momentum_score(prices: List[float], eps_estimates: List[float] = None) -> float:
        """
        Calculate momentum factor score
        
        Args:
            prices: Historical prices
            eps_estimates: EPS estimate changes
        
        Returns:
            momentum_score: Momentum score (0-100)
        """
        # Calculate price momentum
        if len(prices) >= 63:  # 3 months (21 trading days per month)
            price_3m = (prices[-1] / prices[-63]) - 1 if prices[-63] != 0 else 0
            price_momentum_score = MultiFactorCalculator._calculate_price_momentum_score(price_3m)
        else:
            price_momentum_score = 50
        
        # Calculate earnings momentum
        if eps_estimates and len(eps_estimates) >= 4:
            earnings_momentum_score = MultiFactorCalculator._calculate_earnings_momentum_score(eps_estimates)
        else:
            earnings_momentum_score = 50
        
        # Combine (70% price momentum, 30% earnings momentum)
        momentum_score = price_momentum_score * 0.7 + earnings_momentum_score * 0.3
        
        return momentum_score
    
    @staticmethod
    def calculate_low_volatility_score(prices: List[float], beta: Optional[float] = None) -> float:
        """
        Calculate low volatility factor score
        
        Args:
            prices: Historical prices
            beta: Stock beta
        
        Returns:
            volatility_score: Low volatility score (0-100, higher = lower volatility)
        """
        # Calculate historical volatility
        if len(prices) >= 10:
            returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
            historical_vol = np.std(returns) * np.sqrt(252) if returns else 0.3  # Annualized
            
            # Convert to score (lower volatility = higher score)
            if historical_vol < 0.15:
                vol_score = 90
            elif historical_vol < 0.25:
                vol_score = 70
            elif historical_vol < 0.35:
                vol_score = 50
            elif historical_vol < 0.45:
                vol_score = 30
            else:
                vol_score = 10
        else:
            vol_score = 50
        
        # Incorporate beta if available
        if beta:
            beta_score = MultiFactorCalculator._calculate_beta_score(beta)
            # Combine volatility and beta scores (60% vol, 40% beta)
            volatility_score = vol_score * 0.6 + beta_score * 0.4
        else:
            volatility_score = vol_score
        
        return volatility_score
    
    @staticmethod
    def calculate_composite_factor_score(factor_scores: Dict, strategy: str = 'balanced') -> Tuple[float, Dict, str]:
        """
        Calculate composite factor score based on investment strategy
        
        Args:
            factor_scores: Dictionary of factor category scores
            strategy: Investment strategy type
        
        Returns:
            composite_score: Overall factor score (0-100)
            breakdown: Contribution by factor
            strategy: Strategy used
        """
        strategy_weights = get_config('factors', 'strategies', strategy, default={
                'quality': 0.25,
                'value': 0.25,
                'growth': 0.20,
                'momentum': 0.20,
                'low_volatility': 0.10
            })
        
        strategies = {
            'quality_value': strategy_weights if strategy == 'quality_value' else get_config('factors', 'strategies', 'quality_value', default={
                'quality': 0.40, 'value': 0.40, 'growth': 0.10, 'momentum': 0.05, 'low_volatility': 0.05
            }),
            'growth_momentum': strategy_weights if strategy == 'growth_momentum' else get_config('factors', 'strategies', 'growth_momentum', default={
                'quality': 0.20, 'value': 0.10, 'growth': 0.40, 'momentum': 0.25, 'low_volatility': 0.05
            }),
            'balanced': strategy_weights if strategy == 'balanced' else get_config('factors', 'strategies', 'balanced', default={
                'quality': 0.25, 'value': 0.25, 'growth': 0.20, 'momentum': 0.20, 'low_volatility': 0.10
            }),
            'defensive': strategy_weights if strategy == 'defensive' else get_config('factors', 'strategies', 'defensive', default={
                'quality': 0.30, 'value': 0.30, 'growth': 0.10, 'momentum': 0.10, 'low_volatility': 0.20
            }),
            'aggressive_growth': strategy_weights if strategy == 'aggressive_growth' else get_config('factors', 'strategies', 'aggressive_growth', default={
                'quality': 0.15, 'value': 0.10, 'growth': 0.50, 'momentum': 0.20, 'low_volatility': 0.05
            })
        }
        
        weights = strategies.get(strategy, strategies['balanced'])
        
        composite_score = 0
        breakdown = {}
        total_weight = 0
        
        for factor, weight in weights.items():
            factor_value = factor_scores.get(factor, {}).get('score', 50)
            
            contribution = factor_value * weight
            composite_score += contribution
            total_weight += weight
            
            breakdown[factor] = {
                'score': factor_value,
                'weight': weight,
                'contribution': contribution
            }
        
        # Normalize if total_weight < 1
        if total_weight > 0:
            composite_score = composite_score / total_weight
        
        return composite_score, breakdown, strategy
    
    @staticmethod
    def _calculate_roe_score(roe: float) -> float:
        """Convert ROE to 0-100 score"""
        if roe > 25:
            return 90
        elif roe > 20:
            return 80
        elif roe > 15:
            return 70
        elif roe > 10:
            return 60
        elif roe > 5:
            return 50
        elif roe > 0:
            return 40
        else:
            return 20
    
    @staticmethod
    def _calculate_pe_score(pe_ratio: float, sector: Optional[str] = None) -> float:
        """Convert P/E ratio to 0-100 score (lower P/E = higher score)"""
        if pe_ratio <= 0:
            return 50
        
        sector_benchmarks = _get_sector_pe_benchmarks()
        
        if sector and sector in sector_benchmarks:
            cheap = sector_benchmarks[sector]['cheap']
            expensive = sector_benchmarks[sector]['expensive']
        else:
            all_cheaps = [v['cheap'] for v in sector_benchmarks.values()]
            all_expensive = [v['expensive'] for v in sector_benchmarks.values()]
            cheap = sorted(all_cheaps)[len(all_cheaps) // 2]
            expensive = sorted(all_expensive)[len(all_expensive) // 2]
        
        if pe_ratio < cheap:
            return 90  # Very cheap
        elif pe_ratio < (cheap + expensive) / 2:
            return 70  # Cheap
        elif pe_ratio < expensive:
            return 50  # Fair
        elif pe_ratio < expensive * 1.5:
            return 30  # Expensive
        else:
            return 10  # Very expensive
    
    @staticmethod
    def _calculate_fcf_yield_score(fcf_yield: float) -> float:
        """Convert FCF Yield to 0-100 score (higher yield = higher score)"""
        if fcf_yield > 0.10:
            return 90
        elif fcf_yield > 0.07:
            return 80
        elif fcf_yield > 0.05:
            return 70
        elif fcf_yield > 0.03:
            return 60
        elif fcf_yield > 0.01:
            return 50
        elif fcf_yield > 0:
            return 40
        else:
            return 20
    
    @staticmethod
    def _calculate_margin_score(gross_margin: float) -> float:
        """Convert gross margin to 0-100 score"""
        if gross_margin > 0.50:
            return 90
        elif gross_margin > 0.40:
            return 80
        elif gross_margin > 0.30:
            return 70
        elif gross_margin > 0.20:
            return 60
        elif gross_margin > 0.10:
            return 50
        else:
            return 30
    
    @staticmethod
    def _calculate_debt_score(debt_to_equity: float) -> float:
        """Convert debt-to-equity to 0-100 score (lower = better)"""
        if debt_to_equity < 0.3:
            return 90
        elif debt_to_equity < 0.6:
            return 80
        elif debt_to_equity < 1.0:
            return 70
        elif debt_to_equity < 1.5:
            return 60
        elif debt_to_equity < 2.0:
            return 50
        elif debt_to_equity < 3.0:
            return 40
        else:
            return 20
    
    @staticmethod
    def _calculate_ev_ebitda_score(ev_ebitda: float, sector: Optional[str] = None) -> float:
        """Convert EV/EBITDA to 0-100 score (lower = better)"""
        if ev_ebitda <= 0:
            return 50
        
        sector_ev_ebitda = _get_sector_ev_ebitda_benchmarks()
        if sector and sector in sector_ev_ebitda:
            cheap = sector_ev_ebitda[sector]['cheap']
            expensive = sector_ev_ebitda[sector]['expensive']
        else:
            cheap, expensive = 6, 15
        
        if ev_ebitda < cheap:
            return 90
        elif ev_ebitda < (cheap + expensive) / 2:
            return 70
        elif ev_ebitda < expensive:
            return 50
        elif ev_ebitda < expensive * 1.5:
            return 30
        else:
            return 10
    
    @staticmethod
    def _calculate_dividend_score(dividend_yield: float) -> float:
        """Convert dividend yield to 0-100 score (higher = better, but not too high)"""
        if dividend_yield > 0.08:  # Too high, might be unsustainable
            return 40
        elif dividend_yield > 0.05:
            return 80
        elif dividend_yield > 0.03:
            return 70
        elif dividend_yield > 0.02:
            return 60
        elif dividend_yield > 0.01:
            return 50
        elif dividend_yield > 0:
            return 40
        else:
            return 30
    
    @staticmethod
    def _calculate_growth_component_score(growth_rate: float) -> float:
        """Convert growth rate to 0-100 score"""
        if growth_rate > 0.20:
            return 90
        elif growth_rate > 0.15:
            return 80
        elif growth_rate > 0.10:
            return 70
        elif growth_rate > 0.05:
            return 60
        elif growth_rate > 0:
            return 50
        elif growth_rate > -0.05:
            return 40
        else:
            return 20
    
    @staticmethod
    def _calculate_future_growth_score(estimated_growth: float) -> float:
        """Convert estimated future growth to 0-100 score"""
        return MultiFactorCalculator._calculate_growth_component_score(estimated_growth)
    
    @staticmethod
    def _calculate_price_momentum_score(price_momentum: float) -> float:
        """Convert price momentum to 0-100 score"""
        if price_momentum > 0.20:
            return 90
        elif price_momentum > 0.10:
            return 80
        elif price_momentum > 0.05:
            return 70
        elif price_momentum > 0:
            return 60
        elif price_momentum > -0.05:
            return 50
        elif price_momentum > -0.10:
            return 40
        elif price_momentum > -0.20:
            return 30
        else:
            return 10
    
    @staticmethod
    def _calculate_earnings_momentum_score(eps_estimates: List[float]) -> float:
        """Convert earnings momentum to 0-100 score"""
        if len(eps_estimates) < 4:
            return 50
        
        # Calculate percentage of upward revisions
        upward_revisions = sum(1 for change in eps_estimates if change > 0)
        total_revisions = len(eps_estimates)
        
        upward_ratio = upward_revisions / total_revisions
        
        # Convert to score
        if upward_ratio > 0.7:
            return 90
        elif upward_ratio > 0.6:
            return 80
        elif upward_ratio > 0.5:
            return 70
        elif upward_ratio > 0.4:
            return 60
        elif upward_ratio > 0.3:
            return 50
        elif upward_ratio > 0.2:
            return 40
        else:
            return 30
    
    @staticmethod
    def _calculate_beta_score(beta: float) -> float:
        """Convert beta to 0-100 score (lower beta = higher score for low volatility)"""
        if beta < 0.7:
            return 90  # Defensive
        elif beta < 0.9:
            return 80
        elif beta < 1.1:
            return 70  # Market-like
        elif beta < 1.3:
            return 60
        elif beta < 1.5:
            return 50
        else:
            return 30  # Aggressive


class MoatAnalyzer:
    """Analyze economic moat strength based on five moat types."""
    
    SECTOR_GROSS_MARGINS = {
        'Technology': 0.55, 'Healthcare': 0.60, 'Financials': 0.70,
        'Consumer Staples': 0.35, 'Utilities': 0.40, 'Industrials': 0.30,
        'Energy': 0.35, 'Consumer Discretionary': 0.40,
    }
    SECTOR_OP_MARGINS = {
        'Technology': 0.20, 'Healthcare': 0.18, 'Financials': 0.25,
        'Consumer Staples': 0.10, 'Utilities': 0.15, 'Industrials': 0.10,
        'Energy': 0.12, 'Consumer Discretionary': 0.10,
    }
    
    @staticmethod
    def analyze_brand_moat(gross_margin: float, sector: Optional[str], revenue_growth: Optional[float]) -> Tuple[float, List[str]]:
        score = 0.0
        reasons = []
        industry_margin = MoatAnalyzer.SECTOR_GROSS_MARGINS.get(sector, 0.40) if sector else 0.40
        
        if gross_margin is not None:
            premium = gross_margin - industry_margin
            if premium > 0.15:
                score += 0.7
                reasons.append(f"Premium gross margin: +{premium:.1%}")
            elif premium > 0.05:
                score += 0.4
                reasons.append(f"Above-average margin: +{premium:.1%}")
            elif premium > 0:
                score += 0.2
        
        if revenue_growth and revenue_growth > 0.10:
            score += 0.3
            reasons.append(f"Strong revenue growth: {revenue_growth:.1%}")
        
        return min(2.0, score), reasons
    
    @staticmethod
    def analyze_network_moat(market_cap: Optional[float], revenue_growth: Optional[float], sector: Optional[str]) -> Tuple[float, List[str]]:
        score = 0.0
        reasons = []
        platform_sectors = {'Technology', 'Consumer Discretionary', 'Financials'}
        
        if sector in platform_sectors:
            score += 0.3
            reasons.append("Platform-capable sector")
        
        if revenue_growth and revenue_growth > 0.20:
            score += 0.5
            reasons.append(f"Hypergrowth: {revenue_growth:.1%}")
        elif revenue_growth and revenue_growth > 0.10:
            score += 0.3
            reasons.append(f"Strong growth: {revenue_growth:.1%}")
        
        if market_cap and market_cap > 100_000_000_000:
            score += 0.5
            reasons.append("Large-cap with network potential")
        
        return min(2.0, score), reasons
    
    @staticmethod
    def analyze_switching_cost_moat(recurring_revenue_pct: Optional[float], sector: Optional[str]) -> Tuple[float, List[str]]:
        score = 0.0
        reasons = []
        
        if recurring_revenue_pct is not None:
            if recurring_revenue_pct > 0.80:
                score += 0.7
                reasons.append(f"High recurring revenue: {recurring_revenue_pct:.0%}")
            elif recurring_revenue_pct > 0.50:
                score += 0.4
                reasons.append(f"Moderate recurring revenue: {recurring_revenue_pct:.0%}")
        
        high_switching_sectors = {'Technology', 'Financials'}
        if sector in high_switching_sectors:
            score += 0.3
            reasons.append(f"Sector with inherent switching costs: {sector}")
        
        return min(2.0, score), reasons
    
    @staticmethod
    def analyze_cost_advantage_moat(operating_margin: Optional[float], sector: Optional[str]) -> Tuple[float, List[str]]:
        score = 0.0
        reasons = []
        industry_margin = MoatAnalyzer.SECTOR_OP_MARGINS.get(sector, 0.12) if sector else 0.12
        
        if operating_margin is not None:
            advantage = operating_margin - industry_margin
            if advantage > 0.10:
                score += 0.8
                reasons.append(f"Superior operating margin: +{advantage:.1%}")
            elif advantage > 0.05:
                score += 0.5
                reasons.append(f"Above-average margin: +{advantage:.1%}")
            elif advantage > 0:
                score += 0.2
        
        return min(2.0, score), reasons
    
    @staticmethod
    def analyze_regulatory_moat(sector: Optional[str], market_cap: Optional[float]) -> Tuple[float, List[str]]:
        score = 0.0
        reasons = []
        regulated_sectors = {'Financials', 'Utilities', 'Healthcare'}
        
        if sector in regulated_sectors:
            score += 0.5
            reasons.append(f"Regulated sector: {sector}")
        
        if market_cap and market_cap > 50_000_000_000 and sector in regulated_sectors:
            score += 0.5
            reasons.append("Large incumbent in regulated market")
        
        return min(2.0, score), reasons
    
    @staticmethod
    def _get_moat_override(symbol: str) -> dict:
        """Get moat override from watchlist.json if available."""
        try:
            wl_path = Path(__file__).parent.parent / 'references' / 'watchlist.json'
            with open(wl_path) as f:
                wl = json.load(f)
            for item in wl.get('watchlist', []):
                if item.get('symbol', '').upper() == symbol.upper().split('.')[0]:
                    moat = item.get('moat_override')
                    if moat:
                        return moat
        except Exception:
            pass
        return {}
    
    @staticmethod
    def analyze_moat(stock_data: StockData) -> Dict:
        gross_margin = None
        if stock_data.revenue and stock_data.revenue > 0 and stock_data.free_cash_flow is not None:
            estimated_cogs = stock_data.revenue - (stock_data.free_cash_flow * 0.5)
            if estimated_cogs > 0:
                gross_margin = (stock_data.revenue - estimated_cogs) / stock_data.revenue
        
        if gross_margin is None and stock_data.net_income and stock_data.revenue:
            gross_margin = stock_data.net_income / stock_data.revenue * 2
        
        operating_margin = None
        if stock_data.ebitda and stock_data.revenue:
            operating_margin = stock_data.ebitda / stock_data.revenue
        
        recurring_revenue_pct = None
        if stock_data.recurring_revenue_pct is not None:
            recurring_revenue_pct = stock_data.recurring_revenue_pct
        else:
            sector_recurring = get_config('moat', 'sector_recurring_revenue', default={
                'Technology': 0.60, 'Financials': 0.70, 'Healthcare': 0.50,
                'Consumer Staples': 0.40, 'Utilities': 0.50, 'Industrials': 0.30,
                'Energy': 0.20, 'Consumer Discretionary': 0.30
            })
            if stock_data.sector and stock_data.sector in sector_recurring:
                recurring_revenue_pct = sector_recurring[stock_data.sector]
        
        brand_score, brand_reasons = MoatAnalyzer.analyze_brand_moat(
            gross_margin, stock_data.sector, stock_data.revenue_growth
        )
        network_score, network_reasons = MoatAnalyzer.analyze_network_moat(
            stock_data.market_cap, stock_data.revenue_growth, stock_data.sector
        )
        switching_score, switching_reasons = MoatAnalyzer.analyze_switching_cost_moat(
            recurring_revenue_pct, stock_data.sector
        )
        cost_score, cost_reasons = MoatAnalyzer.analyze_cost_advantage_moat(
            operating_margin, stock_data.sector
        )
        regulatory_score, regulatory_reasons = MoatAnalyzer.analyze_regulatory_moat(
            stock_data.sector, stock_data.market_cap
        )
        
        total_score = brand_score + network_score + switching_score + cost_score + regulatory_score
        moat_score = min(10.0, total_score)
        
        all_reasons = (
            [('brand', brand_score, brand_reasons),
             ('network', network_score, network_reasons),
             ('switching', switching_score, switching_reasons),
             ('cost', cost_score, cost_reasons),
             ('regulatory', regulatory_score, regulatory_reasons)]
        )
        
        # Apply watchlist moat overrides if available
        symbol = getattr(stock_data, 'symbol', '') or ''
        moat_override = MoatAnalyzer._get_moat_override(symbol)
        if moat_override:
            if 'moat_score' in moat_override:
                moat_score = moat_override['moat_score']
            if 'moat_width' in moat_override:
                moat_width_override = moat_override['moat_width']
        
        if moat_score >= 7:
            moat_width = 'Wide'
            required_margin = 0.10
        elif moat_score >= 5:
            moat_width = 'Narrow'
            required_margin = 0.20
        elif moat_score >= 3:
            moat_width = 'Minimal'
            required_margin = 0.35
        else:
            moat_width = None  # No moat, not string 'None'
            required_margin = None
        
        # Apply moat_width override after threshold calculation
        if moat_override and 'moat_width' in moat_override:
            moat_width = moat_override['moat_width']
        
        return {
            'moat_score': round(moat_score, 1),
            'moat_width': moat_width,
            'required_safety_margin': required_margin,
            'components': {
                'brand': {'score': brand_score, 'reasons': brand_reasons},
                'network': {'score': network_score, 'reasons': network_reasons},
                'switching': {'score': switching_score, 'reasons': switching_reasons},
                'cost': {'score': cost_score, 'reasons': cost_reasons},
                'regulatory': {'score': regulatory_score, 'reasons': regulatory_reasons},
            }
        }


class ValueTrapDetector:
    """Detect value traps - stocks that appear cheap but are deteriorating."""
    
    @staticmethod
    def check_roic_vs_wacc(stock_data: StockData) -> Dict:
        nopat = None
        invested_capital = None
        
        if stock_data.shareholders_equity:
            tax_rate = 0.25
            if stock_data.ebitda and stock_data.revenue:
                estimated_da = stock_data.revenue * 0.05
                operating_income = stock_data.ebitda - estimated_da
                nopat = operating_income * (1 - tax_rate)
            elif stock_data.net_income is not None:
                # NOPAT = Operating Income × (1 - tax_rate)
                # Net Income already has taxes & interest deducted; estimate:
                #   NOPAT ≈ Net Income + After-tax Interest Expense
                #   Interest Expense ≈ total_debt × cost_of_debt
                cost_of_debt = get_config('value_trap', 'wacc_params', default={}).get('default_cost_of_debt', 0.05)
                interest = (stock_data.total_debt or 0) * cost_of_debt
                nopat = stock_data.net_income + interest * (1 - tax_rate)
            
            invested_capital = stock_data.shareholders_equity
            if stock_data.total_debt:
                invested_capital += stock_data.total_debt
            if stock_data.cash:
                invested_capital -= stock_data.cash
        
        if nopat is None or invested_capital is None or invested_capital <= 0:
            return {'roic': None, 'wacc': None, 'spread': None, 'severity': 'UNKNOWN', 'is_trap': False, 'explanation': 'Insufficient data'}
        
        roic = nopat / invested_capital
        
        wacc_params = get_config('value_trap', 'wacc_params', default={
            'risk_free_rate': 0.045, 'market_risk_premium': 0.06,
            'default_cost_of_debt': 0.05, 'default_tax_rate': 0.25
        })
        risk_free_rate = wacc_params.get('risk_free_rate', 0.045)
        market_risk_premium = wacc_params.get('market_risk_premium', 0.06)
        beta = 1.0
        cost_of_equity = risk_free_rate + beta * market_risk_premium
        
        equity = stock_data.shareholders_equity or 1
        debt = stock_data.total_debt or 0
        total_capital = equity + debt if (equity + debt) > 0 else 1
        equity_weight = equity / total_capital
        debt_weight = 1 - equity_weight
        
        cost_of_debt = wacc_params.get('default_cost_of_debt', 0.05)
        tax_rate = wacc_params.get('default_tax_rate', 0.25)
        wacc = cost_of_equity * equity_weight + cost_of_debt * (1 - tax_rate) * debt_weight
        
        spread = roic - wacc
        
        if spread < -0.05:
            is_trap = True
            severity = 'CRITICAL'
            explanation = f"ROIC ({roic:.1%}) << WACC ({wacc:.1%}), massive value destruction"
        elif spread < 0:
            is_trap = True
            severity = 'HIGH'
            explanation = f"ROIC ({roic:.1%}) < WACC ({wacc:.1%}), destroying value"
        elif spread < 0.03:
            is_trap = False
            severity = 'MEDIUM'
            explanation = f"ROIC ({roic:.1%}) marginally above WACC ({wacc:.1%})"
        else:
            is_trap = False
            severity = 'LOW'
            explanation = f"ROIC ({roic:.1%}) > WACC ({wacc:.1%}), creating value"
        
        return {
            'roic': roic, 'wacc': wacc, 'spread': spread,
            'severity': severity, 'is_trap': is_trap, 'explanation': explanation
        }
    
    @staticmethod
    def check_fcf_health(stock_data: StockData) -> Dict:
        if stock_data.free_cash_flow is None or stock_data.revenue is None:
            return {'is_trap': False, 'severity': 'UNKNOWN', 'explanation': 'Insufficient FCF data'}
        
        fcf_margin = stock_data.free_cash_flow / stock_data.revenue if stock_data.revenue > 0 else 0
        
        if stock_data.free_cash_flow < 0:
            if stock_data.revenue_growth and stock_data.revenue_growth > 0.15:
                return {'is_trap': False, 'severity': 'MEDIUM', 'explanation': f'Negative FCF but high growth ({stock_data.revenue_growth:.1%}) - investing phase'}
            return {'is_trap': True, 'severity': 'HIGH', 'explanation': f'Negative FCF with no compensating growth'}
        
        if fcf_margin < 0.02 and stock_data.eps is not None and stock_data.eps <= 0:
            return {'is_trap': True, 'severity': 'MEDIUM', 'explanation': f'Low FCF margin ({fcf_margin:.1%}) and negative EPS'}
        
        return {'is_trap': False, 'severity': 'LOW', 'explanation': f'Positive FCF, margin {fcf_margin:.1%}'}
    
    @staticmethod
    def check_debt_health(stock_data: StockData) -> Dict:
        if stock_data.total_debt is None or stock_data.shareholders_equity is None:
            return {'is_trap': False, 'severity': 'UNKNOWN', 'explanation': 'Insufficient debt data'}
        
        if stock_data.shareholders_equity <= 0:
            return {'is_trap': True, 'severity': 'CRITICAL', 'explanation': 'Negative shareholders equity'}
        
        debt_to_equity = stock_data.total_debt / stock_data.shareholders_equity
        
        if stock_data.ebitda and stock_data.ebitda > 0:
            debt_to_ebitda = stock_data.total_debt / stock_data.ebitda
            if debt_to_ebitda > 5:
                return {'is_trap': True, 'severity': 'HIGH', 'explanation': f'High leverage: Debt/EBITDA = {debt_to_ebitda:.1f}x'}
            elif debt_to_ebitda > 3:
                return {'is_trap': False, 'severity': 'MEDIUM', 'explanation': f'Elevated leverage: Debt/EBITDA = {debt_to_ebitda:.1f}x'}
        
        if debt_to_equity > 3.0:
            return {'is_trap': True, 'severity': 'HIGH', 'explanation': f'High D/E ratio: {debt_to_equity:.1f}x'}
        
        return {'is_trap': False, 'severity': 'LOW', 'explanation': f'Reasonable leverage: D/E = {debt_to_equity:.1f}x'}
    
    @staticmethod
    def check_earnings_quality(stock_data: StockData) -> Dict:
        if stock_data.eps is None:
            return {'is_trap': False, 'severity': 'UNKNOWN', 'explanation': 'No EPS data'}
        
        if stock_data.eps <= 0:
            return {'is_trap': True, 'severity': 'HIGH', 'explanation': f'Negative EPS: ${stock_data.eps:.2f}'}
        
        if stock_data.eps_growth is not None and stock_data.eps_growth < -0.20:
            return {'is_trap': True, 'severity': 'MEDIUM', 'explanation': f'Sharp EPS decline: {stock_data.eps_growth:.1%}'}
        
        return {'is_trap': False, 'severity': 'LOW', 'explanation': f'Positive EPS with growth'}
    
    @staticmethod
    def detect_trap(stock_data: StockData) -> Dict:
        roic_check = ValueTrapDetector.check_roic_vs_wacc(stock_data)
        fcf_check = ValueTrapDetector.check_fcf_health(stock_data)
        debt_check = ValueTrapDetector.check_debt_health(stock_data)
        earnings_check = ValueTrapDetector.check_earnings_quality(stock_data)
        
        trap_score = 0
        warnings = []
        
        trap_config = get_config('value_trap', 'weights', default={
            'roic_vs_wacc': 25, 'fcf_health': 20, 'debt_health': 20,
            'earnings_quality': 20, 'dividend_yield': 15
        })
        
        # For non-dividend stocks, redistribute dividend_yield weight
        if not (stock_data.dividend_per_share and stock_data.current_price):
            redistribution = {'roic_vs_wacc': 4, 'fcf_health': 4, 'debt_health': 4, 'earnings_quality': 3}
            for name, bonus in redistribution.items():
                trap_config[name] = trap_config.get(name, 20) + bonus
        
        checks = [
            ('roic_vs_wacc', roic_check, trap_config.get('roic_vs_wacc', 25)),
            ('fcf_health', fcf_check, trap_config.get('fcf_health', 20)),
            ('debt_health', debt_check, trap_config.get('debt_health', 20)),
            ('earnings_quality', earnings_check, trap_config.get('earnings_quality', 20)),
        ]
        
        for name, check, weight in checks:
            if check['is_trap']:
                trap_score += weight
            if check['severity'] in ('HIGH', 'CRITICAL'):
                warnings.append(f"{name}: {check['explanation']}")
        
        # Check dividend yield (only for dividend-paying stocks)
        if stock_data.dividend_per_share and stock_data.current_price:
            dividend_yield = stock_data.dividend_per_share / stock_data.current_price
            if dividend_yield > 0.08:
                trap_score += trap_config.get('dividend_yield', 15)
                warnings.append(f"Unsustainable dividend yield: {dividend_yield:.1%}")
        
        if trap_score >= 50:
            risk_level = 'CRITICAL'
            action = 'AVOID'
        elif trap_score >= 30:
            risk_level = 'HIGH'
            action = 'AVOID_OR_MINIMAL'
        elif trap_score >= 15:
            risk_level = 'MEDIUM'
            action = 'CAUTION'
        else:
            risk_level = 'LOW'
            action = 'OK'
        
        return {
            'trap_score': trap_score,
            'risk_level': risk_level,
            'action': action,
            'warnings': warnings,
            'checks': {
                'roic_vs_wacc': roic_check,
                'fcf_health': fcf_check,
                'debt_health': debt_check,
                'earnings_quality': earnings_check,
            }
        }


class ConflictResolver:
    """Resolve conflicts between different analysis frameworks."""
    
    PRIORITY_HIERARCHY = ['market_regime', 'business_quality', 'valuation', 'technical', 'short_term']
    
    @staticmethod
    def resolve(signals: Dict[str, Dict], investment_horizon: str = 'LONG_TERM') -> Dict:
        """
        Resolve conflicting signals from different analysis frameworks.
        
        Args:
            signals: Dict of framework_name -> {'direction': 'bullish'|'bearish'|'neutral', 'strength': 0-1, 'reason': str}
            investment_horizon: 'LONG_TERM', 'SWING_TRADE', 'DAY_TRADE'
            
        Returns:
            Resolution with final action, reasoning, and position adjustment
        """
        framework_priorities = {
            'LONG_TERM': {'market_regime': 0.30, 'business_quality': 0.30, 'valuation': 0.25, 'technical': 0.10, 'short_term': 0.05},
            'SWING_TRADE': {'market_regime': 0.20, 'business_quality': 0.15, 'valuation': 0.20, 'technical': 0.35, 'short_term': 0.10},
            'DAY_TRADE': {'market_regime': 0.10, 'business_quality': 0.05, 'valuation': 0.10, 'technical': 0.50, 'short_term': 0.25},
        }
        
        weights = framework_priorities.get(investment_horizon, framework_priorities['LONG_TERM'])
        
        direction_scores = {'bullish': 1, 'neutral': 0, 'bearish': -1}
        
        weighted_score = 0
        total_weight = 0
        conflicts = []
        framework_contributions = {}
        
        sorted_frameworks = sorted(signals.keys(), key=lambda f: weights.get(f, 0.1), reverse=True)
        dominant_framework = sorted_frameworks[0] if sorted_frameworks else None
        dominant_signal = signals.get(dominant_framework, {})
        
        for framework, signal in signals.items():
            direction = signal.get('direction', 'neutral')
            strength = signal.get('strength', 0.5)
            weight = weights.get(framework, 0.1)
            
            direction_value = direction_scores.get(direction, 0)
            contribution = direction_value * strength * weight
            weighted_score += contribution
            total_weight += weight
            
            framework_contributions[framework] = {
                'direction': direction,
                'strength': strength,
                'weight': weight,
                'contribution': contribution
            }
        
        if total_weight > 0:
            weighted_score /= total_weight
        
        if len(signals) >= 2:
            directions = [s.get('direction', 'neutral') for s in signals.values()]
            unique_dirs = set(d for d in directions if d != 'neutral')
            if len(unique_dirs) > 1:
                conflicts = [f for f, s in signals.items() if s.get('direction') != 'neutral']
        
        if weighted_score > 0.3:
            action = 'BUY'
            position_pct = min(1.0, 0.5 + weighted_score * 0.5)
        elif weighted_score > 0.1:
            action = 'BUY_SMALL'
            position_pct = 0.3 + weighted_score * 0.3
        elif weighted_score > -0.1:
            action = 'HOLD'
            position_pct = 0.3
        elif weighted_score > -0.3:
            action = 'REDUCE'
            position_pct = max(0.1, 0.3 + weighted_score * 0.3)
        else:
            action = 'SELL'
            position_pct = max(0.0, 0.1 + weighted_score * 0.1)
        
        if dominant_signal.get('direction') == 'bearish' and dominant_signal.get('strength', 0) > 0.7:
            position_pct *= 0.5
            action = 'REDUCE' if action in ('HOLD', 'BUY_SMALL') else action
        
        reasons = []
        if conflicts:
            reasons.append(f"Conflicting signals from: {', '.join(conflicts)}")
            reasons.append(f"Resolved via {investment_horizon} priority hierarchy: {dominant_framework} dominates")
        
        for framework in sorted_frameworks[:2]:
            signal = signals.get(framework, {})
            if signal.get('reason'):
                reasons.append(f"{framework}: {signal['reason']}")
        
        return {
            'action': action,
            'position_pct': round(max(0, min(1, position_pct)), 2),
            'weighted_score': round(weighted_score, 3),
            'conflicts': conflicts,
            'dominant_framework': dominant_framework,
            'investment_horizon': investment_horizon,
            'reasons': reasons,
            'framework_contributions': framework_contributions,
        }


class StopLossCalculator:
    """Calculate dynamic stop-loss levels based on ATR and support/resistance.
    
    Uses three complementary methods and selects the most appropriate:
    1. ATR-based trailing stop (volatility-adjusted)
    2. Support-level stop (below nearest support)
    3. Combined optimal stop (weights both approaches)
    """
    
    @staticmethod
    def calculate_atr_stop(current_price: float, atr_value: float, 
                          multiplier: float = 2.0, volatility: float = 0.30) -> Dict:
        """Calculate ATR-based stop-loss.
        
        Higher volatility = wider stop to avoid premature exits.
        """
        vol_adjust = 1.0
        if volatility > 0.60:
            vol_adjust = 1.3  # Wider stop for very volatile stocks
            multiplier = 2.5
        elif volatility > 0.40:
            vol_adjust = 1.1
            multiplier = 2.2
        
        stop_price = current_price - (atr_value * multiplier * vol_adjust)
        stop_pct = (current_price - stop_price) / current_price * 100
        
        return {
            'method': 'ATR',
            'stop_price': round(stop_price, 2),
            'stop_pct': round(stop_pct, 2),
            'atr_value': atr_value,
            'multiplier': multiplier,
            'volatility_adjustment': vol_adjust
        }
    
    @staticmethod
    def calculate_support_stop(current_price: float, nearest_support: Optional[Dict] = None,
                               support_levels: Optional[List[Dict]] = None) -> Optional[Dict]:
        """Calculate stop-loss below nearest support level."""
        if nearest_support and nearest_support.get('price'):
            support_price = nearest_support['price']
            # Place stop 2% below support
            stop_price = support_price * 0.98
            stop_pct = (current_price - stop_price) / current_price * 100
            return {
                'method': 'Support',
                'stop_price': round(stop_price, 2),
                'stop_pct': round(stop_pct, 2),
                'support_price': support_price,
                'support_strength': nearest_support.get('strength', 1)
            }
        return None
    
    @staticmethod
    def calculate_dynamic_stop(current_price: float, atr_value: float,
                               nearest_support: Optional[Dict] = None,
                               volatility: float = 0.30,
                               risk_tolerance: str = 'MODERATE') -> Dict:
        """Calculate the optimal dynamic stop-loss by combining methods.
        
        Args:
            current_price: Current stock price
            atr_value: Average True Range value (from TechnicalIndicatorsCalculator)
            nearest_support: Nearest support level dict
            volatility: Annual volatility (0-1)
            risk_tolerance: 'CONSERVATIVE', 'MODERATE', or 'AGGRESSIVE'
        
        Returns:
            Dict with stop_price, stop_pct, method, and trailing_stop_pct
        """
        atr_stop = StopLossCalculator.calculate_atr_stop(
            current_price, atr_value, volatility=volatility
        )
        support_stop = StopLossCalculator.calculate_support_stop(
            current_price, nearest_support
        )
        
        # Risk tolerance multipliers
        risk_multipliers = {
            'CONSERVATIVE': 0.8,   # Tighter stop
            'MODERATE': 1.0,        # Standard
            'AGGRESSIVE': 1.15      # Wider stop, allow more room
        }
        risk_mult = risk_multipliers.get(risk_tolerance, 1.0)
        
        # Determine optimal stop
        if support_stop and support_stop['stop_price'] >= atr_stop['stop_price']:
            # Support stop is tighter - use it for better risk/reward
            stop_price = support_stop['stop_price'] * risk_mult
            method = f"Support (below ${support_stop['support_price']:.2f})"
        elif support_stop:
            # ATR stop is tighter - use it but respect support
            stop_price = max(atr_stop['stop_price'], support_stop['stop_price'] * 0.95) * risk_mult
            method = f"ATR + Support (max of ATR=${atr_stop['stop_price']:.2f}, 95% support=${support_stop['stop_price']*0.95:.2f})"
        else:
            # No support data, use pure ATR
            stop_price = atr_stop['stop_price'] * risk_mult
            method = "ATR (no support data)"
        
        stop_pct = (current_price - stop_price) / current_price * 100
        
        # Trailing stop percentage (for ongoing position management)
        if volatility > 0.60:
            trailing_stop_pct = 12.0
        elif volatility > 0.40:
            trailing_stop_pct = 8.0
        elif volatility > 0.25:
            trailing_stop_pct = 5.0
        else:
            trailing_stop_pct = 3.0
        
        return {
            'stop_price': round(stop_price, 2),
            'stop_pct': round(stop_pct, 2),
            'method': method,
            'atr_stop': atr_stop,
            'support_stop': support_stop,
            'trailing_stop_pct': trailing_stop_pct,
            'risk_tolerance': risk_tolerance,
            'risk_multiplier': risk_mult
        }


class MarketEnvironmentAnalyzer:
    """Assess market environment: VIX/volatility regime, breadth, sector rotation.
    
    Integrates market conditions into stock-level recommendations.
    Reduces false positives by contextualizing signals within broader market regime.
    """
    
    @staticmethod
    def classify_vix_regime(vix: float) -> Dict:
        """Classify market regime based on VIX level.
        
        Args:
            vix: VIX index value (or VIXM as proxy, since VIX is not tradeable)
        
        Returns:
            Dict with regime, position_adjustment, description
        """
        if vix > 35:
            return {
                'regime': 'CRISIS',
                'label': '恐慌/危机',
                'position_adjustment': 0.3,  # Reduce position by 70%
                'description': 'Extreme fear - capitulation selling. Cash is king.',
                'buy_signal_bonus': 10  # Contrarian: oversold opportunities
            }
        elif vix > 25:
            return {
                'regime': 'FEARFUL',
                'label': '恐惧',
                'position_adjustment': 0.5,  # Reduce position by 50%
                'description': 'Elevated fear - opportunities but volatile.',
                'buy_signal_bonus': 5
            }
        elif vix > 18:
            return {
                'regime': 'ELEVATED',
                'label': '略高波动',
                'position_adjustment': 0.8,  # Reduce position by 20%
                'description': 'Above-average volatility. Selective entries.',
                'buy_signal_bonus': 2
            }
        elif vix > 12:
            return {
                'regime': 'NORMAL',
                'label': '正常',
                'position_adjustment': 1.0,  # Normal position
                'description': 'Normal volatility regime. Standard strategy.',
                'buy_signal_bonus': 0
            }
        else:
            return {
                'regime': 'COMPLACENT',
                'label': '自满/低波动',
                'position_adjustment': 0.7,  # Reduce - complacency precedes volatility
                'description': 'Complacency risk. Low VIX can precede sharp corrections.',
                'buy_signal_bonus': -5  # Penalty: don't chase in complacent markets
            }
    
    @staticmethod
    def analyze_market_breadth(symbols_performance: List[float]) -> Dict:
        """Analyze market breadth from a list of stock performance values.
        
        Args:
            symbols_performance: List of daily % changes for multiple stocks
        
        Returns:
            Dict with breadth ratio, status, and adjustment
        """
        if not symbols_performance:
            return {
                'breadth_ratio': None,
                'status': 'UNKNOWN',
                'description': 'No breadth data available',
                'position_adjustment': 1.0
            }
        
        advancing = sum(1 for p in symbols_performance if p > 0)
        declining = sum(1 for p in symbols_performance if p < 0)
        total = len(symbols_performance)
        
        if total == 0:
            return {
                'breadth_ratio': None,
                'status': 'UNKNOWN',
                'description': 'No breadth data',
                'position_adjustment': 1.0
            }
        
        breadth_ratio = advancing / total if total > 0 else 0.5
        
        if breadth_ratio > 0.70:
            status = 'STRONG_BREADTH'
            description = f'Broad-based rally ({advancing}/{total} advancing)'
            adjustment = 1.1  # 10% bonus for broad participation
        elif breadth_ratio > 0.55:
            status = 'MODERATE_BREADTH'
            description = f'Moderate participation ({advancing}/{total} advancing)'
            adjustment = 1.0
        elif breadth_ratio > 0.40:
            status = 'WEAK_BREADTH'
            description = f'Weak breadth ({advancing}/{total} advancing)'
            adjustment = 0.85
        else:
            status = 'NARROW'
            description = f'Narrow leadership ({advancing}/{total} advancing) - bearish'
            adjustment = 0.70
        
        return {
            'breadth_ratio': round(breadth_ratio, 2),
            'status': status,
            'description': description,
            'position_adjustment': adjustment,
            'advancing': advancing,
            'declining': declining,
            'total': total
        }
    
    @staticmethod
    def assess_market_environment(vix: Optional[float] = None,
                                  market_sentiment: Optional[float] = None,
                                  market_valuation: Optional[float] = None,
                                  is_ath: bool = False,
                                  breadth_data: Optional[List[float]] = None) -> Dict:
        """Comprehensive market environment assessment.
        
        Args:
            vix: VIX/VIXM index value
            market_sentiment: Sentiment score (0-100)
            market_valuation: Valuation score (0-100)
            is_ath: Whether market is at all-time highs
            breadth_data: List of daily % changes for multiple stocks
        
        Returns:
            Dict with environment_score, position_cap, warnings, regime
        """
        env_score = 0
        warnings = []
        
        # 1. Volatility Regime (VIX)
        vix_regime = None
        if vix is not None:
            vix_regime = MarketEnvironmentAnalyzer.classify_vix_regime(vix)
            regime_score = 0
            if vix_regime['regime'] == 'NORMAL':
                regime_score = 80
            elif vix_regime['regime'] == 'ELEVATED':
                regime_score = 55
            elif vix_regime['regime'] == 'FEARFUL':
                regime_score = 35
                warnings.append(f"VIX regime: {vix_regime['label']} - {vix_regime['description']}")
            elif vix_regime['regime'] == 'CRISIS':
                regime_score = 15
                warnings.append(f"VIX regime: {vix_regime['label']} - {vix_regime['description']}")
            elif vix_regime['regime'] == 'COMPLACENT':
                regime_score = 50
                warnings.append(f"VIX regime: {vix_regime['label']} - {vix_regime['description']}")
            env_score += regime_score * 0.30
        
        # 2. Sentiment (0-100)
        if market_sentiment is not None:
            if market_sentiment > 80:
                sentiment_score = 15  # Extreme greed = risky
                warnings.append(f"Extreme greed sentiment ({market_sentiment})")
            elif market_sentiment > 70:
                sentiment_score = 30
            elif market_sentiment > 60:
                sentiment_score = 55
            elif market_sentiment > 40:
                sentiment_score = 75
            elif market_sentiment > 20:
                sentiment_score = 85
            else:
                sentiment_score = 90  # Extreme fear = opportunity
                warnings.append(f"Extreme fear sentiment ({market_sentiment}) - contrarian opportunity")
            env_score += sentiment_score * 0.25
        
        # 3. Valuation (0-100)
        if market_valuation is not None:
            if market_valuation > 85:
                valuation_score = 15
                warnings.append(f"Extreme market valuation ({market_valuation}) - position cap active")
            elif market_valuation > 70:
                valuation_score = 35
            elif market_valuation > 50:
                valuation_score = 55
            elif market_valuation > 30:
                valuation_score = 75
            else:
                valuation_score = 90
            env_score += valuation_score * 0.25
        
        # 4. All-Time High Risk
        ath_score = 50
        if is_ath:
            ath_score = 30
            warnings.append("Market at all-time highs - momentum exhaustion risk")
        env_score += ath_score * 0.10
        
        # 5. Market Breadth
        breadth_result = MarketEnvironmentAnalyzer.analyze_market_breadth(breadth_data or [])
        breadth_score = 50
        if breadth_result.get('status') == 'STRONG_BREADTH':
            breadth_score = 80
        elif breadth_result.get('status') == 'MODERATE_BREADTH':
            breadth_score = 65
        elif breadth_result.get('status') == 'WEAK_BREADTH':
            breadth_score = 40
        elif breadth_result.get('status') == 'NARROW':
            breadth_score = 25
            warnings.append(f"Narrow market breadth: {breadth_result.get('description')}")
        env_score += breadth_score * 0.10
        
        # Classify environment
        if env_score >= 70:
            environment = 'FAVORABLE'
            position_cap = 1.0
        elif env_score >= 55:
            environment = 'NEUTRAL'
            position_cap = 0.85
        elif env_score >= 40:
            environment = 'CAUTIOUS'
            position_cap = 0.65
        elif env_score >= 25:
            environment = 'DEFENSIVE'
            position_cap = 0.40
        else:
            environment = 'HOSTILE'
            position_cap = 0.25
        
        return {
            'environment_score': round(env_score, 1),
            'environment': environment,
            'position_cap': position_cap,
            'warnings': warnings,
            'vix_regime': vix_regime,
            'breadth': breadth_result
        }


class StockAnalysisEngine:
    """
    Comprehensive stock analysis engine integrating all metrics
    """
    
    def __init__(self):
        self.risk_calculator = RiskMetricsCalculator()
        self.valuation_calculator = ValuationMetricsCalculator()
        self.technical_calculator = TechnicalIndicatorsCalculator()
        self.factor_calculator = MultiFactorCalculator()
        self.moat_analyzer = MoatAnalyzer()
        self.value_trap_detector = ValueTrapDetector()
        self.conflict_resolver = ConflictResolver()
    
    def analyze_stock(self, stock_data: StockData, market_returns: Optional[List[float]] = None,
                      market_environment: Optional[Dict] = None) -> Dict:
        """
        Perform comprehensive analysis of a stock
        
        Args:
            stock_data: StockData object with all required data
            market_returns: Optional market returns for beta calculation
            market_environment: Optional market environment assessment from MarketEnvironmentAnalyzer
        
        Returns:
            analysis: Comprehensive analysis dictionary
        """
        analysis = {
            'symbol': stock_data.symbol,
            'analysis_date': datetime.now().isoformat(),
            'current_price': stock_data.current_price
        }
        
        # 1. Risk Analysis
        risk_analysis = self.risk_calculator.analyze_stock_risk(stock_data, market_returns)
        analysis['risk_analysis'] = risk_analysis
        
        # 2. Valuation Analysis
        valuation_analysis = self.valuation_calculator.analyze_stock_valuation(stock_data)
        analysis['valuation_analysis'] = valuation_analysis
        
        # 3. Technical Analysis
        technical_indicators = {}
        
        # Calculate moving averages
        if stock_data.prices:
            ma_dict = self.technical_calculator.calculate_moving_averages(stock_data.prices, [20, 50, 200])
            for period, values in ma_dict.items():
                technical_indicators[f'ma_{period}'] = values
            
            # Calculate RSI
            rsi = self.technical_calculator.calculate_rsi(stock_data.prices)
            if rsi:
                technical_indicators['rsi'] = rsi
            
            # Calculate MACD
            macd = self.technical_calculator.calculate_macd(stock_data.prices)
            technical_indicators.update(macd)
            
            # Calculate Bollinger Bands
            bb = self.technical_calculator.calculate_bollinger_bands(stock_data.prices)
            technical_indicators.update({
                'bb_upper': bb.get('upper_band', []),
                'bb_middle': bb.get('middle_band', []),
                'bb_lower': bb.get('lower_band', []),
                'bb_bandwidth': bb.get('bandwidth', [])
            })
        
        # Calculate Stochastic if highs and lows available
        if all([stock_data.highs, stock_data.lows, stock_data.prices]):
            stochastic = self.technical_calculator.calculate_stochastic(
                stock_data.highs, stock_data.lows, stock_data.prices
            )
            if stochastic:
                technical_indicators.update(stochastic)
        
        # Calculate ATR if highs, lows, and closes available
        if all([stock_data.highs, stock_data.lows, stock_data.prices]):
            atr = self.technical_calculator.calculate_atr(
                stock_data.highs, stock_data.lows, stock_data.prices
            )
            if atr:
                technical_indicators['atr'] = atr
        
        # Calculate price momentum rates for neutral RSI enhancement
        if stock_data.prices and len(stock_data.prices) >= 22:
            technical_indicators['_price_roc'] = TechnicalIndicatorsCalculator.calculate_price_roc(
                stock_data.prices, [5, 10, 21]
            )
            technical_indicators['_trend_strength'] = TechnicalIndicatorsCalculator.calculate_trend_strength(
                stock_data.prices
            )
        
        # Calculate technical score
        if stock_data.current_price and technical_indicators:
            technical_score, tech_breakdown = self.technical_calculator.calculate_technical_score(
                technical_indicators, stock_data.current_price
            )
            technical_indicators['technical_score'] = technical_score
            technical_indicators['technical_breakdown'] = tech_breakdown
        
        analysis['technical_analysis'] = technical_indicators
        
        # Add nearest support/resistance from available indicators
        if stock_data.current_price and technical_indicators:
            current = stock_data.current_price
            nearest_support = None
            nearest_resistance = None
            
            ma_50 = technical_indicators.get('ma_50', [])
            ma_200 = technical_indicators.get('ma_200', [])
            bb_upper = technical_indicators.get('bb_upper', [])
            bb_lower = technical_indicators.get('bb_lower', [])
            
            candidates_below = []
            candidates_above = []
            
            for lst in [ma_50, ma_200, bb_lower]:
                if lst:
                    v = lst[-1]
                    if v is not None and v < current:
                        candidates_below.append(v)
            for lst in [ma_50, ma_200, bb_upper]:
                if lst:
                    v = lst[-1]
                    if v is not None and v > current:
                        candidates_above.append(v)
            
            if candidates_below:
                best = max(candidates_below)
                nearest_support = {'price': round(best, 2), 'source': 'technical_indicator'}
            if candidates_above:
                best = min(candidates_above)
                nearest_resistance = {'price': round(best, 2), 'source': 'technical_indicator'}
            
            technical_indicators['nearest_support'] = nearest_support
            technical_indicators['nearest_resistance'] = nearest_resistance
        
        # 4. Multi-Factor Analysis
        factor_scores = {}
        
        # Prepare financials dictionary
        financials = {
            'roe': stock_data.net_income / stock_data.shareholders_equity 
                   if stock_data.net_income and stock_data.shareholders_equity else None,
            'gross_margin': None,
            'earnings_stability_score': None,
            'debt_to_equity': stock_data.total_debt / stock_data.shareholders_equity 
                             if stock_data.total_debt and stock_data.shareholders_equity else None,
            'pe_ratio': valuation_analysis.get('pe_ratio'),
            'ev_ebitda': valuation_analysis.get('ev_ebitda_ratio'),
            'fcf_yield': valuation_analysis.get('fcf_yield'),
            'dividend_yield': valuation_analysis.get('dividend_yield'),
            'revenue_growth': stock_data.revenue_growth,
            'eps_growth': stock_data.eps_growth,
            'estimated_growth': stock_data.estimated_growth,
            'beta': risk_analysis.get('beta')
        }
        
        # Calculate factor scores
        quality_score = self.factor_calculator.calculate_quality_score(financials)
        factor_scores['quality'] = {'score': quality_score}
        
        value_score = self.factor_calculator.calculate_value_score(
            financials, stock_data.current_price, stock_data.sector
        )
        factor_scores['value'] = {'score': value_score}
        
        growth_score = self.factor_calculator.calculate_growth_score(financials)
        factor_scores['growth'] = {'score': growth_score}
        
        momentum_score = self.factor_calculator.calculate_momentum_score(
            stock_data.prices, None
        )
        factor_scores['momentum'] = {'score': momentum_score}
        
        low_vol_score = self.factor_calculator.calculate_low_volatility_score(
            stock_data.prices, financials.get('beta')
        )
        factor_scores['low_volatility'] = {'score': low_vol_score}
        
        # Calculate composite factor score
        composite_score, factor_breakdown, strategy = self.factor_calculator.calculate_composite_factor_score(
            factor_scores
        )
        
        analysis['factor_analysis'] = {
            'factor_scores': factor_scores,
            'composite_score': composite_score,
            'factor_breakdown': factor_breakdown,
            'strategy': strategy
        }
        
        # 5. Moat Analysis
        analysis['moat_analysis'] = self.moat_analyzer.analyze_moat(stock_data)
        
        # 6. Value Trap Detection
        analysis['value_trap_analysis'] = self.value_trap_detector.detect_trap(stock_data)
        
        # 7. Overall Assessment
        analysis['overall_assessment'] = self._generate_overall_assessment(
            analysis, market_environment
        )
        
        # Phase 2: Include market environment in output
        if market_environment:
            analysis['market_environment'] = market_environment
        
        return analysis
    
    def _generate_overall_assessment(self, analysis: Dict,
                                      market_environment: Optional[Dict] = None) -> Dict:
        """
        Generate overall assessment based on all analyses.
        
        Optimizations (Phase 1.5+):
        1. Lowered buy thresholds (65 instead of 70) for better opportunity capture
        2. Added trend confirmation bonus for oversold + below MA scenarios
        3. Enhanced RSI oversold signals integration
        4. Momentum enhancement for neutral RSI zone (Phase 2 fix for COIN.US)
        5. Dynamic stop-loss via ATR + support levels (Phase 2)
        6. Market environment integration (Phase 2)
        """
        # Extract scores
        risk_score = analysis['risk_analysis'].get('risk_score', 50)
        valuation_score = analysis['valuation_analysis'].get('valuation_score', 50)
        technical_score = analysis['technical_analysis'].get('technical_score', 50)
        factor_score = analysis['factor_analysis'].get('composite_score', 50)
        
        # Calculate weighted overall score
        weights = get_config('overall', 'weights', default={
            'risk': 0.10,
            'valuation': 0.35,
            'technical': 0.30,
            'factor': 0.25
        })
        overall_score = (
            (100 - risk_score) * weights['risk'] +
            (100 - valuation_score) * weights['valuation'] +
            technical_score * weights['technical'] +
            factor_score * weights['factor']
        )
        
        # Phase 1.5: Add trend confirmation bonus for oversold scenarios
        tech_indicators = analysis.get('technical_analysis', {})
        rsi_values = tech_indicators.get('rsi', [])
        ma_50_values = tech_indicators.get('ma_50', [])
        
        if rsi_values and ma_50_values:
            current_rsi = rsi_values[-1] if rsi_values else None
            current_ma_50 = ma_50_values[-1] if ma_50_values else None
            current_price = analysis.get('current_price', 0)
            
            if current_rsi and current_ma_50 and current_price:
                if current_rsi < 35 and current_price < current_ma_50:
                    overall_score += 8
                elif current_rsi < 40 and current_price < current_ma_50:
                    overall_score += 4
        
        # Phase 2: Market environment adjustment
        env_adjustment = 0
        env_details = None
        if market_environment:
            env_score = market_environment.get('environment_score', 50)
            env_pos_cap = market_environment.get('position_cap', 1.0)
            env_details = market_environment
            
            # Apply environment adjustment to overall score
            if env_score >= 70:
                env_adjustment = 3   # Favorable: small boost
            elif env_score >= 55:
                env_adjustment = 0   # Neutral: no change
            elif env_score >= 40:
                env_adjustment = -5  # Cautious: reduce
            elif env_score >= 25:
                env_adjustment = -10 # Defensive: significant reduction
            else:
                env_adjustment = -15 # Hostile: major reduction
            
            overall_score += env_adjustment
            overall_score = max(0, min(100, overall_score))
            
            # Market environment warnings can override position sizing
            for warning in market_environment.get('warnings', []):
                pass  # Warnings passed through, handled in reporting
        
        # Clamp score to 0-100
        overall_score = max(0, min(100, overall_score))
        
        moat = analysis.get('moat_analysis', {})
        moat_score = moat.get('moat_score', 0)
        if moat_score >= 7:
            overall_score += 5
        elif moat_score >= 5:
            overall_score += 3
        elif moat_score < 3:
            overall_score -= 5
        
        value_trap = analysis.get('value_trap_analysis', {})
        trap_score = value_trap.get('trap_score', 0)
        if trap_score >= 50:
            overall_score -= 15
        elif trap_score >= 30:
            overall_score -= 8
        elif trap_score >= 15:
            overall_score -= 3
        
        overall_score = max(0, min(100, overall_score))
        
        # Get volatility for position sizing
        volatility = analysis['risk_analysis'].get('historical_volatility', 0.30)
        position_recommendation = RiskMetricsCalculator.get_volatility_position_recommendation(
            volatility=volatility,
            base_position=0.10
        )
        
        # Phase 2: Apply market environment position cap
        if market_environment:
            env_pos_cap = market_environment.get('position_cap', 1.0)
            capped_size = position_recommendation['recommended_position_size'] * env_pos_cap
            position_recommendation['recommended_position_size'] = round(max(0.02, capped_size), 3)
            position_recommendation['environment_cap_applied'] = env_pos_cap
        
        rec_thresholds = get_config('overall', 'recommendation_thresholds', default={
            'strong_buy': 75, 'buy': 65, 'hold': 55, 'weak_hold': 45, 'sell': 35
        })
        
        if overall_score >= rec_thresholds.get('strong_buy', 75):
            recommendation = 'STRONG BUY'
            confidence = 'HIGH'
        elif overall_score >= rec_thresholds.get('buy', 65):
            recommendation = 'BUY'
            confidence = 'MEDIUM-HIGH'
        elif overall_score >= rec_thresholds.get('hold', 55):
            recommendation = 'HOLD'
            confidence = 'MEDIUM'
        elif overall_score >= rec_thresholds.get('weak_hold', 45):
            recommendation = 'WEAK HOLD'
            confidence = 'LOW-MEDIUM'
        elif overall_score >= rec_thresholds.get('sell', 35):
            recommendation = 'SELL'
            confidence = 'MEDIUM'
        else:
            recommendation = 'STRONG SELL'
            confidence = 'HIGH'
        
        # Adjust recommendation text for high-volatility stocks
        if position_recommendation['volatility_tier'] in ['VERY_HIGH', 'HIGH']:
            recommendation_note = f"{recommendation} (Reduce position to {position_recommendation['recommended_position_size']*100:.1f}% due to {position_recommendation['volatility_tier']} volatility)"
        else:
            recommendation_note = recommendation
        
        # Phase 2: Calculate dynamic stop-loss
        stop_loss = None
        current_price = analysis.get('current_price', 0)
        atr_values = tech_indicators.get('atr', [])
        atr_value = None
        if atr_values:
            for v in reversed(atr_values):
                if v is not None:
                    atr_value = v
                    break
        
        # Get support levels from tech indicators
        nearest_support = tech_indicators.get('nearest_support')
        
        if current_price and atr_value:
            stop_loss = StopLossCalculator.calculate_dynamic_stop(
                current_price=current_price,
                atr_value=atr_value,
                nearest_support=nearest_support,
                volatility=volatility
            )
        elif current_price:
            # Fallback: use percentage-based stop
            if volatility > 0.60:
                stop_pct = 12.0
            elif volatility > 0.40:
                stop_pct = 8.0
            elif volatility > 0.25:
                stop_pct = 5.0
            else:
                stop_pct = 4.0
            stop_loss = {
                'stop_price': round(current_price * (1 - stop_pct/100), 2),
                'stop_pct': stop_pct,
                'method': 'Percentage (no ATR data)',
                'trailing_stop_pct': stop_pct
            }
        
        # Run conflict resolution
        signals = {}
        valuation_attractiveness = analysis.get('valuation_analysis', {}).get('valuation_attractiveness', '')
        if 'Undervalued' in valuation_attractiveness:
            signals['valuation'] = {'direction': 'bullish', 'strength': 0.7, 'reason': valuation_attractiveness}
        elif 'Overvalued' in valuation_attractiveness:
            signals['valuation'] = {'direction': 'bearish', 'strength': 0.7, 'reason': valuation_attractiveness}
        else:
            signals['valuation'] = {'direction': 'neutral', 'strength': 0.5, 'reason': 'Fairly valued'}
        
        if technical_score > 60:
            signals['technical'] = {'direction': 'bullish', 'strength': technical_score / 100, 'reason': f'Technical score: {technical_score:.0f}'}
        elif technical_score < 40:
            signals['technical'] = {'direction': 'bearish', 'strength': (100 - technical_score) / 100, 'reason': f'Technical score: {technical_score:.0f}'}
        else:
            signals['technical'] = {'direction': 'neutral', 'strength': 0.5, 'reason': 'Neutral technicals'}
        
        if moat_score >= 5:
            signals['business_quality'] = {'direction': 'bullish', 'strength': moat_score / 10, 'reason': f'Moat: {moat.get("moat_width", "N/A")} ({moat_score:.1f}/10)'}
        elif moat_score < 3:
            signals['business_quality'] = {'direction': 'bearish', 'strength': (10 - moat_score) / 10, 'reason': f'Weak moat ({moat_score:.1f}/10)'}
        else:
            signals['business_quality'] = {'direction': 'neutral', 'strength': 0.5, 'reason': 'Moderate moat'}
        
        if risk_score > 60:
            signals['short_term'] = {'direction': 'bearish', 'strength': risk_score / 100, 'reason': f'High risk: {risk_score:.0f}'}
        
        # Add market regime signal if available
        if market_environment and market_environment.get('vix_regime'):
            vix_regime = market_environment['vix_regime']
            if vix_regime['regime'] in ('CRISIS', 'FEARFUL'):
                signals['market_regime'] = {'direction': 'bearish', 'strength': 0.8, 
                    'reason': f"VIX {vix_regime['regime']} - {vix_regime['description']}"}
            elif vix_regime['regime'] == 'COMPLACENT':
                signals['market_regime'] = {'direction': 'neutral', 'strength': 0.4,
                    'reason': f"VIX {vix_regime['regime']} - {vix_regime['description']}"}
        
        conflict_resolution = self.conflict_resolver.resolve(signals, 'LONG_TERM')
        
        result = {
            'overall_score': overall_score,
            'recommendation': recommendation,
            'recommendation_note': recommendation_note,
            'confidence': confidence,
            'position_sizing': position_recommendation,
            'moat_adjustment': f"Moat {moat.get('moat_width', 'N/A')} ({moat_score:.1f}/10)",
            'value_trap_risk': f"{value_trap.get('risk_level', 'UNKNOWN')} (score: {trap_score})",
            'conflict_resolution': conflict_resolution,
            'score_breakdown': {
                'risk_score': risk_score,
                'valuation_score': valuation_score,
                'technical_score': technical_score,
                'factor_score': factor_score
            }
        }
        
        # Phase 2: Include stop-loss and market environment in result
        if stop_loss:
            result['stop_loss'] = stop_loss
        if env_adjustment != 0:
            result['environment_adjustment'] = env_adjustment
            result['environment'] = market_environment
        
        return result
    
    def generate_report(self, analysis: Dict, format: str = 'markdown') -> str:
        """
        Generate analysis report in specified format
        
        Args:
            analysis: Analysis dictionary (single stock or portfolio)
            format: Output format ('markdown' or 'json')
        
        Returns:
            report: Formatted report
        """
        if format == 'json':
            return json.dumps(analysis, indent=2, default=str)
        
        # Detect portfolio report (has positions+summary but no top-level symbol)
        if 'positions' in analysis and 'summary' in analysis and 'symbol' not in analysis:
            return self.generate_portfolio_report(analysis)
        
        # Helper function for safe formatting
        def safe_format(value, fmt, default='N/A'):
            if value is None:
                return default
            try:
                return f"{value:{fmt}}"
            except (ValueError, TypeError):
                return default
        
        # Markdown format
        md = f"""
# Stock Analysis Report: {analysis['symbol']}
**Analysis Date:** {analysis['analysis_date']}
**Current Price:** ${analysis['current_price']:.2f}

## Overall Assessment
**Recommendation:** **{analysis['overall_assessment']['recommendation']}** ({analysis['overall_assessment']['confidence']} confidence)
**Overall Score:** {analysis['overall_assessment']['overall_score']:.1f}/100

### Score Breakdown:
- Risk Score: {analysis['overall_assessment']['score_breakdown']['risk_score']:.1f}/100
- Valuation Score: {analysis['overall_assessment']['score_breakdown']['valuation_score']:.1f}/100
- Technical Score: {analysis['overall_assessment']['score_breakdown']['technical_score']:.1f}/100  
- Factor Score: {analysis['overall_assessment']['score_breakdown']['factor_score']:.1f}/100

## Risk Analysis
"""
        
        risk = analysis['risk_analysis']
        md += f"""
**Risk Score:** {risk.get('risk_score', 'N/A')}/100

**Key Metrics:**
- Sharpe Ratio: {safe_format(risk.get('sharpe_ratio'), '.2f')}
- Maximum Drawdown: {safe_format(risk.get('max_drawdown'), '.2%')}
- Sortino Ratio: {safe_format(risk.get('sortino_ratio'), '.2f')}
- Beta: {safe_format(risk.get('beta'), '.2f')}
- Historical Volatility: {safe_format(risk.get('historical_volatility'), '.2%')}
- 95% VaR: {safe_format(risk.get('var_95'), '.2%')}
- Calmar Ratio: {safe_format(risk.get('calmar_ratio'), '.2f')}
"""
        
        valuation = analysis['valuation_analysis']
        md += f"""
## Valuation Analysis
**Valuation Score:** {valuation.get('valuation_score', 'N/A')}/100
**Attractiveness:** {valuation.get('valuation_attractiveness', 'N/A')}

**Key Metrics:**
"""
        
        if 'pe_ratio' in valuation:
            md += f"- P/E Ratio: {valuation['pe_ratio']:.2f}x ({valuation.get('pe_percentile', 'N/A')})\n"
        if 'ev_ebitda_ratio' in valuation:
            md += f"- EV/EBITDA: {valuation['ev_ebitda_ratio']:.2f}x\n"
        if 'peg_ratio' in valuation:
            md += f"- PEG Ratio: {valuation['peg_ratio']:.2f}\n"
        if 'p_fcf_ratio' in valuation:
            md += f"- P/FCF: {valuation['p_fcf_ratio']:.2f}x\n"
        if 'fcf_yield' in valuation:
            md += f"- FCF Yield: {valuation['fcf_yield']:.2%}\n"
        if 'graham_intrinsic_value' in valuation:
            md += f"- Graham Intrinsic Value: ${valuation['graham_intrinsic_value']:.2f}\n"
        
        md += """
## Technical Analysis
"""
        
        tech = analysis['technical_analysis']
        if 'technical_score' in tech:
            md += f"**Technical Score:** {tech['technical_score']:.1f}/100\n\n"
        
        # Add key technical signals
        if 'rsi' in tech and tech['rsi']:
            latest_rsi = tech['rsi'][-1]
            if latest_rsi < 20:
                rsi_signal = "EXTREME OVERSOLD (Strong Buy)"
            elif latest_rsi < 30:
                rsi_signal = "DEEP OVERSOLD (Buy)"
            elif latest_rsi < 35:
                rsi_signal = "OVERSOLD (Opportunity)"
            elif latest_rsi > 80:
                rsi_signal = "EXTREME OVERBOUGHT (Strong Sell)"
            elif latest_rsi > 70:
                rsi_signal = "OVERBOUGHT (Sell)"
            elif latest_rsi > 65:
                rsi_signal = "APPROACHING OVERBOUGHT"
            else:
                rsi_signal = "Neutral"
            md += f"- RSI: {latest_rsi:.1f} ({rsi_signal})\n"
        
        if 'macd_line' in tech and 'signal_line' in tech:
            macd = tech['macd_line'][-1] if tech['macd_line'] else None
            signal = tech['signal_line'][-1] if tech['signal_line'] else None
            if macd and signal:
                macd_signal = "Bullish" if macd > signal else "Bearish"
                md += f"- MACD: {macd_signal} (MACD: {macd:.4f}, Signal: {signal:.4f})\n"
        
        md += """
## Multi-Factor Analysis
"""
        
        factor = analysis['factor_analysis']
        md += f"**Composite Factor Score:** {factor.get('composite_score', 'N/A'):.1f}/100\n"
        md += f"**Strategy:** {factor.get('strategy', 'N/A').replace('_', ' ').title()}\n\n"
        
        md += "**Factor Scores:**\n"
        for factor_name, factor_data in factor.get('factor_scores', {}).items():
            score = factor_data.get('score', 50)
            md += f"- {factor_name.title()}: {score:.1f}/100\n"
        
        md += self._generate_investment_thesis(analysis)
        
        return md

    def _generate_investment_thesis(self, analysis: Dict) -> str:
        """Generate investment thesis from analysis data."""
        md = "\n## Investment Thesis\n"
        md += "Based on the comprehensive analysis:\n\n"
        
        strengths = []
        risks = []
        
        risk = analysis.get('risk_analysis', {})
        valuation = analysis.get('valuation_analysis', {})
        tech = analysis.get('technical_analysis', {})
        overall = analysis.get('overall_assessment', {})
        
        if risk.get('sharpe_ratio') and risk['sharpe_ratio'] > 1.0:
            strengths.append(f"Strong risk-adjusted returns (Sharpe: {risk['sharpe_ratio']:.2f})")
        if risk.get('max_drawdown') and risk['max_drawdown'] > -0.15:
            strengths.append(f"Limited drawdown risk (Max DD: {risk['max_drawdown']:.1%})")
        if valuation.get('valuation_attractiveness') in ('Undervalued', 'Significantly Undervalued'):
            strengths.append(f"Undervalued ({valuation.get('valuation_attractiveness', '')})")
        if valuation.get('peg_ratio') and valuation['peg_ratio'] < 1.0:
            strengths.append(f"PEG ratio suggests growth at reasonable price ({valuation['peg_ratio']:.2f})")
        if tech.get('rsi') and tech['rsi'][-1] < 35:
            strengths.append(f"RSI oversold ({tech['rsi'][-1]:.1f}) - potential bounce opportunity")
        
        # Phase 2: Add momentum-based strengths
        roc = tech.get('_price_roc', {})
        roc_5 = roc.get(5)
        roc_10 = roc.get(10)
        if roc_5 is not None and roc_5 > 3:
            strengths.append(f"Strong 5-day momentum: +{roc_5:.1f}%")
        if roc_10 is not None and roc_10 > 5:
            strengths.append(f"Strong 10-day trend: +{roc_10:.1f}%")
        
        if risk.get('historical_volatility') and risk['historical_volatility'] > 0.40:
            risks.append(f"High volatility ({risk['historical_volatility']:.1%}) - use position sizing")
        if risk.get('max_drawdown') and risk['max_drawdown'] < -0.25:
            risks.append(f"Significant drawdown history (Max DD: {risk['max_drawdown']:.1%})")
        if valuation.get('valuation_attractiveness') in ('Overvalued', 'Significantly Overvalued'):
            risks.append(f"Overvalued ({valuation.get('valuation_attractiveness', '')})")
        if tech.get('rsi') and tech['rsi'][-1] > 70:
            risks.append(f"RSI overbought ({tech['rsi'][-1]:.1f}) - pullback risk")
        if valuation.get('pe_ratio') and valuation['pe_ratio'] > 30:
            risks.append(f"High P/E ratio ({valuation['pe_ratio']:.1f}x) - elevated valuation")
        
        # Phase 2: Market environment risks
        market_env = analysis.get('market_environment', {})
        if market_env.get('warnings'):
            for w in market_env['warnings'][:2]:
                risks.append(f"Market: {w}")
        
        pos_sizing = overall.get('position_sizing', {})
        stop_loss = overall.get('stop_loss')
        
        md += "### Strengths:\n"
        if strengths:
            for i, s in enumerate(strengths[:3], 1):
                md += f"{i}. {s}\n"
        else:
            md += "1. No strong bullish signals identified\n"
        
        md += "\n### Risks:\n"
        if risks:
            for i, r in enumerate(risks[:3], 1):
                md += f"{i}. {r}\n"
        else:
            md += "1. No significant risks identified\n"
        
        md += "\n### Action Plan:\n"
        current_price = analysis.get('current_price', 0)
        rec = overall.get('recommendation', 'HOLD')
        rec_pos = pos_sizing.get('recommended_position_size', 0.10)
        
        if 'BUY' in rec and current_price:
            support = tech.get('nearest_support')
            resistance = tech.get('nearest_resistance')
            entry = current_price * 0.98
            target = current_price * 1.10
            
            if support and support.get('price'):
                entry = support['price'] * 1.01
            if resistance and resistance.get('price'):
                target = resistance['price']
            
            # Phase 2: Use dynamic stop-loss if available
            if stop_loss:
                stop = stop_loss['stop_price']
                stop_method = stop_loss.get('method', 'calculated')
            else:
                stop = current_price * 0.92
                if support and support.get('price'):
                    stop = support['price'] * 0.98
                stop_method = 'percentage-based'
            
            md += f"- **Entry Price:** ${entry:.2f}\n"
            md += f"- **Stop Loss:** ${stop:.2f} ({stop_method})\n"
            md += f"- **Target Price:** ${target:.2f}\n"
            
            # Add trailing stop info
            if stop_loss and stop_loss.get('trailing_stop_pct'):
                md += f"- **Trailing Stop:** {stop_loss['trailing_stop_pct']:.1f}% below recent high\n"
        elif 'SELL' in rec and current_price:
            md += f"- **Current Price:** ${current_price:.2f} (consider reducing)\n"
            md += f"- **Exit Target:** ${current_price * 0.95:.2f}\n"
        else:
            md += f"- **Current Price:** ${current_price:.2f}\n"
            md += "- **Action:** Monitor and hold\n"
            if stop_loss:
                md += f"- **Hard Stop:** ${stop_loss['stop_price']:.2f} ({stop_loss.get('stop_pct', 'N/A')}% below)\n"
        
        md += f"- **Position Size:** {rec_pos * 100:.1f}% of portfolio\n"
        
        # Phase 2: Market environment context
        if market_env.get('environment'):
            env_adj = overall.get('environment_adjustment', 0)
            adj_str = f"{env_adj:+d}" if env_adj else "0"
            md += f"- **Market Environment:** {market_env['environment']} (adjustment: {adj_str} pts)\n"
        
        # Moat Analysis section
        moat = analysis.get('moat_analysis', {})
        if moat:
            md += f"\n## Moat Analysis\n"
            md += f"**Moat Width:** {moat.get('moat_width', 'N/A')}\n"
            md += f"**Moat Score:** {moat.get('moat_score', 0):.1f}/10\n"
            md += f"**Required Safety Margin:** {moat.get('required_safety_margin', 'N/A')}\n\n"
            for component, data in moat.get('components', {}).items():
                if data.get('score', 0) > 0:
                    md += f"- **{component.title()}:** {data['score']:.1f}/2.0"
                    if data.get('reasons'):
                        md += f" ({'; '.join(data['reasons'])})"
                    md += "\n"
        
        # Value Trap Detection section
        value_trap = analysis.get('value_trap_analysis', {})
        if value_trap:
            md += f"\n## Value Trap Detection\n"
            md += f"**Trap Score:** {value_trap.get('trap_score', 0)}/100 ({value_trap.get('risk_level', 'UNKNOWN')})\n"
            md += f"**Action:** {value_trap.get('action', 'OK')}\n"
            if value_trap.get('warnings'):
                md += "\n**Warnings:**\n"
                for w in value_trap['warnings'][:3]:
                    md += f"- {w}\n"
        
        return md
    
    def generate_portfolio_report(self, analysis: Dict) -> str:
        """Generate markdown report for portfolio analysis."""
        summary = analysis.get('summary', {})
        risk = analysis.get('portfolio_risk', {})
        
        md = f"""# Portfolio Analysis Report
**Analysis Date:** {analysis.get('analysis_date', 'N/A')}

## Portfolio Summary
- **Total Positions:** {summary.get('total_positions', 0)} ({summary.get('stock_positions', 0)} stocks, {summary.get('option_positions', 0)} options)
- **Total Market Value:** ${summary.get('total_market_value', 0):,.2f}
- **Total P/L:** ${summary.get('total_profit_loss', 0):,.2f}
- **Average Score:** {summary.get('average_score', 0):.1f}/100

## Stock Positions
"""
        for pos in analysis.get('positions', []):
            symbol = pos.get('symbol', 'N/A')
            oa = pos.get('overall_assessment', {})
            score = oa.get('overall_score', 'N/A')
            rec = oa.get('recommendation', 'N/A')
            pd = pos.get('position_details', {})
            mv = pd.get('market_value', 0)
            pnl = pd.get('profit_loss', 0)
            pnl_pct = pd.get('pnl_percent', 0)
            md += f"- **{symbol}**: Score {score}/100 | {rec} | ${mv:,.2f} | P/L ${pnl:,.2f} ({pnl_pct:+.1f}%)\n"
        
        md += "\n## Option Positions\n"
        for opt in analysis.get('option_positions', []):
            strategy = opt.get('strategy', {})
            md += f"- {strategy.get('name', 'N/A')}: P/L ${opt.get('pnl', 0):,.2f}\n"
        
        if risk:
            md += f"""
## Portfolio Risk
- **Concentration Risk:** {risk.get('concentration_risk', 'N/A')}
- **Sector Diversification:** {risk.get('sector_diversification', 'N/A')}
"""
        
        md += "\n---\n"
        md += "*This report is generated automatically for informational purposes only.*\n"
        return md
if __name__ == "__main__":
    # Example stock data
    stock_data = StockData(
        symbol="AAPL.US",
        prices=[150.0, 152.5, 151.0, 153.0, 155.5, 154.0, 156.0, 158.5, 157.0, 159.5],
        current_price=159.5,
        market_cap=2500000000000,
        sector="Technology",
        eps=6.5,
        revenue=385000000000,
        ebitda=120000000000,
        net_income=100000000000,
        shareholders_equity=65000000000,
        total_debt=120000000000,
        cash=65000000000,
        free_cash_flow=90000000000,
        revenue_growth=0.08,
        eps_growth=0.12,
        estimated_growth=0.10
    )
    
    engine = StockAnalysisEngine()
    analysis = engine.analyze_stock(stock_data)
    
    print("Comprehensive Stock Analysis")
    print("="*50)
    print(f"Symbol: {analysis['symbol']}")
    print(f"Overall Recommendation: {analysis['overall_assessment']['recommendation']}")
    print(f"Overall Score: {analysis['overall_assessment']['overall_score']:.1f}/100")
    print("\n" + "="*50)
    
    # Generate markdown report
    report = engine.generate_report(analysis, format='markdown')
    print(report[:2000])  # Print first 2000 characters