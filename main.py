import sys
import threading
import time
import os
import random
import tempfile
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class LocalAI:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
        self.load_model()
    
    def load_model(self):
        """Load local AI model"""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            print("Loading AI model...")
            model_name = "microsoft/DialoGPT-small"
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
            
            self.is_loaded = True
            print("AI model loaded!")
            
        except Exception as e:
            print("ERROR: " + str(e))
            print("Using fallback...")
            self.is_loaded = False
    
    def generate_response(self, user_text, history):
        """Generate response"""
        if not self.is_loaded:
            return self.fallback_response(user_text)
        
        try:
            prompt = f"User: {user_text}\nBot:"
            
            inputs = self.tokenizer(prompt, return_tensors="pt", max_length=256, truncation=True)
            
            outputs = self.model.generate(
                inputs.input_ids,
                max_new_tokens=50,
                temperature=0.9,
                do_sample=True,
                top_p=0.95,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            if "Bot:" in response:
                response = response.split("Bot:")[-1].strip()
            
            if not response or len(response) < 2:
                return self.fallback_response(user_text)
            
            response = self.remove_emojis(response)
            
            return response
            
        except Exception as e:
            print("AI ERROR: " + str(e))
            return self.fallback_response(user_text)
    
    def remove_emojis(self, text):
        """Remove emojis from text"""
        import re
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"
            u"\U0001F300-\U0001F5FF"
            u"\U0001F680-\U0001F6FF"
            u"\U0001F1E0-\U0001F1FF"
            u"\U00002500-\U00002BEF"
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            u"\U0001f926-\U0001f937"
            u"\U00010000-\U0010FFFF"
            u"\u2640-\u2642"
            u"\u2600-\u2B55"
            u"\u200d"
            u"\u23cf"
            u"\u23e9"
            u"\u231a"
            u"\ufe0f"
            u"\u3030"
            "]+", flags=re.UNICODE)
        return emoji_pattern.sub(r'', text)
    
    def fallback_response(self, user_text):
        """Dark Miku responses in Russian - NO EMOJIS"""
        responses = [
            "Чё надо? Опять доставать будешь?",
            "Блин, ты опять со своими тупыми вопросами",
            "Отвали, я не в настроении сегодня",
            "Слушай, ты реально бесишь",
            "Мне лень с тобой разговаривать",
            "Ну что тебе опять надо?",
            "Серьёзно? Это самый тупой вопрос",
            "Блин, ну ты и зануда",
            "Хватит меня доставать, идиот",
            "Ты вообще думаешь, прежде чем спросить?",
            "Ага, щас, размечтался",
            "Ну ты даёшь",
            "Вот это вопрос, блин",
            "Так, всё, надоел",
            "Ты специально меня бесишь?",
            "Отстань, я занята",
            "Какая разница?",
            "Ну и что?",
            "Сама знаю",
            "Не твоё дело"
        ]
        return random.choice(responses)


