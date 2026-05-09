#!/usr/bin/env python3
"""
Comprehensive unit tests for the analysis engine.
Tests RiskMetricsCalculator, ValuationMetricsCalculator, TechnicalIndicatorsCalculator,
MultiFactorCalculator, MoatAnalyzer, ValueTrapDetector, ConflictResolver, and StockAnalysisEngine.
"""

import sys
from pathlib import Path
import pytest
import numpy as np

# Standardized import path
SKILL_DIR = Path(__file__).parent.parent.parent.parent.resolve()
sys.path.insert(0, str(SKILL_DIR))

from analysis.engine import (
    StockData,
    RiskMetricsCalculator,
    ValuationMetricsCalculator,
    TechnicalIndicatorsCalculator,
    MultiFactorCalculator,
    MoatAnalyzer,
    ValueTrapDetector,
    ConflictResolver,
    StockAnalysisEngine,
)


def _make_stock_data(**overrides):
    defaults = dict(
        symbol="TEST.US",
        prices=[100 + i * 0.5 for i in range(200)],
        volumes=[1000000] * 200,
        highs=[101 + i * 0.5 for i in range(200)],
        lows=[99 + i * 0.5 for i in range(200)],
        current_price=199.5,
        market_cap=500_000_000_000,
        sector="Technology",
        eps=8.0,
        revenue=100_000_000_000,
        ebitda=30_000_000_000,
        net_income=20_000_000_000,
        shareholders_equity=50_000_000_000,
        total_debt=10_000_000_000,
        cash=15_000_000_000,
        free_cash_flow=15_000_000_000,
        revenue_growth=0.12,
        eps_growth=0.15,
        estimated_growth=0.10,
    )
    defaults.update(overrides)
    return StockData(**defaults)


# ============================================================
# RiskMetricsCalculator
# ============================================================

class TestRiskMetrics:
    def test_sharpe_ratio_normal(self):
        returns = [0.01, -0.005, 0.015, 0.008, -0.003, 0.012] * 10
        sharpe = RiskMetricsCalculator.calculate_sharpe_ratio(returns)
        assert sharpe is not None
        assert isinstance(sharpe, float)

    def test_sharpe_ratio_insufficient_data(self):
        assert RiskMetricsCalculator.calculate_sharpe_ratio([0.01]) is None

    def test_sharpe_ratio_zero_std(self):
        assert RiskMetricsCalculator.calculate_sharpe_ratio([0.01, 0.01, 0.01]) is None

    def test_max_drawdown_normal(self):
        prices = [100, 110, 105, 95, 100, 90, 85, 95, 100]
        dd, peak, trough = RiskMetricsCalculator.calculate_max_drawdown(prices)
        assert dd is not None
        assert dd < 0
        assert -0.30 < dd < -0.10

    def test_max_drawdown_insufficient(self):
        dd, peak, trough = RiskMetricsCalculator.calculate_max_drawdown([100])
        assert dd is None

    def test_max_drawdown_monotonic_up(self):
        prices = [100, 110, 120, 130]
        dd, _, _ = RiskMetricsCalculator.calculate_max_drawdown(prices)
        assert dd == 0

    def test_sortino_ratio(self):
        returns = [0.01, -0.02, 0.03, 0.005, -0.01, 0.02] * 5
        sortino = RiskMetricsCalculator.calculate_sortino_ratio(returns)
        assert sortino is not None

    def test_beta(self):
        stock = [0.02, -0.01, 0.03, 0.01, -0.02, 0.015]
        market = [0.015, -0.005, 0.02, 0.01, -0.015, 0.01]
        beta, r2 = RiskMetricsCalculator.calculate_beta(stock, market)
        assert beta is not None
        assert 0 < beta < 3

    def test_beta_mismatched_lengths(self):
        beta, r2 = RiskMetricsCalculator.calculate_beta([0.01, 0.02], [0.01])
        assert beta is None

    def test_var_historical(self):
        returns = list(np.random.normal(0.001, 0.02, 100))
        var = RiskMetricsCalculator.calculate_var(returns, 0.95, 'historical')
        assert var is not None
        assert var < 0

    def test_var_parametric(self):
        returns = list(np.random.normal(0.001, 0.02, 100))
        var = RiskMetricsCalculator.calculate_var(returns, 0.95, 'parametric')
        assert var is not None
        assert var < 0

    def test_var_insufficient_data(self):
        assert RiskMetricsCalculator.calculate_var([0.01] * 5) is None

    def test_historical_volatility(self):
        returns = [0.01, -0.02, 0.015, -0.005, 0.01] * 10
        vol = RiskMetricsCalculator.calculate_historical_volatility(returns)
        assert vol is not None
        assert vol > 0

    def test_comprehensive_risk_score(self):
        metrics = {'max_drawdown': 0.15, 'volatility': 0.25, 'beta': 1.1, 'var_95': 0.02, 'avg_correlation': 0.5}
        score, breakdown = RiskMetricsCalculator.calculate_comprehensive_risk_score(metrics)
        assert 0 <= score <= 100
        assert 'max_drawdown' in breakdown

    def test_volatility_position_recommendation(self):
        rec = RiskMetricsCalculator.get_volatility_position_recommendation(0.70)
        assert rec['volatility_tier'] == 'VERY_HIGH'
        assert rec['recommended_position_size'] < 0.10

    def test_volatility_position_low(self):
        rec = RiskMetricsCalculator.get_volatility_position_recommendation(0.15)
        assert rec['volatility_tier'] == 'LOW'
        assert rec['recommended_position_size'] > 0.10

    def test_analyze_stock_risk(self):
        sd = _make_stock_data()
        result = RiskMetricsCalculator.analyze_stock_risk(sd)
        assert 'sharpe_ratio' in result
        assert 'risk_score' in result
        assert 0 <= result['risk_score'] <= 100


