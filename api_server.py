# api_server.py
API_KEY = "SET_YOUR_API_KEY"
import time
import os
import sys
import traceback
from threading import Thread
from queue import Queue
from flask import Flask, request, jsonify
from waitress import serve
from seleniumbase import SB
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# --- Flask & Security Configuration ---
app = Flask(__name__)

# --- Scraper Configuration ---
NB_client_number = "INSERT_CLIENT_NUMBER_HERE"
NB_password = "INSERT_PASSWORD_HERE"
REFRESH_INTERVAL_SECONDS = 30
KNOWN_TRANSACTION_SAFETY_LIMIT = 5

# --- NEW: Robust File Path Handling ---
# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Join the script directory with the filename to create a foolproof path
TRANSACTIONS_FILE = os.path.join(SCRIPT_DIR, "known_transactions.txt")

# --- NEW: Thread-safe queue ---
transaction_queue = Queue()


def load_known_transactions(filename):
    if not os.path.exists(filename): return set()
    with open(filename, 'r') as f: return set(line.strip() for line in f)


def save_new_transaction(filename, receipt_number):
    with open(filename, 'a') as f: f.write(receipt_number + '\n')


def scrape_page_logic(sb, known_receipts):
    try:
        sb.wait_for_element_visible("tr.transaction-item", timeout=20)
        time.sleep(2)
        num_transactions = len(sb.find_elements("tr.transaction-item"))
        print(f"Found {num_transactions} transactions on the page.")
        known_in_a_row_counter = 0

        for i in range(num_transactions):
            all_transactions = sb.find_elements("tr.transaction-item")
            current_transaction = all_transactions[i]
            sb.execute_script("arguments[0].scrollIntoView(true);", current_transaction)
            time.sleep(0.5)

            if not current_transaction.find_elements("css selector", ".transaction-item__amounts__credit__text"):
                continue

            details_button = current_transaction.find_element("css selector", "button.transaction-item__btn-details")
            sb.execute_script("arguments[0].click();", details_button)
            sb.wait_for_element_visible("div.transaction-details-content")

            receipt_selector = "//span[text()='Receipt number']/parent::div/following-sibling::div/span"
            receipt_number = sb.get_text(receipt_selector)

            if receipt_number not in known_receipts:
                known_in_a_row_counter = 0
                print(f"--- Found new transaction: {receipt_number} ---")

                transaction_title = sb.get_text("h1#transaction-details-modal-heading")
                amount = sb.get_text("span.transaction-details-content__amount span[aria-hidden='true']")
                description, reference = "N/A", "N/A"
                desc_selector = "//span[text()='Description']/parent::div/following-sibling::div/span"
                ref_selector = "//span[text()='Reference']/parent::div/following-sibling::div/span"
                if sb.is_element_present(desc_selector): description = sb.get_text(desc_selector)
                if sb.is_element_present(ref_selector): reference = sb.get_text(ref_selector)

                transaction_data = {
                    "title": transaction_title, "amount": amount,
                    "description": description, "reference": reference,
                    "receipt_number": receipt_number
                }
                transaction_queue.put(transaction_data)
                save_new_transaction(TRANSACTIONS_FILE, receipt_number)
                known_receipts.add(receipt_number)
            else:
                known_in_a_row_counter += 1
                if known_in_a_row_counter >= KNOWN_TRANSACTION_SAFETY_LIMIT:
                    print(f"Safety limit of {KNOWN_TRANSACTION_SAFETY_LIMIT} reached. Ending cycle.")
                    actions = ActionChains(sb.driver)
                    actions.pause(0.5).send_keys(Keys.TAB).pause(0.3).send_keys(Keys.TAB).pause(0.3).send_keys(
                        Keys.ENTER).perform()
                    sb.wait_for_element_not_visible("#transaction-details-modal")
                    break

            actions = ActionChains(sb.driver)
            actions.pause(0.5).send_keys(Keys.TAB).pause(0.3).send_keys(Keys.TAB).pause(0.3).send_keys(
                Keys.ENTER).perform()
            sb.wait_for_element_not_visible("#transaction-details-modal")

    except Exception as e:
        print(f"An error occurred during the scrape cycle: {e}", file=sys.stderr)
        traceback.print_exc()


def scraper_worker():
    print("Scraper thread started. Initializing browser...")
    brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    with SB(uc=True, binary_location=brave_path, headless=False, incognito=True) as sb:
        netbank_url = "https://www.my.commbank.com.au/netbank/Logon/Logon.aspx"
        sb.open(netbank_url)
        sb.type("#txtMyClientNumber_field", NB_client_number)
        sb.type("#txtMyPassword_field", NB_password)
        sb.click("#btnLogon_field")
        if "MFA" in sb.get_current_url():
            print("Waiting for MFA approval in app...")
            timeout = 300
            start = time.time()
            while "MFA" in sb.get_current_url():
                if time.time() - start > timeout:
                    raise TimeoutError("MFA approval took too long.")
                time.sleep(2)

        # --- Using your more specific and reliable account selector ---
        sb.click(".account-name.m-0")

        known_receipts = load_known_transactions(TRANSACTIONS_FILE)

        while True:
            scrape_page_logic(sb, known_receipts)
            print(f"\nCycle complete. Waiting for {REFRESH_INTERVAL_SECONDS} seconds...")
            time.sleep(REFRESH_INTERVAL_SECONDS)
            print("Refreshing page...")
            sb.refresh()


@app.route('/scrape', methods=['POST'])
def scrape_endpoint():
    if request.headers.get('X-API-KEY') != API_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    print("\nReceived authorized request from Discord bot. Checking queue...")

    new_transactions = []
    while not transaction_queue.empty():
        new_transactions.append(transaction_queue.get())

    if new_transactions:
        print(f"Found {len(new_transactions)} new transaction(s) in queue. Sending to bot.")
    else:
        print("Queue is empty. No new transactions to report.")

    return jsonify(new_transactions)


if __name__ == '__main__':
    scraper_thread = Thread(target=scraper_worker, daemon=True)
    scraper_thread.start()

    print("Starting Flask server on http://0.0.0.0:5000")
    serve(app, host='0.0.0.0', port=5000)
