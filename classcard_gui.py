import sys
import json
import os
import time
import threading
import re
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QComboBox, QTextEdit, QCheckBox, QGroupBox, QGridLayout, QMessageBox,
    QProgressBar
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont
from handler.recall_learning import RecallLearning
from handler.spelling_learning import SpellingLearning
from handler.test_learning import TestLearning
from classcard_core import ClassCardCore

CONFIG_FILE = 'config.json'

class AutomationThread(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    
    def __init__(self, core, class_id, start_set_id, end_set_id, modes):
        super().__init__()
        self.core = core
        self.class_id = class_id
        self.start_set_id = start_set_id
        self.end_set_id = end_set_id
        self.modes = modes
        self._stop_requested = False
        
    def run(self):
        try:
            self.progress_signal.emit("[INFO] 자동화 시작...")
            
            # Use the new robust range automation
            results = self.core.run_range_automation_with_stop(
                self.class_id, 
                self.start_set_id, 
                self.end_set_id, 
                self.modes,
                self.is_stop_requested
            )
            
            # Log final results
            self.progress_signal.emit("\n[INFO] 자동화 완료 - 최종 결과:")
            all_completed = True
            
            for set_id, set_data in results.items():
                set_title = set_data["title"]
                self.progress_signal.emit(f"\n[SET] {set_title} (ID: {set_id}):")
                
                for mode, result in set_data["results"].items():
                    percentage = result["percentage"]
                    completed = result["completed_words"]
                    total = result["total_words"]
                    
                    if percentage >= 100:
                        self.progress_signal.emit(f"  ✓ {mode}: {completed}/{total} ({percentage:.1f}%)")
                    else:
                        self.progress_signal.emit(f"  ✗ {mode}: {completed}/{total} ({percentage:.1f}%)")
                        all_completed = False
            
            if all_completed:
                self.progress_signal.emit("\n[SUCCESS] 모든 학습 모드가 100% 완료되었습니다!")
            else:
                self.progress_signal.emit("\n[WARNING] 일부 학습 모드가 100% 미만으로 완료되었습니다.")
            
            self.finished_signal.emit()
            
        except Exception as e:
            self.error_signal.emit(f"[ERROR] 자동화 중 오류 발생: {e}")
            self.finished_signal.emit()

    def request_stop(self):
        self._stop_requested = True

    def is_stop_requested(self):
        return self._stop_requested

class ClassCardGUI(QMainWindow):
    # Define signals for thread-safe GUI updates
    log_signal = pyqtSignal(str)
    class_list_signal = pyqtSignal(list)
    set_list_signal = pyqtSignal(list)
    enable_run_signal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.core = None
        self.is_running = False
        self.init_ui()
        self.load_config()
        
        # Connect signals
        self.log_signal.connect(self.log_message)
        self.class_list_signal.connect(self.update_class_list)
        self.set_list_signal.connect(self.update_set_list)
        self.enable_run_signal.connect(self.run_btn.setEnabled)

    def init_ui(self):
        self.setWindowTitle("ClassCard 자동화 도구")
        self.setGeometry(100, 100, 800, 600)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        
        # Login section
        login_group = QGroupBox("로그인")
        login_layout = QGridLayout()
        
        login_layout.addWidget(QLabel("아이디:"), 0, 0)
        self.id_input = QLineEdit()
        login_layout.addWidget(self.id_input, 0, 1)
        
        login_layout.addWidget(QLabel("비밀번호:"), 1, 0)
        self.pw_input = QLineEdit()
        self.pw_input.setEchoMode(QLineEdit.Password)
        login_layout.addWidget(self.pw_input, 1, 1)
        
        self.login_btn = QPushButton("로그인")
        self.login_btn.clicked.connect(self.login)
        login_layout.addWidget(self.login_btn, 2, 0, 1, 2)
        
        login_group.setLayout(login_layout)
        layout.addWidget(login_group)
        
        # Class and set selection
        selection_group = QGroupBox("클래스 및 세트 선택")
        selection_layout = QVBoxLayout()
        
        # Class selection
        class_layout = QHBoxLayout()
        class_layout.addWidget(QLabel("클래스:"))
        self.class_combo = QComboBox()
        self.class_combo.currentIndexChanged.connect(self.on_class_changed)
        class_layout.addWidget(self.class_combo)
        
        self.load_sets_btn = QPushButton("세트 목록 불러오기")
        self.load_sets_btn.clicked.connect(self.load_sets)
        self.load_sets_btn.setEnabled(False)
        class_layout.addWidget(self.load_sets_btn)
        
        selection_layout.addLayout(class_layout)
        
        # Set selection
        set_layout = QHBoxLayout()
        set_layout.addWidget(QLabel("세트:"))
        self.set_combo = QComboBox()
        self.set_combo.setEnabled(False)
        set_layout.addWidget(self.set_combo)
        
        selection_layout.addLayout(set_layout)
        
        # Range mode
        range_layout = QHBoxLayout()
        self.range_checkbox = QCheckBox("범위 모드")
        self.range_checkbox.stateChanged.connect(self.on_range_changed)
        range_layout.addWidget(self.range_checkbox)
        
        range_layout.addWidget(QLabel("시작:"))
        self.start_set_combo = QComboBox()
        self.start_set_combo.setEnabled(False)
        range_layout.addWidget(self.start_set_combo)
        
        range_layout.addWidget(QLabel("끝:"))
        self.end_set_combo = QComboBox()
        self.end_set_combo.setEnabled(False)
        range_layout.addWidget(self.end_set_combo)
        
        selection_layout.addLayout(range_layout)
        
        selection_group.setLayout(selection_layout)
        layout.addWidget(selection_group)
        
        # Learning modes
        modes_group = QGroupBox("학습 모드")
        modes_layout = QHBoxLayout()
        
        self.recall_checkbox = QCheckBox("리콜학습")
        self.spelling_checkbox = QCheckBox("스펠학습")
        self.test_checkbox = QCheckBox("테스트학습")
        
        modes_layout.addWidget(self.recall_checkbox)
        modes_layout.addWidget(self.spelling_checkbox)
        modes_layout.addWidget(self.test_checkbox)
        
        modes_group.setLayout(modes_layout)
        layout.addWidget(modes_group)
        
        # Run and Stop buttons
        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton("학습 시작")
        self.run_btn.clicked.connect(self.start_automation)
        self.run_btn.setEnabled(False)
        btn_layout.addWidget(self.run_btn)
        self.stop_btn = QPushButton("중지")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_automation)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)
        
        # Status log
        log_group = QGroupBox("상태 로그")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        main_widget.setLayout(layout)
        
    def load_config(self):
        """Load saved credentials from config.json"""
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                self.id_input.setText(config.get("user_id", ""))
                self.pw_input.setText(config.get("password", ""))
        except FileNotFoundError:
            pass
        except Exception as e:
            self.log_signal.emit(f"[WARNING] 설정 파일 로드 실패: {e}")
    
    def save_config(self):
        """Save credentials to config.json"""
        try:
            config = {
                "user_id": self.id_input.text(),
                "password": self.pw_input.text()
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log_signal.emit(f"[WARNING] 설정 파일 저장 실패: {e}")
    
    def log_message(self, message):
        """Add message to log with timestamp"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # Auto-scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def login(self):
        """Handle login"""
        if self.is_running:
            return
            
        user_id = self.id_input.text().strip()
        password = self.pw_input.text().strip()
        
        if not user_id or not password:
            QMessageBox.warning(self, "오류", "아이디와 비밀번호를 입력하세요.")
            return
        
        self.log_message("[INFO] 로그인 시도 중...")
        self.login_btn.setEnabled(False)
        
        # Run login in thread
        def login_thread():
            try:
                self.core = ClassCardCore()
                driver = self.core.setup_driver()
                
                if self.core.login(user_id, password):
                    self.log_message("[INFO] 로그인 성공!")
                    self.save_config()
                    
                    # Get classes
                    classes = self.core.get_classes()
                    if classes:
                        self.log_message(f"[INFO] {len(classes)}개 클래스 발견")
                        
                        # Update UI in main thread
                        class_list = []
                        for i, class_info in classes.items():
                            class_list.append((class_info["class_name"], class_info["class_id"]))
                        
                        self.class_list_signal.emit(class_list)
                        self.load_sets_btn.setEnabled(True)
                    else:
                        self.log_message("[ERROR] 클래스를 찾을 수 없습니다.")
                        
                else:
                    self.log_message("[ERROR] 로그인 실패")
                    
            except Exception as e:
                self.log_message(f"[ERROR] 로그인 중 오류: {e}")
            finally:
                self.login_btn.setEnabled(True)
        
        threading.Thread(target=login_thread, daemon=True).start()
    
    def update_class_list(self, class_list):
        """Update class combo box"""
        self.class_combo.clear()
        for class_name, class_id in class_list:
            self.class_combo.addItem(class_name, class_id)
    
    def on_class_changed(self):
        """Handle class selection change"""
        if self.class_combo.currentData():
            self.load_sets_btn.setEnabled(True)
        else:
            self.load_sets_btn.setEnabled(False)
            self.set_combo.clear()
            self.set_combo.setEnabled(False)
    
    def load_sets(self):
        """Load sets for selected class"""
        if self.is_running or not self.core:
            return
            
        class_id = self.class_combo.currentData()
        if not class_id:
            return
        
        self.log_message("[INFO] 세트 목록 불러오는 중...")
        self.load_sets_btn.setEnabled(False)
        
        def load_sets_thread():
            try:
                sets = self.core.get_sets(class_id)
                if sets:
                    self.log_message(f"[INFO] {len(sets)}개 세트 발견")
                    
                    # Update UI in main thread
                    set_list = []
                    for i, set_info in sets.items():
                        set_name = set_info["title"]
                        set_id = set_info["set_id"]
                        set_list.append((set_name, set_id))
                    
                    self.set_list_signal.emit(set_list)
                    self.run_btn.setEnabled(True)
                else:
                    self.log_message("[ERROR] 세트를 찾을 수 없습니다.")
                    
            except Exception as e:
                self.log_message(f"[ERROR] 세트 로드 중 오류: {e}")
            finally:
                self.load_sets_btn.setEnabled(True)
        
        threading.Thread(target=load_sets_thread, daemon=True).start()
    
    def update_set_list(self, set_list):
        """Update set combo boxes with clearer names"""
        self.set_combo.clear()
        self.start_set_combo.clear()
        self.end_set_combo.clear()
        for idx, (set_name, set_id) in enumerate(set_list, 1):
            display_name = f"{idx}. {set_name}"
            self.set_combo.addItem(display_name, set_id)
            self.start_set_combo.addItem(display_name, set_id)
            self.end_set_combo.addItem(display_name, set_id)
        self.set_combo.setEnabled(True)
        # Make dropdowns wide enough
        self.start_set_combo.setMinimumWidth(250)
        self.end_set_combo.setMinimumWidth(250)
    
    def on_range_changed(self, state):
        """Handle range mode checkbox change"""
        enabled = state == Qt.Checked
        self.start_set_combo.setEnabled(enabled)
        self.end_set_combo.setEnabled(enabled)
        self.set_combo.setEnabled(not enabled)
    
    def start_automation(self):
        """Start the automation process"""
        if self.is_running:
            return
        
        # Get selected modes
        modes = []
        if self.recall_checkbox.isChecked():
            modes.append("recall")
        if self.spelling_checkbox.isChecked():
            modes.append("spelling")
        if self.test_checkbox.isChecked():
            modes.append("test")
        
        if not modes:
            QMessageBox.warning(self, "오류", "최소 하나의 학습 모드를 선택하세요.")
            return
        
        # Get set information
        if self.range_checkbox.isChecked():
            start_set_id = int(self.start_set_combo.currentData())
            end_set_id = int(self.end_set_combo.currentData())
            if not start_set_id or not end_set_id:
                QMessageBox.warning(self, "오류", "범위를 올바르게 선택하세요.")
                return
        else:
            set_id = self.set_combo.currentData()
            if not set_id:
                QMessageBox.warning(self, "오류", "세트를 선택하세요.")
                return
            start_set_id = end_set_id = int(set_id)
        
        class_id = self.class_combo.currentData()
        if not class_id:
            QMessageBox.warning(self, "오류", "클래스를 선택하세요.")
            return
        
        # Start automation
        self.is_running = True
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.log_message(f"[INFO] 자동화 시작 - 모드: {', '.join(modes)}")
        
        # Create and start automation thread
        self.automation_thread = AutomationThread(
            self.core, class_id, start_set_id, end_set_id, modes
        )
        self.automation_thread.progress_signal.connect(self.log_message)
        self.automation_thread.error_signal.connect(self.log_message)
        self.automation_thread.finished_signal.connect(self.on_automation_finished)
        self.automation_thread.start()
    
    def stop_automation(self):
        if self.is_running and hasattr(self, 'automation_thread'):
            self.log_message("[INFO] 중지 요청됨. 자동화 스레드에 안전 종료 신호를 보냅니다...")
            self.automation_thread.request_stop()
            self.automation_thread.wait()
            self.is_running = False
            self.run_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.log_message("[INFO] 자동화가 안전하게 중지되었습니다.")
    
    def on_automation_finished(self):
        """Handle automation completion"""
        self.is_running = False
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log_message("[INFO] 자동화 완료")

def main():
    app = QApplication(sys.argv)
    window = ClassCardGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 