# ============================================================
# ValuationMetricsCalculator
# ============================================================

class TestValuationMetrics:
    def test_pe_ratio_normal(self):
        pe, pct = ValuationMetricsCalculator.calculate_pe_ratio(150.0, 6.5, 'Technology')
        assert pe == pytest.approx(23.08, rel=0.01)
        assert pct in ('Low', 'Average', 'High')

    def test_pe_ratio_zero_eps(self):
        pe, pct = ValuationMetricsCalculator.calculate_pe_ratio(150.0, 0, 'Technology')
        assert pe is None

    def test_pe_ratio_negative_eps(self):
        pe, pct = ValuationMetricsCalculator.calculate_pe_ratio(150.0, -1, 'Technology')
        assert pe is None

    def test_ev_ebitda(self):
        ev = ValuationMetricsCalculator.calculate_ev_ebitda(100, 20, 10, 15)
        assert ev == pytest.approx(7.33, rel=0.01)

    def test_ev_ebitda_zero(self):
        assert ValuationMetricsCalculator.calculate_ev_ebitda(100, 20, 10, 0) is None

    def test_peg_ratio(self):
        peg = ValuationMetricsCalculator.calculate_peg_ratio(23.0, 0.15)
        assert peg is not None
        assert 0 < peg < 5

    def test_peg_ratio_zero_growth(self):
        assert ValuationMetricsCalculator.calculate_peg_ratio(23.0, 0) is None

    def test_fcf_yield(self):
        yield_val = ValuationMetricsCalculator.calculate_fcf_yield(5_000_000_000, 100_000_000_000)
        assert yield_val == pytest.approx(0.05, rel=0.01)

    def test_graham_intrinsic_value(self):
        val = ValuationMetricsCalculator.calculate_graham_intrinsic_value(6.5, 0.12, 0.04)
        assert val is not None
        assert val > 0

    def test_valuation_score(self):
        metrics = {'pe_ratio': 18, 'peg_ratio': 1.2, 'p_fcf_ratio': 15, 'ev_ebitda_ratio': 10}
        score, breakdown = ValuationMetricsCalculator.calculate_valuation_score(metrics, 'Technology')
        assert 0 <= score <= 100

    def test_analyze_stock_valuation(self):
        sd = _make_stock_data()
        result = ValuationMetricsCalculator.analyze_stock_valuation(sd)
        assert 'valuation_score' in result
        assert 'valuation_attractiveness' in result


