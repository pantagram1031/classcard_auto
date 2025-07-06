import time
import warnings
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    UnexpectedAlertPresentException,
    StaleElementReferenceException
)
from handler.recall_learning import RecallLearning, UnknownWordException as RecallUnknownWordException
from handler.spelling_learning import SpellingLearning, UnknownWordException as SpellingUnknownWordException
from handler.rote_learning import RoteLearning
from handler.test_learning import TestLearning
from utility import word_get

warnings.filterwarnings("ignore", category=DeprecationWarning)

class ClassCardCore:
    def __init__(self):
        self.driver = None
        self.user_id = None
        self.class_id = None

    def setup_driver(self):
        from selenium.webdriver.chrome.options import Options
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--log-level=1')
        self.driver = webdriver.Chrome(options=chrome_options)
        return self.driver

    def login(self, user_id, password):
        try:
            self.driver.get("https://www.classcard.net/Login")
            try:
                id_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "login_id"))
                )
                pw_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "login_pwd"))
                )
            except Exception as e:
                print("[LOGIN ERROR] Login fields not found. Possible site change or popup.")
                try:
                    alert = self.driver.switch_to.alert
                    print(f"[LOGIN ERROR] Alert text: {alert.text}")
                    alert.accept()
                except Exception:
                    print("[LOGIN ERROR] No alert present or could not handle alert.")
                return False
            id_element.clear()
            id_element.send_keys(user_id)
            pw_element.send_keys(password)
            time.sleep(1)
            try:
                login_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "btn-login"))
                )
                login_button.click()
                time.sleep(1)
            except UnexpectedAlertPresentException:
                try:
                    alert = self.driver.switch_to.alert
                    print(f"[LOGIN ERROR] Alert text: {alert.text}")
                    alert.accept()
                except Exception:
                    print("[LOGIN ERROR] Unexpected alert present, but could not read text.")
                print("로그인에 실패했습니다. 아이디/비밀번호를 확인하거나, 사이트에서 자동화 로그인을 차단했을 수 있습니다.")
                return False
            self.user_id = int(self.driver.execute_script("return c_u;"))
            print(f"[INFO] Login successful. User ID: {self.user_id}")
            return True
        except Exception as e:
            print(f"[ERROR] Login failed: {e}")
            return False

    def get_classes(self):
        try:
            class_dict = {}
            class_list_element = self.driver.find_element(
                By.CSS_SELECTOR,
                "body > div.mw-1080 > div:nth-child(6) > div > div > div.left-menu > div.left-item-group.p-t-none.p-r-lg > div.m-t-sm.left-class-list",
            )
            class_count = len(class_list_element.find_elements(By.TAG_NAME, "a"))
            for class_item, i in zip(
                class_list_element.find_elements(By.TAG_NAME, "a"),
                range(class_count),
            ):
                class_temp = {}
                class_temp["class_name"] = class_item.text
                class_temp["class_id"] = class_item.get_attribute("href").split("/")[-1]
                if class_temp["class_id"] == "joinClass":
                    break
                class_dict[i] = class_temp
            return class_dict
        except Exception as e:
            print(f"[ERROR] Failed to get classes: {e}")
            return {}

    def get_sets(self, class_id):
        try:
            self.class_id = class_id
            class_url = f"https://www.classcard.net/ClassMain/{class_id}"
            self.driver.get(class_url)
            time.sleep(1)
            sets_dict = {}
            sets_div = self.driver.find_element(
                By.XPATH, "/html/body/div[1]/div[2]/div/div/div[2]/div[3]/div"
            )
            sets = sets_div.find_elements(By.CLASS_NAME, "set-items")
            sets_count = len(sets)
            for set_item, i in zip(sets, range(sets_count)):
                set_temp = {}
                set_temp["card_num"] = (
                    set_item.find_element(By.TAG_NAME, "a").find_element(By.TAG_NAME, "span").text
                )
                set_temp["title"] = set_item.find_element(By.TAG_NAME, "a").text.replace(
                    set_temp["card_num"], ""
                )
                set_temp["set_id"] = set_item.find_element(By.TAG_NAME, "a").get_attribute(
                    "data-idx"
                )
                sets_dict[i] = set_temp
            return sets_dict
        except Exception as e:
            print(f"[ERROR] Failed to get sets: {e}")
            return {}

    def get_words_for_set(self, set_id, class_id):
        try:
            set_site = f"https://www.classcard.net/set/{set_id}/{class_id}"
            self.driver.get(set_site)
            time.sleep(1)
            self.driver.find_element(
                By.CSS_SELECTOR,
                "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown > a",
            ).click()
            self.driver.find_element(
                By.CSS_SELECTOR,
                "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown.open > ul > li:nth-child(1) > a",
            ).click()
            html = BeautifulSoup(self.driver.page_source, "html.parser")
            cards_ele = html.find("div", class_="flip-body")
            num_d = len(cards_ele.find_all("div", class_="flip-card"))
            time.sleep(0.5)
            word_d = word_get(self.driver, num_d)
            da_e, da_k, da_kyn = word_d
            print(f"[DEBUG] 영어단어 리스트: {da_e}")
            print(f"[DEBUG] 한글단어 리스트: {da_k}")
            print(f"[DEBUG] 뜻+예문 리스트: {da_kyn}")
            return num_d, word_d
        except Exception as e:
            print(f"[ERROR] Failed to get words for set: {e}")
            return 0, ([], [], [])

    def run_recall_learning(self, num_d, word_d):
        try:
            print("[INFO] 리콜학습 시작...")
            driver = self.driver
            da_e, da_k, _ = word_d
            driver.find_element(
                By.XPATH,
                "/html/body/div[2]/div/div[2]/div[1]/div[2]",
            ).click()
            time.sleep(1)
            driver.find_element(
                By.CSS_SELECTOR,
                "#wrapper-learn > div.start-opt-body > div > div > div > div.m-t > a",
            ).click()
            time.sleep(2)
            completed_words = 0
            for i in range(num_d):
                try:
                    cash_d = driver.find_element(
                        By.XPATH,
                        f"//*[@id='wrapper-learn']/div[1]/div/div[2]/div[2]/div[{i+1}]/div[1]/div/div/div/div[1]/span",
                    ).text
                    choice_list_element = driver.find_element(
                        By.XPATH,
                        f"//*[@id='wrapper-learn']/div[1]/div/div[2]/div[2]/div[{i+1}]/div[3]",
                    )
                    for choice_item in choice_list_element.find_elements(By.TAG_NAME, "div"):
                        choice_text = choice_item.text
                        if choice_text in da_k:
                            if cash_d == da_e[da_k.index(choice_text)]:
                                choice_item.click()
                                break
                        elif choice_text in da_e:
                            if cash_d == da_k[da_e.index(choice_text)]:
                                choice_item.click()
                                break
                        else:
                            continue
                    else:
                        print("모르는 단어 감지됨")
                        raise RecallUnknownWordException("모르는 단어 감지됨: no match found, random guess made.")
                    completed_words += 1
                    time.sleep(3)
                except RecallUnknownWordException:
                    print(f"[INFO] 리콜학습 중단됨 (모르는 단어): 완료된 단어 {completed_words}/{num_d}")
                    try:
                        driver.find_element(
                            By.CSS_SELECTOR, 
                            "a.cc.remote_left[onclick*='study_end']"
                        ).click()
                        time.sleep(2)
                    except:
                        try:
                            driver.find_element(
                                By.XPATH, "/html/body/div[1]/div/div[1]/div[1]"
                            ).click()
                            time.sleep(1)
                            driver.find_element(
                                By.XPATH, "//*[@id='wrapper-learn']/div[2]/div/div/div/div[5]/a[3]"
                            ).click()
                        except:
                            print("[WARNING] Could not find exit button, trying to go back")
                            driver.back()
                    raise
                except Exception as e:
                    print(f"[WARNING] 리콜학습 중 예외 발생 (단어 {i+1}): {e}")
                    continue
            print(f"[INFO] 리콜학습 완료: {completed_words}/{num_d} 단어")
            try:
                time.sleep(2)
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
            return completed_words, num_d
        except Exception as e:
            print(f"[ERROR] Recall learning failed: {e}")
            raise

    def run_spelling_learning(self, num_d, word_d):
        try:
            print("[INFO] 스펠학습 시작...")
            driver = self.driver
            da_e, da_k, _ = word_d
            driver.find_element(
                By.XPATH,
                "/html/body/div[2]/div/div[2]/div[1]/div[3]",
            ).click()
            time.sleep(1)
            driver.find_element(
                By.XPATH,
                "/html/body/div[2]/div[2]/div/div/div/div[4]/a",
            ).click()
            time.sleep(1)
            completed_words = 0
            try:
                for i in range(1, num_d + 1):
                    cash_d = driver.find_element(
                        By.XPATH,
                        f"//*[@id='wrapper-learn']/div[1]/div/div[2]/div[2]/div[{i}]/div[1]/div/div/div/div[1]/span",
                    ).text.split("\n")[0]
                    try:
                        if cash_d.upper() != cash_d.lower():
                            try:
                                text = da_k[da_e.index(cash_d)]
                            except ValueError:
                                text = da_e[da_k.index(cash_d)]
                        else:
                            text = da_e[da_k.index(cash_d)]
                    except ValueError:
                        print("모르는 단어 감지됨")
                        raise SpellingUnknownWordException("모르는 단어 감지됨: no match found in word list.")
                    in_tag = driver.find_element(
                        By.XPATH,
                        f"/html/body/div[2]/div[1]/div/div[2]/div[2]/div[{i}]/div[2]/div/div/div/div[2]/input",
                    )
                    in_tag.click()
                    in_tag.send_keys(text)
                    driver.find_element(
                        By.XPATH, "//*[@id='wrapper-learn']/div/div/div[3]"
                    ).click()
                    time.sleep(1.5)
                    try:
                        driver.find_element(
                            By.XPATH, "//*[@id='wrapper-learn']/div/div/div[3]/div[2]"
                        ).click()
                    except:
                        pass
                    completed_words += 1
                    time.sleep(0.5)
            except SpellingUnknownWordException:
                print(f"[INFO] 스펠학습 중단됨 (모르는 단어): 완료된 단어 {completed_words}/{num_d}")
                try:
                    driver.find_element(
                        By.CSS_SELECTOR, 
                        "a.cc.remote_left[onclick*='study_end']"
                    ).click()
                    time.sleep(2)
                except:
                    try:
                        driver.find_element(
                            By.XPATH, "/html/body/div[1]/div/div[1]/div[1]"
                        ).click()
                        time.sleep(1)
                        driver.find_element(
                            By.XPATH, "//*[@id='wrapper-learn']/div[2]/div/div/div/div[5]/a[3]"
                        ).click()
                    except:
                        print("[WARNING] Could not find exit button, trying to go back")
                        driver.back()
                raise
            except NoSuchElementException:
                if completed_words < num_d:
                    print(f"[WARNING] 스펠학습이 예상보다 일찍 종료됨. 완료된 단어: {completed_words}/{num_d}")
                else:
                    print(f"[INFO] 스펠학습 완료: {completed_words}/{num_d} 단어")
            try:
                time.sleep(2)
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
            return completed_words, num_d
        except Exception as e:
            print(f"[ERROR] Spelling learning failed: {e}")
            raise

    def run_test_learning(self, num_d, word_d):
        import re
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        driver = self.driver
        da_e, da_k, da_kyn = word_d
        def normalize(text):
            return re.sub(r'[^\u0000-\u007f\w\d]', '', str(text).lower().strip())
        print("[DEBUG] 영어단어 리스트:", da_e)
        print("[DEBUG] 한글단어 리스트:", da_k)
        print("[DEBUG] 뜻+예문 리스트:", da_kyn)
        try:
            for _ in range(3):
                overlays = driver.find_elements(By.CSS_SELECTOR, '.modal, .modal-backdrop, .overlay, .popup, .modal-footer')
                for overlay in overlays:
                    try:
                        if overlay.is_displayed():
                            close_btns = overlay.find_elements(By.TAG_NAME, 'a') + overlay.find_elements(By.TAG_NAME, 'button')
                            if close_btns:
                                close_btns[-1].click()
                                time.sleep(0.2)
                    except Exception as e:
                        print(f"[ERROR] Overlay close failed: {e}")
                time.sleep(0.15)
            for attempt in range(3):
                try:
                    WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/div[2]/div[2]/div"))
                    ).click()
                    break
                except Exception as e:
                    print(f"[ERROR] 테스트 시작 버튼 클릭 실패 (시도 {attempt+1}): {e}")
                    if attempt == 2:
                        input("[MANUAL] 테스트 시작 버튼이 차단되었습니다. 팝업/오버레이를 수동으로 닫고 Enter를 눌러주세요...")
                    time.sleep(0.15)
            else:
                print("[ERROR] 테스트 시작 버튼을 클릭할 수 없습니다. 메뉴로 돌아갑니다.")
                return 0, num_d
            time.sleep(0.15)
            try:
                btn_condition_next = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn.btn-success.btn-lg.shadow.w-250.btn-condition-next"))
                )
                btn_condition_next.click()
                time.sleep(0.15)
            except Exception as e:
                print(f"[ERROR] 조건 확인 버튼 클릭 실패: {e}")
            try:
                btn_quiz_start = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn.btn-success.btn-xl.shadow.w-250.btn-quiz-start"))
                )
                btn_quiz_start.click()
                time.sleep(0.15)
            except Exception as e:
                print(f"[ERROR] 퀴즈 시작 버튼 클릭 실패: {e}")
            try:
                WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#alertModal > div.modal-dialog > div > div.text-center.m-t-xl > a"))
                ).click()
            except Exception:
                pass
            time.sleep(0.15)
            completed_words = 0
            for i in range(1, int(num_d) + 1):
                try:
                    cash_d = driver.find_element(
                        By.XPATH,
                        f"//*[@id='testForm']/div[{i}]/div/div[1]/div[2]/div[2]/div/div",
                    ).text.split("\n")[0]
                    element = driver.find_element(
                        By.XPATH,
                        f"//*[@id='testForm']/div[{i}]/div/div[1]/div[2]/div[2]/div/div",
                    )
                    element.click()
                    print(f"[DEBUG] 카드 {i} 앞면 클릭됨 (original XPath).")
                    time.sleep(1)
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
                    print(f"[PROBLEM] 카드 {i} 질문: '{cash_d}' | [SUPPOSED ANSWER]: '{text}'")
                    try:
                        input_tag = driver.find_element(
                            By.XPATH,
                            f"//*[@id='testForm']/div[{i}]/div/div[2]/div/div[2]/div[1]/input",
                        )
                        submit_tag = driver.find_element(
                            By.XPATH,
                            f"//*[@id='testForm']/div[{i}]/div/div[2]/div/div[2]/div[2]/a",
                        )
                        input_tag.click()
                        input_tag.send_keys(text)
                        submit_tag.click()
                        print(f"[DEBUG] 카드 {i} 입력창에 답안 입력 및 제출: '{text}' (original XPath)")
                    except NoSuchElementException:
                        try:
                            box_items = driver.find_element(
                                By.XPATH,
                                f"/html/body/div[2]/div/div[2]/div[2]/form/div[{i}]/div/div[2]/div/div[1]",
                            )
                            box_items = box_items.find_elements(By.TAG_NAME, "div")
                            if text == "모름":
                                print("모르는 단어 감지됨")
                                box_items[0].click()
                            for box_item in box_items:
                                if box_item.text == text:
                                    box_item.click()
                                    print(f"[DEBUG] 카드 {i} 선택지 클릭: '{box_item.text}' (정답: '{text}') (original XPath)")
                                    break
                        except Exception as e:
                            print(f"[ERROR] 카드 {i} 선택지 클릭 실패 (original XPath): {e}")
                    time.sleep(2)
                    completed_words += 1
                except Exception as e:
                    print(f"[ERROR] 카드 {i} 처리 중 예외 발생: {e}")
                    continue
            print(f"[INFO] 테스트학습 완료: {completed_words}/{num_d} 단어")
            return completed_words, num_d
        except Exception as e:
            print(f"[ERROR] 테스트학습 실패: {e}")
            raise

    def run_multiple_modes(self, set_id, class_id, modes):
        results = {}
        num_d, word_d = self.get_words_for_set(set_id, class_id)
        for mode in modes:
            retry_count = 0
            completed = False
            while retry_count < 5 and not completed:
                try:
                    if mode == "recall":
                        completed_words, total_words = self.run_recall_learning(num_d, word_d)
                    elif mode == "spelling":
                        completed_words, total_words = self.run_spelling_learning(num_d, word_d)
                    elif mode == "test":
                        completed_words, total_words = self.run_test_learning(num_d, word_d)
                    else:
                        continue
                    completion_percentage = (completed_words / total_words) * 100
                    results[mode] = {
                        "completed_words": completed_words,
                        "total_words": total_words,
                        "percentage": completion_percentage
                    }
                    if completion_percentage >= 100:
                        print(f"[SUCCESS] {mode} learning completed: {completed_words}/{total_words} ({completion_percentage:.1f}%)")
                        completed = True
                    else:
                        print(f"[RETRY] {mode} learning incomplete: {completed_words}/{total_words} ({completion_percentage:.1f}%) - Retrying...")
                        retry_count += 1
                        set_site = f"https://www.classcard.net/set/{set_id}/{class_id}"
                        self.driver.get(set_site)
                        time.sleep(2)
                        num_d, word_d = self.get_words_for_set(set_id, class_id)
                except Exception as e:
                    print(f"[ERROR] {mode} learning failed: {e}")
                    retry_count += 1
                    set_site = f"https://www.classcard.net/set/{set_id}/{class_id}"
                    self.driver.get(set_site)
                    time.sleep(2)
                    num_d, word_d = self.get_words_for_set(set_id, class_id)
        return results

    def run_range_automation(self, class_id, start_set_id, end_set_id, modes):
        sets = self.get_sets(class_id)
        set_indices = [i for i in sets if start_set_id <= int(sets[i]["set_id"]) <= end_set_id]
        results = {}
        for i in set_indices:
            set_id = sets[i]["set_id"]
            set_title = sets[i]["title"]
            print(f"[INFO] Processing set {set_id}")
            print(f"[INFO] Set: {set_title}")
            set_results = self.run_multiple_modes(set_id, class_id, modes)
            results[set_id] = {
                "title": set_title,
                "results": set_results
            }
        return results

    def run_range_automation_with_stop(self, class_id, start_set_id, end_set_id, modes, stop_callback):
        sets = self.get_sets(class_id)
        set_indices = [i for i in sets if start_set_id <= int(sets[i]["set_id"]) <= end_set_id]
        results = {}
        for i in set_indices:
            if stop_callback and stop_callback():
                print("[INFO] 중지 요청 감지됨. 자동화 중단.")
                break
            set_id = sets[i]["set_id"]
            set_title = sets[i]["title"]
            print(f"[INFO] Processing set {set_id}")
            print(f"[INFO] Set: {set_title}")
            set_results = {}
            for mode in modes:
                if stop_callback and stop_callback():
                    print("[INFO] 중지 요청 감지됨. 자동화 중단.")
                    break
                retry_count = 0
                completed = False
                num_d, word_d = self.get_words_for_set(set_id, class_id)
                while retry_count < 5 and not completed:
                    try:
                        if mode == "recall":
                            completed_words, total_words = self.run_recall_learning(num_d, word_d)
                        elif mode == "spelling":
                            completed_words, total_words = self.run_spelling_learning(num_d, word_d)
                        elif mode == "test":
                            completed_words, total_words = self.run_test_learning(num_d, word_d)
                        else:
                            continue
                        completion_percentage = (completed_words / total_words) * 100
                        set_results[mode] = {
                            "completed_words": completed_words,
                            "total_words": total_words,
                            "percentage": completion_percentage
                        }
                        if completion_percentage >= 100:
                            print(f"[SUCCESS] {mode} learning completed: {completed_words}/{total_words} ({completion_percentage:.1f}%)")
                            completed = True
                        else:
                            print(f"[RETRY] {mode} learning incomplete: {completed_words}/{total_words} ({completion_percentage:.1f}%) - Retrying...")
                            retry_count += 1
                            set_site = f"https://www.classcard.net/set/{set_id}/{class_id}"
                            self.driver.get(set_site)
                            time.sleep(2)
                            num_d, word_d = self.get_words_for_set(set_id, class_id)
                    except Exception as e:
                        print(f"[ERROR] {mode} learning failed: {e}")
                        retry_count += 1
                        set_site = f"https://www.classcard.net/set/{set_id}/{class_id}"
                        self.driver.get(set_site)
                        time.sleep(2)
                        num_d, word_d = self.get_words_for_set(set_id, class_id)
                    if stop_callback and stop_callback():
                        print("[INFO] 중지 요청 감지됨. 자동화 중단.")
                        break
                results[set_id] = {
                    "title": set_title,
                    "results": set_results
                }
        return results

    def close(self):
        if self.driver:
            self.driver.quit() 