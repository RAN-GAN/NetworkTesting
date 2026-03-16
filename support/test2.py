import os
import json
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

SHARED_DIR = "C:\\Users\\ASUS\\Downloads\\host"
VERSION_FILE = "support/version.txt"
VERSION=""
TEST="test"
SEQ_NUM=""

def get_version():
    with open(VERSION_FILE, "r") as f:
        version = f.readline().strip()
        return version
    
VERSION = get_version()

# -------- Write Log ---------
def write_log(event_type, success, error_message=None):
    version = get_version()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    if os.path.exists(LOG_FILE): 
        with open(LOG_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    version_entry = next((item for item in data if item["version"] == version), None)
    status = "Success" if success else f"Failed{': ' + error_message if error_message else ''}"
    message = f"{event_type}:{status}"
    entry_text = f"[Machine {SEQ_NUM}] [{TEST}] {timestamp} - {message}"

    if version_entry:
        if "logs" not in version_entry:
            version_entry["logs"] = []
        version_entry["logs"].append(entry_text)
    else:
        data.append({
            "version": version,
            "logs": [entry_text]
        })

    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=4)
  
EXCEL_FILE = "support/SKG_Credentials.xlsx"
SEQ_FILE = "support/sequence.txt"

print("Running Test 2")

options = webdriver.ChromeOptions()
options.add_argument("--disable-gpu")
options.add_argument("--disable-extensions")
options.add_argument("--no-sandbox")
options.add_argument(f"--remote-debugging-port={random.randint(9000,9999)}")
options.add_argument("--start-maximized")

# -------- Normalize time function ---------
def normalize_time(run_time):
    run_time = run_time.strip().upper().replace(";", ":")
    if "AM" not in run_time and "PM" not in run_time:
        run_time += "AM"
    if ":" not in run_time:
        run_time = run_time.replace("AM", ":00AM").replace("PM", ":00PM")
    dt_obj = datetime.strptime(run_time, "%I:%M%p")
    return dt_obj.strftime("%I:%M %p")

# -------- Read sequence and scheduled time ---------
def read_sequence_file():
    global SEQ_NUM

    seq_num = None
    run_time = None
    with open(SEQ_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line.lower().startswith("machine:"):
                seq_num = int(line.split(":", 1)[1].strip())
            elif line.lower().startswith("time:"):
                run_time = line.split(":", 1)[1].strip()
    if seq_num is None or run_time is None:
        raise ValueError("sequence.txt must contain machine:<num> and time:<HH:MMAM/PM>")
    SEQ_NUM=seq_num

    return seq_num, normalize_time(run_time)

# -------- Pick user by sequence ---------
def pick_user_by_sequence(seq_num):
    df = pd.read_excel(EXCEL_FILE)
    df.columns = df.columns.str.strip().str.lower()
    if seq_num < 1 or seq_num > len(df):
        raise IndexError(f"Sequence number {seq_num} is out of range. Total users: {len(df)}")
    return df.iloc[seq_num - 1]

# -------- Login Function with Scheduler ---------
def login_user_scheduled(url, username, password, scheduled_time):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 45)
    status = "❌ Failed"
    try:
        driver.get(url)
        time.sleep(5)
        print("entering uname")
        email_box = wait.until(EC.element_to_be_clickable((By.ID, "email")))
        email_box.send_keys(username)
        time.sleep(3)
        print("clicking pass")

        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']")))
        next_btn.click()
        time.sleep(2)
        print("entering pass")

        pwd_box = wait.until(EC.element_to_be_clickable((By.ID, "password")))
        time.sleep(2)
        pwd_box.send_keys(password)
        time.sleep(10)

        # # --- Wait for scheduled time ---
        # scheduled_dt = datetime.strptime(scheduled_time, "%I:%M %p").replace(
        #     year=datetime.now().year,
        #     month=datetime.now().month,
        #     day=datetime.now().day
        # )
        # print(f"[INFO] Waiting until scheduled time: {scheduled_dt.strftime('%I:%M %p')}")
        # while True:
        #     now = datetime.now()
        #     if now >= scheduled_dt:
        #         break
        #     time.sleep(5)

        login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Login']")))
        login_btn.click()
        time.sleep(10)
        print(f"[OK] Login button clicked at {datetime.now().strftime('%I:%M %p')}")

        try:
            verify_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Verify']"))
            )
            verify_btn.click()
            print("[INFO] Verification pop-up clicked")
            time.sleep(2)
        except:
            print("[INFO] No verification pop-up")

        wait.until(EC.url_contains("dashboard"))
        write_log("login", True)


    except Exception as e:
        error_msg = str(e).splitlines()[0]
        write_log("login", False, error_msg)
        return False, driver

    return status, driver

# -------- Update Excel ---------
def update_result(seq_num, result):
    df = pd.read_excel(EXCEL_FILE)
    df.columns = df.columns.str.strip().str.lower()
    df.loc[seq_num - 1, 'status'] = result
    df.to_excel(EXCEL_FILE, index=False)

