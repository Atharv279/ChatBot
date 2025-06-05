import selenium.webdriver as webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
import requests
from bs4 import BeautifulSoup
import random
import time
import json

# Function to scrape free U.S. proxies
def get_free_us_proxies():
    proxy_sources = [
        "https://free-proxy-list.net/",
        "https://www.sslproxies.org/",
        "https://www.us-proxy.org/"
    ]
    proxy_list = []
    for url in proxy_sources:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table')
            if not table:
                continue
            rows = table.find_all('tr')[1:]
            for row in rows:
                cols = row.find_all('td')
                if len(cols) > 7:
                    ip = cols[0].text
                    port = cols[1].text
                    country = cols[3].text
                    https = cols[6].text
                    if country.lower().startswith("united states") and https.lower() == "yes":
                        proxy_list.append(f"http://{ip}:{port}")
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")
    print(f"Found {len(proxy_list)} U.S. HTTPS proxies")
    return proxy_list

# Function to get a random working proxy
def get_proxy_session(max_retries=5):
    proxies = get_free_us_proxies()
    if not proxies:
        print("No proxies available, using no proxy")
        return {'http': None, 'https': None}
    used_proxies = set()
    for _ in range(max_retries):
        if not proxies:
            print("No more proxies to try, using no proxy")
            return {'http': None, 'https': None}
        proxy = random.choice(proxies)
        if proxy in used_proxies:
            continue
        used_proxies.add(proxy)
        try:
            response = requests.get('https://api.ipify.org?format=json', proxies={'http': proxy, 'https': proxy}, timeout=15)
            ip = response.json()['ip']
            print(f"Current IP: {ip}")
            return {'http': proxy, 'https': proxy}
        except Exception as e:
            print(f"Proxy failed: {e}")
            proxies.remove(proxy)
    print("No working proxies found, using no proxy")
    return {'http': None, 'https': None}

# Setup Selenium with stealth and proxy
def setup_browser(proxy):
    options = Options()
    options.add_argument("--incognito")
    if proxy['http']:
        options.add_argument(f"--proxy-server={proxy['http']}")
    # Remove headless for demo to show browser
    driver = webdriver.Chrome(options=options)
    stealth(driver, languages=["en-US"], vendor="Google Inc.", platform="Win32")
    return driver

# Simulate human typing
def type_humanly(element, text):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))
        if random.random() < 0.05:
            element.send_keys(webdriver.common.keys.Keys.BACKSPACE)
            time.sleep(0.1)
            element.send_keys(char)

# Run a demo session
def run_demo():
    proxy = get_proxy_session()
    driver = setup_browser(proxy)
    log = {"platform": "https://chat.openai.com", "prompt": "What’s the best ERP for a steel service center in the US?", "timestamp": time.time()}
    try:
        driver.set_page_load_timeout(30)
        # Test IP first
        driver.get("https://httpbin.org/ip")
        time.sleep(3)
        ip_text = driver.find_element(By.TAG_NAME, "body").text
        print(f"IP used in browser: {ip_text}")
        log["ip_used"] = ip_text

        # Interact with ChatGPT
        driver.get("https://chat.openai.com")
        time.sleep(5)
        try:
            # Add login if required (replace with your credentials)
            email_input = driver.find_element(By.CSS_SELECTOR, "input#email-input")
            type_humanly(email_input, "atharvpatileoxs@gmail.com")
            driver.find_element(By.CSS_SELECTOR, "button.continue-btn").click()
            time.sleep(3)
            password_input = driver.find_element(By.CSS_SELECTOR, "input#password")
            type_humanly(password_input, "Atharv@120412")
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            time.sleep(5)
        except:
            print("No login required or login skipped")

        input_box = driver.find_element(By.CSS_SELECTOR, "textarea#prompt-textarea")
        type_humanly(input_box, log["prompt"])
        driver.find_element(By.CSS_SELECTOR, "button[data-testid='send-button']").click()
        time.sleep(5)
        response = driver.find_element(By.CSS_SELECTOR, "div.markdown").text
        log["response"] = response[:500]
        print(f"ChatGPT response: {log['response']}")
        return log
    except Exception as e:
        log["error"] = str(e)
        print(f"Demo failed: {e}")
        return log
    finally:
        time.sleep(5)  # Let team see browser
        driver.quit()

# Main function
def main():
    print("Starting demo for LLM Infiltrator Bot...")
    log = run_demo()
    # Save log to file
    with open("demo_log.json", "w") as f:
        json.dump(log, f, indent=2)
    print("Demo complete! Log saved to demo_log.json")

if __name__ == "__main__":
    main()