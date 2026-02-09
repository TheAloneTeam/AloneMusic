# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
- Planned: (e.g., add subscription module, support for music playlists, apply NSFW filters for media, improve welcome image generator)  
- Planned: (e.g., refactor settings panel UI, optimize performance for voice‐chat streaming, update dependencies)

## [1.0.0] – YYYY-MM-DD  
### Added  
- Initial release of the project based on AloneMusic.  
- Core bot features: play/pause/skip, playlist management, voice chat streaming.  
- Settings panel and admin controls for groups, links & banned words.  
- Welcome image generator with circular avatars and custom assets.  
- NSFW detection system for images/stickers/videos.  
- Subscription/quota system: `/subscribe`, `/song`, `/admin`, user quota tracking.  
- YouTube thumbnail‐based media panel generation with blurred backgrounds.  
- Welcome panel styling and asset integration.  

### Changed  
- Improved performance and message handling logic.  
- Updated UI assets for music panel, welcome screen.  
- Refactored settings and database schema for MongoDB and/or SQLite.  

### Fixed  
- Bug: playback issues for certain YouTube links.  
- Bug: message deletion didn’t catch some link formats in groups.  
- Dependency conflicts resolved (e.g., updated Pyrogram, TF, PIL versions).  

## [0.9.0] – YYYY-MM-DD  
### Added  
- Prototype version: basic music streaming in voice chat.  
- Basic settings: owner/admin roles, playmode/votemode toggles.  
- Welcome message system (text only).  

### Fixed  
- Minor bug fixes in command handling and voice chat join/leave events.
