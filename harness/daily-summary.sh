#!/bin/bash
# Daily summary script for stock analysis harness
# Run at 9:00 AM Beijing Time to analyze previous US trading day's performance and predict next day

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$SCRIPT_DIR/data"  # Correct: stock-analysis/harness/data/

# Load configuration
CONFIG_FILE="$SCRIPT_DIR/config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Parse YAML (simple approach)
get_config() {
    grep "^$1:" "$CONFIG_FILE" | cut -d: -f2- | sed 's/#.*$//' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | sed 's/^"//;s/"$//'
}

DATA_DIR="$SCRIPT_DIR/$(get_config data_dir)"
DAILY_REPORTS_DIR="$DATA_DIR/$(get_config daily_reports_dir)"
PREDICTIONS_DIR="$DATA_DIR/$(get_config predictions_dir)"
METRICS_DIR="$DATA_DIR/$(get_config metrics_dir)"

# Create directories if they don't exist
mkdir -p "$DAILY_REPORTS_DIR" "$PREDICTIONS_DIR" "$METRICS_DIR"

# Get current date
TODAY=$(date +%Y-%m-%d)
YESTERDAY=$(date -v-1d +%Y-%m-%d)

# Check if market is open (simple check: weekday and time)
DAY_OF_WEEK=$(date +%u)  # 1=Monday, 7=Sunday
if [ "$DAY_OF_WEEK" -ge 6 ]; then
    echo "Weekend - skipping analysis"
    exit 0
fi

echo "Generating daily summary for $TODAY"
echo "====================================="

# Step 1: Get market sentiment
echo "1. Fetching market sentiment..."
MARKET_SENTIMENT=$(longbridge market-temp 2>/dev/null || echo "N/A")
echo "Market sentiment: $MARKET_SENTIMENT"

# Step 2: Get major indices
echo "2. Fetching major indices..."
MAJOR_INDICES=$(longbridge quote .^GSPC.US .^DJI.US .^IXIC.US 2>/dev/null || echo "N/A")

