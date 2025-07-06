import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
)


class UnknownWordException(Exception):
    pass


class SpellingLearning:
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver  # webdriver

    def run(self, num_d: int, word_d: list, auto_exit: bool = True) -> None:  # 핸들러 실행
        driver = self.driver
        da_e, da_k, _ = word_d
        
        print(f"[DEBUG] Starting spelling learning entry button detection...")
        print(f"[DEBUG] Current URL: {driver.current_url}")
        
        # Wait longer for page to be fully loaded
        time.sleep(3)
        
        # Wait for and click the spelling learning entry button with multiple selectors
        spelling_entry_clicked = False
        selectors_to_try = [
            # Try the most specific selectors first
            "//div[contains(@class, 'set-body')]//a[contains(text(), '스펠')]",  # Set body with spelling
            "//div[contains(@class, 'set-body')]//div[contains(text(), '스펠')]",  # Set body div with spelling
            "//div[contains(@class, 'card')]//a[contains(text(), '스펠')]",  # Card with spelling
            "//div[contains(@class, 'card')]//div[contains(text(), '스펠')]",  # Card div with spelling
            # Try button-like elements
            "//div[contains(@class, 'btn') and contains(text(), '스펠')]",  # Button div with spelling text
            "//a[contains(@class, 'btn') and contains(text(), '스펠')]",  # Button link with spelling text
            "//div[contains(@class, 'learning') and contains(text(), '스펠')]",  # Learning div with spelling
            "//a[contains(@class, 'learning') and contains(text(), '스펠')]",  # Learning link with spelling
            # Try more generic selectors
            "//a[contains(text(), '스펠')]",  # Link with text
            "//div[contains(text(), '스펠')]",  # Div with text
            "//button[contains(text(), '스펠')]",  # Button with text
            "//*[contains(text(), '스펠')]",  # Any element with text
            "//a[contains(@href, 'spelling')]",  # Link with spelling in href
            "//div[contains(@class, 'spelling')]",  # Div with spelling class
            # Try even more generic selectors
            "//*[contains(text(), '스펠링')]",  # Any element with spelling (Korean)
            "//*[contains(text(), 'spelling')]",  # Any element with spelling (English)
        ]
        
        for i, selector in enumerate(selectors_to_try):
            try:
                print(f"[DEBUG] Trying selector {i+1}: {selector}")
                element = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                print(f"[DEBUG] Found element with selector: {selector}")
                element.click()
                spelling_entry_clicked = True
                print(f"[DEBUG] Spelling entry clicked using selector: {selector}")
                break
            except (TimeoutException, NoSuchElementException) as e:
                print(f"[DEBUG] Selector {i+1} failed: {e}")
                continue
        
        if not spelling_entry_clicked:
            print(f"[DEBUG] All selectors failed, trying fallback methods...")
            # Try to find any clickable element that might be the spelling button
            try:
                # Look for any element with spelling-related text
                all_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '스펠')]")
                print(f"[DEBUG] Found {len(all_elements)} elements with '스펠' text")
                for j, element in enumerate(all_elements):
                    try:
                        print(f"[DEBUG] Checking element {j+1}: {element.text}")
                        if element.is_displayed() and element.is_enabled():
                            print(f"[DEBUG] Clicking element {j+1}")
                            element.click()
                            spelling_entry_clicked = True
                            print(f"[DEBUG] Spelling entry clicked using fallback method")
                            break
                    except Exception as e:
                        print(f"[DEBUG] Failed to click element {j+1}: {e}")
                        continue
            except Exception as e:
                print(f"[DEBUG] Fallback method failed: {e}")
        
        if not spelling_entry_clicked:
            # Try one more time with a longer wait and different approach
            print(f"[DEBUG] Trying final approach with longer wait...")
            time.sleep(5)
            try:
                # Try to find any button or link that might be clickable
                all_clickable = driver.find_elements(By.XPATH, "//a | //button | //div[contains(@class, 'btn')]")
                print(f"[DEBUG] Found {len(all_clickable)} potentially clickable elements")
                for k, element in enumerate(all_clickable):
                    try:
                        text = element.text.lower()
                        if '스펠' in text or 'spelling' in text:
                            print(f"[DEBUG] Found spelling-related element {k+1}: {element.text}")
                            if element.is_displayed() and element.is_enabled():
                                element.click()
                                spelling_entry_clicked = True
                                print(f"[DEBUG] Spelling entry clicked using final fallback")
                                break
                    except Exception as e:
                        print(f"[DEBUG] Failed to check element {k+1}: {e}")
                        continue
            except Exception as e:
                print(f"[DEBUG] Final approach failed: {e}")
        
        if not spelling_entry_clicked:
            print(f"[DEBUG] All methods failed. Current page source preview:")
            try:
                page_source = driver.page_source
                print(f"[DEBUG] Page source length: {len(page_source)}")
                # Print a small portion of the page source to debug
                if len(page_source) > 1000:
                    print(f"[DEBUG] Page source preview: {page_source[:1000]}...")
                else:
                    print(f"[DEBUG] Page source: {page_source}")
            except Exception as e:
                print(f"[DEBUG] Could not get page source: {e}")
            raise Exception("Could not find spelling learning entry button")
        
        time.sleep(2)  # Wait longer after clicking entry button
        
        # Wait for and click the spelling learning start button
        start_button_clicked = False
        start_selectors = [
            "//a[contains(text(), '시작')]",  # Link with start text
            "//button[contains(text(), '시작')]",  # Button with start text
            "//div[contains(text(), '시작')]",  # Div with start text
            "//*[contains(text(), '시작')]",  # Any element with start text
            "//a[contains(@class, 'btn')]",  # Any button link
            "//button[contains(@class, 'btn')]",  # Any button
            "//div[contains(@class, 'btn') and contains(text(), '시작')]",  # Button div with start text
            "//a[contains(@class, 'btn') and contains(text(), '시작')]",  # Button link with start text
        ]
        
        for selector in start_selectors:
            try:
                element = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                element.click()
                start_button_clicked = True
                print(f"[DEBUG] Spelling start button clicked using selector: {selector}")
                break
            except (TimeoutException, NoSuchElementException):
                continue
        
        if not start_button_clicked:
            raise Exception("Could not find spelling learning start button")
        
        time.sleep(1)
        
        completed_words = 0
        unknown_word_count = 0  # Track unknown words to prevent infinite loops
        
        try:
            for i in range(1, num_d + 1):  # Fixed range to include num_d
                # Wait for the word element to be present - use more robust selectors
                word_selectors = [
                    "//div[contains(@class, 'word')]//span[1]",  # First span in word div
                    "//div[contains(@class, 'question')]//span[1]",  # First span in question div
                    "//div[contains(@class, 'card')]//span[1]",  # First span in card div
                    "//div[contains(@class, 'text')]//span[1]",  # First span in text div
                    "//span[contains(@class, 'word')]",  # Span with word class
                    "//div[contains(@class, 'word')]//div[contains(@class, 'text')]",  # Text div in word div
                    "//div[contains(@class, 'question')]//div[contains(@class, 'text')]",  # Text div in question div
                    "//div[contains(@class, 'card')]//div[contains(@class, 'text')]",  # Text div in card div
                    "//span[1]",  # First span anywhere (fallback)
                ]
                
                word_element = None
                for selector in word_selectors:
                    try:
                        word_element = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                        # Check if the element has actual text content
                        if word_element.text.strip():
                            break
                        else:
                            word_element = None
                    except (TimeoutException, NoSuchElementException):
                        continue
                
                if not word_element:
                    print(f"[DEBUG] Could not find word element for word {i}")
                    print(f"[DEBUG] Current page source preview:")
                    try:
                        page_source = driver.page_source
                        if len(page_source) > 2000:
                            print(f"[DEBUG] Page source preview: {page_source[:2000]}...")
                        else:
                            print(f"[DEBUG] Page source: {page_source}")
                    except Exception as e:
                        print(f"[DEBUG] Could not get page source: {e}")
                    raise Exception("Could not find word element")
                
                # Get the word text and clean it
                cash_d = word_element.text.strip()
                if not cash_d:
                    print(f"[DEBUG] Word element found but text is empty for word {i}")
                    print(f"[DEBUG] Word element HTML: {word_element.get_attribute('outerHTML')}")
                    raise Exception("Word element has no text content")
                
                print(f"[DEBUG] Found word: '{cash_d}' for word {i}")
                
                try:
                    if cash_d.upper() != cash_d.lower():
                        try:
                            text = da_k[da_e.index(cash_d)]
                        except ValueError:
                            text = da_e[da_k.index(cash_d)]
                    else:
                        text = da_e[da_k.index(cash_d)]
                except ValueError:
                    unknown_word_count += 1
                    print(f"모르는 단어 감지됨 (단어 {i}: {cash_d}) - {unknown_word_count}번째")
                    
                    # If too many unknown words, just continue instead of raising exception
                    if unknown_word_count >= 3:  # Allow up to 3 unknown words before giving up
                        print(f"[WARNING] Too many unknown words ({unknown_word_count}), continuing without raising exception")
                        # Make a random guess to continue
                        text = "unknown"
                    else:
                        # Raise exception to trigger recovery in main only for first few unknown words
                        raise UnknownWordException(f"모르는 단어 감지됨: {cash_d}")
                
                print(f"[DEBUG] Using answer: '{text}' for word '{cash_d}'")
                
                # Wait for and find the input field - use simpler selector
                input_selectors = [
                    "//input[@type='text']",  # Any text input
                    "//input",  # Any input
                    "//input[contains(@class, 'answer')]",  # Input with answer class
                    "//input[contains(@class, 'spelling')]",  # Input with spelling class
                    "//input[contains(@placeholder, '단어')]",  # Input with word placeholder
                    "//input[contains(@placeholder, 'word')]",  # Input with word placeholder
                ]
                
                input_element = None
                for selector in input_selectors:
                    try:
                        input_element = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                        break
                    except (TimeoutException, NoSuchElementException):
                        continue
                
                if not input_element:
                    raise Exception("Could not find input field")
                
                input_element.click()
                input_element.send_keys(text)
                
                # Click the submit button - use simpler selector
                submit_selectors = [
                    "//button[contains(text(), '확인')]",  # Button with confirm text
                    "//button[contains(text(), '제출')]",  # Button with submit text
                    "//a[contains(text(), '확인')]",  # Link with confirm text
                    "//div[contains(@class, 'btn') and contains(text(), '확인')]",  # Div button with confirm text
                    "//button[contains(@class, 'btn')]",  # Any button with btn class
                    "//a[contains(@class, 'btn')]",  # Any link with btn class
                ]
                
                submit_button = None
                for selector in submit_selectors:
                    try:
                        submit_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        break
                    except (TimeoutException, NoSuchElementException):
                        continue
                
                if not submit_button:
                    raise Exception("Could not find submit button")
                
                submit_button.click()
                time.sleep(1.5)
                
                # Try to click the next button if it exists - use simpler selector
                try:
                    next_selectors = [
                        "//button[contains(text(), '다음')]",  # Button with next text
                        "//a[contains(text(), '다음')]",  # Link with next text
                        "//div[contains(text(), '다음')]",  # Div with next text
                    ]
                    
                    for selector in next_selectors:
                        try:
                            next_button = WebDriverWait(driver, 3).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                            next_button.click()
                            break
                        except (TimeoutException, NoSuchElementException):
                            continue
                except (TimeoutException, NoSuchElementException):
                    pass
                
                completed_words += 1
                time.sleep(0.5)
        except UnknownWordException:
            # Only exit early for UnknownWordException if we haven't had too many
            if unknown_word_count < 3:
                print(f"[INFO] 스펠학습 중단됨 (모르는 단어): 완료된 단어 {completed_words}/{num_d}")
                # Use the proper 학습종료 button
                try:
                    driver.find_element(
                        By.CSS_SELECTOR, 
                        "a.cc.remote_left[onclick*='study_end']"
                    ).click()
                    time.sleep(2)
                except:
                    # Fallback to old method if new button not found
                    try:
                        driver.find_element(
                            By.XPATH, "/html/body/div[1]/div/div[1]/div[1]"
                        ).click()  # 학습 종료 버튼 클릭
                        time.sleep(1)
                        driver.find_element(
                            By.XPATH, "//*[@id='wrapper-learn']/div[2]/div/div/div/div[5]/a[3]"
                        ).click()  # 학습 종료 확인 버튼 클릭
                    except:
                        print("[WARNING] Could not find exit button, trying to go back")
                        driver.back()
                raise  # Re-raise the exception for main to handle
            else:
                # Continue with the learning even with unknown words
                print(f"[INFO] Continuing spelling learning despite unknown words: {completed_words}/{num_d}")
        
        print(f"[INFO] 스펠학습 완료: {completed_words}/{num_d} 단어")
        # Ensure we're back to the set page after completion only if auto_exit is True
        if auto_exit:
            try:
                # Wait a bit for any completion screens
                time.sleep(2)
                # Check if we need to exit to get back to set page
                current_url = driver.current_url
                if "wrapper-learn" in current_url or "study" in current_url:
                    try:
                        driver.find_element(
                            By.CSS_SELECTOR, 
                            "a.cc.remote_left[onclick*='study_end']"
                        ).click()
                        time.sleep(2)
                    except:
                        driver.back()
            except Exception as e:
                print(f"[WARNING] Error during spelling completion cleanup: {e}")
