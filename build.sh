#!/usr/bin/env bash
# exit on error
set -o errexit

# Ensure we're using Python 3.10
python --version

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
python -m pip install -r requirements.txt