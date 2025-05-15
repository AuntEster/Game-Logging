# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2025-05-14

### Added
- SteamGridDB API integration to automatically resolve executable names into game titles.
- In-memory caching for SteamGridDB lookup results to reduce API calls and improve performance.
- Timeout handling for external API calls to avoid hangs if the service is unresponsive.
- Basic executable name filtering to avoid logging system apps like Discord, Notepad, etc.
- SQLite session tracking for game start and end times.
- Grace period for session endings to accommodate launchers and brief process drops.

### Changed
- Log output now shows resolved game names rather than raw `.exe` names (when possible).
- Game detection no longer relies on a hardcoded watch list (WATCHED_GAMES removed).

### Known Issues
- Games launched through elevated processes (like Warframe maybe?) may not be detected unless logger is run as administrator.
- SteamGridDB autocomplete endpoint occasionally returns non-game matches (e.g. system tools).
- Some processes are missed if they start and end between polling intervals.

---

## [0.1.0] - 2025-05-12

### Added
- Initial version of the game logger.
- Hardcoded "warframe.x64.exe" in a WATCHED_GAMES list to detect and track Warframe sessions during testing.
- SQLite database (game_session.db) created to store game session start and end times.
- Captures active window title during session start for context.
- Basic terminal output for debugging.