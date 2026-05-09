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

sys.path.insert(0, str(Path(__file__).parent.parent))
from watchlist_utils import load_watchlist

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
    def fetch_financials(symbol: str, cache: Optional[DataCache] = None) -> Dict:
        """Fetch financial statements (IS, BS, CF) from longbridge financial-report.

        Fetches both quarterly (qf) and annual (af) data:
        - qf: used for balance sheet snapshots, quarterly growth rates
        - af: used for TTM/annualized income and cash flow (no missing quarters)

        Returns:
            {
                'is_data': {'revenue': ..., 'net_income': ..., 'eps': ..., 'operating_income': ...},
                'bs_data': {'total_assets': ..., 'total_liabilities': ..., 'cash': ..., 'net_debt': ...},
                'cf_data': {'operating_cf': ..., 'free_cash_flow': ..., 'capex': ...},
                'growth': {'revenue_growth': ..., 'eps_growth': ...},
                'ttm_data': {'revenue': ..., 'net_income': ..., 'eps': ..., 'free_cash_flow': ...},
                'latest_period': 'Q1 2026',
            }
        """
        if cache:
            cached = cache.get('financials', symbol)
            if cached:
                try:
                    return json.loads(cached)
                except json.JSONDecodeError:
                    pass

        def _fetch_raw(report_type: str) -> Optional[Dict]:
            output = LongbridgeDataFetcher.run_command([
                'longbridge', 'financial-report', symbol,
                '--kind', 'ALL', '--report', report_type, '--format', 'json'
            ])
            if not output or not output.strip():
                return None
            lines = output.strip().split('\n')
            json_lines = [l for l in lines if not l.startswith('New version')]
            try:
                return json.loads('\n'.join(json_lines))
            except json.JSONDecodeError:
                return None

        raw_qf = _fetch_raw('qf')
        raw_af = _fetch_raw('af')

        if not raw_qf and not raw_af:
            return {}

        result = LongbridgeDataFetcher._extract_financial_data(raw_qf, raw_af)

        # Run data quality validation before returning
        result['data_quality'] = LongbridgeDataFetcher._validate_financial_data(
            result, raw_qf, raw_af
        )

        if cache and result:
            cache.set('financials', symbol, json.dumps(result))

        return result

    @staticmethod
    def _get_latest_value(accounts: List[Dict], field: str, period_offset: int = 0) -> Optional[float]:
        """Extract the latest value for a given field from accounts list.

        Args:
            accounts: List of account dicts with 'field' and 'values' keys
            field: The field name to extract
            period_offset: 0 = latest period, 1 = 1 period back, etc.

        Returns:
            Float value or None if not found
        """
        for acct in accounts:
            if acct.get('field') == field:
                values = acct.get('values', [])
                if values and period_offset < len(values):
                    val = values[period_offset].get('value', '')
                    if val and val.strip() and val != 'None':
                        try:
                            return float(val)
                        except (ValueError, TypeError):
                            pass
        return None

    @staticmethod
    def _get_yoy_growth(accounts: List[Dict], field: str) -> Optional[float]:
        """Calculate year-over-year growth for a field.
        Assumes quarterly data where period_offset=0 is latest quarter
        and period_offset=4 is same quarter last year (4 quarters back).

        Returns growth as decimal (0.15 = 15% growth), or None if not computable.
        """
        latest = LongbridgeDataFetcher._get_latest_value(accounts, field, 0)
        yoy = LongbridgeDataFetcher._get_latest_value(accounts, field, 4)
        if latest and yoy and yoy != 0:
            return (latest - yoy) / abs(yoy) if yoy > 0 else None
        return None

    @staticmethod
    def _get_ttm_sum(accounts: List[Dict], field: str) -> Optional[float]:
        """Sum last 4 quarters of a field to get trailing twelve months (TTM).

        For balance sheet fields (snapshots at period end), use the latest single value.
        For income/cash flow fields, sum the last 4 quarterly values.
        """
        total = 0.0
        has_data = False
        for offset in range(4):
            val = LongbridgeDataFetcher._get_latest_value(accounts, field, offset)
            if val is not None:
                total += val
                has_data = True
        return total if has_data else None

    @staticmethod
    def _extract_financial_data(raw_qf: Optional[Dict], raw_af: Optional[Dict] = None) -> Dict:
        """Parse financial-report JSON into structured financial data.

        Args:
            raw_qf: Quarterly financial data (for BS snapshots, quarterly metrics, growth)
            raw_af: Annual financial data (for TTM values — no missing quarters)
        """
        def _get_accounts(raw: Dict, stype: str) -> List[Dict]:
            items = raw.get('list', {}).get(stype, {})
            accts = []
            for ind in items.get('indicators', []):
                accts.extend(ind.get('accounts', []))
            return accts

        # Use qf for quarterly data and balance sheet; af for annualized TTM
        raw_main = raw_qf or raw_af or {}

        # --- Income Statement (qf for quarterly snapshot, af for TTM) ---
        is_accounts_qf = _get_accounts(raw_main, 'IS') if raw_qf else []
        is_accounts_af = _get_accounts(raw_af, 'IS') if raw_af else []

        latest_period = ''
        if is_accounts_qf:
            first_vals = is_accounts_qf[0].get('values', []) if is_accounts_qf else []
            if first_vals:
                latest_period = first_vals[0].get('period', '')

        revenue = LongbridgeDataFetcher._get_latest_value(is_accounts_qf, 'OperatingRevenue')
        net_income = LongbridgeDataFetcher._get_latest_value(is_accounts_qf, 'NetProfit')
        eps = LongbridgeDataFetcher._get_latest_value(is_accounts_qf, 'EPS')
        operating_income = LongbridgeDataFetcher._get_latest_value(is_accounts_qf, 'OperatingIncome')
        gross_margin = LongbridgeDataFetcher._get_latest_value(is_accounts_qf, 'GrossMgn')
        net_margin = LongbridgeDataFetcher._get_latest_value(is_accounts_qf, 'NetProfitMargin')
        roe = LongbridgeDataFetcher._get_latest_value(is_accounts_qf, 'ROE')

        is_data = {
            'revenue': revenue,
            'net_income': net_income,
            'eps': eps,
            'operating_income': operating_income,
            'gross_margin': gross_margin,
            'net_margin': net_margin,
            'roe': roe,
        }

        # --- Balance Sheet (qf — point-in-time snapshot) ---
        bs_accounts = _get_accounts(raw_main, 'BS') if raw_qf else _get_accounts(raw_af or {}, 'BS')

        total_assets = LongbridgeDataFetcher._get_latest_value(bs_accounts, 'TotalAssets')
        total_liabilities = LongbridgeDataFetcher._get_latest_value(bs_accounts, 'TotalLiability')
        cash_st_invest = LongbridgeDataFetcher._get_latest_value(bs_accounts, 'CashSTInvest')
        net_debt = LongbridgeDataFetcher._get_latest_value(bs_accounts, 'NetDebt')
        bps = LongbridgeDataFetcher._get_latest_value(bs_accounts, 'BPS')

        shareholders_equity = None
        if total_assets and total_liabilities:
            shareholders_equity = total_assets - total_liabilities

        bs_data = {
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'shareholders_equity': shareholders_equity,
            'cash': cash_st_invest,
            'net_debt': net_debt,
            'book_value_per_share': bps,
        }

        # --- Cash Flow (qf for latest quarter; af for TTM) ---
        cf_accounts_qf = _get_accounts(raw_main, 'CF') if raw_qf else []
        cf_accounts_af = _get_accounts(raw_af, 'CF') if raw_af else []

        operating_cf = LongbridgeDataFetcher._get_latest_value(cf_accounts_qf, 'NetOperateCashFlow')
        free_cash_flow = LongbridgeDataFetcher._get_latest_value(cf_accounts_qf, 'NetFreeCashFlow')
        capex = LongbridgeDataFetcher._get_latest_value(cf_accounts_qf, 'CapEx')

        if free_cash_flow is None and operating_cf is not None and capex is not None:
            free_cash_flow = operating_cf + capex

        cf_data = {
            'operating_cash_flow': operating_cf,
            'free_cash_flow': free_cash_flow,
            'capex': capex,
        }

        # --- Growth (YoY from qf) ---
        revenue_growth = LongbridgeDataFetcher._get_yoy_growth(is_accounts_qf, 'OperatingRevenue')
        eps_growth = LongbridgeDataFetcher._get_yoy_growth(is_accounts_qf, 'EPS')

        growth = {
            'revenue_growth': revenue_growth,
            'eps_growth': eps_growth,
        }

        # --- Trailing Twelve Months (TTM) ---
        # Use annual (af) data when available — no missing quarters.
        # Fall back to summing 4 quarters from qf.
        if raw_af and is_accounts_af:
            ttm_revenue = LongbridgeDataFetcher._get_latest_value(is_accounts_af, 'OperatingRevenue')
            ttm_net_income = LongbridgeDataFetcher._get_latest_value(is_accounts_af, 'NetProfit')
            ttm_eps = LongbridgeDataFetcher._get_latest_value(is_accounts_af, 'EPS')
            ttm_fcf = LongbridgeDataFetcher._get_latest_value(cf_accounts_af, 'NetFreeCashFlow')
            if ttm_fcf is None:
                ttm_ocf = LongbridgeDataFetcher._get_latest_value(cf_accounts_af, 'NetOperateCashFlow')
                ttm_capex = LongbridgeDataFetcher._get_latest_value(cf_accounts_af, 'CapEx')
                if ttm_ocf is not None and ttm_capex is not None:
                    ttm_fcf = ttm_ocf + ttm_capex
        else:
            ttm_revenue = LongbridgeDataFetcher._get_ttm_sum(is_accounts_qf, 'OperatingRevenue')
            ttm_net_income = LongbridgeDataFetcher._get_ttm_sum(is_accounts_qf, 'NetProfit')
            ttm_eps = LongbridgeDataFetcher._get_ttm_sum(is_accounts_qf, 'EPS')
            ttm_fcf = LongbridgeDataFetcher._get_ttm_sum(cf_accounts_qf, 'NetFreeCashFlow')
            if ttm_fcf is None:
                ttm_ocf = LongbridgeDataFetcher._get_ttm_sum(cf_accounts_qf, 'NetOperateCashFlow')
                ttm_capex = LongbridgeDataFetcher._get_ttm_sum(cf_accounts_qf, 'CapEx')
                if ttm_ocf is not None and ttm_capex is not None:
                    ttm_fcf = ttm_ocf + ttm_capex

        ttm_data = {
            'revenue': ttm_revenue,
            'net_income': ttm_net_income,
            'eps': ttm_eps,
            'free_cash_flow': ttm_fcf,
        }

        return {
            'is_data': is_data,
            'bs_data': bs_data,
            'cf_data': cf_data,
            'growth': growth,
            'ttm_data': ttm_data,
            'latest_period': latest_period,
        }

    @staticmethod
    def _validate_financial_data(result: Dict, raw_qf: Optional[Dict] = None, raw_af: Optional[Dict] = None) -> Dict:
        """Validate financial data quality, flag anomalies for downstream consumers.

        Two severity levels:
        - 'error': genuine data problem (missing fields, corrupted balance sheet)
                  — causes recommendation downgrade
        - 'warn': informational (FCF quarterly/annual mismatch)
                  — shown in output but does NOT block buy signals

        Checks performed:
        1. TTM completeness — are key fields populated?
        2. EPS availability — usable EPS?
        3. Balance sheet equation — Assets ≈ Liabilities + Equity?
        4. (warn) FCF cross-check — quarterly sum vs annual (natural difference, not blocking)
        5. (warn) Anomalous QoQ swings >500%
        6. (warn) Revenue vs income sign sanity

        Returns:
            {'is_clean': bool, 'warnings': [str], 'checks': {name: {'passed': bool, 'severity': str, 'detail': str}}}
        """
        warnings = []
        checks = {}
        has_error = False

        ttm = result.get('ttm_data', {})
        is_data = result.get('is_data', {})
        bs_data = result.get('bs_data', {})
        cf_data = result.get('cf_data', {})

        # --- ERROR: TTM completeness ---
        ttm_fields_with_data = sum(1 for f in ('revenue', 'net_income', 'eps', 'free_cash_flow')
                                   if ttm.get(f) is not None)
        checks['ttm_fields_populated'] = {
            'passed': ttm_fields_with_data >= 3,
            'severity': 'error',
            'detail': f'{ttm_fields_with_data}/4 TTM fields have values',
        }
        if ttm_fields_with_data < 3:
            has_error = True
            warnings.append(f'Low data quality: only {ttm_fields_with_data}/4 TTM fields available')

        # --- ERROR: EPS availability ---
        eps = ttm.get('eps') or is_data.get('eps')
        checks['eps_available'] = {
            'passed': eps is not None,
            'severity': 'error',
            'detail': f'EPS={"not available" if eps is None else f"available ({eps:.2f})"}',
        }
        if eps is None:
            has_error = True
            warnings.append('EPS not available from financial statements')

        # --- ERROR: Balance sheet equation ---
        total_assets = bs_data.get('total_assets')
        total_liabilities = bs_data.get('total_liabilities')
        equity = bs_data.get('shareholders_equity')
        if total_assets and total_liabilities is not None and equity is not None:
            expected = total_liabilities + equity
            if total_assets > 0:
                bs_diff = abs(expected - total_assets) / total_assets * 100
                checks['balance_sheet'] = {
                    'passed': bs_diff < 5,
                    'severity': 'error',
                    'detail': f'A=${total_assets:,.0f} ≈ L+E=${expected:,.0f} (diff={bs_diff:.2f}%)',
                }
                if bs_diff >= 5:
                    has_error = True
                    warnings.append(f'Balance sheet off by {bs_diff:.1f}%')
        else:
            checks['balance_sheet'] = {
                'passed': True,
                'severity': 'error',
                'detail': 'Insufficient balance sheet data to check',
            }

        # --- WARN: FCF cross-check (informational — quarterly/annual cycles differ naturally) ---
        if raw_af and raw_qf:
            cf_af = []
            for ind in raw_af.get('list', {}).get('CF', {}).get('indicators', []):
                cf_af.extend(ind.get('accounts', []))
            cf_qf = []
            for ind in raw_qf.get('list', {}).get('CF', {}).get('indicators', []):
                cf_qf.extend(ind.get('accounts', []))

            annual_fcf = LongbridgeDataFetcher._get_latest_value(cf_af, 'NetFreeCashFlow')
            sum_qf = LongbridgeDataFetcher._get_ttm_sum(cf_qf, 'NetFreeCashFlow')
            if annual_fcf and sum_qf:
                diff_pct = abs(sum_qf - annual_fcf) / abs(annual_fcf) * 100
                checks['fcf_qf_vs_af'] = {
                    'passed': diff_pct < 20,
                    'severity': 'warn',
                    'detail': f'qf-sum=${sum_qf:,.0f} vs af=${annual_fcf:,.0f} (diff={diff_pct:.1f}%)',
                }
                if diff_pct >= 20:
                    warnings.append(f'FCF qf-sum (${sum_qf:,.0f}) ≠ annual (${annual_fcf:,.0f}) — using annual')

        # --- WARN: Anomalous QoQ swings ---
        if raw_qf:
            is_qf = []
            for ind in raw_qf.get('list', {}).get('IS', {}).get('indicators', []):
                is_qf.extend(ind.get('accounts', []))
            for field_name in ('OperatingRevenue', 'NetProfit', 'EPS'):
                v0 = LongbridgeDataFetcher._get_latest_value(is_qf, field_name, 0)
                v1 = LongbridgeDataFetcher._get_latest_value(is_qf, field_name, 1)
                if v0 and v1 and v1 != 0:
                    swing = abs((v0 - v1) / v1) * 100
                    if swing > 500:
                        checks[f'{field_name}_qoq'] = {
                            'passed': False,
                            'severity': 'warn',
                            'detail': f'{field_name} QoQ swing {swing:.0f}% (${v1:.2f}→${v0:.2f})',
                        }
                        warnings.append(f'{field_name} QoQ {swing:.0f}% swing — verify')

        # --- WARN: Revenue sign sanity ---
        rev = ttm.get('revenue')
        net_income = ttm.get('net_income')
        if rev and net_income:
            if rev < 0 and net_income > 0:
                checks['rev_sign'] = {
                    'passed': False,
                    'severity': 'warn',
                    'detail': 'Negative revenue but positive net income',
                }
                warnings.append('Revenue is negative — data may be corrupted')

        is_clean = not has_error
        return {'is_clean': is_clean, 'warnings': warnings, 'checks': checks}

    @staticmethod
    def fetch_market_sentiment(cache: Optional[DataCache] = None) -> Dict:
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
    
    def prepare_stock_data(self, symbol: str, quote: Dict, kline_data: List[Dict],
                           calc_index: Optional[Dict] = None,
                           financial_data: Optional[Dict] = None) -> StockData:
        """Prepare StockData object from fetched data.
        
        Args:
            symbol: Stock symbol
            quote: Quote data from longbridge quote
            kline_data: Historical K-line data
            calc_index: Calculated indices (PE, PB, market cap)
            financial_data: Parsed financial statement data from fetch_financials()
        """
        
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
        
        # Calculate EPS from PE ratio if we have it (fallback, replaced by financial_data if available)
        eps = None
        if pe_ratio and pe_ratio > 0 and current_price > 0:
            eps = current_price / pe_ratio
        
        # Use real EPS from financial statements if available (more accurate than PE-derived)
        is_data = financial_data.get('is_data', {}) if financial_data else {}
        bs_data = financial_data.get('bs_data', {}) if financial_data else {}
        cf_data = financial_data.get('cf_data', {}) if financial_data else {}
        growth_data = financial_data.get('growth', {}) if financial_data else {}
        ttm_data = financial_data.get('ttm_data', {}) if financial_data else {}
        
        # TTM EPS takes priority for valuation (annualized across 4 quarters)
        ttm_eps = ttm_data.get('eps')
        if ttm_eps is not None:
            eps = ttm_eps
        elif is_data.get('eps') is not None:
            # Single-quarter EPS fallback (less accurate for P/E)
            eps = is_data.get('eps')
        
        # Calculate book value per share from PB ratio
        book_value_per_share = None
        if pb_ratio and pb_ratio > 0 and current_price > 0:
            book_value_per_share = current_price / pb_ratio
        # Real BPS from balance sheet takes priority
        real_bps = bs_data.get('book_value_per_share')
        if real_bps is not None:
            book_value_per_share = real_bps
        
        # Estimate growth rate from price momentum (simplified fallback)
        estimated_growth = None
        if len(prices) >= 200:
            ma_200 = sum(prices[-200:]) / 200
            ma_50 = sum(prices[-50:]) / 50
            if ma_200 > 0:
                estimated_growth = ((ma_50 / ma_200) - 1)
        # Prefer real revenue growth over price momentum proxy
        real_rev_growth = growth_data.get('revenue_growth')
        if real_rev_growth is not None and real_rev_growth != 0:
            estimated_growth = real_rev_growth
        
        # Extract financial metrics — prefer real data from financial statements
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
            revenue=ttm_data.get('revenue') or is_data.get('revenue'),
            ebitda=None,  # Not directly available from financial-report
            net_income=ttm_data.get('net_income') or is_data.get('net_income'),
            shareholders_equity=bs_data.get('shareholders_equity') or float(quote.get('shareholders_equity', 0)) if quote.get('shareholders_equity') else None,
            total_debt=bs_data.get('net_debt') or float(quote.get('total_debt', 0)) if quote.get('total_debt') else None,
            cash=bs_data.get('cash') or float(quote.get('cash', 0)) if quote.get('cash') else None,
            free_cash_flow=ttm_data.get('free_cash_flow') or cf_data.get('free_cash_flow'),
            dividend_per_share=float(quote.get('dividend_per_share', 0)) if quote.get('dividend_per_share') else None,
            revenue_growth=real_rev_growth or float(quote.get('revenue_growth', 0)) if quote.get('revenue_growth') else None,
            eps_growth=growth_data.get('eps_growth') or float(quote.get('eps_growth', 0)) if quote.get('eps_growth') else None,
            estimated_growth=estimated_growth,
            book_value_per_share=book_value_per_share
        )
        
        # Store financial data provenance for downstream use
        stock_data._financial_period = financial_data.get('latest_period', '') if financial_data else ''
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
        
        print("Fetching financial statements...")
        financial_data = self.fetcher.fetch_financials(symbol)
        
        if not kline_data:
            print(f"Warning: No historical data available for {symbol}")
            return {"error": "No data available", "symbol": symbol}
        
        # Prepare stock data
        print("Preparing stock data...")
        stock_data = self.prepare_stock_data(symbol, quote, kline_data, calc_index, financial_data)
        
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
        
        # Add financial statement data
        if financial_data:
            analysis['financial_data'] = {
                'latest_period': financial_data.get('latest_period', ''),
                'is_data': financial_data.get('is_data', {}),
                'bs_data': financial_data.get('bs_data', {}),
                'cf_data': financial_data.get('cf_data', {}),
                'growth': financial_data.get('growth', {}),
                'ttm_data': financial_data.get('ttm_data', {}),
                'data_quality': financial_data.get('data_quality', {}),
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
        # Analyze default watchlist from references/watchlist.json
        watchlist = load_watchlist()
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
