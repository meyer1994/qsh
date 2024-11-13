#!/bin/bash
set -e

# Create directories
mkdir -p dependencies/python
rm -rf dependencies/python/*

# Install dependencies using pip into the layer directory
pip install -r requirements.txt --target dependencies/python

# Remove unnecessary files to reduce size
find dependencies/python -type d -name "__pycache__" -exec rm -rf {} +
find dependencies/python -type d -name "*.dist-info" -exec rm -rf {} +
find dependencies/python -type d -name "*.egg-info" -exec rm -rf {} +
