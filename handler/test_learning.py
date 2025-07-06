import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementNotInteractableException,
    TimeoutException,
    ElementClickInterceptedException,
)


class TestLearning:
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver  # webdriver

    def run(self, num_d: int, word_d: list) -> None:  # 핸들러 실행
        driver = self.driver
        da_e, da_k, _ = word_d
        wait = WebDriverWait(driver, 10)
        
        # Robust click helper with minimal modal handling for btn-quiz-start
        def robust_click(by, selector, desc, allow_modal_close=False):
            try:
                elem = wait.until(EC.element_to_be_clickable((by, selector)))
                print(f"[DEBUG] {desc} found. Displayed: {elem.is_displayed()}, Enabled: {elem.is_enabled()}")
                try:
                    elem.click()
                    print(f"[DEBUG] {desc} clicked.")
                    return True
                except ElementClickInterceptedException as e:
                    print(f"[WARN] {desc} click intercepted: {e}")
                    if allow_modal_close:
                        # Try to close modal
                        try:
                            modals = driver.find_elements(By.CSS_SELECTOR, '.modal-dialog, .modal')
                            for modal in modals:
                                if modal.is_displayed():
                                    print(f"[DEBUG] Modal found. Attempting to close.")
                                    btns = modal.find_elements(By.TAG_NAME, 'button') + modal.find_elements(By.TAG_NAME, 'a')
                                    for btn in btns:
                                        if btn.is_displayed() and btn.is_enabled():
                                            print(f"[DEBUG] Clicking modal button: '{btn.text}'")
                                            btn.click()
                                            time.sleep(0.5)
                                            break
                                    break
                        except Exception as e2:
                            print(f"[WARN] Failed to close modal: {e2}")
                        # Retry click ONCE
                        try:
                            elem = wait.until(EC.element_to_be_clickable((by, selector)))
                            elem.click()
                            print(f"[DEBUG] {desc} clicked after closing modal.")
                            return True
                        except Exception as e3:
                            print(f"[ERROR] {desc} still not clickable after modal close: {e3}")
                            return False
                    else:
                        return False
                except ElementNotInteractableException:
                    print(f"[WARN] {desc} not interactable. Skipping.")
                    return False
            except TimeoutException:
                print(f"[WARN] {desc} not found/clickable in time. Skipping.")
                return False

        # 테스트 시작 (btn btn-success btn-xl shadow w-250 btn-quiz-start)
        robust_click(By.XPATH, "/html/body/div[2]/div/div[2]/div[2]/div", "테스트 학습 버튼 (세트 화면)")
        time.sleep(1)
        robust_click(By.CSS_SELECTOR, "#wrapper-test > div > div.quiz-start-div > div.layer.retry-layer.box > div.m-t-xl > a", "테스트 학습 시작 버튼 1")
        time.sleep(0.5)
        robust_click(By.CSS_SELECTOR, "#wrapper-test > div > div.quiz-start-div > div.layer.prepare-layer.box.bg-gray.text-white > div.text-center.m-t-md > a", "테스트 학습 시작 버튼 2")
        time.sleep(0.5)
        robust_click(By.CSS_SELECTOR, ".btn.btn-success.btn-xl.shadow.w-250.btn-quiz-start", "테스트 시작 (btn-quiz-start)", allow_modal_close=True)
        time.sleep(0.5)

        # 응시 (btn btn-primary shadow btn-ok m-l-xs)
        robust_click(By.CSS_SELECTOR, ".btn.btn-primary.shadow.btn-ok.m-l-xs", "응시 버튼 (btn-ok m-l-xs)")
        time.sleep(0.5)
        # 새로 시작 (btn shadow btn-ok m-l-xs btn-danger)
        robust_click(By.CSS_SELECTOR, ".btn.shadow.btn-ok.m-l-xs.btn-danger", "새로 시작 버튼 (btn-danger)")
        time.sleep(0.5)
        
        # 테스트 학습 유의사항 확인 버튼 클릭
        try:
            elem = driver.find_element(By.CSS_SELECTOR, "#alertModal > div.modal-dialog > div > div.text-center.m-t-xl > a")
            print(f"[DEBUG] 유의사항 확인 버튼 found. Displayed: {elem.is_displayed()}, Enabled: {elem.is_enabled()}")
            elem.click()
            print(f"[DEBUG] 유의사항 확인 버튼 clicked.")
        except Exception:
            print(f"[WARN] 유의사항 확인 버튼 not found or not interactable. Skipping.")
        time.sleep(1.5)
        
        # Get the number of problems from the page
        num_d = driver.find_element(
            By.XPATH, "/html/body/div[2]/div/div[2]/div[1]/div/span[2]/span"
        ).text
        
        for i in range(1, int(num_d) + 1):
            # Get the problem word from the card front
            cash_d = driver.find_element(
                By.XPATH,
                f"//*[@id='testForm']/div[{i}]/div/div[1]/div[2]/div[2]/div/div",
            ).text.split("\n")[0]
            
            # Click the card front
            element = driver.find_element(
                By.XPATH,
                f"//*[@id='testForm']/div[{i}]/div/div[1]/div[2]/div[2]/div/div",
            )
            print(f"[DEBUG] 카드 {i} 앞면. Displayed: {element.is_displayed()}, Enabled: {element.is_enabled()}")
            try:
                element.click()
                print(f"[DEBUG] 카드 {i} 앞면 클릭됨.")
            except ElementNotInteractableException:
                print(f"[WARN] 카드 {i} 앞면 not interactable. Skipping.")
                continue
            time.sleep(1)
            
            # Determine the answer
            try:
                if cash_d.upper() != cash_d.lower():
                    try:
                        text = da_k[da_e.index(cash_d)]
                    except ValueError:
                        text = da_e[da_k.index(cash_d)]
                else:
                    text = da_e[da_k.index(cash_d)]
            except ValueError:
                text = "모름"
            
            # Try input box first
            try:
                input_tag = driver.find_element(
                    By.XPATH,
                    f"//*[@id='testForm']/div[{i}]/div/div[2]/div/div[2]/div[1]/input",
                )
                submit_tag = driver.find_element(
                    By.XPATH,
                    f"//*[@id='testForm']/div[{i}]/div/div[2]/div/div[2]/div[2]/a",
                )
                print(f"[DEBUG] 카드 {i} 입력창. Displayed: {input_tag.is_displayed()}, Enabled: {input_tag.is_enabled()}")
                input_tag.click()
                input_tag.send_keys("123456")  # Use "123456" for answer inputting
                submit_tag.click()
                print(f"[DEBUG] 카드 {i} 입력창에 답안 입력 및 제출.")
            except NoSuchElementException:
                # 입력창이 없으면 선택지 시스템 사용
                box_items = driver.find_element(
                    By.XPATH,
                    f"/html/body/div[2]/div/div[2]/div[2]/form/div[{i}]/div/div[2]/div/div[1]",
                )
                box_items = box_items.find_elements(By.TAG_NAME, "div")
                print(f"[DEBUG] 카드 {i} 선택지 {len(box_items)}개.")
                if text == "모름":
                    print("모르는 단어 감지됨")
                    box_items[0].click()
                else:
                    for box_item in box_items:
                        print(f"[DEBUG] 카드 {i} 선택지: '{box_item.text}' Displayed: {box_item.is_displayed()}, Enabled: {box_item.is_enabled()}")
                        if box_item.text == text:
                            box_item.click()
                            print(f"[DEBUG] 카드 {i} 선택지 클릭됨.")
                            break
            time.sleep(2) 