# ============================================================
# TechnicalIndicatorsCalculator
# ============================================================

class TestTechnicalIndicators:
    def _prices(self):
        return [100 + i * 0.5 + (i % 5) * 0.3 for i in range(200)]

    def test_moving_averages_sma(self):
        prices = self._prices()
        ma = TechnicalIndicatorsCalculator.calculate_moving_averages(prices, [20, 50])
        assert 20 in ma
        assert 50 in ma
        assert ma[20][-1] is not None

    def test_moving_averages_ema(self):
        prices = self._prices()
        ma = TechnicalIndicatorsCalculator.calculate_moving_averages(prices, [12, 26], 'ema')
        assert 12 in ma
        assert 26 in ma

    def test_moving_averages_insufficient(self):
        ma = TechnicalIndicatorsCalculator.calculate_moving_averages([100, 101], [50])
        assert 50 not in ma

    def test_rsi(self):
        prices = self._prices()
        rsi = TechnicalIndicatorsCalculator.calculate_rsi(prices, 14)
        assert rsi is not None
        assert 0 <= rsi[-1] <= 100

    def test_rsi_insufficient(self):
        assert TechnicalIndicatorsCalculator.calculate_rsi([100, 101, 102], 14) is None

    def test_macd(self):
        prices = self._prices()
        macd = TechnicalIndicatorsCalculator.calculate_macd(prices)
        assert 'macd_line' in macd
        assert 'signal_line' in macd
        assert 'histogram' in macd

    def test_bollinger_bands(self):
        prices = self._prices()
        bb = TechnicalIndicatorsCalculator.calculate_bollinger_bands(prices)
        assert 'upper_band' in bb
        assert 'lower_band' in bb
        assert bb['upper_band'][-1] > bb['lower_band'][-1]

    def test_stochastic(self):
        prices = self._prices()
        highs = [p + 1 for p in prices]
        lows = [p - 1 for p in prices]
        stoch = TechnicalIndicatorsCalculator.calculate_stochastic(highs, lows, prices)
        assert stoch is not None
        assert 'percent_k' in stoch

    def test_atr(self):
        prices = self._prices()
        highs = [p + 1 for p in prices]
        lows = [p - 1 for p in prices]
        atr = TechnicalIndicatorsCalculator.calculate_atr(highs, lows, prices)
        assert atr is not None
        assert atr[-1] is not None

    def test_identify_support_resistance(self):
        prices = self._prices()
        highs = [p + 2 for p in prices]
        lows = [p - 2 for p in prices]
        result = TechnicalIndicatorsCalculator.identify_support_resistance(highs, lows, prices)
        assert 'support_levels' in result
        assert 'resistance_levels' in result
        assert 'price_gaps' in result

    def test_get_rsi_signal(self):
        signal = TechnicalIndicatorsCalculator.get_rsi_signal(25)
        assert signal['signal'] == 'BUY'
        signal = TechnicalIndicatorsCalculator.get_rsi_signal(75)
        assert signal['signal'] == 'SELL'
        signal = TechnicalIndicatorsCalculator.get_rsi_signal(50)
        assert signal['signal'] == 'NEUTRAL'


# ============================================================
# MultiFactorCalculator
# ============================================================

