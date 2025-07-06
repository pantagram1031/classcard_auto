import time
import warnings
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from handler.recall_learning import RecallLearning, UnknownWordException as RecallUnknownWordException
from handler.spelling_learning import SpellingLearning, UnknownWordException as SpellingUnknownWordException
from handler.rote_learning import RoteLearning
from handler.test_learning import TestLearning
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import UnexpectedAlertPresentException

# 함수불러오기
from utility import (
    chd_wh,
    get_account,
    word_get,
    choice_set,
    choice_class,
    classcard_api_post,
)

warnings.filterwarnings("ignore", category=DeprecationWarning)

def get_section_progress(driver, set_id, class_id):
    """Get recall and spelling progress percentages for a section"""
    try:
        set_site = f"https://www.classcard.net/set/{set_id}/{class_id}"
        driver.get(set_site)
        time.sleep(2)
        
        # Parse the page to find progress information
        html = BeautifulSoup(driver.page_source, "html.parser")
        
        # Step 1: Try to find a container for the current section
        section_container = (
            html.find("div", class_="learning-section") or
            html.find("div", class_="study-section") or
            html.find("div", class_="set-overview") or
            html.find("div", class_="progress-overview")
        )
        recall_progress = None
        spelling_progress = None
        container_used = None
        if section_container:
            container_used = section_container.get("class")
            container_text = section_container.get_text()
            # Try to find patterns like '리콜 ... 200%' or '스펠 ... 100%' in the container
            progress_pairs = re.findall(r'(리콜|스펠)[^\d]*(\d+)%', container_text)
            if progress_pairs:
                for label, value in progress_pairs:
                    pct = int(value)
                    if '리콜' in label:
                        recall_progress = pct
                    elif '스펠' in label:
                        spelling_progress = pct
            # Fallback: Try to find any percentages in the container
            if (recall_progress is None or spelling_progress is None):
                all_percentages = re.findall(r'(\d+)%', container_text)
                if all_percentages:
                    if recall_progress is None and len(all_percentages) > 0:
                        recall_progress = int(all_percentages[0])
                    if spelling_progress is None and len(all_percentages) > 1:
                        spelling_progress = int(all_percentages[1])
        else:
            print("[DEBUG] No section container found, using full page fallback (may be unreliable)")
            all_text = html.get_text()
            progress_pairs = re.findall(r'(리콜|스펠)[^\d]*(\d+)%', all_text)
            if progress_pairs:
                for label, value in progress_pairs:
                    pct = int(value)
                    if '리콜' in label:
                        recall_progress = pct
                    elif '스펠' in label:
                        spelling_progress = pct
            if (recall_progress is None or spelling_progress is None):
                all_percentages = re.findall(r'(\d+)%', all_text)
                if all_percentages:
                    if recall_progress is None and len(all_percentages) > 0:
                        recall_progress = int(all_percentages[0])
                    if spelling_progress is None and len(all_percentages) > 1:
                        spelling_progress = int(all_percentages[1])
        # If still None, set to 0
        if recall_progress is None:
            recall_progress = 0
        if spelling_progress is None:
            spelling_progress = 0
        # If fallback found a suspicious pair (e.g., 0 and 200), treat both as 0
        if (container_used is None) and (
            (recall_progress == 0 and spelling_progress >= 100) or
            (spelling_progress == 0 and recall_progress >= 100)
        ):
            print(f"[DEBUG] Fallback found suspicious pair (Recall: {recall_progress}%, Spelling: {spelling_progress}%), treating both as 0%.")
            recall_progress = 0
            spelling_progress = 0
        print(f"[DEBUG] Progress detection container: {container_used}")
        print(f"[DEBUG] Progress detection - Recall: {recall_progress}%, Spelling: {spelling_progress}%")
        return recall_progress, spelling_progress
        
    except Exception as e:
        print(f"[WARNING] Could not get progress for section {set_id}: {e}")
        return 0, 0

