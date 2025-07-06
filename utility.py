import json
import os
import time

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By


def word_get(driver: webdriver.Chrome, num_d: int) -> list:
    da_e = ["" for _ in range(num_d)]
    da_k = ["" for _ in range(num_d)]
    da_kyn = ["" for _ in range(num_d)]

    try:
        # Get English words first
        for i in range(num_d):
            try:
                # Try multiple selectors for English words
                selectors = [
                    f"//*[@id='tab_set_all']/div[2]/div[{i+1}]/div[4]/div[1]/div[1]/div/div",
                    f"//div[@class='flip-card'][{i+1}]//div[@class='card-front']//div[@class='card-text']",
                    f"//div[@class='flip-body']//div[@class='flip-card'][{i+1}]//div[@class='card-front']//div[@class='card-text']"
                ]
                
                for selector in selectors:
                    try:
                        element = driver.find_element(By.XPATH, selector)
                        da_e[i] = element.text.strip()
                        if da_e[i]:
                            break
                    except:
                        continue
                
                if not da_e[i]:
                    print(f"[WARNING] Could not find English word for index {i}")
                    
            except Exception as e:
                print(f"[WARNING] Error getting English word {i}: {e}")

        # Switch to Korean words
        try:
            # Try multiple selectors for the Korean toggle button
            korean_selectors = [
                "#tab_set_all > div.card-list-title > div > div:nth-child(1) > a",
                "//a[contains(text(), '한글')]",
                "//a[contains(text(), 'Korean')]",
                "//div[@class='card-list-title']//a[1]"
            ]
            
            korean_clicked = False
            for selector in korean_selectors:
                try:
                    element = driver.find_element(By.CSS_SELECTOR if selector.startswith("#") else By.XPATH, selector)
                    if element.is_displayed() and element.is_enabled():
                        element.click()
                        print("[DEBUG] Korean toggle clicked")
                        korean_clicked = True
                        time.sleep(1)
                        break
                except:
                    continue
            
            if not korean_clicked:
                print("[WARNING] Could not click Korean toggle button")
                
        except Exception as e:
            print(f"[WARNING] Error switching to Korean: {e}")

        # Get Korean words
        for i in range(num_d):
            try:
                # Try multiple selectors for Korean words
                korean_selectors = [
                    f"//*[@id='tab_set_all']/div[2]/div[{i+1}]/div[4]/div[2]/div[1]/div/div",
                    f"//div[@class='flip-card'][{i+1}]//div[@class='card-back']//div[@class='card-text']",
                    f"//div[@class='flip-body']//div[@class='flip-card'][{i+1}]//div[@class='card-back']//div[@class='card-text']"
                ]
                
                ko_d = ""
                for selector in korean_selectors:
                    try:
                        element = driver.find_element(By.XPATH, selector)
                        ko_d = element.text.strip()
                        if ko_d:
                            break
                    except:
                        continue
                
                if ko_d:
                    ko_d = ko_d.split("\n")  # 한글단어를 뜻과 예문으로 나눔
                    da_k[i] = f"{ko_d[0]}"  # 뜻만 저장
                    if len(ko_d) != 1:  # 예문이 있으면
                        da_kyn[i] = f"{ko_d[0]} {ko_d[1]}"  # 뜻과 예문 저장
                    else:
                        da_kyn[i] = f"{ko_d[0]}"  # 뜻만 저장
                else:
                    print(f"[WARNING] Could not find Korean word for index {i}")
                    
            except Exception as e:
                print(f"[WARNING] Error getting Korean word {i}: {e}")

    except Exception as e:
        print(f"[ERROR] Error in word_get: {e}")

    print("[DEBUG] 영어단어 리스트:", da_e)
    print("[DEBUG] 한글단어 리스트:", da_k)
    print("[DEBUG] 뜻+예문 리스트:", da_kyn)
    return [da_e, da_k, da_kyn]  # 영어단어, 한글단어, 뜻과 예문


