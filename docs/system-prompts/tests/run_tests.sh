#!/bin/bash
# Test runner for Agent Kernel tools (bootstrap.py and docscan.py)
#
# Usage:
#   ./docs/system-prompts/tests/run_tests.sh          # Run all tests
#   ./docs/system-prompts/tests/run_tests.sh docscan  # Run docscan tests only
#   ./docs/system-prompts/tests/run_tests.sh bootstrap # Run bootstrap tests only
#   ./docs/system-prompts/tests/run_tests.sh -v       # Verbose output

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../../../.." && pwd )"

echo "================================================================================"
echo "Agent Kernel Test Suite"
echo "================================================================================"
echo ""
echo "Testing: $SCRIPT_DIR"
echo "Project: $PROJECT_ROOT"
echo ""

# Determine which tests to run
if [ $# -eq 0 ]; then
    # Run all tests
    echo "Running all tests..."
    python3 -m unittest discover -s "$SCRIPT_DIR" -p "test_*.py" -v
elif [ "$1" = "docscan" ]; then
    echo "Running docscan tests only..."
    python3 "$SCRIPT_DIR/test_docscan.py" -v
elif [ "$1" = "bootstrap" ]; then
    echo "Running bootstrap tests only..."
    python3 "$SCRIPT_DIR/test_bootstrap.py" -v
elif [ "$1" = "-v" ] || [ "$1" = "--verbose" ]; then
    echo "Running all tests (verbose)..."
    python3 -m unittest discover -s "$SCRIPT_DIR" -p "test_*.py" -v
else
    echo "Usage: $0 [docscan|bootstrap|--verbose|-v]"
    exit 1
fi

echo ""
echo "================================================================================"
echo "Test run complete"
echo "================================================================================"
