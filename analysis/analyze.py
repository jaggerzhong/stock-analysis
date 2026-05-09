#!/usr/bin/env python3
"""
Comprehensive Stock Analysis Script
Integrates with Longbridge CLI to fetch real-time data and perform complete analysis.
"""

import sys
import os
import json
import subprocess
import argparse
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from analysis.engine import (
    StockData, 
    StockAnalysisEngine,
    RiskMetricsCalculator,
    ValuationMetricsCalculator,
    TechnicalIndicatorsCalculator,
    MultiFactorCalculator,
    OptionPosition,
    OptionAnalyzer,
)


class DataCache:
    """TTL-based cache for longbridge CLI results to avoid redundant fetches."""
    
    def __init__(self, ttl_seconds: int = 300, cache_dir: Optional[str] = None):
        self.ttl = ttl_seconds
        if cache_dir is None:
            cache_dir = str(Path.home() / '.cache' / 'stock-analysis')
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: Dict[str, tuple] = {}
    
    def _key(self, prefix: str, args: str) -> str:
        raw = f"{prefix}:{args}"
        return hashlib.md5(raw.encode()).hexdigest()
    
    def _file_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"
    
    def get(self, prefix: str, args: str) -> Optional[str]:
        key = self._key(prefix, args)
        
        if key in self._memory_cache:
            data, ts = self._memory_cache[key]
            if time.time() - ts < self.ttl:
                return data
            del self._memory_cache[key]
        
        fp = self._file_path(key)
        if fp.exists():
            try:
                with open(fp, 'r') as f:
                    cached = json.load(f)
                if time.time() - cached.get('ts', 0) < self.ttl:
                    self._memory_cache[key] = (cached['data'], cached['ts'])
                    return cached['data']
            except (json.JSONDecodeError, KeyError):
                pass
        
        return None
    
    def set(self, prefix: str, args: str, data: str):
        key = self._key(prefix, args)
        ts = time.time()
        self._memory_cache[key] = (data, ts)
        
        fp = self._file_path(key)
        try:
            with open(fp, 'w') as f:
                json.dump({'data': data, 'ts': ts}, f)
        except OSError:
            pass
    
    def clear(self):
        self._memory_cache.clear()
        if self.cache_dir.exists():
            for f in self.cache_dir.glob('*.json'):
                try:
                    f.unlink()
                except OSError:
                    pass


