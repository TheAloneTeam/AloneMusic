# 🎵 AloneMusic

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Stars](https://img.shields.io/github/stars/TheAloneTeam/AloneMusic?style=social)](https://github.com/TheAloneTeam/AloneMusic/stargazers)
[![Forks](https://img.shields.io/github/forks/TheAloneTeam/AloneMusic?style=social)](https://github.com/TheAloneTeam/AloneMusic/network/members)

---


## 🚀 Introduction
**AloneMusic** is a Python-based **music bot/service** that allows users to play, pause, skip, and manage playlists with ease.  
It’s designed to be lightweight, fast, and customizable.  

---

## ✨ Features
- 🎶 Play / Pause / Skip / Stop songs  
- 📂 Playlist management (add/remove/list)  
- 🔗 Play via song name or URL  
- ⚡ Fast and smooth performance  
- ⚙️ Easy configuration with `.env` file  
- 🐳 Docker & Heroku deployment support  

---
## ❤️ Support

💬 **Telegram:** [AloneMusic](https://t.me/TheTeamHacker)  

🆘 **Any Problem? DM:** [𝚨Łꪮⲛ𝛆 🚩𝗧ε᧘‌ᴍ](https://t.me/codeshivu)

📂 **GitHub Issues:** [Report a Problem](https://github.com/TheAloneTeam/AloneMusic/issues/new)

---

## 📜 License

🧾 This project is licensed under the **GNU GPLv3 License** — see the [LICENSE](/LICENSE) file for details.

---

## 🚀 Deployment Methods

### 🔹 1. Deploy on **Heroku** (One Click)
Click this button to deploy instantly on **Heroku**:

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/TheAloneTeam/AloneMusic)


- **Update System and Install Dependencies**:  
  ```bash
  sudo apt update && sudo apt upgrade -y && sudo apt install -y ffmpeg git python3-pip tmux nano
  ```

- **Install uv for Efficient Dependency Management**:
  ```bash
  pip install uv
  ```
- **Clone the Repository:**  
  ```bash
  git clone https://github.com/TheAloneTeam/AloneMusic cd AloneMusic
  ```
  
- **Create and Activate a Virtual Environment:**
  - You can create and activate the virtual Environment before cloning the repo.
  ```bash
  uv venv .venv && source .venv/bin/activate
  ```

- Install Python Requirements:  
  ```bash
  uv pip install -e .
  ```

- Copy and Edit Environment Variables:  
  ```bash
  cp sample.env .env && nano .env
  ```
  After editing, press `Ctrl+X`, then `Y`, and press **Enter** to save the changes.

- Start a tmux Session to Keep the Bot Running:  
  ```bash
  tmux
  ```

- Run the Bot:  
  ```bash
  python3 -m AloneMusic
  ```

- Detach from the **tmux** Session (Bot keeps running):  
  Press `Ctrl+b`, then `d`
