"""
Główny moduł interfejsu użytkownika dla programu wyceny detali laserowych.
Umożliwia wczytanie pliku (HTML lub LST) i prezentację danych programu oraz detali.
"""

import os
import sys
from pathlib import Path
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog
from parser_dispatcher import get_program_data
from detail_data import get_element_data
import glob


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.program_data = None
        self.detail_list = []
        self.setup_ui()

    def setup_ui(self):
        self.setObjectName("MainWindow")
        self.resize(1024, 768)
        self.centralwidget = QtWidgets.QWidget(self)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setStyleSheet("font: 10pt 'MS Shell Dlg 2';")

        # Tab 1: Program Data and Details Table
        self.tab1 = QtWidgets.QWidget()
        self.btn_Open_File = QtWidgets.QPushButton(self.tab1)
        self.btn_Open_File.setGeometry(QtCore.QRect(10, 10, 121, 28))
        self.btn_Open_File.setText("Wczytaj plik")
        self.btn_Open_File.clicked.connect(self.open_file_dialog)

        self.label_Program_Path = QtWidgets.QLabel(self.tab1)
        self.label_Program_Path.setGeometry(QtCore.QRect(10, 50, 135, 25))
        self.label_Program_Path.setText("Ścieżka programu:")

        self.lbl_Program_Path_Value = QtWidgets.QLabel(self.tab1)
        self.lbl_Program_Path_Value.setGeometry(QtCore.QRect(150, 50, 800, 25))
        self.lbl_Program_Path_Value.setHidden(True)

        # GroupBox: Dane programu
        self.groupBox_ProgramDatas = QtWidgets.QGroupBox(self.tab1)
        self.groupBox_ProgramDatas.setGeometry(QtCore.QRect(10, 90, 400, 160))
        self.groupBox_ProgramDatas.setTitle("Dane programu:")

        self.formLayoutWidget = QtWidgets.QWidget(self.groupBox_ProgramDatas)
        self.formLayoutWidget.setGeometry(QtCore.QRect(10, 30, 380, 120))
        self.formLayout = QtWidgets.QFormLayout(self.formLayoutWidget)
        self.formLayout.setContentsMargins(0, 0, 0, 0)

        self.label_Program_Name = QtWidgets.QLabel("Nazwa programu:")
        self.lbl_Program_Name_Value = QtWidgets.QLabel("")
        self.lbl_Program_Name_Value.setHidden(True)
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_Program_Name)
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.lbl_Program_Name_Value)

        self.label_Material = QtWidgets.QLabel("Materiał:")
        self.lbl_Material_Value = QtWidgets.QLabel("")
        self.lbl_Material_Value.setHidden(True)
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_Material)
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.lbl_Material_Value)

        self.label_Thicknes = QtWidgets.QLabel("Grubość:")
        self.lbl_Thicknes_Value = QtWidgets.QLabel("")
        self.lbl_Thicknes_Value.setHidden(True)
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_Thicknes)
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.lbl_Thicknes_Value)

        self.label_Program_Time = QtWidgets.QLabel("Czas trwania programu:")
        self.lbl_Program_Time_Value = QtWidgets.QLabel("")
        self.lbl_Program_Time_Value.setHidden(True)
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.label_Program_Time)
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.lbl_Program_Time_Value)

        self.label_Program_Quantity = QtWidgets.QLabel("Ilość powtórzeń:")
        self.lbl_Program_Quantity_Value = QtWidgets.QLabel("")
        self.lbl_Program_Quantity_Value.setHidden(True)
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.label_Program_Quantity)
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.lbl_Program_Quantity_Value)

        # GroupBox: Tabela detali
        self.groupBox_Details = QtWidgets.QGroupBox(self.tab1)
        self.groupBox_Details.setGeometry(QtCore.QRect(10, 260, 1000, 400))
        self.groupBox_Details.setTitle("Detale / Wycena:")
        self.tableWidget = QtWidgets.QTableWidget(self.groupBox_Details)
        self.tableWidget.setGeometry(QtCore.QRect(10, 30, 980, 360))
        headers = [
            "Rysunek detalu", "Nazwa detalu", "Materiał", "Grubość", "Wymiar X", "Wymiar Y",
            "Czas cięcia", "Ilość", "Koszt cięcia", "Koszt materiału",
            "Koszt detalu", "Łączny koszt"
        ]
        self.tableWidget.setColumnCount(len(headers))
        self.tableWidget.setHorizontalHeaderLabels(headers)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        self.tabWidget.addTab(self.tab1, "Program Data")
        self.verticalLayout.addWidget(self.tabWidget)
        self.setCentralWidget(self.centralwidget)

        self.statusBar().showMessage("Gotowy")

    def open_file_dialog(self):
        home_dir = str(Path.home())
        file_filter = "HTML files (*.html);;LST files (*.lst)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Otwórz plik", home_dir, file_filter)
        if file_path:
            self.lbl_Program_Path_Value.setHidden(False)
            self.lbl_Program_Path_Value.setText(file_path)
            self.program_data = get_program_data(file_path)
            self.lbl_Program_Name_Value.setHidden(False)
            self.lbl_Program_Name_Value.setText(self.program_data.program_name)
            self.lbl_Material_Value.setHidden(False)
            self.lbl_Material_Value.setText(self.program_data.material)
            self.lbl_Thicknes_Value.setHidden(False)
            self.lbl_Thicknes_Value.setText(f"{self.program_data.thickness} mm")
            self.lbl_Program_Time_Value.setHidden(False)
            self.lbl_Program_Time_Value.setText(self.program_data.program_time)
            self.lbl_Program_Quantity_Value.setHidden(False)
            self.lbl_Program_Quantity_Value.setText(self.program_data.program_counts)

            # Pobranie danych detali i uzupełnienie tabeli
            self.detail_list = get_element_data(file_path)
            print("Pobrano detale:", len(self.detail_list))
            if not self.detail_list:
                print("UWAGA: Lista detali jest pusta!")

            # Jeśli wczytano plik HTML, przypisujemy ścieżki do rysunków bmp
            if file_path.lower().endswith(".html"):
                base_dir = os.path.dirname(file_path)
                for detail in self.detail_list:
                    # Upewnij się, że nazwy są bez zbędnych spacji
                    prog_name = self.program_data.program_name.strip()
                    det_name = detail.name.strip()
                    # Wzorzec: nazwa-programu_nazwa-detalu*.bmp
                    pattern = os.path.join(base_dir, f"{prog_name}_{det_name}*.bmp")
                    print("Szukam plików według wzorca:", pattern)
                    matches = glob.glob(pattern)
                    if matches:
                        print("Znaleziono:", matches)
                        detail.drawing_path = matches[0]
                    else:
                        print("Nie znaleziono plików dla wzorca:", pattern)
                        detail.drawing_path = None

            self.populate_details_table()
            self.statusBar().showMessage(f"Załadowano {len(self.detail_list)} detali.")


            # # Jeżeli wczytany plik to LST – wywołaj funkcję ekstrakcji plików GEO
            # if file_path.lower().endswith(".lst"):
            #     # Ustal katalog wyjściowy – np. w tym samym folderze co LST lub inny (możesz dodać wybór w GUI)
            #     output_dir = os.path.join(os.path.dirname(file_path), "geo_extracted")
            #     import os
            #     os.makedirs(output_dir, exist_ok=True)
            #     # Importujemy funkcję z naszego modułu lst_geo_extractor
            #     from lst_geo_extractor import extract_geo_files
            #     extract_geo_files(file_path, output_dir)
            #     self.statusBar().showMessage(
            #         f"Załadowano {len(self.detail_list)} detali. Pliki GEO zapisane w {output_dir}")

    def populate_details_table(self):
        self.tableWidget.setRowCount(0)
        for detail in self.detail_list:
            row = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row)

            # Kolumna 0: Rysunek detalu
            item_drawing = QtWidgets.QTableWidgetItem()
            drawing_path = getattr(detail, "drawing_path", None)
            if drawing_path and os.path.exists(drawing_path):
                try:
                    pixmap = QtGui.QPixmap(drawing_path)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(64, 64, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                        item_drawing.setIcon(QtGui.QIcon(scaled_pixmap))
                    else:
                        item_drawing.setText("Brak rysunku")
                except Exception as e:
                    print("Błąd podczas wczytywania obrazka:", e)
                    item_drawing.setText("Błąd wczytywania")
            else:
                item_drawing.setText("Brak rysunku")
            self.tableWidget.setItem(row, 0, item_drawing)

            # Pozostałe kolumny (przesunięte o 1)
            name = detail.name
            material = detail.material
            thickness = f"{detail.thickness} mm"
            dimX = f"{detail.dimension_x} mm"
            dimY = f"{detail.dimension_y} mm"
            cut_time = f"{detail.element_cut_time} min"
            quantity = str(detail.quantity)
            cost_cut = f"{detail.element_cut_cost()} zł"
            cost_material = f"{detail.element_material_cost()} zł"
            cost_detail = f"{detail.total_detail_cost()} zł"
            total_cost = f"{detail.quantity_total_cost()} zł"

            values = [name, material, thickness, dimX, dimY, cut_time,
                      quantity, cost_cut, cost_material, cost_detail, total_cost]
            for col, val in enumerate(values, start=1):
                item = QtWidgets.QTableWidgetItem(val)
                if col == 11:  # przykładowe wyśrodkowanie ostatniej kolumny
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.tableWidget.setItem(row, col, item)
        self.statusBar().showMessage(f"Załadowano {len(self.detail_list)} detali.")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
