# AtoZDiscordBot
webhook for getting jobs off that platform (hiring.amazon.com) | (a to z)

# Automated Job Post Monitor & Discord Webhook Alert

A lightweight, automated web-scraping script built with **Python** and **Playwright** that continuously monitors targeted job search URLs (configured out-of-the-box for portal-style hiring sites like Amazon), parses shift card parameters (such as Full-Time, Part-Time, Regular, or Seasonal), and pushes real-time alert notifications directly to a **Discord channel via Webhook**.

---

## Features

* **Headless Browser Automation:** Utilizes Playwright with anti-bot detection flags (`--disable-blink-features=AutomationControlled`) to reliably query modern dynamic web apps.
* **Granular Shift Filtering:** Differentiates between shift types (Full-Time, Part-Time, Flex) and employment durations (Regular vs. Seasonal).
* **Smart Priority Badging:** Tags high-value listings with custom visual markers and priority alerts.
* **Built-in Verification Loop:** Once a listing is found, it waits 30 seconds and re-scans the URL to confirm whether the position is still active before sending a follow-up alert.
* **Discord Integration:** Sends cleanly formatted markdown alerts straight to your server.

---

## Prerequisites

* **Python 3.8+** installed on your machine.
* `pip` package manager.

---

## Installation & Setup

1. **Clone or download** this repository/script.
2. **Install dependencies:**
   ```bash
   pip install requests playwright