class TTSManager:
    def __init__(self):
        self.tts_available = self.check_tts()
        self.miku_voice_available = self.check_miku_voice()
    
    def check_tts(self):
        try:
            import pygame
            pygame.mixer.init()
            return True
        except:
            return False
    
    def check_miku_voice(self):
        """Check if Miku voice files exist"""
        voice_dir = os.path.join(os.path.dirname(__file__), "miku_voice")
        if os.path.exists(voice_dir):
            files = os.listdir(voice_dir)
            if any(f.endswith('.mp3') or f.endswith('.wav') for f in files):
                return True
        return False
    
    def speak(self, text):
        """Speak using Miku voice files"""
        if not self.tts_available:
            print("TTS: " + text)
            return
        
        if self.miku_voice_available:

            threading.Thread(target=self._speak_miku, args=(text,), daemon=True).start()
        else:

            threading.Thread(target=self._speak_fallback, args=(text,), daemon=True).start()
    
    def _speak_miku(self, text):
        """Play Miku voice samples"""
        try:
            import pygame
            
            voice_dir = os.path.join(os.path.dirname(__file__), "miku_voice")
            voice_files = [f for f in os.listdir(voice_dir) if f.endswith('.mp3') or f.endswith('.wav')]
            
            if not voice_files:

                self._speak_fallback(text)
                return
            

            words = text.split()
            

            samples_to_play = []
            

            for i, word in enumerate(words):
                if len(word) > 2:

                    voice_file = random.choice(voice_files)
                    samples_to_play.append(os.path.join(voice_dir, voice_file))
            

            pygame.mixer.init()
            
            for sample in samples_to_play:
                if os.path.exists(sample):
                    pygame.mixer.music.load(sample)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        pygame.time.wait(100)
                    pygame.time.wait(50)  # Small pause between words
            
            pygame.mixer.quit()
            
        except Exception as e:
            print("MIKU VOICE ERROR: " + str(e))
            self._speak_fallback(text)
    
    def _speak_fallback(self, text):
        """Fallback to gTTS"""
        try:
            from gtts import gTTS
            import pygame
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
                temp_file = f.name
            
            tts = gTTS(text=text, lang='ru', slow=False)
            tts.save(temp_file)
            
            pygame.mixer.init()
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
            
            pygame.mixer.quit()
            os.unlink(temp_file)
            
        except Exception as e:
            print("FALLBACK TTS ERROR: " + str(e))
            print("TTS: " + text)