class LongbridgeDataFetcher:
    """Fetch stock data from Longbridge CLI with caching."""
    
    def __init__(self, cache_ttl: int = 300):
        self.cache = DataCache(ttl_seconds=cache_ttl)
    
    @staticmethod
    def run_command(cmd: List[str]) -> Optional[str]:
        """Run a shell command and return output"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return result.stdout
            else:
                print(f"Command failed: {' '.join(cmd)}")
                print(f"Error: {result.stderr}")
                return None
        except subprocess.TimeoutExpired:
            print(f"Command timed out: {' '.join(cmd)}")
            return None
        except Exception as e:
            print(f"Exception running command: {e}")
            return None
    
    @staticmethod
    def parse_quote(quote_output: str) -> Union[Dict, List[Dict]]:
        """Parse quote output from longbridge CLI.
        
        Returns:
            - Dict for single-symbol queries (backward compatible)
            - List[Dict] for batch queries (all symbols preserved)
        """
        data = {}
        
        if not quote_output or not quote_output.strip():
            return data
        
        try:
            parsed = json.loads(quote_output.strip())
            
            if isinstance(parsed, list):
                return parsed  # Return full list for batch queries
            elif isinstance(parsed, dict):
                return parsed
            
        except json.JSONDecodeError as e:
            print(f"Error parsing quote JSON: {e}")
            print(f"Output preview: {quote_output[:200]}")
        except Exception as e:
            print(f"Error parsing quote: {e}")
        
        return data
    
    @staticmethod
    def parse_batch_quotes(quote_output: str) -> List[Dict]:
        """Parse quote output, always returning a list of quote dicts."""
        result = LongbridgeDataFetcher.parse_quote(quote_output)
        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            return [result] if result else []
        return []
    
    @staticmethod
    def fetch_quote(symbol: str, cache: Optional[DataCache] = None) -> Dict:
        """Fetch current quote for a single symbol. Always returns a Dict."""
        cache_key = f"quote_{symbol}"
        if cache:
            cached = cache.get('quote', symbol)
            if cached:
                parsed = LongbridgeDataFetcher.parse_quote(cached)
                if isinstance(parsed, list) and len(parsed) > 0:
                    return parsed[0]
                elif isinstance(parsed, dict):
                    return parsed
        
        output = LongbridgeDataFetcher.run_command([
            'longbridge', 'quote', symbol, '--format', 'json'
        ])
        
        if cache and output:
            cache.set('quote', symbol, output)
        
        parsed = LongbridgeDataFetcher.parse_quote(output or '')
        if isinstance(parsed, list) and len(parsed) > 0:
            return parsed[0]
        elif isinstance(parsed, dict):
            return parsed
        return {}
    
    @staticmethod
    def fetch_batch_quotes(symbols: List[str], cache: Optional[DataCache] = None) -> Dict[str, Dict]:
        """Fetch quotes for multiple symbols in one call. Returns {symbol: quote_dict}."""
        if not symbols:
            return {}
        
        cache_key = "batch_" + "_".join(sorted(symbols))
        if cache:
            cached = cache.get('batch_quote', cache_key)
            if cached:
                try:
                    return json.loads(cached)
                except json.JSONDecodeError:
                    pass
        
        output = LongbridgeDataFetcher.run_command([
            'longbridge', 'quote'] + symbols + ['--format', 'json'
        ])
        
        if cache and output:
            cache.set('batch_quote', cache_key, output)
        
        quotes_list = LongbridgeDataFetcher.parse_batch_quotes(output or '')
        result = {}
        for q in quotes_list:
            sym = q.get('symbol', '')
            if sym:
                result[sym] = q
        
        return result
    
    @staticmethod
    def fetch_kline(symbol: str, days: int = 200, period: str = 'day', cache: Optional[DataCache] = None) -> List[Dict]:
        """Fetch historical K-line data"""
        cache_key = f"{symbol}_{days}_{period}"
        if cache:
            cached = cache.get('kline', cache_key)
            if cached:
                try:
                    return json.loads(cached)
                except json.JSONDecodeError:
                    pass
        
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        output = LongbridgeDataFetcher.run_command([
            'longbridge', 'kline', 'history', symbol,
            '--start', start_date,
            '--end', end_date,
            '--period', period,
            '--format', 'json'
        ])
        
        if not output or not output.strip():
            print(f"Warning: Empty response for kline {symbol}")
            return []
        
        if cache and output:
            cache.set('kline', cache_key, output)
        
        try:
            data = json.loads(output)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError as e:
            print(f"JSON decode error for kline {symbol}: {e}")
            print(f"Response preview: {output[:200] if output else 'None'}")
            return []
    
    @staticmethod
    def fetch_calc_index(symbol: str, cache: Optional[DataCache] = None) -> Dict:
        """Fetch calculated indexes (PE, PB, market cap, etc.)"""
        if cache:
            cached = cache.get('calc_index', symbol)
            if cached:
                try:
                    return json.loads(cached)
                except json.JSONDecodeError:
                    pass
        
        output = LongbridgeDataFetcher.run_command([
            'longbridge', 'calc-index', symbol, '--format', 'json'
        ])
        
        if not output or not output.strip():
            return {}
        
        if cache and output:
            cache.set('calc_index', symbol, output)
        
        try:
            data = json.loads(output)
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}
    
    @staticmethod
    def fetch_valuation(symbol: str, cache: Optional[DataCache] = None) -> Dict:
        """Fetch valuation data (PE percentile, historical range)"""
        if cache:
            cached = cache.get('valuation', symbol)
            if cached:
                try:
                    return json.loads(cached)
                except json.JSONDecodeError:
                    pass
        
        output = LongbridgeDataFetcher.run_command([
            'longbridge', 'valuation', symbol, '--format', 'json'
        ])
        
        if not output or not output.strip():
            return {}
        
        # Remove "New version" message at end
        lines = output.strip().split('\n')
        json_lines = []
        for line in lines:
            if line.startswith('New version'):
                continue
            json_lines.append(line)
        
        clean_output = '\n'.join(json_lines)
        
        if cache and clean_output:
            cache.set('valuation', symbol, clean_output)
        
        try:
            return json.loads(clean_output)
        except json.JSONDecodeError:
            return {}
    
    @staticmethod
    def fetch_market_sentiment(cache: Optional[DataCache] = None) -> Dict:
        """Fetch market sentiment"""
        if cache:
            cached = cache.get('sentiment', 'market')
            if cached:
                try:
                    return json.loads(cached)
                except json.JSONDecodeError:
                    pass
        
        output = LongbridgeDataFetcher.run_command(['longbridge', 'market-temp'])
        
        if not output:
            return {}
        
        sentiment = {}
        try:
            lines = output.strip().split('\n')
            for line in lines:
                if 'sentiment' in line.lower() or 'temperature' in line.lower() or 'valuation' in line.lower():
                    import re
                    numbers = re.findall(r'\d+\.?\d*', line)
                    if numbers:
                        if 'sentiment' in line.lower():
                            sentiment['sentiment'] = float(numbers[0])
                        elif 'temperature' in line.lower():
                            sentiment['temperature'] = float(numbers[0])
                        elif 'valuation' in line.lower():
                            sentiment['valuation'] = float(numbers[0])
        except Exception as e:
            print(f"Error parsing sentiment: {e}")
        
        if cache and sentiment:
            cache.set('sentiment', 'market', json.dumps(sentiment))
        
        return sentiment
    
    @staticmethod
    def fetch_positions() -> List[Dict]:
        """Fetch current positions"""
        output = LongbridgeDataFetcher.run_command([
            'longbridge', 'positions', '--format', 'json'
        ])
        
        if not output or not output.strip():
            print("Warning: Empty response for positions")
            return []
        
        try:
            data = json.loads(output)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError as e:
            print(f"JSON decode error for positions: {e}")
            print(f"Response preview: {output[:200] if output else 'None'}")
            return []


class StockAnalyzer:
    """Main stock analyzer integrating all components"""
    
    def __init__(self, cache_ttl: int = 300):
        self.engine = StockAnalysisEngine()
        self.cache = DataCache(ttl_seconds=cache_ttl)
        self.fetcher = LongbridgeDataFetcher(cache_ttl=cache_ttl)
        self.fetcher.cache = self.cache
    
    def prepare_stock_data(self, symbol: str, quote: Dict, kline_data: List[Dict], calc_index: Optional[Dict] = None) -> StockData:
        """Prepare StockData object from fetched data"""
        
        # Extract prices from K-line data
        prices = []
        highs = []
        lows = []
        volumes = []
        
        for candle in kline_data:
            prices.append(float(candle.get('close', 0)))
            highs.append(float(candle.get('high', 0)))
            lows.append(float(candle.get('low', 0)))
            volumes.append(float(candle.get('volume', 0)))
        
        # Get current price from quote (prefer live price over stale kline close)
        live_price = quote.get('last') or quote.get('last_done')
        if live_price:
            current_price = float(live_price)
            price_source = 'live_quote'
        elif prices:
            current_price = prices[-1]
            price_source = 'kline_close_stale'
            print(f"  WARNING: Live quote unavailable for {symbol}, using last kline close (may be stale)")
        else:
            current_price = 0
            price_source = 'unavailable'
        
        # Extract market cap from calc_index if available
        market_cap = None
        pe_ratio = None
        pb_ratio = None
        
        if calc_index:
            if calc_index.get('total_market_value'):
                market_cap = float(calc_index['total_market_value'])
            if calc_index.get('pe'):
                pe_ratio = float(calc_index['pe'])
            if calc_index.get('pb'):
                pb_ratio = float(calc_index['pb'])
        
        # Fallback to quote data
        if not market_cap and quote.get('market_cap'):
            market_cap = float(quote['market_cap'])
        
        # Calculate EPS from PE ratio if we have it
        eps = None
        if pe_ratio and pe_ratio > 0 and current_price > 0:
            eps = current_price / pe_ratio
        
        # Calculate book value per share from PB ratio
        book_value_per_share = None
        if pb_ratio and pb_ratio > 0 and current_price > 0:
            book_value_per_share = current_price / pb_ratio
        
        # Estimate growth rate from price momentum (simplified)
        estimated_growth = None
        if len(prices) >= 200:
            ma_200 = sum(prices[-200:]) / 200
            ma_50 = sum(prices[-50:]) / 50
            if ma_200 > 0:
                # Return as decimal (0.05 = 5%), not percentage
                estimated_growth = ((ma_50 / ma_200) - 1)
        
        # Extract financial metrics from quote (simplified)
        stock_data = StockData(
            symbol=symbol,
            prices=prices,
            volumes=volumes,
            highs=highs,
            lows=lows,
            current_price=current_price,
            market_cap=market_cap,
            sector=quote.get('sector', 'Technology'),
            eps=eps,
            revenue=float(quote.get('revenue', 0)) if quote.get('revenue') else None,
            ebitda=float(quote.get('ebitda', 0)) if quote.get('ebitda') else None,
            net_income=float(quote.get('net_income', 0)) if quote.get('net_income') else None,
            shareholders_equity=float(quote.get('shareholders_equity', 0)) if quote.get('shareholders_equity') else None,
            total_debt=float(quote.get('total_debt', 0)) if quote.get('total_debt') else None,
            cash=float(quote.get('cash', 0)) if quote.get('cash') else None,
            free_cash_flow=float(quote.get('free_cash_flow', 0)) if quote.get('free_cash_flow') else None,
            dividend_per_share=float(quote.get('dividend_per_share', 0)) if quote.get('dividend_per_share') else None,
            revenue_growth=float(quote.get('revenue_growth', 0)) if quote.get('revenue_growth') else None,
            eps_growth=float(quote.get('eps_growth', 0)) if quote.get('eps_growth') else None,
            estimated_growth=estimated_growth,
            book_value_per_share=book_value_per_share
        )
        
        # Set price source metadata
        stock_data._price_source = price_source
        
        return stock_data
    
    def analyze_symbol(self, symbol: str, include_market: bool = True) -> Dict:
        """Analyze a single stock symbol"""
        print(f"\n{'='*60}")
        print(f"Analyzing: {symbol}")
        print(f"{'='*60}\n")
        
        # Fetch data
        print("Fetching quote data...")
        quote = self.fetcher.fetch_quote(symbol)
        
        print("Fetching historical data...")
        kline_data = self.fetcher.fetch_kline(symbol, days=365)
        
        print("Fetching valuation metrics...")
        calc_index = self.fetcher.fetch_calc_index(symbol)
        
        if not kline_data:
            print(f"Warning: No historical data available for {symbol}")
            return {"error": "No data available", "symbol": symbol}
        
        # Prepare stock data
        print("Preparing stock data...")
        stock_data = self.prepare_stock_data(symbol, quote, kline_data, calc_index)
        
        # Fetch market sentiment for context
        market_context = {}
        if include_market:
            print("Fetching market sentiment...")
            market_context = self.fetcher.fetch_market_sentiment()
        
        # Run comprehensive analysis
        print("Running comprehensive analysis...")
        analysis = self.engine.analyze_stock(stock_data)
        
        # Add market context
        analysis['market_context'] = market_context
        
        # Add quote details
        analysis['quote_details'] = {
            'symbol': symbol,
            'current_price': quote.get('last') or quote.get('last_done'),
            'change': quote.get('change_val'),
            'change_rate': quote.get('change_rate'),
            'volume': quote.get('volume'),
            'turnover': quote.get('turnover'),
            'high': quote.get('high'),
            'low': quote.get('low'),
            'open': quote.get('open'),
            'previous_close': quote.get('prev_close'),
            '52_week_high': quote.get('week_52_high') or quote.get('high_52_week'),
            '52_week_low': quote.get('week_52_low') or quote.get('low_52_week'),
            'calc_index': calc_index  # PE, PB, market cap from calc-index
        }
        
        # Ensure current_price uses live quote, not stale kline close
        live_price = quote.get('last') or quote.get('last_done')
        if live_price:
            analysis['current_price'] = float(live_price)
        
        return analysis
    
    def analyze_portfolio(self) -> Dict:
        """Analyze entire portfolio including stocks and options"""
        print("\n" + "="*60)
        print("PORTFOLIO ANALYSIS")
        print("="*60 + "\n")
        
        # Fetch positions
        print("Fetching portfolio positions...")
        positions = self.fetcher.fetch_positions()
        
        if not positions:
            print("No positions found")
            return {"error": "No positions found"}
        
        portfolio_analysis = {
            'analysis_date': datetime.now().isoformat(),
            'positions': [],
            'option_positions': [],
            'summary': {}
        }
        
        total_value = 0
        total_pnl = 0
        analyses = []
        option_analyses = []

        # Separate option positions from stock positions
        option_positions = OptionAnalyzer.parse_positions(positions)
        option_symbols = {o.symbol for o in option_positions}

        # Analyze stock positions (skip option symbols)
        for position in positions:
            symbol = position.get('symbol', '')
            if not symbol or symbol in option_symbols:
                continue
            
            print(f"\nAnalyzing position: {symbol}")
            
            # Get position details from positions data
            quantity = float(position.get('quantity', 0))
            cost_price = float(position.get('cost_price', 0))
            
            # Fetch current quote to get current price
            print(f"  Fetching current price for {symbol}...")
            current_quote = self.fetcher.fetch_quote(symbol)
            
            # Get current price from quote (longbridge uses 'last' field)
            current_price = float(current_quote.get('last', 0)) if current_quote else 0
            
            # Calculate market value and P/L
            market_value = current_price * quantity if current_price > 0 else 0
            pnl = (current_price - cost_price) * quantity if current_price > 0 and cost_price > 0 else 0
            pnl_percent = ((current_price / cost_price) - 1) * 100 if cost_price > 0 else 0
            
            print(f"  Current Price: ${current_price:.2f}")
            print(f"  Market Value: ${market_value:.2f}")
            print(f"  P/L: ${pnl:.2f} ({pnl_percent:+.2f}%)")
            
            total_value += market_value
            total_pnl += pnl
            
            # Run analysis
            analysis = self.analyze_symbol(symbol, include_market=False)
            analysis['position_details'] = {
                'quantity': quantity,
                'cost_price': cost_price,
                'current_price': current_price,
                'market_value': market_value,
                'profit_loss': pnl,
                'pnl_percent': pnl_percent
            }
            
            analyses.append(analysis)

        # Analyze option positions
        for option in option_positions:
            print(f"\nAnalyzing option position: {option.symbol}")
            print(f"  {option.underlying} {option.option_type} ${option.strike} exp {option.expiry}")

            # Fetch underlying price
            underlying_quote = self.fetcher.fetch_quote(f"{option.underlying}.US")
            underlying_price = float(underlying_quote.get('last', 0)) if underlying_quote else 0

            if underlying_price == 0:
                print(f"  Warning: Could not fetch price for {option.underlying}")
                underlying_price = option.strike

            print(f"  Underlying price: ${underlying_price:.2f}")

            opt_analysis = OptionAnalyzer.analyze_option(option, underlying_price)
            print(f"  Strategy: {opt_analysis['strategy']['name']}")
            print(f"  P/L: ${opt_analysis['pnl']:.2f}" if opt_analysis['pnl'] is not None else "  P/L: N/A")
            print(f"  Prob of Profit: {opt_analysis['risk_metrics']['prob_of_profit']:.1%}")
            print(f"  Recommendation: {opt_analysis['recommendation']['action']}")

            option_analyses.append(opt_analysis)

            total_value += opt_analysis.get('market_value', 0)
            if opt_analysis.get('pnl') is not None:
                total_pnl += opt_analysis['pnl']
        
        # Generate portfolio summary
        all_count = len(analyses) + len(option_analyses)
        portfolio_analysis['positions'] = analyses
        portfolio_analysis['option_positions'] = option_analyses
        portfolio_analysis['summary'] = {
            'total_positions': all_count,
            'stock_positions': len(analyses),
            'option_positions': len(option_analyses),
            'total_market_value': total_value,
            'total_profit_loss': total_pnl,
            'total_return_percent': (total_pnl / (total_value - total_pnl) * 100) if total_value > total_pnl else 0,
            'average_score': sum(a.get('overall_assessment', {}).get('overall_score', 50) for a in analyses) / len(analyses) if analyses else 0
        }
        
        # Add risk metrics at portfolio level
        portfolio_analysis['portfolio_risk'] = self._calculate_portfolio_risk(analyses)
        
        return portfolio_analysis
    
    def _calculate_portfolio_risk(self, analyses: List[Dict]) -> Dict:
        """Calculate portfolio-level risk metrics"""
        if not analyses:
            return {}
        
        # Weight-average portfolio metrics
        total_value = sum(a.get('position_details', {}).get('market_value', 0) for a in analyses)
        
        if total_value == 0:
            return {}
        
        weighted_beta = 0
        weighted_volatility = 0
        
        for analysis in analyses:
            market_value = analysis.get('position_details', {}).get('market_value', 0)
            weight = market_value / total_value
            
            beta = analysis.get('risk_analysis', {}).get('beta', 1.0)
            volatility = analysis.get('risk_analysis', {}).get('historical_volatility', 0.3)
            
            if beta:
                weighted_beta += weight * beta
            if volatility:
                weighted_volatility += weight * volatility
        
        return {
            'weighted_beta': weighted_beta,
            'weighted_volatility': weighted_volatility,
            'risk_level': 'Low' if weighted_beta < 0.8 else 'Medium' if weighted_beta < 1.2 else 'High'
        }
    
    def generate_watchlist_report(self, symbols: List[str]) -> str:
        """Generate watchlist analysis report"""
        print("\n" + "="*60)
        print("WATCHLIST ANALYSIS")
        print("="*60 + "\n")
        
        # Fetch market sentiment
        market_sentiment = self.fetcher.fetch_market_sentiment()
        
        # Analyze each symbol
        analyses = []
        for symbol in symbols:
            try:
                analysis = self.analyze_symbol(symbol, include_market=False)
                analyses.append(analysis)
            except Exception as e:
                print(f"Error analyzing {symbol}: {e}")
                continue
        
        # Generate report
        report = self._format_watchlist_report(analyses, market_sentiment)
        
        return report
    
    def _format_watchlist_report(self, analyses: List[Dict], market_sentiment: Dict) -> str:
        """Format watchlist analysis as markdown report"""
        report_date = datetime.now().strftime('%Y-%m-%d')
        
        md = f"""# 📊 Stock Analysis Watchlist Report
