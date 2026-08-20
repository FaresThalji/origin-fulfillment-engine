
# ORIGIN · Operations Console & Fulfillment Engine

ORIGIN is a production-focused fulfillment automation platform built to streamline multi-channel e-commerce operations. It connects warehouse management systems (WMS), carrier tracking services, and marketplace channels through automated workflows for order processing, fulfillment monitoring, tracking, and exception handling.

Designed with a high-performance, developer-first architecture, ORIGIN provides a unified operations interface for managing complex fulfillment workflows while reducing repetitive manual processes.

---

## 🚀 Key Features

Multi-Channel Operations Console: A unified workspace for monitoring fulfillment activity across marketplace channels, with real-time KPIs, processing status, tracking visibility, and exception monitoring.

Batch Order Processing: Bulk order lookup and processing through flexible input handling for PO numbers, enabling operators to process large order sets without repetitive manual entry.

WMS & Carrier Integration: Asynchronous data retrieval and concurrent processing designed to connect warehouse systems with carrier tracking data and provide up-to-date fulfillment status.

Marketplace Automation: Dedicated automation workflows for marketplace-specific operations, including authentication, order synchronization, fulfillment updates, and channel-specific processing.

Operational Intelligence: Built-in filtering, validation warnings, tracking references, detailed order inspection, and spreadsheet ingestion for quickly analyzing and acting on fulfillment data.
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

    
⚙️ Installation & Local Setup
1. Clone the Repository
Bash
git clone [https://github.com/YourUsername/origin-operations-console.git](https://github.com/YourUsername/origin-operations-console.git)
cd origin-operations-console
2. Install Dependencies
Make sure you install Flask with the [async] extra so asynchronous route views execute correctly:

Bash
pip install -r requirements.txt
(Or install manually via: pip install "Flask[async]==3.0.3" aiohttp==3.9.5 pandas==2.2.2 openpyxl==3.1.2)

3. Run the Application
Bash
python app.py
The server will start locally on http://127.0.0.1:5000 and automatically open the console in your default browser.

🔒 Sandbox & Mock Mode
This repository is pre-configured with secure fallback behaviors and sandbox login routes (demo / demo) so developers can evaluate the UI layout, command console, and workflow layouts instantly without needing active corporate API keys.

📄 License
This project is open-source and available under the MIT License.
