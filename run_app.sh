#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python is not installed. Please install Python and try again."
    exit 1
fi

# Install necessary libraries
echo "Installing required libraries..."
python3 -m pip install --user flask flask-cors flask-socketio undetected-chromedriver requests &> /dev/null
if [ $? -ne 0 ]; then
    echo "Failed to install required libraries. Please check your Python environment."
    exit 1
fi

# Start the Flask app in the background
python3 app.py &
FLASK_PID=$!

# Wait for the Flask server to start
sleep 2

# Open the default browser
if command -v xdg-open &> /dev/null; then
    xdg-open http://127.0.0.1:5000
else
    echo "Please open your browser and navigate to http://127.0.0.1:5000"
fi

# Wait for the Flask app process to complete
wait $FLASK_PID