def process_section_range(driver, class_id, start_section, end_section, sets_dict, auto_detect=True, manual_input=False):
    """Process multiple sections automatically based on progress"""
    print(f"[AUTO-PROCESS] Starting automatic processing from section {start_section} to {end_section}")
    
    for section_num in range(start_section, end_section + 1):
        if section_num >= len(sets_dict):
            print(f"[AUTO-PROCESS] Section {section_num} does not exist. Stopping.")
            break
            
        set_info = sets_dict[section_num]
        set_id = set_info["set_id"]
        set_title = set_info["title"]
        
        print(f"\n[AUTO-PROCESS] Processing section {section_num}: {set_title}")
        
        # Get progress for this section
        if auto_detect:
            recall_progress, spelling_progress = get_section_progress(driver, set_id, class_id)
            print(f"[PROGRESS] Recall: {recall_progress}%, Spelling: {spelling_progress}%")
        elif manual_input:
            try:
                print(f"섹션 {section_num}의 진행률을 수동으로 입력하세요:")
                recall_input = input("리콜학습 진행률 (%): ").strip()
                spelling_input = input("스펠학습 진행률 (%): ").strip()
                
                recall_progress = int(recall_input) if recall_input.isdigit() else 0
                spelling_progress = int(spelling_input) if spelling_input.isdigit() else 0
                
                print(f"[PROGRESS] Recall: {recall_progress}%, Spelling: {spelling_progress}%")
            except ValueError:
                print("[WARNING] 잘못된 입력입니다. 0%로 설정합니다.")
                recall_progress, spelling_progress = 0, 0
        else:
            # Ignore progress - assume both are incomplete
            recall_progress, spelling_progress = 0, 0
            print(f"[PROGRESS] Progress ignored - assuming both incomplete")
        
        # Determine what needs to be done
        if recall_progress >= 100 and spelling_progress >= 100:
            print(f"[AUTO-PROCESS] Section {section_num} already completed (Recall: {recall_progress}%, Spelling: {spelling_progress}%). Skipping.")
            continue
        elif recall_progress >= 100 and spelling_progress < 100:
            print(f"[AUTO-PROCESS] Section {section_num} - Recall complete ({recall_progress}%), doing Spelling only ({spelling_progress}%).")
            # Do spelling only
            process_single_section(driver, class_id, set_id, section_num, sets_dict, do_recall=False, do_spelling=True)
        elif recall_progress < 100 and spelling_progress >= 100:
            print(f"[AUTO-PROCESS] Section {section_num} - Spelling complete ({spelling_progress}%), doing Recall only ({recall_progress}%).")
            # Do recall only
            process_single_section(driver, class_id, set_id, section_num, sets_dict, do_recall=True, do_spelling=False)
        else:
            print(f"[AUTO-PROCESS] Section {section_num} - Both incomplete (Recall: {recall_progress}%, Spelling: {spelling_progress}%), doing Recall+Spelling.")
            # Do both
            process_single_section(driver, class_id, set_id, section_num, sets_dict, do_recall=True, do_spelling=True)
    
    print(f"[AUTO-PROCESS] Completed processing sections {start_section} to {end_section}")

