import time
import warnings
from classcard_core import ClassCardCore
from utility import choice_set, choice_class

warnings.filterwarnings("ignore", category=DeprecationWarning)

def main():
    print("ClassCard 자동화 도구")
    print("=" * 50)
    
    # Setup core
    core = ClassCardCore()
    driver = core.setup_driver()
    
    try:
        # Login
        print("\n로그인 정보를 입력하세요.")
        user_id = input("아이디: ").strip()
        password = input("비밀번호: ").strip()
        
        if not core.login(user_id, password):
            print("[ERROR] 로그인 실패")
            return
        
        print("[INFO] 로그인 성공!")
        
        # Get classes
        classes = core.get_classes()
        if not classes:
            print("[ERROR] 클래스를 찾을 수 없습니다.")
            return
        
        print(f"\n[INFO] {len(classes)}개 클래스 발견:")
        for i, class_info in classes.items():
            print(f"  {i}: {class_info['class_name']}")
        
        # Select class
        if len(classes) == 1:
    choice_class_val = 0
            print(f"[INFO] 단일 클래스 자동 선택: {classes[0]['class_name']}")
else:
            choice_class_val = choice_class(class_dict=classes)
        
        class_id = classes[choice_class_val]["class_id"]
        print(f"[INFO] 선택된 클래스: {classes[choice_class_val]['class_name']}")
        
        # Get sets
        sets = core.get_sets(class_id)
        if not sets:
            print("[ERROR] 세트를 찾을 수 없습니다.")
            return
        
        print(f"\n[INFO] {len(sets)}개 세트 발견:")
        for i, set_info in sets.items():
            print(f"  {i}: {set_info['title']}")
        
        # Learning mode menu
        while True:
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
            
            try:
                ch_d = input(">>> ").strip()
                if ch_d == "0":
                    break
                
                ch_d = int(ch_d)
                
                if ch_d == 2:
        print("리콜학습을 시작합니다.")
                    # Select set
                    if len(sets) == 1:
                        choice_set_val = 0
                        print(f"[INFO] 단일 세트 자동 선택: {sets[0]['title']}")
                    else:
                        choice_set_val = choice_set(sets_dict=sets)
                    
                    set_id = sets[choice_set_val]["set_id"]
                    print(f"[INFO] 선택된 세트: {sets[choice_set_val]['title']}")
                    
                    # Get words
                    num_d, word_d = core.get_words_for_set(set_id, class_id)
                    if num_d == 0:
                        print("[ERROR] 단어를 가져올 수 없습니다.")
                        continue
                    
                    print(f"[INFO] {num_d}개 단어 로드 완료")
                    
                    # Run recall learning with robust completion tracking
                    try:
                        completed_words, total_words = core.run_recall_learning(num_d, word_d)
                        completion_percentage = (completed_words / total_words) * 100
                        print(f"[SUCCESS] 리콜학습 완료: {completed_words}/{total_words} ({completion_percentage:.1f}%)")
                        
                        if completion_percentage < 100:
                            print(f"[WARNING] 리콜학습이 100% 미만으로 완료되었습니다. ({completion_percentage:.1f}%)")
                    except Exception as e:
                        print(f"[ERROR] 리콜학습 실패: {e}")
                
    elif ch_d == 3:
        print("스펠학습을 시작합니다.")
                    # Select set
                    if len(sets) == 1:
                        choice_set_val = 0
                        print(f"[INFO] 단일 세트 자동 선택: {sets[0]['title']}")
                    else:
                        choice_set_val = choice_set(sets_dict=sets)
                    
                    set_id = sets[choice_set_val]["set_id"]
                    print(f"[INFO] 선택된 세트: {sets[choice_set_val]['title']}")
                    
                    # Get words
                    num_d, word_d = core.get_words_for_set(set_id, class_id)
                    if num_d == 0:
                        print("[ERROR] 단어를 가져올 수 없습니다.")
                        continue
                    
                    print(f"[INFO] {num_d}개 단어 로드 완료")
                    
                    # Run spelling learning with robust completion tracking
                    try:
                        completed_words, total_words = core.run_spelling_learning(num_d, word_d)
                        completion_percentage = (completed_words / total_words) * 100
                        print(f"[SUCCESS] 스펠학습 완료: {completed_words}/{total_words} ({completion_percentage:.1f}%)")
                        
                        if completion_percentage < 100:
                            print(f"[WARNING] 스펠학습이 100% 미만으로 완료되었습니다. ({completion_percentage:.1f}%)")
                    except Exception as e:
                        print(f"[ERROR] 스펠학습 실패: {e}")
                
                elif ch_d == 8:
                    print("리콜+스펠학습을 시작합니다.")
                    # Select set
                    if len(sets) == 1:
                        choice_set_val = 0
                        print(f"[INFO] 단일 세트 자동 선택: {sets[0]['title']}")
                    else:
                        choice_set_val = choice_set(sets_dict=sets)
                    
                    set_id = sets[choice_set_val]["set_id"]
                    print(f"[INFO] 선택된 세트: {sets[choice_set_val]['title']}")
                    
                    # Run multiple modes with robust completion tracking
                    try:
                        results = core.run_multiple_modes(set_id, class_id, ["recall", "spelling"])
                        
                        print("\n[INFO] 학습 결과:")
                        all_completed = True
                        for mode, result in results.items():
                            percentage = result["percentage"]
                            completed = result["completed_words"]
                            total = result["total_words"]
                            
                            if percentage >= 100:
                                print(f"  ✓ {mode}: {completed}/{total} ({percentage:.1f}%)")
                            else:
                                print(f"  ✗ {mode}: {completed}/{total} ({percentage:.1f}%)")
                                all_completed = False
                        
                        if all_completed:
                            print("\n[SUCCESS] 모든 학습 모드가 100% 완료되었습니다!")
                        else:
                            print("\n[WARNING] 일부 학습 모드가 100% 미만으로 완료되었습니다.")
                            
                    except Exception as e:
                        print(f"[ERROR] 리콜+스펠학습 실패: {e}")
                
                elif ch_d == 9:
                    print("자동 다중 섹션 처리를 시작합니다.")
                    print("처리할 섹션 범위를 입력하세요.")
                    
                    try:
                        start_section = int(input("시작 섹션 번호: "))
                        end_section = int(input("끝 섹션 번호: "))
                        
                        if start_section > end_section:
                            print("[ERROR] 시작 섹션이 끝 섹션보다 클 수 없습니다.")
                            continue
                        
                        print(f"[INFO] 섹션 {start_section}부터 {end_section}까지 처리합니다.")
                        
                        # Run range automation with robust completion tracking
                        try:
                            results = core.run_range_automation(class_id, start_section, end_section, ["recall", "spelling"])
                            
                            print("\n[INFO] 범위 자동화 완료 - 최종 결과:")
                            all_completed = True
                            
                            for set_id, set_data in results.items():
                                set_title = set_data["title"]
                                print(f"\n[SET] {set_title} (ID: {set_id}):")
                                
                                for mode, result in set_data["results"].items():
                                    percentage = result["percentage"]
                                    completed = result["completed_words"]
                                    total = result["total_words"]
                                    
                                    if percentage >= 100:
                                        print(f"  ✓ {mode}: {completed}/{total} ({percentage:.1f}%)")
                                    else:
                                        print(f"  ✗ {mode}: {completed}/{total} ({percentage:.1f}%)")
                                        all_completed = False
                            
                            if all_completed:
                                print("\n[SUCCESS] 모든 학습 모드가 100% 완료되었습니다!")
                            else:
                                print("\n[WARNING] 일부 학습 모드가 100% 미만으로 완료되었습니다.")
                                
                        except Exception as e:
                            print(f"[ERROR] 범위 자동화 실패: {e}")
                        
                    except ValueError:
                        print("[ERROR] 올바른 숫자를 입력하세요.")
                        continue
                
                else:
                    print("지원하지 않는 옵션입니다.")
                    
            except ValueError:
                print("잘못된 입력입니다. 다시 선택해주세요.")
            except KeyboardInterrupt:
                print("\n프로그램을 종료합니다.")
                break
            except Exception as e:
                print(f"[ERROR] 예기치 않은 오류: {e}")
    
    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다.")
    except Exception as e:
        print(f"[ERROR] 프로그램 오류: {e}")
    finally:
        core.close()

if __name__ == "__main__":
    main()