# Step 3: Fetch quotes for watchlist
echo "3. Fetching watchlist quotes..."
# Load watchlist from references/watchlist.json (single source of truth)
WATCHLIST_JSON="$SKILL_DIR/references/watchlist.json"
if [ -f "$WATCHLIST_JSON" ]; then
    WATCHLIST=($(python3 -c "
import json
with open('$WATCHLIST_JSON') as f:
    data = json.load(f)
print(' '.join(item['symbol'] for item in data['watchlist']))
"))
else
    # Fallback if watchlist.json is missing
    WATCHLIST=($(python3 -c "from watchlist_utils import load_watchlist; print(' '.join(load_watchlist()))"))
fi

QUOTES_FILE="$DAILY_REPORTS_DIR/quotes-$TODAY.json"
echo "Fetching quotes for: ${WATCHLIST[*]}"
longbridge quote "${WATCHLIST[@]}" --format json > "$QUOTES_FILE" 2>/dev/null || echo "Failed to fetch quotes"

# Step 4: Get news for each symbol
echo "4. Fetching news for watchlist..."
NEWS_DIR="$DAILY_REPORTS_DIR/news-$TODAY"
mkdir -p "$NEWS_DIR"
for symbol in "${WATCHLIST[@]}"; do
    echo "  - $symbol"
    longbridge news "$symbol" --limit 3 > "$NEWS_DIR/${symbol}.txt" 2>/dev/null || echo "No news for $symbol"
done

# Step 5: Generate structured market environment assessment
echo "5. Generating market environment assessment..."
MARKET_ENV_FILE="$DAILY_REPORTS_DIR/market-environment-$TODAY.json"
python3 "$SCRIPT_DIR/market_environment.py" --quotes "$QUOTES_FILE" --output "$MARKET_ENV_FILE" 2>/dev/null || {
    echo "Warning: Market environment generation failed"
    echo "{}" > "$MARKET_ENV_FILE"
}

# Step 6: Generate value assessment (MUST be before report, so valuation data is available)
echo "6. Generating value assessment..."
PREDICTION_FILE="$PREDICTIONS_DIR/assessment-$TODAY.json"

python3 "$SCRIPT_DIR/generate_valuation.py" --date "$TODAY" --output "$PREDICTION_FILE" 2>/dev/null || {
    echo "Warning: Valuation generation failed, using fallback"
    echo "{}" > "$PREDICTION_FILE"
}

echo "Predictions saved to: $PREDICTION_FILE"

# Step 7: Generate summary report with valuation ranges
echo "7. Generating summary report..."
REPORT_FILE="$DAILY_REPORTS_DIR/report-$TODAY.md"

# Fetch positions data (includes options)
echo "  Fetching portfolio positions..."
POSITIONS_FILE="$DAILY_REPORTS_DIR/positions-$TODAY.json"
longbridge positions --format json > "$POSITIONS_FILE" 2>/dev/null || echo "[]"

# Run option analysis via Python
echo "  Running option analysis..."
OPTION_REPORT_FILE="$DAILY_REPORTS_DIR/options-$TODAY.md"
python3 "$SCRIPT_DIR/option-analysis.py" --positions "$POSITIONS_FILE" --output "$OPTION_REPORT_FILE" 2>/dev/null || {
    echo "  Warning: Option analysis failed, will include raw data"
    OPTION_REPORT_FILE=""
}

# Helper to extract valuation range for a symbol from the prediction JSON
get_valuation_for_symbol() {
    local sym="$1"
    local pred_file="$2"
    if [ -f "$pred_file" ] && [ -s "$pred_file" ]; then
        python3 -c "
import json, sys
try:
    with open('$pred_file') as f:
        data = json.load(f)
    for a in data.get('watchlist_assessments', []):
        if a['symbol'] == '$sym':
            v = a.get('valuation_range', {}) or {}
            lo = v.get('valuation_lower', '')
            hi = v.get('valuation_upper', '')
            cv = a.get('core_value', '')
            src = a.get('core_value_source', '')
            act = a.get('action', '')
            dev = a.get('deviation_pct', '')
            ts = a.get('value_trap_score', 0)
            mw = a.get('moat_width', 'None')
            # Format: lower|upper|core|source|action|deviation|trap_score|moat
            print(f'{lo}|{hi}|{cv}|{src}|{act}|{dev}|{ts}|{mw}')
            sys.exit(0)
    print('|||||||')
except:
    print('|||||||')
" 2>/dev/null
    else
        echo '|||||||'
    fi
}

MARKET_ENV_SUMMARY=$(python3 -c "
import json
try:
    with open('$MARKET_ENV_FILE') as f:
        data = json.load(f)
    a = data.get('assessment', {})
    caps = ', '.join(a.get('position_caps_applied') or []) or 'none'
    dims = a.get('dimension_breakdown', {})
    dim_text = ', '.join('{}:{}'.format(k, v.get('score', 'N/A')) for k, v in dims.items() if isinstance(v, dict) and k != 'sentiment_modifier')
    print('Score {} | {} | Position cap {} | Caps: {} | Dimensions: {}'.format(a.get('environment_score', 'N/A'), a.get('environment', 'UNKNOWN'), a.get('position_cap', 'N/A'), caps, dim_text))
except Exception:
    print('N/A')
" 2>/dev/null)

cat > "$REPORT_FILE" << EOF
# 📊 Daily Stock Analysis Summary
Date: $TODAY
Generated: $(date)

## Market Overview
- **Market Sentiment:** $MARKET_SENTIMENT
- **Major Indices:** $MAJOR_INDICES
- **Five-Factor Environment:** $MARKET_ENV_SUMMARY
- **Environment Data:** $MARKET_ENV_FILE

## Watchlist Performance
| Symbol | Price | Chg% | Volume | Valuation Range | Core Value | Deviation | Moat | Action |
|--------|-------|------|--------|-----------------|------------|-----------|------|--------|
EOF

# Parse quotes and valuation JSON and add rows
for symbol in "${WATCHLIST[@]}"; do
    PRICE="N/A"
    CHANGE="N/A"
    VOLUME="N/A"

    if [ -f "$QUOTES_FILE" ]; then
        if command -v jq &> /dev/null; then
            PRICE=$(jq -r ".[] | select(.symbol == \"$symbol\") | .last_done // .last // \"N/A\"" "$QUOTES_FILE" 2>/dev/null || echo "N/A")
            CHANGE=$(jq -r ".[] | select(.symbol == \"$symbol\") | .change_percentage // .change_rate // \"N/A\"" "$QUOTES_FILE" 2>/dev/null || echo "N/A")
            VOLUME=$(jq -r ".[] | select(.symbol == \"$symbol\") | .volume // \"N/A\"" "$QUOTES_FILE" 2>/dev/null || echo "N/A")
        fi
    fi

    # Get valuation range from prediction JSON
    VAL_DATA=$(get_valuation_for_symbol "$symbol" "$PREDICTION_FILE")
    VAL_LOWER=$(echo "$VAL_DATA" | cut -d'|' -f1)
    VAL_UPPER=$(echo "$VAL_DATA" | cut -d'|' -f2)
    CORE_VALUE=$(echo "$VAL_DATA" | cut -d'|' -f3)
    VAL_SOURCE=$(echo "$VAL_DATA" | cut -d'|' -f4)
    VAL_ACTION=$(echo "$VAL_DATA" | cut -d'|' -f5)
    VAL_DEV=$(echo "$VAL_DATA" | cut -d'|' -f6)
    TRAP_SCORE=$(echo "$VAL_DATA" | cut -d'|' -f7)
    MOAT=$(echo "$VAL_DATA" | cut -d'|' -f8)

    # Format valuation range display
    if [ -n "$VAL_LOWER" ] && [ "$VAL_LOWER" != "" ]; then
        VAL_RANGE_DISPLAY="\$$VAL_LOWER - \$$VAL_UPPER"
    else
        VAL_RANGE_DISPLAY="N/A"
    fi

    if [ -n "$CORE_VALUE" ] && [ "$CORE_VALUE" != "" ]; then
        CORE_DISPLAY="\$$CORE_VALUE"
    else
        CORE_DISPLAY="N/A"
    fi

    if [ -n "$VAL_DEV" ] && [ "$VAL_DEV" != "" ]; then
        DEV_DISPLAY="${VAL_DEV}%"
    else
        DEV_DISPLAY="N/A"
    fi

    # Format action with emoji
    case "$VAL_ACTION" in
        GET_ON_BOARD) ACTION_DISPLAY="🚀 Buy" ;;
        BUY) ACTION_DISPLAY="✅ Buy" ;;
        BUY_SMALL) ACTION_DISPLAY="➕ Add" ;;
        HOLD) ACTION_DISPLAY="➡️ Hold" ;;
        WAIT) ACTION_DISPLAY="⏳ Wait" ;;
        AVOID) ACTION_DISPLAY="❌ Avoid" ;;
        *) ACTION_DISPLAY="$VAL_ACTION" ;;
    esac

    echo "| $symbol | $PRICE | ${CHANGE}% | $VOLUME | $VAL_RANGE_DISPLAY | $CORE_DISPLAY | $DEV_DISPLAY | $MOAT | $ACTION_DISPLAY |" >> "$REPORT_FILE"
