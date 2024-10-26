import sys
import re

import ebooklib
from ebooklib import epub

from book_progress import update_progress, get_progress


from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget, QFileDialog, QDialog, QDialogButtonBox, QApplication
from PyQt6.QtCore import QUrl, Qt, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut

from bs4 import BeautifulSoup

class FastReader(QMainWindow):
    book_plaintext: list[str]
    book_filename: str
    playing: bool
    word_index: int
    words_per_min: int
    book_length: int
    word_index: int

    def __init__(self):
        super().__init__()
        self.playing = False
        self.word_index = 0
        main_layout = QVBoxLayout()
        control_buttons= QHBoxLayout()
        button_box = QHBoxLayout()

        self.space_shortcut = QShortcut(QKeySequence("Space"), self)
        self.space_shortcut.activated.connect(self.toggle_play_pause)

        self.p_shortcut = QShortcut(QKeySequence("p"), self)
        self.p_shortcut.activated.connect(lambda: self.change_speed_by(10))
        self.o_shortcut = QShortcut(QKeySequence("o"), self)
        self.o_shortcut.activated.connect(lambda: self.change_speed_by(-10))

        self.right_arrow_shortcut = QShortcut(QKeySequence("Right"), self)
        self.right_arrow_shortcut.activated.connect(lambda: self.change_position_by(1))
        self.left_arrow_shortcut = QShortcut(QKeySequence("Left"), self)
        self.left_arrow_shortcut.activated.connect(lambda: self.change_position_by(-1))


        self.file_label = QLabel("No file loaded")
        self.open_file_button = QPushButton("Open File")
        self.open_file_button.clicked.connect(self.open_file)
        self.play_pause_button = QPushButton("Play")
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.set_word_index = QPushButton("Go to Word:")
        self.set_word_index.clicked.connect(self.go_to_word)

        self.main_label = QLabel("*******")
        self.main_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_label.setStyleSheet("font-size: 32px;")

        self.less_button = QPushButton("-")
        self.less_button.setFixedSize(50, 30)
        self.less_button.clicked.connect(lambda: self.change_speed_by(-10))
        self.more_button = QPushButton("+")
        self.more_button.setFixedSize(50, 30)
        self.more_button.clicked.connect(lambda: self.change_speed_by(10))
        self.info_label = QLabel("Speed: wpm        Progress: 0/??? words [???%]")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        top_layout = QVBoxLayout()
        top_layout.addWidget(self.file_label)
        top_layout.addWidget(self.main_label)

        control_buttons.addWidget(self.open_file_button)
        control_buttons.addWidget(self.play_pause_button)
        control_buttons.addWidget(self.set_word_index)
        top_layout.addLayout(control_buttons)


        button_box.addWidget(self.less_button)
        button_box.addWidget(self.info_label)
        button_box.addWidget(self.more_button)
        top_layout.addLayout(button_box)

        main_layout.addLayout(top_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_main_label)

        self.words_per_min = 500

        # Window settings
        self.setWindowTitle("Fast E-Book Reader")
        self.resize(360, 180)

    def change_position_by(self, ammount):
        if not self.playing:
            self.word_index += ammount
            self.set_info_label_text()
            self.update_main_label()

    def closeEvent(self, event):
        update_progress(self.book_filename, self.word_index-60)

    def open_file(self):
        epub_file, _ = QFileDialog.getOpenFileName(self, "Open ePUB File", "/home/georgiou/Downloads", filter = "EPUB Files (*.epub)")
        self.book_filename = epub_file.split(".")[0].split("/")[-1]
        print(self.book_filename)
        self.file_label.setText(f"Loaded: {self.book_filename[:max(50, len(self.book_filename))]}")
        self.book_plaintext = self.extract_all_words_from_epub(epub_file)

        if get_progress(self.book_filename):
            self.word_index = get_progress(self.book_filename)
        else:
            update_progress(self.book_filename, self.word_index)

    def extract_all_words_from_epub(self, epub_file):
        book = epub.read_epub(epub_file)

        words = []

        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                content = item.get_content()
                soup = BeautifulSoup(content, 'html.parser')
                for w in re.split(r'[ \n]+', soup.get_text()):
                    if str(w) != "": words.append(str(w))

        # Join all the text into a single string
        return words

    def toggle_play_pause(self):
        self.playing = not self.playing
        if self.playing:
            self.play_pause_button.setText("Pause")
            self.timer.start((60*1000)//self.words_per_min)
        else:
            self.play_pause_button.setText("Play")
            self.timer.stop()

    def go_to_word(self):
        search_box = QDialog(self)
        search_box.setWindowTitle("Which word do you want to jump to?")

        layout = QVBoxLayout()
        query_input = QLineEdit(str(self.word_index))
        layout.addWidget(query_input)

        # OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(button_box)

        button_box.accepted.connect(search_box.accept)
        button_box.rejected.connect(search_box.reject)

        search_box.setLayout(layout)

        if search_box.exec() == QDialog.DialogCode.Accepted:
            self.word_index = int(query_input.text())
            self.main_label.setText(" ".join(self.book_plaintext[max(self.word_index-10, 0):self.word_index]))

    def set_info_label_text(self, ):
        length = len(self.book_plaintext)
        speed = self.words_per_min
        index = self.word_index
        total_minutes = (length - index) // speed

        hours = total_minutes // 60
        minutes = total_minutes % 60

        if hours > 0:
            time_left = f"{hours}h {minutes}m"
        else:
            time_left = f"{minutes}m"

        self.info_label.setText(f"Speed: {speed} wpm (~{time_left})      Progress: {index}/{length} words [{100*(index/length):.2f}%]")

    def update_main_label(self):
        if self.playing:
            self.word_index += 1
            self.main_label.setText(self.book_plaintext[self.word_index].strip())
            self.set_info_label_text()

            last_char = self.book_plaintext[self.word_index].strip()[-1]
            match last_char:
                case "." | "?" |"!":
                    self.timer.setInterval(int((2* 60 * 1000) // self.words_per_min))
                case ";":
                    self.timer.setInterval(int((1.75 * 60 * 1000) // self.words_per_min))
                case ",":
                    self.timer.setInterval(int((1.5 * 60 * 1000) // self.words_per_min))
                case _:
                    self.timer.setInterval(int((60 * 1000) // self.words_per_min))
        else:
            self.main_label.setText(self.book_plaintext[self.word_index].strip())

    def change_speed_by(self, delta):
        self.words_per_min = max(1, self.words_per_min + delta)
        self.set_info_label_text()
        if self.playing:
            self.timer.setInterval((60 * 1000) // self.words_per_min)

app = QApplication(sys.argv)
app.setStyleSheet("""

     QPushButton {
        background-color: #4a34aa;
        color: white;
        font-size: 14px;
        border-radius: 15px;
        padding: 8px;
    }
    QPushButton:hover {
        background-color: #6555aa;
    }
    QLabel {
        font-size: 16px;
        border-radius: 10px;

    }
""")

window = FastReader()
window.show()
sys.exit(app.exec())