class TestMultiFactor:
    def test_quality_score(self):
        financials = {'roe': 0.25, 'gross_margin': 0.45, 'debt_to_equity': 0.3}
        score = MultiFactorCalculator.calculate_quality_score(financials)
        assert 0 <= score <= 100

    def test_quality_score_none_values(self):
        financials = {}
        score = MultiFactorCalculator.calculate_quality_score(financials)
        assert score == 50

    def test_value_score(self):
        financials = {'pe_ratio': 18, 'ev_ebitda': 10, 'fcf_yield': 0.05, 'dividend_yield': 0.02}
        score = MultiFactorCalculator.calculate_value_score(financials, 100, 'Technology')
        assert 0 <= score <= 100

    def test_growth_score(self):
        financials = {'revenue_growth': 0.15, 'eps_growth': 0.20, 'estimated_growth': 0.12}
        score = MultiFactorCalculator.calculate_growth_score(financials)
        assert 0 <= score <= 100

    def test_momentum_score(self):
        prices = list(range(100, 200))
        score = MultiFactorCalculator.calculate_momentum_score(prices)
        assert 0 <= score <= 100

    def test_low_volatility_score(self):
        prices = [100 + (i % 3 - 1) * 0.1 for i in range(100)]
        score = MultiFactorCalculator.calculate_low_volatility_score(prices)
        assert 0 <= score <= 100

    def test_composite_factor_score(self):
        factor_scores = {
            'quality': {'score': 75},
            'value': {'score': 60},
            'growth': {'score': 80},
            'momentum': {'score': 65},
            'low_volatility': {'score': 50},
        }
        score, breakdown, strategy = MultiFactorCalculator.calculate_composite_factor_score(factor_scores)
        assert 0 <= score <= 100
        assert strategy == 'balanced'

    def test_composite_different_strategies(self):
        factor_scores = {k: {'score': 60} for k in ['quality', 'value', 'growth', 'momentum', 'low_volatility']}
        for strat in ['quality_value', 'growth_momentum', 'balanced', 'defensive', 'aggressive_growth']:
            score, _, s = MultiFactorCalculator.calculate_composite_factor_score(factor_scores, strat)
            assert s == strat


# ============================================================
# MoatAnalyzer
# ============================================================

class TestMoatAnalyzer:
    def test_brand_moat_high_margin(self):
        score, reasons = MoatAnalyzer.analyze_brand_moat(0.70, 'Technology', 0.20)
        assert score > 0.5
        assert len(reasons) > 0

    def test_brand_moat_no_data(self):
        score, reasons = MoatAnalyzer.analyze_brand_moat(None, None, None)
        assert score == 0

    def test_network_moat_tech(self):
        score, reasons = MoatAnalyzer.analyze_network_moat(500_000_000_000, 0.25, 'Technology')
        assert score > 0

    def test_switching_cost_moat(self):
        score, reasons = MoatAnalyzer.analyze_switching_cost_moat(0.85, 'Technology')
        assert score > 0.5

    def test_cost_advantage_moat(self):
        score, reasons = MoatAnalyzer.analyze_cost_advantage_moat(0.30, 'Technology')
        assert score > 0

    def test_regulatory_moat(self):
        score, reasons = MoatAnalyzer.analyze_regulatory_moat('Financials', 100_000_000_000)
        assert score > 0

    def test_analyze_moat_wide(self):
        sd = StockData(
            symbol="AAPL.US", prices=[150]*10,
            market_cap=3000000000000, sector='Technology',
            revenue=400000000000, net_income=100000000000, ebitda=130000000000,
            shareholders_equity=70000000000, free_cash_flow=110000000000,
            revenue_growth=0.08, eps=6.5,
        )
        result = MoatAnalyzer.analyze_moat(sd)
        assert 'moat_score' in result
        assert 'moat_width' in result
        assert result['moat_width'] in (None, 'Minimal', 'Narrow', 'Wide')
        assert 'components' in result
        assert 'brand' in result['components']

    def test_analyze_moat_no_data(self):
        sd = StockData(symbol="UNKNOWN.US", prices=[100]*10)
        result = MoatAnalyzer.analyze_moat(sd)
        assert result['moat_score'] < 3

    def test_required_safety_margin(self):
        sd = _make_stock_data(market_cap=3e12, revenue=400e9, net_income=100e9, ebitda=130e9, shareholders_equity=70e9, free_cash_flow=110e9, revenue_growth=0.08)
        result = MoatAnalyzer.analyze_moat(sd)
        assert 'required_safety_margin' in result
        if result['moat_score'] >= 3:
            assert result['required_safety_margin'] is not None


