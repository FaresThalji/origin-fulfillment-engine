
# ORIGIN · Operations Console & Fulfillment Engine

**ORIGIN** is a high-performance, dark-mode operations console and order fulfillment automation tool designed to bridge warehouse management systems (WMS), live carrier tracking feeds, and marketplace channels (such as Walmart). 

It features an ultra-low latency, modern developer-first interface inspired by Linear and Vercel design principles.

---

## 🚀 Key Features

* **Unified Multi-Channel Dashboard:** A high-speed command center featuring live KPI monitoring (Shipped, No Tracking, Exceptions, Total Processed).
* **Batch Order Extraction:** A streamlined command input node supporting newline, comma, or space-separated PO numbers for bulk warehouse lookups.
* **WMS & Carrier Integration:** Asynchronous backend (`asyncio` / `aiohttp`) designed to query warehouse data and cross-reference live shipping milestones concurrently.
* **Marketplace Automation Workspace:** Dedicated portals to handle channel-specific sync tasks, cookie authentication management, and automated fulfillment push updates.
* **Precision Ergonomics:** Built-in category filters, smart prefix warning flags, clickable tracking references, detail inspection drawers, and instant spreadsheet parsing (`xlsx`/`csv`).

---

## 🛠️ Tech Stack

* **Backend:** Python, Flask (with `async` support), `aiohttp`, `requests`
* **Frontend:** HTML5, CSS3 (Custom Design Tokens, responsive dark mode), Vanilla JavaScript (ES6+)
* **Utilities:** SheetJS (`xlsx`) for spreadsheet imports

---

## 📁 Project Structure

```text
Orders-automation/
│
├── app.py                  # Core Flask application & asynchronous API controllers
├── requirements.txt        # Python package dependencies
└── templates/              # Frontend templates
    ├── dashboard.html      # Mission-control operations deck & client-side app logic
    └── login.html          # Secure entry interface with system boot sequence