Date: {report_date}

## Market Overview
- **Market Sentiment:** {market_sentiment.get('sentiment', 'N/A')}
- **Market Temperature:** {market_sentiment.get('temperature', 'N/A')}
- **Market Valuation:** {market_sentiment.get('valuation', 'N/A')}

## Watchlist Summary

| Symbol | Price | Change | Score | Recommendation | Risk Level |
|--------|-------|--------|-------|----------------|------------|
"""
        
        for analysis in analyses:
            symbol = analysis.get('symbol', 'N/A')
            quote = analysis.get('quote_details', {})
            overall = analysis.get('overall_assessment', {})
            risk = analysis.get('risk_analysis', {})
            
            price = quote.get('current_price', 'N/A')
            # Handle None or string values for change_rate
            change_raw = quote.get('change_rate')
            if change_raw is None or change_raw == 'None':
                change = 0.0
            elif isinstance(change_raw, str):
                try:
                    change = float(change_raw)
                except (ValueError, TypeError):
                    change = 0.0
            else:
                change = float(change_raw)
            
            score = overall.get('overall_score', 50)
            recommendation = overall.get('recommendation', 'HOLD')
            risk_level = risk.get('risk_score', 50)
            
            risk_label = 'Low' if risk_level < 40 else 'Medium' if risk_level < 60 else 'High'
            
            # Format price
            if price == 'N/A' or price is None:
                price_str = 'N/A'
            else:
                try:
                    price_str = f"{float(price):.2f}"
                except (ValueError, TypeError):
                    price_str = str(price)
            
            md += f"| {symbol} | ${price_str} | {change:+.2f}% | {score:.1f}/100 | {recommendation} | {risk_label} |\n"
        
        md += "\n---\n\n## Detailed Analysis\n\n"
        
        for analysis in analyses:
            symbol = analysis.get('symbol', 'N/A')
            md += f"### {symbol}\n\n"
            
            # Overall assessment
            overall = analysis.get('overall_assessment', {})
            md += f"**Recommendation:** {overall.get('recommendation', 'N/A')} "
            md += f"({overall.get('confidence', 'N/A')} confidence)\n\n"
            md += f"**Overall Score:** {overall.get('overall_score', 50):.1f}/100\n\n"
            
            # Score breakdown
            breakdown = overall.get('score_breakdown', {})
            md += "**Score Breakdown:**\n"
            md += f"- Risk: {breakdown.get('risk_score', 50):.1f}/100\n"
            md += f"- Valuation: {breakdown.get('valuation_score', 50):.1f}/100\n"
            md += f"- Technical: {breakdown.get('technical_score', 50):.1f}/100\n"
            md += f"- Factor: {breakdown.get('factor_score', 50):.1f}/100\n\n"
            
            # Risk analysis
            risk = analysis.get('risk_analysis', {})
            md += "**Risk Metrics:**\n"
            
            # Helper function to format numeric values
            def format_value(value, format_spec=':.2f', default='N/A'):
                if value is None or value == 'N/A':
                    return default
                try:
                    return f"{float(value)}{format_spec}"
                except (ValueError, TypeError):
                    return default
            
            sharpe = risk.get('sharpe_ratio')
            md += f"- Sharpe Ratio: {format_value(sharpe, ':.2f')}\n"
            
            max_dd = risk.get('max_drawdown')
            md += f"- Max Drawdown: {format_value(max_dd, ':.2%')}\n"
            
            vol = risk.get('historical_volatility')
            md += f"- Historical Volatility: {format_value(vol, ':.2%')}\n"
            
            risk_score = risk.get('risk_score', 50)
            md += f"- Risk Score: {format_value(risk_score, ':.1f/100', '50.0/100')}\n\n"
            
            # Valuation analysis
            valuation = analysis.get('valuation_analysis', {})
            md += "**Valuation:**\n"
            
            pe = valuation.get('pe_ratio')
            md += f"- P/E Ratio: {format_value(pe, ':.2fx', 'N/A')}\n"
            
            val_score = valuation.get('valuation_score', 50)
            md += f"- Valuation Score: {format_value(val_score, ':.1f/100', '50.0/100')}\n"
            md += f"- Attractiveness: {valuation.get('valuation_attractiveness', 'N/A')}\n\n"
            
            # Technical signals
            tech = analysis.get('technical_analysis', {})
            md += "**Technical Signals:**\n"
            if tech.get('rsi'):
                latest_rsi = tech['rsi'][-1] if tech['rsi'] else None
                if latest_rsi:
                    md += f"- RSI: {latest_rsi:.1f}\n"
            if tech.get('technical_score'):
                md += f"- Technical Score: {tech['technical_score']:.1f}/100\n"
            md += "\n"
            
            # Factor analysis
            factor = analysis.get('factor_analysis', {})
            md += "**Factor Scores:**\n"
            for factor_name, factor_data in factor.get('factor_scores', {}).items():
                score = factor_data.get('score', 50)
                md += f"- {factor_name.title()}: {score:.1f}/100\n"
            md += f"- Composite: {factor.get('composite_score', 50):.1f}/100\n\n"
            
            md += "---\n\n"
        
        # Add recommendations
        md += "## Top Recommendations\n\n"
        
        # Sort by overall score
        sorted_analyses = sorted(analyses, key=lambda x: x.get('overall_assessment', {}).get('overall_score', 0), reverse=True)
        
        # Top buy candidates
        buy_candidates = [a for a in sorted_analyses if 'BUY' in a.get('overall_assessment', {}).get('recommendation', '')]
        
        if buy_candidates:
            md += "### 📈 Strong Buy Candidates\n\n"
            for i, analysis in enumerate(buy_candidates[:3], 1):
                symbol = analysis.get('symbol', 'N/A')
                score = analysis.get('overall_assessment', {}).get('overall_score', 0)
                valuation = analysis.get('valuation_analysis', {}).get('valuation_attractiveness', 'N/A')
                md += f"{i}. **{symbol}** (Score: {score:.1f}/100)\n"
                md += f"   - Valuation: {valuation}\n"
                md += f"   - Risk: {analysis.get('risk_analysis', {}).get('risk_score', 50):.1f}/100\n\n"
        
        # Risk warnings
        high_risk = [a for a in sorted_analyses if a.get('risk_analysis', {}).get('risk_score', 0) > 60]
        if high_risk:
            md += "### ⚠️ High Risk Positions\n\n"
            for analysis in high_risk:
                symbol = analysis.get('symbol', 'N/A')
                risk_score = analysis.get('risk_analysis', {}).get('risk_score', 0)
                max_dd = analysis.get('risk_analysis', {}).get('max_drawdown', 0)
                md += f"- **{symbol}** (Risk Score: {risk_score:.1f}/100, Max DD: {max_dd:.2%})\n"
            md += "\n"
        
        md += """---

