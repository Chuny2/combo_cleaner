import sys
import re
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QFileDialog, QTextEdit, QLabel, QProgressBar, 
                             QFrame, QSizePolicy, QLineEdit, QTabWidget)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QPalette, QFont, QIcon

def clasificar_identificador(identificador):
    if "@" in identificador:
        return "EMAIL"
    elif re.match(r'^\d{7,8}[A-Za-z]$', identificador):
        return "DNI"
    else:
        return "USUARIO"

def es_url(texto):
    return texto.startswith('http://') or texto.startswith('https://') or texto.startswith('//')

def procesar_linea(linea):
    """
    Procesa una línea para extraer IDENTIFICADOR:PASSWORD.
    Maneja líneas con o sin URLs, y diferentes separadores.
    """
    # Reemplazar el primer espacio encontrado por ':', si existe
    if ' ' in linea:
        linea = linea.replace(' ', ':', 1)
    
    # Manejar casos con '|' como separador
    if '|' in linea:
        partes = linea.split('|')
        if len(partes) >= 3 and es_url(partes[0]):
            identificador, password = partes[1], partes[2]
        elif len(partes) >= 2:
            identificador, password = partes[0], partes[1]
        else:
            return None
    else:
        # Dividir la línea en hasta tres partes desde la derecha
        partes = linea.rsplit(':', 2)
        
        if len(partes) == 3:
            # Formato: URL:IDENTIFICADOR:PASSWORD o IDENTIFICADOR:PASSWORD:URL
            if es_url(partes[0]):
                identificador, password = partes[1], partes[2]
            elif es_url(partes[2]):
                identificador, password = partes[0], partes[1]
            else:
                identificador, password = partes[1], partes[2]
        elif len(partes) == 2:
            # Formato: IDENTIFICADOR:PASSWORD
            identificador, password = partes
        else:
            # Formato incorrecto
            return None
    
    identificador = identificador.strip()
    password = password.strip()
    
    # Validar que identificador y password no estén vacíos
    if not identificador or not password:
        return None
    
    # Validar que password no sea una URL
    if es_url(password):
        return None
    
    # Nueva verificación adicional
    if ':' in password:
        password = password.split(':')[0]
    
    # Opcional: Clasificar el identificador
    tipo_identificador = clasificar_identificador(identificador)
    
    return f"{identificador}:{password}"

class WorkerThread(QThread):
    update_progress = pyqtSignal(int)
    update_output = pyqtSignal(str)
    update_stats = pyqtSignal(dict)
    update_skipped = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, input_file, output_file):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file

    def run(self):
        stats = {"total": 0, "valid": 0, "invalid": 0}
        with open(self.input_file, 'r', encoding='utf-8') as infile, \
             open(self.output_file, 'w', encoding='utf-8') as outfile:
            
            total_lines = sum(1 for _ in infile)
            infile.seek(0)
            
            for linea_num, linea in enumerate(infile, 1):
                linea = linea.strip()
                if not linea:
                    continue
                
                stats["total"] += 1
                resultado = procesar_linea(linea)
                if resultado:
                    outfile.write(f"{resultado}\n")
                    self.update_output.emit(f"Processed: {resultado}")
                    stats["valid"] += 1
                else:
                    self.update_skipped.emit(f"Line {linea_num}: {linea}")
                    stats["invalid"] += 1
                
                self.update_progress.emit(int((linea_num / total_lines) * 100))
                self.update_stats.emit(stats)
        
        self.finished.emit()

class ModernButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2573a7;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)

class ModernFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #2d3436;
                border-radius: 15px;
                padding: 20px;
            }
        """)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ultra Modern Combo Cleaner")
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e272e;
                color: white;
            }
            QLabel {
                font-size: 14px;
                color: #dfe6e9;
            }
            QLineEdit {
                background-color: #2d3436;
                border: 1px solid #3498db;
                padding: 8px;
                border-radius: 10px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # File selection frame
        file_frame = ModernFrame()
        file_layout = QVBoxLayout()
        file_frame.setLayout(file_layout)

        # Input file selection
        input_layout = QHBoxLayout()
        self.input_label = QLabel("Input File:")
        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText("Select input file...")
        self.input_path.setReadOnly(True)
        self.input_button = ModernButton("Browse")
        self.input_button.clicked.connect(self.select_input)
        input_layout.addWidget(self.input_label)
        input_layout.addWidget(self.input_path)
        input_layout.addWidget(self.input_button)
        file_layout.addLayout(input_layout)

        # Output file selection
        output_layout = QHBoxLayout()
        self.output_label = QLabel("Output File:")
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("Enter output file name...")
        self.output_button = ModernButton("Browse")
        self.output_button.clicked.connect(self.select_output)
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(self.output_button)
        file_layout.addLayout(output_layout)

        layout.addWidget(file_frame)

        # Start button
        self.start_button = ModernButton("Start Cleaning")
        self.start_button.clicked.connect(self.start_cleaning)
        layout.addWidget(self.start_button)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3498db;
                border-radius: 10px;
                text-align: center;
                height: 25px;
                background-color: #2d3436;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                width: 10px;
                margin: 0.5px;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Tabs for output, statistics, and skipped lines
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3498db;
                background: #2d3436;
                border-radius: 15px;
            }
            QTabBar::tab {
                background: #34495e;
                color: white;
                padding: 8px;
                margin-right: 2px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            QTabBar::tab:selected {
                background: #3498db;
            }
        """)

        # Output text area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: #2d3436;
                border: none;
                border-radius: 10px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                color: #dfe6e9;
            }
        """)

        # Statistics text area
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setStyleSheet(self.output_text.styleSheet())

        # Skipped lines text area
        self.skipped_text = QTextEdit()
        self.skipped_text.setReadOnly(True)
        self.skipped_text.setStyleSheet(self.output_text.styleSheet())

        self.tabs.addTab(self.output_text, "Output")
        self.tabs.addTab(self.stats_text, "Statistics")
        self.tabs.addTab(self.skipped_text, "Skipped Lines")

        layout.addWidget(self.tabs)

        self.load_settings()

    def select_input(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Input File", "", "Text Files (*.txt)")
        if file_name:
            self.input_path.setText(file_name)

    def select_output(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Select Output File", "", "Text Files (*.txt)")
        if file_name:
            if not file_name.lower().endswith('.txt'):
                file_name += '.txt'
            self.output_path.setText(file_name)

    def start_cleaning(self):
        if not self.input_path.text() or not self.output_path.text():
            self.output_text.append("Please select both input and output files.")
            return

        self.start_button.setEnabled(False)
        self.output_text.clear()
        self.stats_text.clear()
        self.skipped_text.clear()
        self.progress_bar.setValue(0)

        self.worker = WorkerThread(self.input_path.text(), self.output_path.text())
        self.worker.update_progress.connect(self.update_progress)
        self.worker.update_output.connect(self.update_output)
        self.worker.update_stats.connect(self.update_stats)
        self.worker.update_skipped.connect(self.update_skipped)
        self.worker.finished.connect(self.cleaning_finished)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_output(self, text):
        self.output_text.append(text)

    def update_stats(self, stats):
        self.stats_text.setText(f"""
        Total lines processed: {stats['total']}
        Valid entries: {stats['valid']}
        Invalid entries: {stats['invalid']}
        """)

    def update_skipped(self, text):
        self.skipped_text.append(text)

    def cleaning_finished(self):
        self.start_button.setEnabled(True)
        self.output_text.append("Cleaning process completed!")
        self.save_settings()

    def save_settings(self):
        settings = {
            "input_path": self.input_path.text(),
            "output_path": self.output_path.text()
        }
        with open("settings.json", "w") as f:
            json.dump(settings, f)

    def load_settings(self):
        try:
            with open("settings.json", "r") as f:
                settings = json.load(f)
            self.input_path.setText(settings.get("input_path", ""))
            self.output_path.setText(settings.get("output_path", ""))
        except FileNotFoundError:
            pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())