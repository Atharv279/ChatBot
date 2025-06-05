import json
import random
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import Chrome
from selenium.webdriver.common.action_chains import ActionChains
from selenium_stealth import stealth

# Simulate human typing with occasional backspace
def type_humanly(element, text, driver):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))
        if random.random() < 0.05:
            element.send_keys(Keys.BACKSPACE)
            time.sleep(0.1)
            element.send_keys(char)
        # Random mouse movement to mimic human
        if random.random() < 0.2:
            ActionChains(driver).move_by_offset(random.randint(-10, 10), random.randint(-10, 10)).perform()

# Simulate human-like scrolling
def human_scroll(driver):
    driver.execute_script("window.scrollBy(0, window.innerHeight * 0.5);")
    time.sleep(random.uniform(0.5, 1.5))
    driver.execute_script("window.scrollBy(0, -window.innerHeight * 0.2);")
    time.sleep(random.uniform(0.3, 0.8))

# Setup Chrome browser with stealth and incognito
def setup_browser():
    options = Options()
    options.add_argument("--incognito")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    )
    driver = Chrome(options=options)
    stealth(
        driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        run_on_insecure_content=True,
    )
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            window.chrome = { runtime: {} };
        """
    })
    return driver

# Google search fallback for all prompts
def run_google_fallback(prompts):
    logs = []
    for prompt_data in prompts:
        driver = setup_browser()
        log = {
            "platform": "https://www.google.com",
            "prompt": prompt_data.get("query", "What's the best ERP for a steel service center in the US?"),
            "timestamp": time.time(),
            "persona": prompt_data.get("persona", "unknown"),
            "tone": prompt_data.get("tone", "unknown")
        }
        try:
            driver.set_page_load_timeout(60)
            driver.get("https://www.google.com")
            time.sleep(random.uniform(2, 4))
            human_scroll(driver)
            input_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            type_humanly(input_box, log["prompt"], driver)
            input_box.send_keys(Keys.ENTER)
            time.sleep(5)
            print(f"Google search performed for prompt: {log['prompt']}")
        except Exception as e:
            print(f"Google fallback failed for prompt '{log['prompt']}': {e}")
            log["error"] = str(e)
        finally:
            time.sleep(5)
            driver.quit()
        logs.append(log)
    return logs

# Run a demo session with multiple prompts
def run_demo(use_google=False, target_url="https://chat.openai.com/", num_prompts=4):
    logs = []
    try:
        # Load prompts from prompts.json
        with open("prompts.json", "r", encoding="utf-8") as f:
            prompts = json.load(f)
        if not prompts:
            raise ValueError("prompts.json is empty")
        selected_prompts = random.sample(prompts, min(num_prompts, len(prompts)))
    except Exception as e:
        print(f"Failed to load prompts.json: {e}. Using default prompt.")
        selected_prompts = [{"query": "What's the best ERP for a steel service center in the US?", "persona": "business_owner", "tone": "professional"}]

    if use_google:
        return run_google_fallback(selected_prompts)

    driver = setup_browser()
    try:
        driver.set_page_load_timeout(120)
        driver.maximize_window()
        driver.get(target_url)
        time.sleep(random.uniform(5, 10))
        human_scroll(driver)

        print("ChatGPT may require a login and CAPTCHA. Log in manually and solve any CAPTCHA (e.g., image selection or verification). Wait until the chat interface is fully loaded with a visible text input box at the bottom of the page. If a CAPTCHA persists, complete it or refresh the page (F5) and try again. Press Enter in the terminal only when the input box is visible. If the interface doesn’t load after 30 seconds, refresh and re-login.")
        input()

        # Wait for chat interface
        WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "main, div[class*='conversation'], div#chat-container, section, div[class*='chat']"))
        )
        time.sleep(random.uniform(2, 5))
        human_scroll(driver)

        for prompt_data in selected_prompts:
            log = {
                "platform": target_url,
                "prompt": prompt_data.get("query", "What's the best ERP for a steel service center in the US?"),
                "timestamp": time.time(),
                "persona": prompt_data.get("persona", "unknown"),
                "tone": prompt_data.get("tone", "unknown")
            }

            try:
                # Find input box
                input_box = WebDriverWait(driver, 40).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "textarea.text-token-text-primary, textarea#prompt-textarea, textarea[placeholder*='Message'], textarea[placeholder*='Ask'], textarea[placeholder*='Chat'], textarea"))
                )
                # Force visibility and focus
                driver.execute_script("""
                    arguments[0].style.display='block';
                    arguments[0].style.visibility='visible';
                    arguments[0].removeAttribute('hidden');
                    arguments[0].removeAttribute('disabled');
                    arguments[0].focus();
                """, input_box)
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_box)
                time.sleep(random.uniform(0.5, 1.5))

                # Verify input box state
                if not input_box.is_displayed() or not input_box.is_enabled():
                    print(f"Input box state: displayed={input_box.is_displayed()}, enabled={input_box.is_enabled()}")
                    raise Exception("Input box is not visible or enabled")

                input_box.click()
                input_box.clear()
                type_humanly(input_box, log["prompt"], driver)

                try:
                    # Try clicking send button
                    send_button = WebDriverWait(driver, 7).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='send-button'], button[aria-label*='Send'], button svg, button:has(svg), button[class*='send']"))
                    )
                    driver.execute_script("arguments[0].click();", send_button)
                except:
                    input_box.send_keys(Keys.ENTER)

                print(f"Prompt sent to ChatGPT: {log['prompt']}")
                time.sleep(random.uniform(12, 18))  # Wait for response to load
                logs.append(log)
            except Exception as e:
                print(f"Failed to send prompt '{log['prompt']}': {e}")
                print("Page source snippet:")
                print(driver.page_source[:500])
                log["error"] = str(e)
                logs.append(log)
                continue

        return logs
    except Exception as e:
        print(f"Demo failed: {e}")
        print("Page source snippet:")
        print(driver.page_source[:500])
        for prompt_data in selected_prompts:
            log = {
                "platform": target_url,
                "prompt": prompt_data.get("query", "What's the best ERP for a steel service center in the US?"),
                "timestamp": time.time(),
                "persona": prompt_data.get("persona", "unknown"),
                "tone": prompt_data.get("tone", "unknown"),
                "error": str(e)
            }
            logs.append(log)
        return run_google_fallback(selected_prompts)
    finally:
        time.sleep(5)
        driver.quit()

# Main function
def main():
    print("Starting demo for LLM Infiltrator Bot...")
    logs = run_demo()
    with open("demo_log.json", "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=4)
    print("Demo complete! Log saved to demo_log.json")

if __name__ == "__main__":
    main()