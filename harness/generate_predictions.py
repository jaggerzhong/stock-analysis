#!/usr/bin/env python3
"""
Generate real predictions using the analysis engine.
Called by daily-summary.sh to produce data-driven predictions instead of hardcoded templates.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta

# Standardized import path
SKILL_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(SKILL_DIR))

from analysis.analyze import StockAnalyzer


def generate_predictions(date_str: str, watchlist: list) -> dict:
    """
    Generate predictions for watchlist symbols using the analysis engine.
    
    Args:
        date_str: Date string YYYY-MM-DD for the prediction date
        watchlist: List of symbol strings
        
    Returns:
        Prediction dict compatible with backtest.py
    """
    analyzer = StockAnalyzer()
    predictions = []
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    for symbol in watchlist:
        try:
            analysis = analyzer.analyze_symbol(symbol, include_market=False)
            
            overall = analysis.get('overall_assessment', {})
            rec = overall.get('recommendation', 'HOLD')
            score = overall.get('overall_score', 50)
            tech = analysis.get('technical_analysis', {})
            valuation = analysis.get('valuation_analysis', {})
            
            current_price = analysis.get('current_price', 0)
            if not current_price:
                continue
            
            if 'BUY' in rec:
                predicted_direction = 'up'
                confidence = min(0.95, max(0.3, score / 100))
            elif 'SELL' in rec:
                predicted_direction = 'down'
                confidence = min(0.95, max(0.3, (100 - score) / 100))
            else:
                predicted_direction = 'neutral'
                confidence = 0.4
            
            target_price = None
            stop_loss = None
            
            if predicted_direction == 'up':
                nearest_resistance = tech.get('nearest_resistance')
                if nearest_resistance and nearest_resistance.get('price'):
                    target_price = f"{nearest_resistance['price']:.2f}"
                else:
                    target_price = f"{current_price * 1.05:.2f}"
                
                nearest_support = tech.get('nearest_support')
                if nearest_support and nearest_support.get('price'):
                    stop_loss = f"{nearest_support['price'] * 0.98:.2f}"
                else:
                    stop_loss = f"{current_price * 0.93:.2f}"
            elif predicted_direction == 'down':
                nearest_support = tech.get('nearest_support')
                if nearest_support and nearest_support.get('price'):
                    target_price = f"{nearest_support['price']:.2f}"
                else:
                    target_price = f"{current_price * 0.95:.2f}"
                stop_loss = f"{current_price * 1.03:.2f}"
            
            pred = {
                'symbol': symbol,
                'predicted_direction': predicted_direction,
                'confidence': round(confidence, 2),
                'recommendation': rec,
                'overall_score': round(score, 1),
                'target_price': target_price,
                'stop_loss': stop_loss,
                'current_price': f"{current_price:.2f}",
            }
            predictions.append(pred)
            
        except Exception as e:
            print(f"  Warning: Failed to analyze {symbol}: {e}", file=sys.stderr)
            continue
    
    return {
        'date': date_str,
        'prediction_date': tomorrow,
        'generated_at': datetime.now().isoformat(),
        'engine_version': '2.0',
        'watchlist_predictions': predictions
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate stock predictions')
    parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'))
    parser.add_argument('--output', '-o', help='Output JSON file path')
    parser.add_argument('symbols', nargs='*', default=['BABA.US', 'NVDA.US', 'TSLA.US', 'CEG.US', 'COIN.US', 'PLTR.US'])
    args = parser.parse_args()
    
    result = generate_predictions(args.date, args.symbols)
    
    output = json.dumps(result, indent=2)
    
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Predictions saved to: {args.output}")
    else:
        print(output)


if __name__ == '__main__':
    main()