def process_single_section(driver, class_id, set_id, section_num, sets_dict, do_recall=True, do_spelling=True):
    """Process a single section with specified learning modes"""
    set_site = f"https://www.classcard.net/set/{set_id}/{class_id}"
    driver.get(set_site)
    time.sleep(1)
    
    # Get words for this section
    try:
        driver.find_element(
            By.CSS_SELECTOR,
            "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown > a",
        ).click()
        driver.find_element(
            By.CSS_SELECTOR,
            "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown.open > ul > li:nth-child(1) > a",
        ).click()
        
        html = BeautifulSoup(driver.page_source, "html.parser")
        cards_ele = html.find("div", class_="flip-body")
        num_d = len(cards_ele.find_all("div", class_="flip-card"))
        time.sleep(0.5)
        word_d = word_get(driver, num_d)
        da_e, da_k, da_kyn = word_d
    except Exception as e:
        print(f"[ERROR] Could not get words for section {section_num}: {e}")
        return
    
    # Process Recall Learning if needed
    if do_recall:
        print(f"[SECTION {section_num}] Starting Recall Learning...")
        recall_completed = False
        while not recall_completed:
            try:
                controler = RecallLearning(driver=driver)
                controler.run(num_d=num_d, word_d=word_d, auto_exit=False)
                print(f'[SECTION {section_num}] Recall Learning completed successfully.')
                recall_completed = True
            except Exception as e:
                if isinstance(e, RecallUnknownWordException):
                    print(f'[AUTO-RECOVERY] Section {section_num} - Recall: Unknown word detected, restarting...')
                    # Recovery logic
                    driver.get(set_site)
                    time.sleep(1)
                    driver.get(f"https://www.classcard.net/ClassMain/{class_id}")
                    time.sleep(1)
                    driver.get(set_site)
                    time.sleep(1)
                    # Reprocess words
                    try:
                        driver.find_element(
                            By.CSS_SELECTOR,
                            "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown > a",
                        ).click()
                        driver.find_element(
                            By.CSS_SELECTOR,
                            "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown.open > ul > li:nth-child(1) > a",
                        ).click()
                        html = BeautifulSoup(driver.page_source, "html.parser")
                        cards_ele = html.find("div", class_="flip-body")
                        num_d = len(cards_ele.find_all("div", class_="flip-card"))
                        time.sleep(0.5)
                        word_d = word_get(driver, num_d)
                        da_e, da_k, da_kyn = word_d
                        continue
                    except:
                        print(f"[ERROR] Section {section_num} - Could not recover from unknown word error")
                        break
                else:
                    print(f'[ERROR] Section {section_num} - Unexpected exception in Recall: {e}')
                    break
    
    # Process Spelling Learning if needed
    if do_spelling:
        if do_recall:
            # If we did recall, go back to set page first
            print(f"[SECTION {section_num}] Returning to set page for Spelling Learning...")
            driver.get(set_site)
            time.sleep(2)
        
        print(f"[SECTION {section_num}] Starting Spelling Learning...")
        spelling_completed = False
        while not spelling_completed:
            try:
                controler = SpellingLearning(driver=driver)
                controler.run(num_d=num_d, word_d=word_d, auto_exit=True)
                print(f'[SECTION {section_num}] Spelling Learning completed successfully.')
                spelling_completed = True
            except Exception as e:
                if isinstance(e, SpellingUnknownWordException):
                    print(f'[AUTO-RECOVERY] Section {section_num} - Spelling: Unknown word detected, restarting...')
                    # Recovery logic
                    driver.get(set_site)
                    time.sleep(1)
                    driver.get(f"https://www.classcard.net/ClassMain/{class_id}")
                    time.sleep(1)
                    driver.get(set_site)
                    time.sleep(1)
                    # Reprocess words
                    try:
                        driver.find_element(
                            By.CSS_SELECTOR,
                            "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown > a",
                        ).click()
                        driver.find_element(
                            By.CSS_SELECTOR,
                            "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown.open > ul > li:nth-child(1) > a",
                        ).click()
                        html = BeautifulSoup(driver.page_source, "html.parser")
                        cards_ele = html.find("div", class_="flip-body")
                        num_d = len(cards_ele.find_all("div", class_="flip-card"))
                        time.sleep(0.5)
                        word_d = word_get(driver, num_d)
                        da_e, da_k, da_kyn = word_d
                        continue
                    except:
                        print(f"[ERROR] Section {section_num} - Could not recover from unknown word error")
                        break
                else:
                    print(f'[ERROR] Section {section_num} - Unexpected exception in Spelling: {e}')
                    break
    
    print(f"[SECTION {section_num}] Processing completed.")

account = get_account()  # 계정 가져오기

print("크롬 드라이브를 불러오고 있습니다 잠시만 기다려주세요!")

# Chrome 옵션 설정
chrome_options = Options()
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument('--log-level=1')

# 드라이버 생성
driver = webdriver.Chrome(options=chrome_options)

# 로그인 시행
driver.get("https://www.classcard.net/Login")

# Wait for login fields to be present
try:
    id_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "login_id"))
    )
    pw_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "login_pwd"))
    )
