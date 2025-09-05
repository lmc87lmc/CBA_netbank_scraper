# CBA Netbank Scraper API

This project provides a solution for automatically scraping transaction data from the Commonwealth Bank of Australia's (CBA) NetBank web portal. It includes scripts for automated login, handling of Multi-Factor Authentication (MFA) via an Android emulator, and a simple API to expose the scraped data for other applications, such as a Discord bot.

## About The Project

This project is composed of three main Python scripts that work together to achieve automated transaction monitoring:

*   `Netbank_Scraper.py`: A `seleniumbase`-powered scraper that handles the browser automation. It logs into NetBank, navigates to the transactions page, and systematically clicks on each transaction to extract its details.
*   `ADB_CBA_MFA_APPROVE.py`: A helper script that uses the Android Debug Bridge (ADB) to automate the MFA approval process. When a login is initiated, this script simulates the necessary taps within the CommBank app running on an Android emulator to approve the session.
*   `api_server.py`: A Flask-based API server that runs the scraper in a background thread. It provides a secure endpoint that other applications can call to retrieve newly detected transactions from a queue.

### Key Features

*   **Automated Login**: Securely logs into NetBank using provided client number and password.
*   **MFA Automation**: Seamlessly handles the MFA approval process by interacting with the CommBank mobile app via ADB.
*   **Detailed Transaction Scraping**: Extracts comprehensive transaction information, including title, amount, description, reference, and the unique receipt number.
*   **Persistent Transaction Tracking**: Avoids reprocessing duplicates by saving known transaction receipt numbers to a local file (`known_transactions.txt`).
*   **API for Easy Integration**: Provides a simple, key-protected API endpoint to fetch newly scraped transactions, allowing for straightforward integration with other services.
*   **Continuous Monitoring**: Runs in a loop to periodically refresh the transaction page and check for new activity.

## Getting Started

Follow these steps to get the project set up and running on your local machine.

### Prerequisites

*   Python 3.x
*   An Android emulator with the CommBank app installed (e.g., [LDPlayer](https://www.ldplayer.net/)).
*   Android Debug Bridge (ADB) installed and configured to connect to your emulator.
*   A web browser compatible with Selenium (e.g., Google Chrome or Brave Browser).

### Installation

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/lmc87lmc/CBA_netbank_scraper.git
    cd CBA_netbank_scraper
    ```
2.  **Install Python dependencies:**
    ```sh
    pip install seleniumbase flask waitress
    ```

### Configuration

Before running the scripts, you need to configure your sensitive information and environment-specific paths. **It is highly recommended to use environment variables for sensitive data in a production environment.**

1.  **`api_server.py` (Main Scraper & API):**
    *   Set your NetBank client number: `NB_client_number = "YOUR_CLIENT_NUMBER"`
    *   Set your NetBank password: `NB_password = "YOUR_PASSWORD"`
    *   Set a secure, private API key: `API_KEY = "SET_YOUR_API_KEY"`

2.  **`ADB_CBA_MFA_APPROVE.py` (MFA Handler):**
    *   Update `LDPLAYER_ADB_PATH` to the correct absolute path of your `adb.exe` executable.
    *   Set your CommBank app PIN: `COMMBANK_PIN = "YOUR_4_DIGIT_PIN"`
    *   **Crucially**, you may need to adjust the tap coordinates based on your emulator's screen resolution. Use ADB's "Layout Inspector" or developer options to find the correct `(x, y)` coordinates for the following steps:
        *   `STEP_1_INITIAL_NOTIFICATION_COORDS`
        *   `STEP_2_CHECK_DETAILS_COORDS`
        *   `STEP_3_FINAL_APPROVAL_COORDS`

## Usage

The system is designed to run continuously. The API server starts the scraper, and the MFA script is run manually when a new login session is required.

1.  **Start the API Server:**
    Open a terminal and run the `api_server.py` script. This will initialize the Selenium browser, begin the login process, and start the Flask server.
    ```sh
    python api_server.py
    ```
    The server will be accessible at `http://0.0.0.0:5000`. The scraper will pause and wait at the MFA screen.

2.  **Trigger MFA Approval:**
    With the emulator running and the CommBank app notification visible, open a second terminal and run the MFA approval script.
    ```sh
    python ADB_CBA_MFA_APPROVE.py
    ```
    This script will automatically open the app, enter the PIN, and perform the three taps required to approve the login. The Selenium browser in the first terminal will then proceed to the account page.

3.  **Fetching New Transactions:**
    Once logged in, the scraper will continuously monitor for new transactions. To retrieve any newly found transactions, make a POST request to the `/scrape` endpoint with your API key in the headers.

    **Example using `curl`:**
    ```sh
    curl -X POST -H "X-API-KEY: SET_YOUR_API_KEY" http://localhost:5000/scrape
    ```

    The API will return a JSON array of new transaction data. If no new transactions are found, it will return an empty array `[]`.

## Disclaimer

This project is intended for educational and personal use only. Automating interactions with a bank's website may be against their terms of service. Use this project responsibly and at your own risk. The author is not responsible for any issues, account limitations, or financial losses that may arise from its use.
