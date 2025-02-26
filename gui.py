import sys
import os
import ntpath
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QMainWindow, QFileDialog, QTableWidgetItem
from html_parser import parse_html
from pdf_parser import parse_pdf
from config import load_config
from models import Program


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1024, 768)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setStyleSheet("font: 10pt \"MS Shell Dlg 2\";")
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")

        # Przycisk do otwierania pliku
        self.btn_Open_File = QtWidgets.QPushButton(self.tab)
        self.btn_Open_File.setGeometry(QtCore.QRect(1, 9, 121, 28))
        self.btn_Open_File.setObjectName("btn_Open_File")

        # Etykieta ścieżki programu
        self.label_Program_Path = QtWidgets.QLabel(self.tab)
        self.label_Program_Path.setGeometry(QtCore.QRect(0, 200, 135, 25))
        self.label_Program_Path.setObjectName("label_Program_Path")

        self.layoutWidget = QtWidgets.QWidget(self.tab)
        self.layoutWidget.setGeometry(QtCore.QRect(140, 0, 841, 201))
        self.layoutWidget.setObjectName("layoutWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.layoutWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")

        # GroupBox z danymi programu
        self.groupBox_ProgramDatas = QtWidgets.QGroupBox(self.layoutWidget)
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        self.groupBox_ProgramDatas.setFont(font)
        self.groupBox_ProgramDatas.setObjectName("groupBox_ProgramDatas")
        self.layoutWidget1 = QtWidgets.QWidget(self.groupBox_ProgramDatas)
        self.layoutWidget1.setGeometry(QtCore.QRect(10, 30, 381, 241))
        self.layoutWidget1.setObjectName("layoutWidget1")
        self.formLayout = QtWidgets.QFormLayout(self.layoutWidget1)
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.formLayout.setObjectName("formLayout")

        # Etykiety danych programu
        self.label_Program_Name = QtWidgets.QLabel(self.layoutWidget1)
        self.label_Program_Name.setObjectName("label_Program_Name")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_Program_Name)
        self.lbl_Program_Name_Value = QtWidgets.QLabel(self.layoutWidget1)
        self.lbl_Program_Name_Value.setObjectName("lbl_Program_Name_Value")
        self.lbl_Program_Name_Value.setHidden(True)
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.lbl_Program_Name_Value)

        self.label_Material = QtWidgets.QLabel(self.layoutWidget1)
        self.label_Material.setObjectName("label_Material")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_Material)
        self.lbl_Material_Value = QtWidgets.QLabel(self.layoutWidget1)
        self.lbl_Material_Value.setObjectName("lbl_Material_Value")
        self.lbl_Material_Value.setHidden(True)
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.lbl_Material_Value)

        self.label_Thicknes = QtWidgets.QLabel(self.layoutWidget1)
        self.label_Thicknes.setObjectName("label_Thicknes")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_Thicknes)
        self.lbl_Thicknes_Value = QtWidgets.QLabel(self.layoutWidget1)
        self.lbl_Thicknes_Value.setObjectName("lbl_Thicknes_Value")
        self.lbl_Thicknes_Value.setHidden(True)
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.lbl_Thicknes_Value)

        self.label_Program_Time = QtWidgets.QLabel(self.layoutWidget1)
        self.label_Program_Time.setObjectName("label_Program_Time")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.label_Program_Time)
        self.lbl_Program_Time_Value = QtWidgets.QLabel(self.layoutWidget1)
        self.lbl_Program_Time_Value.setObjectName("lbl_Program_Time_Value")
        self.lbl_Program_Time_Value.setHidden(True)
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.lbl_Program_Time_Value)

        self.label_Program_Quantity = QtWidgets.QLabel(self.layoutWidget1)
        self.label_Program_Quantity.setObjectName("label_Program_Quantity")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.label_Program_Quantity)
        self.lbl_Program_Quantity_Value = QtWidgets.QLabel(self.layoutWidget1)
        self.lbl_Program_Quantity_Value.setObjectName("lbl_Program_Quantity_Value")
        self.lbl_Program_Quantity_Value.setHidden(True)
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.lbl_Program_Quantity_Value)

        self.horizontalLayout.addWidget(self.groupBox_ProgramDatas)

        # GroupBox wyceny – pozostawiony jak w oryginale
        self.groupBox_Pricing = QtWidgets.QGroupBox(self.layoutWidget)
        self.groupBox_Pricing.setObjectName("groupBox_Pricing")
        self.horizontalLayout.addWidget(self.groupBox_Pricing)

        self.lbl_Program_Path_Value = QtWidgets.QLabel(self.tab)
        self.lbl_Program_Path_Value.setGeometry(QtCore.QRect(140, 200, 900, 25))
        self.lbl_Program_Path_Value.setObjectName("lbl_Program_Path_Value")
        self.lbl_Program_Path_Value.setHidden(True)

        # Tabela detali – 12 kolumn (pierwsza to rysunek detalu)
        self.tableWidget = QtWidgets.QTableWidget(self.tab)
        self.tableWidget.setGeometry(QtCore.QRect(10, 310, 1024, 400))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(10)
        sizePolicy.setVerticalStretch(10)
        self.tableWidget.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setBold(True)
        self.tableWidget.setFont(font)
        self.tableWidget.setTabletTracking(True)
        self.tableWidget.setAcceptDrops(True)
        self.tableWidget.setAutoFillBackground(True)
        self.tableWidget.setFrameShadow(QtWidgets.QFrame.Raised)
        self.tableWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.tableWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.tableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContentsOnFirstShow)
        self.tableWidget.setGridStyle(QtCore.Qt.SolidLine)
        # Ustawienie tymczasowej liczby wierszy; przed wypełnieniem tabela zostanie wyczyszczona
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(12)
        self.tableWidget.setObjectName("tableWidget")
        headers = ["Rysunek", "Nazwa detalu", "Materiał", "Grubość", "Wymiar X", "Wymiar Y",
                   "Czas cięcia", "Ilość", "Koszt cięcia", "Koszt materiału", "Koszt detalu", "Całkowity koszt"]
        for i, header in enumerate(headers):
            item = QtWidgets.QTableWidgetItem()
            item.setText(header)
            self.tableWidget.setHorizontalHeaderItem(i, item)

        # Ustawienie, aby kolumny automatycznie rozciągały się do szerokości okna
        self.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.tabWidget.addTab(self.tab_2, "")
        self.verticalLayout.addWidget(self.tabWidget)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1024, 26))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QtWidgets.QToolBar(MainWindow)
        self.toolBar.setObjectName("toolBar")
        MainWindow.addToolBar(QtCore.Qt.BottomToolBarArea, self.toolBar)
        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)

        # Połączenie sygnału przycisku
        self.btn_Open_File.clicked.connect(self.OpenFileDialog)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        # Inicjalizacja zmiennych
        self.current_program = None
        self.config = load_config()

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "LassSup"))
        self.btn_Open_File.setText(_translate("MainWindow", "Wczytaj plik"))
        self.label_Program_Path.setText(_translate("MainWindow", "Ścieżka programu:"))
        self.groupBox_ProgramDatas.setTitle(_translate("MainWindow", "Dane programu:"))
        self.label_Program_Name.setText(_translate("MainWindow", "Nazwa programu:"))
        self.lbl_Program_Name_Value.setText(_translate("MainWindow", "TextLabel"))
        self.label_Material.setText(_translate("MainWindow", "Materiał:"))
        self.lbl_Material_Value.setText(_translate("MainWindow", "TextLabel"))
        self.label_Thicknes.setText(_translate("MainWindow", "Grubość:"))
        self.lbl_Thicknes_Value.setText(_translate("MainWindow", "TextLabel"))
        self.label_Program_Time.setText(_translate("MainWindow", "Czas trwania programu:"))
        self.lbl_Program_Time_Value.setText(_translate("MainWindow", "TextLabel"))
        self.label_Program_Quantity.setText(_translate("MainWindow", "Ilość powtórzeń:"))
        self.lbl_Program_Quantity_Value.setText(_translate("MainWindow", "TextLabel"))
        self.groupBox_Pricing.setTitle(_translate("MainWindow", "Wycena:"))
        self.lbl_Program_Path_Value.setText(_translate("MainWindow", "TextLabel"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "Tab 1"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "Tab 2"))
        self.toolBar.setWindowTitle(_translate("MainWindow", "toolBar"))

    def OpenFileDialog(self):
        home_dir = os.path.expanduser("~")
        fname, _ = QFileDialog.getOpenFileName(None, 'Otwórz plik', home_dir, 'Pliki HTML/PDF (*.html *.pdf)')
        if fname:
            # Czyszczenie tabeli przy każdym nowym wczytaniu pliku
            self.tableWidget.setRowCount(0)
            self.lbl_Program_Path_Value.setHidden(False)
            self.lbl_Program_Path_Value.setText(fname)
            ext = os.path.splitext(fname)[1].lower()
            if ext == ".html":
                self.current_program = parse_html(fname)
            elif ext == ".pdf":
                self.current_program = parse_pdf(fname)
            else:
                return
            self.lbl_Program_Name_Value.setHidden(False)
            self.lbl_Program_Name_Value.setText(self.current_program.name)
            self.lbl_Material_Value.setHidden(False)
            self.lbl_Material_Value.setText(self.current_program.material)
            self.lbl_Thicknes_Value.setHidden(False)
            self.lbl_Thicknes_Value.setText(f"{self.current_program.thicknes} mm")
            self.lbl_Program_Time_Value.setHidden(False)
            self.lbl_Program_Time_Value.setText(self.current_program.machine_time)
            self.lbl_Program_Quantity_Value.setHidden(False)
            self.lbl_Program_Quantity_Value.setText(str(self.current_program.program_counts))
            self.populate_table()

    def populate_table(self):
        if not self.current_program:
            return
        details = self.current_program.details
        self.tableWidget.setRowCount(len(details))
        for row, detail in enumerate(details):
            # Kolumna 0: Rysunek (jeśli dostępny)
            item = QTableWidgetItem()
            if detail.image_path and os.path.exists(detail.image_path):
                icon = QtGui.QIcon(detail.image_path)
                item.setIcon(icon)
            self.tableWidget.setItem(row, 0, item)
            # Kolumna 1: Nazwa detalu
            self.tableWidget.setItem(row, 1, QTableWidgetItem(detail.name))
            # Kolumna 2: Materiał (przyjmujemy ten sam co w programie)
            self.tableWidget.setItem(row, 2, QTableWidgetItem(self.current_program.material))
            # Kolumna 3: Grubość (program)
            self.tableWidget.setItem(row, 3, QTableWidgetItem(f"{self.current_program.thicknes}"))
            # Kolumna 4 i 5: Wymiary X i Y – rozdzielone ze stringa, np. "60.000 x 78.000 mm"
            dims = detail.dimensions.replace("mm", "").strip().split("x")
            if len(dims) >= 2:
                dim_x = dims[0].strip()
                dim_y = dims[1].strip()
            else:
                dim_x = dim_y = ""
            self.tableWidget.setItem(row, 4, QTableWidgetItem(dim_x))
            self.tableWidget.setItem(row, 5, QTableWidgetItem(dim_y))
            # Kolumna 6: Czas cięcia
            self.tableWidget.setItem(row, 6, QTableWidgetItem(f"{detail.cut_time}"))
            # Kolumna 7: Ilość
            self.tableWidget.setItem(row, 7, QTableWidgetItem(str(detail.quantity)))
            # Kolumna 8: Koszt cięcia
            cutting_cost = detail.cutting_cost(self.config)
            self.tableWidget.setItem(row, 8, QTableWidgetItem(f"{cutting_cost}"))
            # Kolumna 9: Koszt materiału
            material_cost = detail.material_cost(self.config)
            self.tableWidget.setItem(row, 9, QTableWidgetItem(f"{material_cost}"))
            # Kolumna 10: Koszt detalu (jednej sztuki)
            total_cost = detail.total_cost(self.config)
            self.tableWidget.setItem(row, 10, QTableWidgetItem(f"{total_cost}"))
            # Kolumna 11: Całkowity koszt (koszt detalu * ilość)
            total_cost_quantity = total_cost * detail.quantity
            self.tableWidget.setItem(row, 11, QTableWidgetItem(f"{total_cost_quantity}"))
        self.tableWidget.resizeColumnsToContents()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
