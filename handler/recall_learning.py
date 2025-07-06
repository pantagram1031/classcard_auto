import contextlib
import random
import time
from selenium import webdriver
from selenium.webdriver.common.by import By


class UnknownWordException(Exception):
    pass


class RecallLearning:
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver  # webdriver

    def run(self, num_d: int, word_d: list, auto_exit: bool = True) -> None:  # 핸들러 실행
        driver = self.driver
        da_e, da_k, _ = word_d
        driver.find_element(
            By.XPATH,
            "/html/body/div[2]/div/div[2]/div[1]/div[2]",
        ).click()  # 리콜학습 진입 버튼
        time.sleep(1)
        driver.find_element(
            By.CSS_SELECTOR,
            "#wrapper-learn > div.start-opt-body > div > div > div > div.m-t > a",
        ).click()  # 리콜학습 시작 버튼
        time.sleep(2)
        
        completed_words = 0
        unknown_word_count = 0  # Track unknown words to prevent infinite loops
        
        for i in range(num_d):  # 단어 수 만큼 반복
            try:
                cash_d = driver.find_element(
                    By.XPATH,
                    f"//*[@id='wrapper-learn']/div[1]/div/div[2]/div[2]/div[{i+1}]/div[1]/div/div/div/div[1]/span",
                ).text  # 메인 단어 추출

                choice_list_element = driver.find_element(
                    By.XPATH,
                    f"//*[@id='wrapper-learn']/div[1]/div/div[2]/div[2]/div[{i+1}]/div[3]",
                )
                
                choice_made = False
                for choice_item in choice_list_element.find_elements(
                    By.TAG_NAME, "div"
                ):
                    choice_text = choice_item.text
                    if choice_text in da_k:
                        if cash_d == da_e[da_k.index(choice_text)]:
                            choice_item.click()
                            choice_made = True
                            break
                    elif choice_text in da_e:
                        if cash_d == da_k[da_e.index(choice_text)]:
                            choice_item.click()
                            choice_made = True
                            break
                    else:
                        continue
                
                if not choice_made:
                    unknown_word_count += 1
                    print(f"모르는 단어 감지됨 (단어 {i+1}: {cash_d}) - {unknown_word_count}번째")
                    
                    # If too many unknown words, just continue instead of raising exception
                    if unknown_word_count >= 3:  # Allow up to 3 unknown words before giving up
                        print(f"[WARNING] Too many unknown words ({unknown_word_count}), continuing without raising exception")
                        # Make a random choice to continue
                        choice_items = choice_list_element.find_elements(By.TAG_NAME, "div")
                        if choice_items:
                            random.choice(choice_items).click()
                    else:
                        # Raise exception to trigger recovery in main only for first few unknown words
                        raise UnknownWordException(f"모르는 단어 감지됨: {cash_d}")
                
                completed_words += 1
                time.sleep(3)
            except UnknownWordException:
                # Only exit early for UnknownWordException if we haven't had too many
                if unknown_word_count < 3:
                    print(f"[INFO] 리콜학습 중단됨 (모르는 단어): 완료된 단어 {completed_words}/{num_d}")
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
                    print(f"[INFO] Continuing recall learning despite unknown words: {completed_words}/{num_d}")
                    continue
            except Exception as e:  # Other exceptions - log but continue
                print(f"[WARNING] 리콜학습 중 예외 발생 (단어 {i+1}): {e}")
                # Try to continue with next word instead of exiting
                continue
        
        print(f"[INFO] 리콜학습 완료: {completed_words}/{num_d} 단어")
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
                print(f"[WARNING] Error during recall completion cleanup: {e}")