def chd_wh() -> int:  # 학습유형 선택
    os.system("cls")
    choice_dict = {
        1: "암기학습(매크로) 지원하지 않음",
        2: "리콜학습(매크로)",
        3: "스펠학습(매크로)",
        4: "테스트학습(매크로) 지원하지 않음",
        5: "암기학습(API 요청[경고])",
        6: "리콜학습(API 요청[경고])",
        7: "스펠학습(API 요청[경고])",
    }
    print(
        "학습유형을 선택해주세요.\n"
        "Ctrl + C 를 눌러 종료\n"
        "[1] 암기학습(매크로) 지원하지 않음\n"
        "[2] 리콜학습(매크로)\n"
        "[3] 스펠학습(매크로)\n"
        "[4] 테스트학습(매크로) 지원하지 않음\n"
        "[5] 암기학습(API 요청[경고])\n"
        "[6] 리콜학습(API 요청[경고])\n"
        "[7] 스펠학습(API 요청[경고])"
    )
    while 1:
        try:
            ch_d = int(input(">>> "))
            if ch_d >= 1 and ch_d <= 7:
                break
            else:
                raise ValueError
        except ValueError:
            print("학습유형을 다시 입력해주세요.")
        except KeyboardInterrupt:
            quit()
    os.system("cls")
    print(f"{ch_d}번 {choice_dict[ch_d]}를 선택하셨습니다.")
    return ch_d


def choice_set(sets: dict) -> int:  # 세트 선택
    os.system("cls")
    print("학습할 세트를 선택해주세요.")
    print("Ctrl + C 를 눌러 종료")
    for set_item in sets:
        print(
            f"[{set_item+1}] {sets[set_item].get('title')} | {sets[set_item].get('card_num')}"
        )
    while True:
        try:
            ch_s = int(input(">>> "))
            if ch_s >= 1 and ch_s <= len(sets):
                break
            else:
                raise ValueError
        except ValueError:
            print("세트를 다시 입력해주세요.")
        except KeyboardInterrupt:
            quit()
    os.system("cls")
    print(f"{sets[ch_s-1].get('title')}를 선택하셨습니다.")
    return ch_s - 1


def choice_class(class_dict: dict) -> int:  # 학습할 반 선택
    os.system('cls' if os.name == 'nt' else 'clear')
    print("학습할 클래스를 선택해주세요.")
    print("Ctrl + C 를 눌러 종료")
    for class_item in class_dict:
        print(f"[{class_item+1}] {class_dict[class_item].get('class_name')}")
    while True:
        try:
            ch_c = int(input(">>> "))
            if ch_c >= 1 and ch_c <= len(class_dict):
                break
            else:
                raise ValueError
        except ValueError:
            print("클래스를 다시 입력해주세요.")
        except KeyboardInterrupt:
            quit()
    os.system("cls")
    print(f"{class_dict[ch_c-1].get('class_name')}를 선택하셨습니다.")
    return ch_c - 1


def check_id(id: str, pw: str) -> bool:
    print("계정 정보를 확인하고 있습니다 잠시만 기다려주세요!")
    headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
    data = {"login_id": id, "login_pwd": pw}
    res = requests.post(
        "https://www.classcard.net/LoginProc", headers=headers, data=data
    )
    status = res.json()
    return status["result"] == "ok"


def save_id() -> dict:
    while True:
        id = input("아이디를 입력하세요 : ")
        password = input("비밀번호를 입력하세요 : ")
        if check_id(id, password):
            data = {"id": id, "pw": password}
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print("아이디 비밀번호가 저장되었습니다.\n")
            return data
        else:
            print("아이디 또는 비밀번호가 잘못되었습니다.\n")
            continue


def classcard_api_post(
    user_id: int,
    set_id: int,
    class_id: int,
    view_cnt: int,
    activity: int,
) -> None:
    url = "https://www.classcard.net/ViewSetAsync/resetAllLog"
    payload = f"set_idx={set_id}&activity={activity}&user_idx={user_id}&view_cnt={view_cnt}&class_idx={class_id}"
    headers = {
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    }
    requests.request("POST", url, data=payload, headers=headers)


def get_account() -> dict:
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            json_data = json.load(f)
            json_data["id"]
            json_data["pw"]
            return json_data
    except Exception:
        return save_id()
