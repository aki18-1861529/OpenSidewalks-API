#!/bin/sh

echo "Processing..."
python workspace.py $1

python merging.py $1