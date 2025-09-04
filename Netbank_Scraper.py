from seleniumbase import SB
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import os

# - config
NB_client_number = "INSERT_CLIENT_NUMBER_HERE" # good practice to use a .env to store this sensitive information
NB_password = "INSERT_PASSWORD_HERE" # good practice to use a .env to store this sensitive information
TRANSACTIONS_FILE = "known_transactions.txt"
REFRESH_INTERVAL_SECONDS = 30  # Wait 30 seconds between checks


def load_known_transactions(filename):
    if not os.path.exists(filename):
        return set()
    with open(filename, 'r') as f:
        return set(line.strip() for line in f)


def save_new_transaction(filename, receipt_number):
    with open(filename, 'a') as f:
        f.write(receipt_number + '\n')


def scrape_page_for_new_transactions(sb, known_receipts):
    newly_found_transactions = []

    sb.wait_for_element_visible("tr.transaction-item")
    time.sleep(2)

    num_transactions = len(sb.find_elements("tr.transaction-item"))
    print(f"Found {num_transactions} transactions on the page.")

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
            print(f"--- Found new transaction: {receipt_number} ---")

            transaction_title = sb.get_text("h1#transaction-details-modal-heading")
            amount = sb.get_text("span.transaction-details-content__amount span[aria-hidden='true']")

            description = "N/A"
            reference = "N/A"

            description_selector = "//span[text()='Description']/parent::div/following-sibling::div/span"
            reference_selector = "//span[text()='Reference']/parent::div/following-sibling::div/span"

            if sb.is_element_present(description_selector):
                description = sb.get_text(description_selector)

            if sb.is_element_present(reference_selector):
                reference = sb.get_text(reference_selector)

            # Store all the relevant data
            transaction_data = {
                "title": transaction_title,
                "amount": amount,
                "description": description,
                "reference": reference,  # Add the new field
                "receipt_number": receipt_number
            }
            newly_found_transactions.append(transaction_data)

            save_new_transaction(TRANSACTIONS_FILE, receipt_number)
            known_receipts.add(receipt_number)

            # --- Print all the new data for confirmation ---
            print(f"Title: {transaction_title}")
            print(f"Amount: {amount}")
            print(f"Description: {description}")
            print(f"Reference: {reference}")
            print(f"Receipt Number: {receipt_number}")

        else:
            # Uncomment to see skipped transactions
            # print(f"Skipping known transaction: {receipt_number}")
            pass

        # Close the modal
        actions = ActionChains(sb.driver)
        actions.pause(0.5).send_keys(Keys.TAB).pause(0.3).send_keys(Keys.TAB).pause(0.3).send_keys(Keys.ENTER).perform()
        sb.wait_for_element_not_visible("#transaction-details-modal")

    return newly_found_transactions


def main():
    """Main function to handle login and the continuous monitoring loop."""
 #   brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    with SB(uc=True, headless=False, incognito=True) as sb:
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

        sb.click(".account-name.m-0")

        print("Login successful. Starting monitoring loop...")

        # Load known transactions once at the start
        known_receipts = load_known_transactions(TRANSACTIONS_FILE)

        # --- CONTINUOUS MONITORING LOOP ---
        try:
            while True:
                new_transactions = scrape_page_for_new_transactions(sb, known_receipts)
                if new_transactions:
                    print("\n--- NEW TRANSACTIONS DETECTED ---")
                    for txn in new_transactions:
                        # In your Discord bot, you would process these transactions here
                        print(txn)
                else:
                    print("No new transactions found on this cycle.")

                print(f"\nWaiting for {REFRESH_INTERVAL_SECONDS} seconds before next check...")
                time.sleep(REFRESH_INTERVAL_SECONDS)

                print("Refreshing page...")
                sb.refresh()

        except KeyboardInterrupt:
            print("\nMonitoring stopped by user. Exiting.")


if __name__ == "__main__":
    main()