# -------- Step Executor ---------
def do_step(driver, wait, action, xpath, value=None, slow_type=False):
    time.sleep(1)
    try:
        if action == "CLICK":
            print("Clicking",xpath)
            elem = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            time.sleep(0.5)
            driver.execute_script("arguments[0].scrollIntoView(true);", elem)
            elem.click()
            time.sleep(2)
        elif action == "SEND":
            print("Sending",xpath)

            elem = wait.until(EC.visibility_of_element_located((By.XPATH, xpath)))
            elem.clear()
            if slow_type:
                for char in value:
                    elem.send_keys(char)
                    time.sleep(0.3)
            else:
                elem.send_keys(value)
            time.sleep(1)
        elif action == "WAIT":
            wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    except Exception as e:
        print(f"[ERR] {action} failed on {xpath}: {e}")

# -------- Run Single Test Flow ---------
def run_single_test(driver, wait):
    # Click Labs
    do_step(driver, wait, "CLICK", "//div[contains(text(),'Labs')]")
    time.sleep(3)

    content_xpaths = [
        # "//div[@class='trans-scroll scrollbar-gutter !t-overflow-hidden t-pb-20 t-h-[92%] t-box-border t-justify-center t-grid t-snap-y t-scroll-smooth t-snap-mandatory t-grid-cols-3 ng-star-inserted']//div[@class='t-flex t-justify-between t-items-center t-mb-10 t-relative sm:t-mb-20']",
        # "//div[@class='trans-scroll scrollbar-gutter t-pr-4 t-box-border t-justify-center t-pt-10 t-grid t-grid-cols-1 sm:t-grid-cols-2 xl:t-grid-cols-[repeat(auto-fit,_minmax(310px,_2fr))] ng-star-inserted']//div[@class='t-flex t-justify-between t-items-center t-mb-10 t-relative sm:t-mb-20']",
        # "//div[@aria-labelledby='card-list']"
        '//*[@id="courseCardID-1"]/div',
        '/html/body/app-root/div/div/div/app-mycourse-details/div[2]/div[1]/div/div[2]/app-accordian/div[2]/div/div/div',
        '//*[@id="pannel10"]'
    ]
    for xp in content_xpaths:
        try:
            do_step(driver, wait, "CLICK", xp)
        except:
            continue
    time.sleep(3)


    # Click Take / Resume / Retake Test
    test_btns = [
        "//div[@id='viewInstructionLinkID']//following::button"
        # "//span[normalize-space()='Take Test']",
        # "//span[normalize-space()='Resume Test']",
        # "//span[normalize-space()='Retake Test']"
    ]
    for btn in test_btns:
        try:
            do_step(driver, wait, "CLICK", btn)
            break
        except:
            continue

    # Agree & Proceed, Cookies
    do_step(driver, wait, "CLICK", "//span[normalize-space()='Agree & Proceed']")
    do_step(driver, wait, "CLICK", "//input[@id='cookies-enabled']")
    do_step(driver, wait, "CLICK", "//button[@id='accept-cookies-button']")

    # Wait for submit project button
    submit_project_xpath = "//button[@id='tt-footer-submit-answer']"
    print("[INFO] Waiting for Submit Project button...")

    try:
        submit_project_btn = WebDriverWait(driver, 600, poll_frequency=5).until(
            EC.element_to_be_clickable((By.XPATH, submit_project_xpath))
        )
        write_log("submit_found", True)
        submit_project_btn.click()
        print("[OK] Submit Project clicked.")
    except:
        write_log("submit_not_found", False)
        print("[ERROR] Submit Project button not found within timeout.")

    time.sleep(random.randint(6, 10))

    # Close big popup
    try:
        close_popup_xpath = "//img[@class='t-w-12 t-h-12 t-cursor-pointer sm:t-w-16 sm:t-h-16']"
        do_step(driver, wait, "CLICK", close_popup_xpath)
        print("[OK] Big popup closed.")
    except:
        pass

    # Close top-right corner popup
    try:
        top_right_popup = "//img[@class='t-cursor-pointer t-w-100 t-max-w-[10px] t-h-10 lg:t-w-100 lg:t-max-w-[12px] lg:t-h-12']"
        do_step(driver, wait, "CLICK", top_right_popup)
    except:
        pass

    # Submit Test
    do_step(driver, wait, "CLICK", "//span[normalize-space()='Submit Test']")
    do_step(driver, wait, "SEND", "//input[@id='name']", value="END", slow_type=True)
    do_step(driver, wait, "CLICK", "//span[normalize-space()='Yes']")

    print("[INFO] Test flow completed. Back to dashboard.")

# -------- Main ---------
if __name__ == "__main__":
    seq_num, scheduled_time = read_sequence_file()

    LOG_FILE = f'{SHARED_DIR}\\logs\\{SEQ_NUM}.json'
    write_log("Running", True)

    print(f"[INFO] Machine: {seq_num} | Scheduled Time: {scheduled_time}")

    user = pick_user_by_sequence(seq_num)
    print(f"[INFO] User: {user['username']} | Preparing login...")

    result, driver = login_user_scheduled(user['url'], user['username'], user['password'], scheduled_time)
    print(f"[INFO] {user['username']} login result: {result}")
    update_result(seq_num, result)

    wait = WebDriverWait(driver, 30)
    run_single_test(driver, wait)

    print("[INFO] Automation completed. Browser remains open. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("Script terminated by user.")
