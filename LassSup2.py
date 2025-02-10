#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interfejs użytkownika dla programu wyceny wycinania detali laserem.
Umożliwia wczytanie pliku (HTML lub LST) i wyświetlenie pobranych danych.
"""

import sys
from pathlib import Path
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog
from data_parser import get_program_data
from get_element_data import get_element_data, Detail


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

        # Tab 1: Program Data
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
            "Nazwa detalu", "Materiał", "Grubość", "Wymiar X", "Wymiar Y",
            "Czas cięcia", "Ilość", "Koszt cięcia", "Koszt materiału",
            "Koszt detalu", "Łączny koszt"
        ]
        self.tableWidget.setColumnCount(len(headers))
        self.tableWidget.setHorizontalHeaderLabels(headers)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        # Dodajemy wszystkie elementy do głównego layoutu
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
            # Pobranie danych programu (HTML lub LST)
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
            self.populate_details_table()

    def populate_details_table(self):
        self.tableWidget.setRowCount(0)
        for detail in self.detail_list:
            row = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row)

            # Pobieramy poszczególne wartości
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
            for col, val in enumerate(values):
                item = QtWidgets.QTableWidgetItem(val)
                # Wyśrodkowanie ostatniej kolumny
                if col == 10:
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.tableWidget.setItem(row, col, item)
        self.statusBar().showMessage(f"Załadowano {len(self.detail_list)} detali.")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
