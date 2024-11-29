#!/bin/bash

echo "Running initial test post..."
python src/test_post.py

# Check if test was successful
if [ $? -eq 0 ]; then
    echo "Test post successful! Starting main application..."
    exec python -u src/main.py
else
    echo "Test post failed! Check the logs for details."
    exit 1
fi
