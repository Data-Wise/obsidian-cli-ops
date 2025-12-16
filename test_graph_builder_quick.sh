#!/bin/bash
# Quick test script for graph_builder tests

cd /Users/dt/projects/dev-tools/obsidian-cli-ops

# Run only the graph_builder tests
PYTHONPATH=src/python pytest src/python/tests/test_graph_builder.py -v

# Show exit code
echo ""
echo "Exit code: $?"