# ============================================================
# ValueTrapDetector
# ============================================================

class TestValueTrapDetector:
    def test_healthy_company(self):
        sd = _make_stock_data()
        result = ValueTrapDetector.detect_trap(sd)
        assert result['trap_score'] < 15
        assert result['risk_level'] == 'LOW'

    def test_negative_equity(self):
        sd = _make_stock_data(shareholders_equity=-1000, total_debt=50000)
        result = ValueTrapDetector.detect_trap(sd)
        assert result['trap_score'] >= 20

    def test_negative_eps(self):
        sd = _make_stock_data(eps=-5)
        result = ValueTrapDetector.detect_trap(sd)
        assert result['trap_score'] >= 15

    def test_high_debt(self):
        sd = _make_stock_data(total_debt=300_000_000_000, shareholders_equity=10_000_000_000, ebitda=5_000_000_000)
        result = ValueTrapDetector.detect_trap(sd)
        assert result['trap_score'] >= 15

    def test_negative_fcf_no_growth(self):
        sd = _make_stock_data(free_cash_flow=-5_000_000_000, revenue_growth=0.01)
        result = ValueTrapDetector.detect_trap(sd)
        assert result['trap_score'] >= 15

    def test_no_data(self):
        sd = StockData(symbol="X.US", prices=[100]*10)
        result = ValueTrapDetector.detect_trap(sd)
        assert result['risk_level'] in ('LOW', 'UNKNOWN')

    def test_trap_actions(self):
        sd_low = StockData(symbol="LOW.US", prices=[100]*10, eps=5.0, eps_growth=0.10,
                           shareholders_equity=10_000_000_000, net_income=2_000_000_000,
                           ebitda=4_000_000_000, revenue=20_000_000_000)
        result_low = ValueTrapDetector.detect_trap(sd_low)
        assert result_low['action'] in ('OK', 'CAUTION'), \
            f"Expected OK or CAUTION for low-trap stock, got {result_low['action']}"
        
        sd_high = StockData(symbol="HIGH.US", prices=[100]*10, eps=-1.0,
                            shareholders_equity=10_000_000_000, net_income=-2_000_000_000,
                            ebitda=-1_000_000_000, revenue=20_000_000_000,
                            free_cash_flow=-5_000_000_000, total_debt=50_000_000_000)
        result_high = ValueTrapDetector.detect_trap(sd_high)
        assert result_high['action'] in ('AVOID', 'AVOID_OR_MINIMAL'), \
            f"Expected AVOID or AVOID_OR_MINIMAL for high-trap stock, got {result_high['action']}"
        assert result_high['trap_score'] >= 30, \
            f"Expected trap_score >= 30 for high-trap stock, got {result_high['trap_score']}"


# ============================================================
# ConflictResolver
# ============================================================