class AnimeGirl(QWidget):
    def __init__(self):
        super().__init__()
        
        self.ai = LocalAI()
        self.tts = TTSManager()
        
        self.setWindowTitle("Miku")
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        self.setFixedSize(350, 500)
        
        self.images = {}
        self.load_images()
        
        self.current_state = "molk"
        self.is_processing = False
        
        self.init_ui()
        self.update_position()
        self.show()
        
        print("=" * 50)
        print("HATSUNE MIKU STARTED")
        print("AI: " + ("LOADED" if self.ai.is_loaded else "FALLBACK"))
        print("TTS: " + ("MIKU VOICE" if self.tts.miku_voice_available else "gTTS FALLBACK"))
        print("=" * 50)
        
        if not self.tts.miku_voice_available:
            print("WARNING: Miku voice files not found!")
            print("Create 'miku_voice' folder and add .mp3 samples")
            print("Or use gTTS fallback")
            print("=" * 50)
    
    def load_images(self):
        """Load images"""
        if not os.path.exists("images"):
            os.makedirs("images")
            print("WARNING: images folder created")
            self.create_placeholder("molk")
            self.create_placeholder("talk")
            return
        
        image_files = {
            "molk": "images/molk.png",
            "talk": "images/talk.png"
        }
        
        for state, filepath in image_files.items():
            if os.path.exists(filepath):
                try:
                    pixmap = QPixmap(filepath)
                    if not pixmap.isNull():
                        self.images[state] = pixmap.scaled(
                            350, 450,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation
                        )
                        print("Loaded: " + filepath)
                    else:
                        self.create_placeholder(state)
                except:
                    self.create_placeholder(state)
            else:
                self.create_placeholder(state)
    
    def create_placeholder(self, state):
        """Create placeholder"""
        pixmap = QPixmap(350, 450)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.setBrush(QColor(200, 200, 200, 200))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(50, 50, 250, 350, 20, 20)
        
        painter.setPen(QColor(80, 80, 80))
        painter.setFont(QFont("Arial", 24, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "MIKU\n" + state.upper())
        
        painter.end()
        self.images[state] = pixmap
    
    def init_ui(self):
        """Create UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background: transparent;")
        self.image_label.setFixedSize(350, 500)
        self.set_state("molk")
        layout.addWidget(self.image_label)
        
        self.setLayout(layout)
    
    def set_state(self, state):
        """Set state"""
        self.current_state = state
        if state in self.images:
            self.image_label.setPixmap(self.images[state])
    
    def update_position(self):
        """Update position"""
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 20,
                 screen.height() - self.height() - 50)
    
    def show_response(self, response):
        """Show response"""
        self.set_state("talk")
        
        # Speak with Miku voice
        self.tts.speak(response)
        
        # Show popup
        self.show_popup(response)
        
        QTimer.singleShot(3000, lambda: self.set_state("molk"))
    
    def show_popup(self, text):
        """Show popup"""
        popup = QMessageBox(self)
        popup.setWindowTitle("Miku")
        popup.setText(text)
        popup.setIcon(QMessageBox.Information)
        popup.setStandardButtons(QMessageBox.Ok)
        popup.setStyleSheet("""
            QMessageBox {
                background: white;
            }
            QMessageBox QLabel {
                font-size: 13px;
                color: #333;
                padding: 10px;
                min-width: 200px;
            }
            QPushButton {
                background: #6c5ce7;
                border: none;
                border-radius: 10px;
                padding: 8px 30px;
                color: white;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #5a4bd1;
            }
        """)
        popup.exec_()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Miku Chat")
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.WindowCloseButtonHint |
            Qt.WindowMinimizeButtonHint
        )
        self.setFixedSize(400, 80)
        
        self.center_window()
        
        self.setStyleSheet("""
            QWidget {
                background: white;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 8px 12px;
                font-size: 13px;
                background: white;
            }
            QLineEdit:focus {
                border: 1px solid #666;
            }
            QPushButton {
                background: #e0e0e0;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 8px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #d0d0d0;
            }
            QLabel {
                color: #666;
                font-size: 11px;
            }
        """)
        
        self.init_ui()
        
        self.is_processing = False
        self.girl = AnimeGirl()
        
        self.input_field.setFocus()
        
        print("CHAT READY")
    
    def center_window(self):
        """Center window"""
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def init_ui(self):
        """Create UI"""
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask Miku something...")
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedWidth(70)
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)
        
        layout.addLayout(input_layout)
        
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def send_message(self):
        """Send message"""
        user_text = self.input_field.text().strip()
        
        if not user_text:
            self.input_field.setPlaceholderText("Type something!")
            self.input_field.setStyleSheet("""
                QLineEdit {
                    border: 1px solid #ff6b6b;
                    border-radius: 5px;
                    padding: 8px 12px;
                    font-size: 13px;
                    background: white;
                }
            """)
            QTimer.singleShot(2000, self.reset_input_style)
            return
        
        if self.is_processing:
            self.status_label.setText("Wait...")
            return
        
        self.input_field.clear()
        self.status_label.setText("Thinking...")
        self.send_btn.setEnabled(False)
        
        print("")
        print("USER: " + user_text)
        print("MIKU: thinking...")
        
        self.is_processing = True
        
        thread = threading.Thread(target=self.ask_local_ai, args=(user_text,), daemon=True)
        thread.start()
    
    def reset_input_style(self):
        """Reset input style"""
        self.input_field.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 8px 12px;
                font-size: 13px;
                background: white;
            }
            QLineEdit:focus {
                border: 1px solid #666;
            }
        """)
        self.input_field.setPlaceholderText("Ask Miku something...")
    
    def ask_local_ai(self, user_text):
        """Ask local AI"""
        response = self.girl.ai.generate_response(user_text, [])
        
        self.is_processing = False
        
        QMetaObject.invokeMethod(self, "show_response",
                                Qt.QueuedConnection,
                                Q_ARG(str, response))
    
    @pyqtSlot(str)
    def show_response(self, response):
        """Show response"""
        self.status_label.setText("Ready")
        self.send_btn.setEnabled(True)
        self.input_field.setFocus()
        
        self.girl.show_response(response)
        
        print("MIKU: " + response)
        print("-" * 40)
    
    def closeEvent(self, event):
        """Close event"""
        if self.girl:
            self.girl.close()
        event.accept()


class App(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(True)
        self.setWindowIcon(QIcon())
        
        print("=" * 50)
        print("HATSUNE MIKU CHAT")
        print("=" * 50)


if __name__ == "__main__":
    app = App(sys.argv)
    
    # Create folders
    if not os.path.exists("images"):
        os.makedirs("images")
        print("Created: images folder")
        print("Place: molk.png and talk.png")
    
    if not os.path.exists("miku_voice"):
        os.makedirs("miku_voice")
        print("Created: miku_voice folder")
        print("Place: Miku voice samples (.mp3)")
        print("Download from: https://github.com/your-repo/miku-samples")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())