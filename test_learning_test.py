import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from handler.test_learning import TestLearning
from utility import get_account, word_get

def test_test_learning():
    print("Testing new test learning implementation...")
    
    # Get account info
    account = get_account()
    print(f"Using account: {account['id']}")
    
    # Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--log-level=1')
    
    # Create driver
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Login
        print("Logging in...")
        driver.get("https://www.classcard.net/Login")
        
        # Wait for login fields
        id_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "login_id"))
        )
        pw_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "login_pwd"))
        )
        
        # Handle any alerts that might appear
        try:
            alert = driver.switch_to.alert
            print(f"Alert detected: {alert.text}")
            alert.accept()
        except:
            pass
        
        # Login
        id_element.clear()
        id_element.send_keys(account["id"])
        pw_element.send_keys(account["pw"])
        time.sleep(1)
        
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "btn-login"))
        )
        login_button.click()
        time.sleep(3)  # Increased wait time
        
        # Handle any alerts after login
        try:
            alert = driver.switch_to.alert
            print(f"Post-login alert: {alert.text}")
            alert.accept()
        except:
            pass
        
        # Select first class
        print("Selecting first class...")
        try:
            class_list_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "body > div.mw-1080 > div:nth-child(6) > div > div > div.left-menu > div.left-item-group.p-t-none.p-r-lg > div.m-t-sm.left-class-list"
                ))
            )
            class_links = class_list_element.find_elements(By.TAG_NAME, "a")
            
            if len(class_links) == 0:
                print("No classes found!")
                return
            
            print(f"Found {len(class_links)} classes")
            
            # Click first class
            class_links[0].click()
            time.sleep(3)  # Increased wait time
            
            # Get class ID from URL
            current_url = driver.current_url
            class_id = current_url.split("/")[-1]
            print(f"Selected class ID: {class_id}")
            
        except Exception as e:
            print(f"Error selecting class: {e}")
            return
        
        # Go to class main page
        print("Going to class main page...")
        driver.get(f"https://www.classcard.net/ClassMain/{class_id}")
        time.sleep(3)  # Increased wait time
        
        # Select set 9 (index 8) for testing
        print("Selecting set 9 for testing...")
        sets_div = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                By.XPATH, "/html/body/div[1]/div[2]/div/div/div[2]/div[3]/div"
            ))
        )
        sets = sets_div.find_elements(By.CLASS_NAME, "set-items")
        
        if len(sets) < 9:
            print("Less than 9 sets found! Cannot test set 9.")
            return
        
        # Get set info before clicking
        test_set_link = sets[8].find_element(By.TAG_NAME, "a")
        set_id = test_set_link.get_attribute("data-idx")
        print(f"Selected set ID (set 9): {set_id}")
        
        # Click set 9
        test_set_link.click()
        time.sleep(3)  # Increased wait time
        
        # Get words
        print("Getting words...")
        try:
            # Wait for dropdown to be present
            dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((
                    By.CSS_SELECTOR,
                    "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown > a"
                ))
            )
            dropdown.click()
            time.sleep(1)
            
            # Click first option
            first_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((
                    By.CSS_SELECTOR,
                    "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown.open > ul > li:nth-child(1) > a"
                ))
            )
            first_option.click()
            time.sleep(2)
            
            # Get word data
            word_d = word_get(driver, 10)  # Assume 10 words for testing
            num_d = len(word_d[0])
            print(f"Found {num_d} words")
            print(f"English words: {word_d[0]}")
            print(f"Korean words: {word_d[1]}")
            
        except Exception as e:
            print(f"Error getting words: {e}")
            return
        
        # Test the new test learning
        print("Starting test learning...")
        try:
            test_learning = TestLearning(driver=driver)
            test_learning.run(num_d=num_d, word_d=word_d)
            print("Test learning completed!")
        except Exception as e:
            print(f"Error during test learning: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("Closing browser...")
        driver.quit()

if __name__ == "__main__":
    test_test_learning() 