class TestConflictResolver:
    def test_all_bullish(self):
        signals = {
            'valuation': {'direction': 'bullish', 'strength': 0.8, 'reason': 'Cheap'},
            'technical': {'direction': 'bullish', 'strength': 0.7, 'reason': 'Oversold'},
            'business_quality': {'direction': 'bullish', 'strength': 0.9, 'reason': 'Wide moat'},
        }
        result = ConflictResolver.resolve(signals)
        assert result['action'] == 'BUY'
        assert result['position_pct'] > 0.5

    def test_all_bearish(self):
        signals = {
            'valuation': {'direction': 'bearish', 'strength': 0.8, 'reason': 'Expensive'},
            'technical': {'direction': 'bearish', 'strength': 0.7, 'reason': 'Overbought'},
        }
        result = ConflictResolver.resolve(signals)
        assert result['action'] in ('SELL', 'REDUCE')
        assert result['position_pct'] < 0.3

    def test_conflicting_signals(self):
        signals = {
            'valuation': {'direction': 'bullish', 'strength': 0.8, 'reason': 'Undervalued'},
            'technical': {'direction': 'bearish', 'strength': 0.6, 'reason': 'Overbought'},
        }
        result = ConflictResolver.resolve(signals)
        assert len(result['conflicts']) > 0
        assert result['dominant_framework'] is not None

    def test_swing_trade_horizon(self):
        signals = {
            'valuation': {'direction': 'bullish', 'strength': 0.8, 'reason': 'Cheap'},
            'technical': {'direction': 'bearish', 'strength': 0.9, 'reason': 'Death cross'},
        }
        result = ConflictResolver.resolve(signals, 'SWING_TRADE')
        assert result['investment_horizon'] == 'SWING_TRADE'
        assert result['dominant_framework'] == 'technical'

    def test_empty_signals(self):
        result = ConflictResolver.resolve({})
        assert result['action'] in ('HOLD', 'BUY_SMALL', 'REDUCE')

    def test_neutral_signals(self):
        signals = {k: {'direction': 'neutral', 'strength': 0.5, 'reason': 'N/A'} for k in ('valuation', 'technical', 'business_quality')}
        result = ConflictResolver.resolve(signals)
        assert result['action'] == 'HOLD'


# ============================================================
# StockAnalysisEngine (Integration)
# ============================================================

class TestStockAnalysisEngine:
    def test_analyze_stock_basic(self):
        sd = _make_stock_data()
        engine = StockAnalysisEngine()
        result = engine.analyze_stock(sd)
        
        assert 'symbol' in result
        assert 'risk_analysis' in result
        assert 'valuation_analysis' in result
        assert 'technical_analysis' in result
        assert 'factor_analysis' in result
        assert 'moat_analysis' in result
        assert 'value_trap_analysis' in result
        assert 'overall_assessment' in result
        
        overall = result['overall_assessment']
        assert 'recommendation' in overall
        assert 'overall_score' in overall
        assert 'confidence' in overall
        assert 'conflict_resolution' in overall
        assert 0 <= overall['overall_score'] <= 100

    def test_analyze_stock_minimal_data(self):
        sd = StockData(symbol="MIN.US", prices=[100]*50)
        engine = StockAnalysisEngine()
        result = engine.analyze_stock(sd)
        assert result['overall_assessment']['overall_score'] is not None

    def test_generate_report_markdown(self):
        sd = _make_stock_data()
        engine = StockAnalysisEngine()
        analysis = engine.analyze_stock(sd)
        report = engine.generate_report(analysis, 'markdown')
        assert 'Moat Analysis' in report
        assert 'Value Trap' in report
        assert 'Conflict Resolution' in report

    def test_generate_report_json(self):
        sd = _make_stock_data()
        engine = StockAnalysisEngine()
        analysis = engine.analyze_stock(sd)
        report = engine.generate_report(analysis, 'json')
        import json
        parsed = json.loads(report)
        assert 'moat_analysis' in parsed

    def test_overall_assessment_has_new_fields(self):
        sd = _make_stock_data()
        engine = StockAnalysisEngine()
        result = engine.analyze_stock(sd)
        overall = result['overall_assessment']
        assert 'moat_adjustment' in overall
        assert 'value_trap_risk' in overall
        assert 'conflict_resolution' in overall

    def test_value_trap_reduces_score(self):
        healthy = _make_stock_data()
        trap = _make_stock_data(eps=-5, free_cash_flow=-5_000_000_000, total_debt=300_000_000_000, shareholders_equity=10_000_000_000, ebitda=5_000_000_000)
        engine = StockAnalysisEngine()
        healthy_result = engine.analyze_stock(healthy)
        trap_result = engine.analyze_stock(trap)
        assert trap_result['overall_assessment']['overall_score'] < healthy_result['overall_assessment']['overall_score']
