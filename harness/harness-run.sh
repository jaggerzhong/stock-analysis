#!/bin/bash
# Main harness runner - orchestrates daily summary, backtest, and adjustment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
}

print_step() {
    echo -e "${GREEN}[+]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[x]${NC} $1"
}

# Check dependencies
check_dependencies() {
    local missing=0
    
    # Check for longbridge CLI
    if ! command -v longbridge &> /dev/null; then
        print_error "longbridge CLI not found. Please install from https://open.longbridge.com"
        missing=1
    fi
    
    # Check for Python
    if ! command -v python3 &> /dev/null; then
        print_error "python3 not found. Please install Python 3.8+"
        missing=1
    fi
    
    # Check for jq (optional but recommended)
    if ! command -v jq &> /dev/null; then
        print_warning "jq not found. JSON parsing will be limited."
    fi
    
    # Check for yaml module
    python3 -c "import yaml" 2>/dev/null || {
        print_warning "PyYAML not installed. Installing with pip..."
        pip3 install pyyaml || {
            print_error "Failed to install PyYAML. Some features may not work."
        }
    }
    
    return $missing
}

# Run daily summary
run_daily_summary() {
    print_header "DAILY SUMMARY"
    print_step "Running daily summary..."
    
    if [ ! -x "./daily-summary.sh" ]; then
        print_error "daily-summary.sh not found or not executable"
        return 1
    fi
    
    ./daily-summary.sh
    local status=$?
    
    if [ $status -eq 0 ]; then
        print_step "Daily summary completed successfully"
    else
        print_error "Daily summary failed with status $status"
    fi
    
    return $status
}

# Run backtest
run_backtest() {
    print_header "BACKTEST"
    print_step "Running backtest..."
    
    if [ ! -f "./backtest.py" ]; then
        print_error "backtest.py not found"
        return 1
    fi
    
    python3 ./backtest.py
    local status=$?
    
    if [ $status -eq 0 ]; then
        print_step "Backtest completed successfully"
    else
        print_error "Backtest failed with status $status"
    fi
    
    return $status
}

# Run metrics adjustment analysis
run_adjustment_analysis() {
    print_header "METRICS ADJUSTMENT ANALYSIS"
    print_step "Analyzing metrics performance..."
    
    if [ ! -f "./adjust-metrics.py" ]; then
        print_error "adjust-metrics.py not found"
        return 1
    fi
    
    # Only run adjustment analysis if we have enough data
    DATA_DIR="data"
    if [ -f "$DATA_DIR/metrics/cumulative_metrics.json" ]; then
        history_count=$(python3 -c "
import json
try:
    with open('$DATA_DIR/metrics/cumulative_metrics.json') as f:
        data = json.load(f)
    print(len(data.get('backtest_history', [])))
except:
    print(0)
        ")
        
        if [ "$history_count" -ge 5 ]; then
            print_step "Found $history_count days of backtest data - running analysis"
            python3 ./adjust-metrics.py
            local status=$?
        else
            print_warning "Insufficient backtest data ($history_count days). Need at least 5 days."
            print_step "Skipping adjustment analysis for now"
            return 0
        fi
    else
        print_warning "No cumulative metrics found. Run backtests first."
        return 0
    fi
    
    return $status
}

# Generate overall report
generate_report() {
    print_header "HARNESS REPORT"
    
    TODAY=$(date +%Y-%m-%d)
    DATA_DIR="data"
    
    echo "Harness Run Summary - $TODAY"
    echo "========================================"
    echo ""
    
    # Check daily report
    if [ -f "$DATA_DIR/daily/report-$TODAY.md" ]; then
        echo "✅ Daily report generated"
    else
        echo "❌ Daily report not generated"
    fi
    
    # Check backtest results (compares yesterday vs yesterday)
    YESTERDAY=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "yesterday" +%Y-%m-%d)
    if [ -f "$DATA_DIR/backtests/backtest-$YESTERDAY-$YESTERDAY.json" ]; then
        echo "✅ Backtest completed for $YESTERDAY"
    else
        echo "❌ Backtest not completed"
    fi
    
    # Check cumulative metrics
    if [ -f "$DATA_DIR/metrics/cumulative_metrics.json" ]; then
        echo "✅ Cumulative metrics updated"
    else
        echo "❌ Cumulative metrics not available"
    fi
    
    echo ""
    echo "Next Steps (Beijing Time):"
    echo "1. Review daily report: $DATA_DIR/daily/report-$TODAY.md"
    echo "2. Run backtest at 9:30 AM: ./harness-run.sh --backtest"
    echo "3. Check backtest results: $DATA_DIR/backtests/"
    echo "4. Consider adjustments if needed (Friday 10:00 AM)"
    echo ""
    echo "To set up automatic daily runs (Beijing Time), add to crontab:"
    echo "0 9 * * * cd $SCRIPT_DIR && ./harness-run.sh --daily"
}

# Parse command line arguments
MODE="full"

while [[ $# -gt 0 ]]; do
    case $1 in
        --daily)
            MODE="daily"
            shift
            ;;
        --backtest)
            MODE="backtest"
            shift
            ;;
        --adjust)
            MODE="adjust"
            shift
            ;;
        --report)
            MODE="report"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTION]"
            echo "Run stock analysis harness"
            echo ""
            echo "Options:"
            echo "  --daily     Run only daily summary"
            echo "  --backtest  Run only backtest"
            echo "  --adjust    Run only adjustment analysis"
            echo "  --report    Generate report only"
            echo "  --help      Show this help"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_header "STOCK ANALYSIS HARNESS"
    echo "Mode: $MODE"
    echo "Date: $(date)"
    echo ""
    
    # Check dependencies
    check_dependencies || {
        print_error "Missing dependencies. Please install required tools."
        exit 1
    }
    
    case $MODE in
        daily)
            run_daily_summary
            ;;
        backtest)
            run_backtest
            ;;
        adjust)
            run_adjustment_analysis
            ;;
        report)
            generate_report
            ;;
        full)
            print_step "Running full harness workflow..."
            run_daily_summary
            echo ""
            run_backtest
            echo ""
            run_adjustment_analysis
            echo ""
            generate_report
            ;;
    esac
    
    print_header "HARNESS COMPLETE"
    echo "All tasks finished at $(date)"
}

# Run main function
main "$@"