**Disclaimer:** This report is generated automatically for informational purposes only. 
Always conduct your own research and consult with a financial advisor before making investment decisions.
"""
        
        return md
    
    def save_report(self, report: str, output_path: str):
        """Save report to file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\nReport saved to: {output_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Comprehensive Stock Analysis Tool')
    parser.add_argument('symbols', nargs='*', help='Stock symbols to analyze (e.g., AAPL.US NVDA.US)')
    parser.add_argument('--portfolio', action='store_true', help='Analyze portfolio positions')
    parser.add_argument('--watchlist', action='store_true', help='Analyze default watchlist')
    parser.add_argument('--output', '-o', help='Output file path for report')
    parser.add_argument('--format', choices=['markdown', 'json'], default='markdown', help='Output format')
    
    args = parser.parse_args()
    
    analyzer = StockAnalyzer()
    
    if args.portfolio:
        # Analyze portfolio
        analysis = analyzer.analyze_portfolio()
        if args.format == 'json':
            report = json.dumps(analysis, indent=2, default=str)
        else:
            report = analyzer.engine.generate_report(analysis, format='markdown')
    
    elif args.watchlist:
        # Analyze default watchlist
        watchlist = ['BABA.US', 'NVDA.US', 'TSLA.US', 'CEG.US', 'COIN.US', 'PLTR.US']
        report = analyzer.generate_watchlist_report(watchlist)
    
    elif args.symbols:
        # Analyze specified symbols
        if len(args.symbols) == 1:
            analysis = analyzer.analyze_symbol(args.symbols[0])
            report = analyzer.engine.generate_report(analysis, format=args.format)
        else:
            report = analyzer.generate_watchlist_report(args.symbols)
    
    else:
        # Default: show help
        parser.print_help()
        return
    
    # Output report
    if args.output:
        analyzer.save_report(report, args.output)
    else:
        print("\n" + "="*60)
        print("ANALYSIS REPORT")
        print("="*60 + "\n")
        print(report)


if __name__ == "__main__":
    main()
