# Game Logging Project

A simple Python tool that automatically detects running games on Windows, logs session times, and stores them on a
server for later analysis.

# Features
- Detect games using running process names and window titles
- Log start and end times for gameplay sessions
- Store data in local SQLite database
- Prepare for syncing to a remote Ubuntu server

# Setup
pip install -r requirements.txt
python game_logger.py