except Exception as e:
    print("[LOGIN ERROR] Login fields not found. Possible site change or popup.")
    # Try to handle alert if present
    try:
        alert = driver.switch_to.alert
        print(f"[LOGIN ERROR] Alert text: {alert.text}")
        alert.accept()
    except Exception:
        print("[LOGIN ERROR] No alert present or could not handle alert.")
    driver.quit()
    exit()

id_element.clear() # Autofill 억제
id_element.send_keys(account["id"])
pw_element.send_keys(account["pw"])
time.sleep(1)
try:
    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "btn-login"))
    )
    login_button.click()  # 로그인 버튼
time.sleep(1)  # 로딩 대기
except UnexpectedAlertPresentException:
    try:
        alert = driver.switch_to.alert
        print(f"[LOGIN ERROR] Alert text: {alert.text}")
        alert.accept()
    except Exception:
        print("[LOGIN ERROR] Unexpected alert present, but could not read text.")
    print("로그인에 실패했습니다. 아이디/비밀번호를 확인하거나, 사이트에서 자동화 로그인을 차단했을 수 있습니다.")
    driver.quit()
    exit()

# 클래스 선택
class_dict = {}
class_list_element = driver.find_element(
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

if len(class_dict) == 0:
    print("클래스가 없습니다.")
    quit()
elif len(class_dict) == 1:
    choice_class_val = 0
else:
    choice_class_val = choice_class(class_dict=class_dict)  # 클래스 입력

class_id = class_dict[choice_class_val].get("class_id")  # 클래스 아이디 가져오기
driver.get(f"https://www.classcard.net/ClassMain/{class_id}")  # 클래스 페이지로 이동
time.sleep(1)  # 로딩 대기

while True:  # Outer loop for set selection
    driver.get(f"https://www.classcard.net/ClassMain/{class_id}")
    time.sleep(1)
sets_div = driver.find_element(
    By.XPATH, "/html/body/div[1]/div[2]/div/div/div[2]/div[3]/div"
)
sets = sets_div.find_elements(By.CLASS_NAME, "set-items")
sets_count = len(sets)
sets_dict = {}
for set_item, i in zip(sets, range(sets_count)):
    set_temp = {}
    set_temp["card_num"] = (
        set_item.find_element(By.TAG_NAME, "a").find_element(By.TAG_NAME, "span").text
    )  # 카드 개수 가져오기 예) "10 카드"
    set_temp["title"] = set_item.find_element(By.TAG_NAME, "a").text.replace(
        set_temp["card_num"], ""
    )  # 카드 개수 제거
    set_temp["set_id"] = set_item.find_element(By.TAG_NAME, "a").get_attribute(
        "data-idx"
    )  # 세트 아이디 가져오기
    sets_dict[i] = set_temp

    print("[x] 뒤로가기 (클래스 선택으로)")
    set_choice_input = input("세트 번호를 선택하세요 (또는 x 입력시 클래스 선택으로): ").strip().lower()
    if set_choice_input == "x":
        # Go back to class selection
        class_dict = {}
        class_list_element = driver.find_element(
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
        if len(class_dict) == 0:
            print("클래스가 없습니다.")
            quit()
        elif len(class_dict) == 1:
            choice_class_val = 0
        else:
            choice_class_val = choice_class(class_dict=class_dict)  # 클래스 입력
        class_id = class_dict[choice_class_val].get("class_id")  # 클래스 아이디 가져오기
        continue  # Restart set selection with new class
    try:
        set_choice = int(set_choice_input)
        if set_choice < 0 or set_choice >= len(sets_dict):
            raise ValueError
    except ValueError:
        print("잘못된 입력입니다. 다시 선택해주세요.")
        continue
set_site = (f"https://www.classcard.net/set/{sets_dict[set_choice]['set_id']}/{class_id}")
driver.get(set_site)  # 세트 페이지로 이동
time.sleep(1)  # 로딩 대기

user_id = int(driver.execute_script("return c_u;"))  # API 요청을 위해 유저 아이디 가져오기

# 단어 저장
driver.find_element(
    By.CSS_SELECTOR,
    "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown > a",
).click()  # 학습구간 선택
driver.find_element(
    By.CSS_SELECTOR,
    "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown.open > ul > li:nth-child(1) > a",
).click()  # 학습구간 전체로 변경
html = BeautifulSoup(driver.page_source, "html.parser")  # 페이지 소스를 html로 파싱
cards_ele = html.find("div", class_="flip-body")  # 카드들을 찾음
    num_d = len(cards_ele.find_all("div", class_="flip-card"))  # 카드의 개수를 구함
time.sleep(0.5)  # 로딩 대기
word_d = word_get(driver, num_d)  # 단어를 가져옴
da_e, da_k, da_kyn = word_d

    while True:  # Inner loop for 학습유형 menu
        print("\n학습유형을 선택해주세요.")
        print("Ctrl + C 를 눌러 종료")
        print("[1] 암기학습(매크로) 지원하지 않음")
        print("[2] 리콜학습(매크로)")
        print("[3] 스펠학습(매크로)")
        print("[4] 테스트학습(매크로) 지원하지 않음")
        print("[5] 암기학습(API 요청[경고])")
        print("[6] 리콜학습(API 요청[경고])")
        print("[7] 스펠학습(API 요청[경고])")
        print("[8] 리콜+스펠(매크로)")
        print("[9] 자동 다중 섹션 처리 (범위 선택)")
        print("[0] 뒤로가기 (세트/클래스 선택으로)")
        ch_d = input(">>> ").strip()
        if ch_d == "0":
            break  # Go back to set selection
        try:
            ch_d = int(ch_d)
        except ValueError:
            print("잘못된 입력입니다. 다시 선택해주세요.")
            continue
    if ch_d == 1:
            print("암기학습을 시작합니다.")
            controler = RoteLearning(driver=driver)
            controler.run(num_d=num_d)
    elif ch_d == 2:
        print("리콜학습을 시작합니다.")
            while True:
                try:
                    controler = RecallLearning(driver=driver)
                    controler.run(num_d=num_d, word_d=word_d)
                    print('[INFO] 리콜학습이 정상적으로 완료되었습니다.')
                    break  # Success, exit loop
                except Exception as e:
                    if isinstance(e, RecallUnknownWordException):
                        print('[AUTO-RECOVERY] 모르는 단어 감지됨: 자동으로 세트/홈/세트 이동 및 재시작합니다.')
                        # Go to set selection page
                        driver.get(set_site)
                        time.sleep(1)
                        # Go to class main page
                        driver.get(f"https://www.classcard.net/ClassMain/{class_id}")
                        time.sleep(1)
                        # Go to set page again
                        driver.get(set_site)
                        time.sleep(1)
                        # Reprocess words
                        driver.find_element(
                            By.CSS_SELECTOR,
                            "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown > a",
                        ).click()
                        driver.find_element(
                            By.CSS_SELECTOR,
                            "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown.open > ul > li:nth-child(1) > a",
                        ).click()  # 학습구간 전체로 변경
                        html = BeautifulSoup(driver.page_source, "html.parser")
                        cards_ele = html.find("div", class_="flip-body")
                        num_d = len(cards_ele.find_all("div", class_="flip-card"))
                        time.sleep(0.5)
                        word_d = word_get(driver, num_d)
                        da_e, da_k, da_kyn = word_d
                        print('[AUTO-RECOVERY] 리콜학습을 자동으로 재시작합니다. (2번을 누른 것처럼)')
                        continue  # Retry recall
                    else:
                        print('[ERROR] 예기치 않은 예외:', e)
                        print('메뉴로 돌아갑니다.')
                        break
    elif ch_d == 3:
        print("스펠학습을 시작합니다.")
            while True:
                try:
                    controler = SpellingLearning(driver=driver)
                    controler.run(num_d=num_d, word_d=word_d)
                    print('[INFO] 스펠학습이 정상적으로 완료되었습니다.')
                    break  # Success, exit loop
                except Exception as e:
                    if isinstance(e, SpellingUnknownWordException):
                        print('[AUTO-RECOVERY] 모르는 단어 감지됨: 자동으로 세트/홈/세트 이동 및 재시작합니다.')
                        # Go to set selection page
                        driver.get(set_site)
                        time.sleep(1)
                        # Go to class main page
                        driver.get(f"https://www.classcard.net/ClassMain/{class_id}")
                        time.sleep(1)
                        # Go to set page again
                        driver.get(set_site)
                        time.sleep(1)
                        # Reprocess words
                        driver.find_element(
                            By.CSS_SELECTOR,
                            "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown > a",
                        ).click()
                        driver.find_element(
                            By.CSS_SELECTOR,
                            "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown.open > ul > li:nth-child(1) > a",
                        ).click()  # 학습구간 전체로 변경
                        html = BeautifulSoup(driver.page_source, "html.parser")
                        cards_ele = html.find("div", class_="flip-body")
                        num_d = len(cards_ele.find_all("div", class_="flip-card"))
                        time.sleep(0.5)
                        word_d = word_get(driver, num_d)
                        da_e, da_k, da_kyn = word_d
                        print('[AUTO-RECOVERY] 스펠학습을 자동으로 재시작합니다.')
                        continue  # Retry spelling
                    else:
                        print('[ERROR] 예기치 않은 예외:', e)
                        print('메뉴로 돌아갑니다.')
                        break
        elif ch_d == 8:
            print("리콜+스펠학습을 시작합니다.")
            
            # Combined Recall + Spelling Learning with automatic flow
            recall_completed = False
            while not recall_completed:
                try:
                    print("[리콜학습] 시작...")
                    controler = RecallLearning(driver=driver)
                    controler.run(num_d=num_d, word_d=word_d, auto_exit=False)
                    print('[INFO] 리콜학습이 정상적으로 완료되었습니다.')
                    recall_completed = True
                except Exception as e:
                    if isinstance(e, RecallUnknownWordException):
                        print('[AUTO-RECOVERY] 리콜학습에서 모르는 단어 감지됨: 자동으로 세트/홈/세트 이동 및 전체 과정 재시작합니다.')
                        # Go to set selection page
                        driver.get(set_site)
                        time.sleep(1)
                        # Go to class main page
                        driver.get(f"https://www.classcard.net/ClassMain/{class_id}")
                        time.sleep(1)
                        # Go to set page again
                        driver.get(set_site)
                        time.sleep(1)
                        # Reprocess words
                        driver.find_element(
                            By.CSS_SELECTOR,
                            "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown > a",
                        ).click()
                        driver.find_element(
                            By.CSS_SELECTOR,
                            "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown.open > ul > li:nth-child(1) > a",
                        ).click()  # 학습구간 전체로 변경
                        html = BeautifulSoup(driver.page_source, "html.parser")
                        cards_ele = html.find("div", class_="flip-body")
                        num_d = len(cards_ele.find_all("div", class_="flip-card"))
                        time.sleep(0.5)
                        word_d = word_get(driver, num_d)
                        da_e, da_k, da_kyn = word_d
                        print('[AUTO-RECOVERY] 리콜+스펠학습 전체 과정을 자동으로 재시작합니다.')
                        continue  # Restart entire process
                    else:
                        print('[ERROR] 예기치 않은 예외:', e)
                        print('메뉴로 돌아갑니다.')
                        break
            
            # If recall completed successfully, proceed to spelling
            if recall_completed:
                # Ensure we're back to the set page before starting spelling
                print("[INFO] 리콜학습 완료. 세트 페이지로 이동 후 스펠학습을 시작합니다.")
                driver.get(set_site)
                time.sleep(2)
                
                spelling_completed = False
                while not spelling_completed:
                    try:
                        print("[스펠학습] 시작...")
                        controler = SpellingLearning(driver=driver)
                        controler.run(num_d=num_d, word_d=word_d)
                        print("[스펠학습] 완료.")
                        spelling_completed = True
                    except Exception as e:
                        if isinstance(e, SpellingUnknownWordException):
                            print('[AUTO-RECOVERY] 스펠학습에서 모르는 단어 감지됨: 자동으로 세트/홈/세트 이동 및 스펠학습만 재시작합니다.')
                            # Go to set selection page
                            driver.get(set_site)
                            time.sleep(1)
                            # Go to class main page
                            driver.get(f"https://www.classcard.net/ClassMain/{class_id}")
                            time.sleep(1)
                            # Go to set page again
                            driver.get(set_site)
                            time.sleep(1)
                            # Reprocess words
                            driver.find_element(
                                By.CSS_SELECTOR,
                                "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown > a",
                            ).click()
                            driver.find_element(
                                By.CSS_SELECTOR,
                                "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown.open > ul > li:nth-child(1) > a",
                            ).click()  # 학습구간 전체로 변경
                            html = BeautifulSoup(driver.page_source, "html.parser")
                            cards_ele = html.find("div", class_="flip-body")
                            num_d = len(cards_ele.find_all("div", class_="flip-card"))
                            time.sleep(0.5)
                            word_d = word_get(driver, num_d)
                            da_e, da_k, da_kyn = word_d
                            print('[AUTO-RECOVERY] 스펠학습만 자동으로 재시작합니다.')
                            continue  # Restart only spelling
                        else:
                            print('[ERROR] 예기치 않은 예외:', e)
                            print('메뉴로 돌아갑니다.')
                            break
        elif ch_d == 9:
            print("자동 다중 섹션 처리를 시작합니다.")
            print(f"사용 가능한 섹션: 0 ~ {len(sets_dict) - 1}")
            
            # Get range input
            try:
                start_input = input("시작 섹션 번호를 입력하세요: ").strip()
                end_input = input("끝 섹션 번호를 입력하세요: ").strip()
                
                start_section = int(start_input)
                end_section = int(end_input)
                
                if start_section < 0 or end_section >= len(sets_dict) or start_section > end_section:
                    print("잘못된 범위입니다. 다시 선택해주세요.")
                    continue
                
                # Ask about progress detection method
                print("\n진행률 감지 방법을 선택하세요:")
                print("[1] 자동 감지 (권장)")
                print("[2] 수동 입력 (자동 감지가 작동하지 않을 때)")
                print("[3] 진행률 무시하고 모든 섹션 처리")
                
                detection_choice = input(">>> ").strip()
                
                if detection_choice == "1":
                    # Automatic detection
                    process_section_range(driver, class_id, start_section, end_section, sets_dict, auto_detect=True)
                elif detection_choice == "2":
                    # Manual input
                    process_section_range(driver, class_id, start_section, end_section, sets_dict, auto_detect=False, manual_input=True)
                elif detection_choice == "3":
                    # Ignore progress and process all
                    process_section_range(driver, class_id, start_section, end_section, sets_dict, auto_detect=False, manual_input=False)
                else:
                    print("잘못된 선택입니다. 자동 감지를 사용합니다.")
                    process_section_range(driver, class_id, start_section, end_section, sets_dict, auto_detect=True)
                
            except ValueError:
                print("잘못된 입력입니다. 다시 선택해주세요.")
                continue
    elif ch_d == 4:
            print("테스트학습을 시작합니다.")
            # Go to set page and fetch words before starting test
            driver.get(set_site)
            time.sleep(1)
            driver.find_element(
                By.CSS_SELECTOR,
                "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown > a",
            ).click()
            driver.find_element(
                By.CSS_SELECTOR,
                "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown.open > ul > li:nth-child(1) > a",
            ).click()  # 학습구간 전체로 변경
            html = BeautifulSoup(driver.page_source, "html.parser")
            cards_ele = html.find("div", class_="flip-body")
            num_d = len(cards_ele.find_all("div", class_="flip-card"))
            time.sleep(0.5)
            word_d = word_get(driver, num_d)
            da_e, da_k, da_kyn = word_d
            controler = TestLearning(driver=driver)
            controler.run(num_d=num_d, word_d=word_d)
    elif ch_d == 5:
        print("암기학습 API 요청을 시작합니다.")
        classcard_api_post(
            user_id=user_id,
            set_id=sets_dict[set_choice]["set_id"],
            class_id=class_id,
            view_cnt=num_d,
            activity=3,
        )
        else:
            print("잘못된 입력입니다. 다시 선택해주세요.")
            continue
    print("학습이 종료되었습니다.")
    driver.get(set_site)  # 다시 세트페이지로 이동
    time.sleep(1)