done

cat >> "$REPORT_FILE" << EOF

## Key Observations

### Market Sentiment Analysis
- **Raw Data:** $MARKET_SENTIMENT

### Individual Stock Analysis
EOF

for symbol in "${WATCHLIST[@]}"; do
    PRICE="N/A"
    CHANGE="N/A"
    VOLUME="N/A"

    if [ -f "$QUOTES_FILE" ]; then
        if command -v jq &> /dev/null; then
            PRICE=$(jq -r ".[] | select(.symbol == \"$symbol\") | .last_done // .last // \"N/A\"" "$QUOTES_FILE" 2>/dev/null || echo "N/A")
            CHANGE=$(jq -r ".[] | select(.symbol == \"$symbol\") | .change_percentage // .change_rate // \"N/A\"" "$QUOTES_FILE" 2>/dev/null || echo "N/A")
            VOLUME=$(jq -r ".[] | select(.symbol == \"$symbol\") | .volume // \"N/A\"" "$QUOTES_FILE" 2>/dev/null || echo "N/A")
        fi
    fi

    # Get valuation data for this symbol
    VAL_DATA=$(get_valuation_for_symbol "$symbol" "$PREDICTION_FILE")
    VAL_LOWER=$(echo "$VAL_DATA" | cut -d'|' -f1)
    VAL_UPPER=$(echo "$VAL_DATA" | cut -d'|' -f2)
    CORE_VALUE=$(echo "$VAL_DATA" | cut -d'|' -f3)
    VAL_SOURCE=$(echo "$VAL_DATA" | cut -d'|' -f4)
    VAL_ACTION=$(echo "$VAL_DATA" | cut -d'|' -f5)
    VAL_DEV=$(echo "$VAL_DATA" | cut -d'|' -f6)
    TRAP_SCORE=$(echo "$VAL_DATA" | cut -d'|' -f7)
    MOAT=$(echo "$VAL_DATA" | cut -d'|' -f8)

    # Format valuation display
    VALUATION_SECTION=""
    if [ -n "$VAL_LOWER" ] && [ "$VAL_LOWER" != "" ]; then
        VALUATION_SECTION="
