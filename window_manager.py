import pyautogui
import pygetwindow as gw
import time
import threading
import sys
import random
from selenium import webdriver

class WindowManager:
    def __init__(self, browser_driver=None, window_title_part="Chrome"):
        self.driver = browser_driver
        self.window_title_part = window_title_part
        self.is_running = False
        self.monitor_thread = None
        
    def find_browser_window(self):
        """Find the browser window by partial title match"""
        try:
            windows = gw.getAllWindows()
            for window in windows:
                if self.window_title_part.lower() in window.title.lower():
                    return window
            return None
        except Exception as e:
            print(f"[WARN] Could not find browser window: {e}")
            return None
    
    def keep_window_active(self):
        """Keep the browser window active and visible"""
        while self.is_running:
            try:
                window = self.find_browser_window()
                if window:
                    # Check if window is minimized
                    if window.isMinimized:
                        print("[INFO] Browser window was minimized, restoring...")
                        window.restore()
                        time.sleep(0.5)
                    
                    # Bring window to front if it's not active
                    if not window.isActive:
                        print("[INFO] Bringing browser window to front...")
                        window.activate()
                        time.sleep(0.5)
                    
                    # Move mouse to window area to simulate activity
                    if window.isActive and not window.isMinimized:
                        # Move mouse to a random position in the window
                        x = window.left + (window.width // 2) + (random.randint(-100, 100))
                        y = window.top + (window.height // 2) + (random.randint(-50, 50))
                        
                        # Ensure mouse stays within window bounds
                        x = max(window.left + 50, min(x, window.left + window.width - 50))
                        y = max(window.top + 50, min(y, window.top + window.height - 50))
                        
                        pyautogui.moveTo(x, y, duration=0.3)
                        
                        # Occasionally scroll or click to simulate human activity
                        if random.random() < 0.1:  # 10% chance
                            pyautogui.scroll(random.randint(-5, 5))
                        elif random.random() < 0.05:  # 5% chance
                            pyautogui.click()
                
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                print(f"[WARN] Window management error: {e}")
                time.sleep(2)
    
    def start_monitoring(self):
        """Start the window monitoring thread"""
        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            self.is_running = True
            self.monitor_thread = threading.Thread(target=self.keep_window_active, daemon=True)
            self.monitor_thread.start()
            print("[INFO] Window monitoring started - browser will stay visible")
    
    def stop_monitoring(self):
        """Stop the window monitoring"""
        self.is_running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1)
        print("[INFO] Window monitoring stopped")
    
    def human_like_activity(self):
        """Perform a single human-like activity"""
        try:
            window = self.find_browser_window()
            if window and not window.isMinimized:
                # Move mouse to random position in window
                x = window.left + random.randint(100, window.width - 100)
                y = window.top + random.randint(100, window.height - 100)
                pyautogui.moveTo(x, y, duration=0.5)
                
                # Random activity
                if random.random() < 0.3:
                    pyautogui.scroll(random.randint(-10, 10))
                elif random.random() < 0.2:
                    pyautogui.click()
                    
        except Exception as e:
            print(f"[WARN] Human-like activity failed: {e}")

# Example usage function
def setup_window_manager(driver, window_title_part="Chrome"):
    """Setup and return a window manager for the browser"""
    try:
        manager = WindowManager(driver, window_title_part)
        manager.start_monitoring()
        return manager
    except Exception as e:
        print(f"[ERROR] Failed to setup window manager: {e}")
        return None

if __name__ == "__main__":
    # Test the window manager
    print("Window Manager Test")
    print("This will keep Chrome windows visible and active")
    print("Press Ctrl+C to stop")
    
    try:
        manager = WindowManager(window_title_part="Chrome")
        manager.start_monitoring()
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping window manager...")
        manager.stop_monitoring()
        print("Window manager stopped") 