- **估值区间:** \$${VAL_LOWER} - \$${VAL_UPPER} (核心价值: \$${CORE_VALUE})
- **偏离度:** ${VAL_DEV}%
- **估值方法:** ${VAL_SOURCE}
- **护城河:** ${MOAT}
- **价值陷阱评分:** ${TRAP_SCORE}/100
- **估值建议:** ${VAL_ACTION}"
    else
        VALUATION_SECTION="
- **估值数据:** 暂不可用（请验证财务数据或等待下次更新）"
    fi

    cat >> "$REPORT_FILE" << EOF

#### $symbol
- **Price:** $PRICE
- **Change:** $CHANGE%
- **Volume:** $VOLUME${VALUATION_SECTION}
- **Catalysts:** See news in ${NEWS_DIR}/${symbol}.txt
EOF
done

cat >> "$REPORT_FILE" << EOF

## Option Positions

EOF

# Append option analysis if available
if [ -f "$OPTION_REPORT_FILE" ] && [ -s "$OPTION_REPORT_FILE" ]; then
    cat "$OPTION_REPORT_FILE" >> "$REPORT_FILE"
else
    # Fallback: include raw option positions from JSON
    if command -v jq &> /dev/null && [ -f "$POSITIONS_FILE" ]; then
        OPTION_COUNT=$(jq '[.[] | select(.symbol | test("^[A-Z]+[0-9]{6}[CP][0-9]+\\.US$"))]' "$POSITIONS_FILE" 2>/dev/null | jq 'length' 2>/dev/null || echo "0")
        if [ "$OPTION_COUNT" -gt 0 ]; then
            echo "Detected $OPTION_COUNT option position(s) - detailed analysis pending" >> "$REPORT_FILE"
            jq -r '.[] | select(.symbol | test("^[A-Z]+[0-9]{6}[CP][0-9]+\\.US$")) | "- \(.symbol): \(.quantity) contracts @ \(.cost_price)"' "$POSITIONS_FILE" 2>/dev/null >> "$REPORT_FILE" || true
        else
            echo "No option positions found" >> "$REPORT_FILE"
        fi
    else
        echo "Option analysis unavailable (install jq for basic option detection)" >> "$REPORT_FILE"
    fi
fi

cat >> "$REPORT_FILE" << EOF

## Predictions for Tomorrow ($(date -v+1d +%Y-%m-%d))
See predictions file: $PREDICTIONS_DIR/assessment-$TODAY.json

## Notes
- This report is generated automatically for review purposes.
- Always conduct your own research before making investment decisions.
EOF

echo "Summary report saved to: $REPORT_FILE"

# Step 8: Update metrics
echo "8. Updating performance metrics..."
METRICS_FILE="$METRICS_DIR/metrics-$TODAY.json"
cat > "$METRICS_FILE" << EOF
{
  "date": "$TODAY",
  "metrics": {
    "report_generated": true,
    "predictions_saved": true,
    "market_environment_saved": true,
    "symbols_analyzed": ${#WATCHLIST[@]}
  }
}
EOF

echo "Daily summary completed successfully!"
echo "====================================="
echo "Next steps:"
echo "1. Review report: $REPORT_FILE"
echo "2. Run backtest at 9:30 AM Beijing Time to compare predictions vs actual"
echo "3. Adjust tracking metrics if needed (Friday 10:00 AM)"
