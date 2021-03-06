import sys
import time
from typing import List, Tuple
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QComboBox, QHBoxLayout, QVBoxLayout, QPushButton,
    QProgressDialog, QMessageBox, QListWidget, QListWidgetItem, QFileDialog, QLineEdit, QInputDialog
)
from PyQt5.QtCore import Qt, QModelIndex

from src.services import service, data_handler
from src.domain.entity.complex import Complex
from src.domain.values import Region
from src.ui.data_edit import DataEditView
from src.ui.checkable_combobox import CheckableComboBox


class MyApp(QWidget):
    MIN_HOUSEHOLD_COUNT = 0
    MAX_HOUSEHOLD_COUNT = 100000

    def __init__(self):
        super().__init__()
        self.is_progress_canceled = False
        self.cities = []
        self.regions = []
        self.towns = []
        self.cb_city = QComboBox()
        self.cb_region = QComboBox()
        self.cb_town = CheckableComboBox()
        self.btn_import = QPushButton('데이터수집')
        self.data: List[Tuple[Region, List[Complex]]] = []
        self.data_list_widget = QListWidget()
        self.btn_data_remove = QPushButton('선택삭제')
        self.btn_data_edit = QPushButton('자세히')
        self.btn_data_excel = QPushButton('엑셀출력(평형데이터)')
        self.btn_data_analysis_excel = QPushButton('엑셀출력(동별가격비교)')
        self.input_low_household_count = QLineEdit()
        self.set_low_hc = self.MIN_HOUSEHOLD_COUNT
        self.input_high_household_count = QLineEdit()
        self.set_high_hc = self.MAX_HOUSEHOLD_COUNT
        self.main_box = QVBoxLayout()
        self.init_handler()
        self.init_ui()

    def init_ui(self):
        self.main_box = QVBoxLayout()
        self.set_default_box()
        self.setWindowTitle('SuperRich')
        self.setGeometry(300, 300, 300, 200)

    def set_default_box(self):
        lbl_city = QLabel('시/도')
        self.cb_city.addItem('초기화중')

        lbl_region = QLabel('시/군/구')
        lbl_town = QLabel('읍/면/동')

        region_select_box = QHBoxLayout()
        region_select_box.addStretch(1)
        region_select_box.addWidget(lbl_city)
        region_select_box.addWidget(self.cb_city)
        region_select_box.addWidget(lbl_region)
        region_select_box.addWidget(self.cb_region)
        region_select_box.addWidget(lbl_town)
        region_select_box.addWidget(self.cb_town)
        region_select_box.addStretch(1)

        btn_box = QHBoxLayout()
        btn_box.addWidget(self.btn_import)

        data_group_box = QHBoxLayout()

        data_left_box = QVBoxLayout()
        data_left_box.addWidget(self.btn_data_remove)
        data_left_box.addWidget(self.btn_data_edit)
        data_left_box.addWidget(self.data_list_widget)

        data_right_box = QVBoxLayout()
        data_right_box.addWidget(QLabel('엑셀출력조건설정'))
        data_right_low_filter_box = QHBoxLayout()
        data_right_low_filter_box.addWidget(QLabel('최소세대수:'))
        data_right_low_filter_box.addWidget(self.input_low_household_count)
        data_right_high_filter_box = QHBoxLayout()
        data_right_high_filter_box.addWidget(QLabel('최대세대수:'))
        data_right_high_filter_box.addWidget(self.input_high_household_count)
        data_right_box.addLayout(data_right_low_filter_box)
        data_right_box.addLayout(data_right_high_filter_box)
        data_right_box.addWidget(self.btn_data_excel)
        data_right_box.addWidget(self.btn_data_analysis_excel)

        data_group_box.addLayout(data_left_box)
        data_group_box.addLayout(data_right_box)

        self.main_box.addLayout(region_select_box)
        self.main_box.addLayout(btn_box)
        self.main_box.addLayout(data_group_box)
        self.setLayout(self.main_box)

    def set_cities(self):
        self.cities = service.get_main_cities()
        self.cb_city.clear()
        self.cb_city.addItem('선택')
        for city in self.cities:
            self.cb_city.addItem(city.region_name)

    def init_handler(self):
        self.cb_city.activated.connect(self.city_selected)
        self.cb_region.activated.connect(self.region_selected)
        self.btn_import.clicked.connect(self.start_import)
        self.btn_data_remove.clicked.connect(self.data_remove_pushed)
        self.btn_data_edit.clicked.connect(self.data_edit_pushed)
        self.btn_data_excel.clicked.connect(self.data_excel_pushed)
        self.btn_data_analysis_excel.clicked.connect(self.data_analysis_excel_pushed)
        self.input_low_household_count.textChanged.connect(self.input_low_household_count_changed)
        self.input_high_household_count.textChanged.connect(self.input_high_household_count_changed)

    def city_selected(self):
        city_index = self.cb_city.currentIndex()
        if city_index == 0:
            self.cb_region.clear()
            self.cb_town.clear()
            return
        region_no = self.cities[city_index-1].region_no
        self.regions = service.get_regions(region_no)
        self.cb_region.clear()
        self.cb_town.clear()
        self.cb_region.addItem('선택')
        for region in self.regions:
            self.cb_region.addItem(region.region_name)

    def region_selected(self):
        region_index = self.cb_region.currentIndex()
        if region_index == 0:
            self.cb_town.clear()
            return
        region_no = self.regions[region_index-1].region_no
        self.towns = service.get_regions(region_no)
        self.cb_town.clear()
        self.cb_town.addItem('선택')
        for town in self.towns:
            self.cb_town.addItem(town.region_name)

    def data_remove_pushed(self):
        if self.data:
            row = self.data_list_widget.currentRow()
            self.data_list_widget.takeItem(row)
            self.data.pop(row)

    def data_edit_pushed(self):
        if self.data:
            row = self.data_list_widget.currentRow()
            self.data_edit_view = DataEditView(data=self.data[row][1])
            self.data_edit_view.show()

    def data_excel_pushed(self):
        if self.data:
            file_name, ok = QFileDialog.getSaveFileUrl(self, "저장할 위치를 선택하세요.")
            if ok:
                data_handler.LandXlsHandler(file_name.path() + ".xlsx", self.filtered_data()).write_raw_xls()
                QMessageBox.information(self, "성공", "엑셀추출이 완료되었습니다.", QMessageBox.Ok)

    def data_analysis_excel_pushed(self):
        if self.data:
            err_msg = ""
            while True:
                try:
                    latest_year, ok = QInputDialog.getText(self, "신축기준년도", f"{err_msg}신축기준년도를 입력하세요:")
                    if not ok:
                        return
                    latest_year = int(latest_year)
                    break
                except (ValueError, TypeError):
                    err_msg = "올바른 년도를 입력하세요.(예:2020)\n"
                    continue
            err_msg = ""
            while True:
                try:
                    sub_latest_year, ok = QInputDialog.getText(self, "준 신축기준년도", f"{err_msg}준 신축기준년도를 입력하세요:")
                    if not ok:
                        return
                    sub_latest_year = int(sub_latest_year)
                    if sub_latest_year >= latest_year:
                        err_msg = f"신축년도 기준보다 작아야합니다.(신축년도:{latest_year})\n"
                        continue
                    break
                except (ValueError, TypeError):
                    err_msg = "올바른 년도를 입력하세요.(예:2020)\n"
                    continue

            file_name, ok = QFileDialog.getSaveFileUrl(self, "저장할 위치를 선택하세요.")
            if ok:
                xls_handler = data_handler.LandXlsHandler(file_name.path() + ".xlsx", self.filtered_data())
                xls_handler.write_analysis_xls(latest_year, sub_latest_year)
                QMessageBox.information(self, "성공", "엑셀추출이 완료되었습니다.", QMessageBox.Ok)

    def input_low_household_count_changed(self, text):
        try:
            if len(text) and self.MIN_HOUSEHOLD_COUNT <= int(text) <= self.MAX_HOUSEHOLD_COUNT:
                self.set_low_hc = int(text)
            else:
                if not len(text):
                    self.set_low_hc = self.MIN_HOUSEHOLD_COUNT
                    return
                raise ValueError
        except ValueError:
            self.input_low_household_count.setText(str(self.set_low_hc))

    def input_high_household_count_changed(self, text):
        try:
            if len(text) and self.MIN_HOUSEHOLD_COUNT <= int(text) <= self.MAX_HOUSEHOLD_COUNT:
                self.set_high_hc = int(text)
            else:
                if not len(text):
                    self.set_high_hc = self.MAX_HOUSEHOLD_COUNT
                    return
                raise ValueError
        except ValueError:
            self.input_high_household_count.setText(str(self.set_high_hc))

    def start_import(self):
        selected_indices = self.cb_town.get_select_items()
        town_complex_list = []
        complex_counts = 0
        progress_title = f'선택하신 지역의 단지 리스트를 수집중입니다. 잠시만 기다려주세요.'
        progress_dialog = QProgressDialog(progress_title, "취소", 0, len(selected_indices) + 1, self)
        progress_dialog.canceled.connect(self.progress_canceled)
        progress = 0
        progress_dialog.setValue(progress)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.show()
        progress_dialog.setLabelText(progress_title)
        for town_index in selected_indices:
            if self.is_progress_canceled is True:
                self.is_progress_canceled = False
                return
            if town_index == -1 or town_index == 0:
                continue
            town = self.towns[town_index-1]
            complexes = service.get_complexes(town.region_no)
            complex_counts += len(complexes)
            if complexes:
                town_complex_list.append((town, complexes))
            progress += 1
            progress_dialog.setValue(progress)
        time.sleep(1)
        progress += 1
        progress_dialog.setValue(progress)

        progress_title = f'{self.cb_city.currentText()} {self.cb_region.currentText()} {complex_counts}개 단지의 데이터를 수집합니다.'
        progress_dialog = QProgressDialog(progress_title, "취소", 0, complex_counts+1, self) if town_complex_list else QProgressDialog("수집할 데이터가 없습니다.", "취소", 0,complex_counts+1, self)
        progress_dialog.canceled.connect(self.progress_canceled)
        progress = 0
        progress_dialog.setValue(progress)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.show()
        selected_towns = [town.region_name for town, _ in town_complex_list]
        for town, complexes in town_complex_list:
            for complex in complexes:
                if self.is_progress_canceled is True:
                    self.is_progress_canceled = False
                    return
                time.sleep(0.15)
                progress_text = f'선택지역 :{selected_towns}\n[{progress}/{complex_counts}] {town.region_name} - {complex.complex_name} 단지 데이터를 수집중입니다.'
                progress_dialog.setLabelText(progress_text)
                service.apply_price(complex)
                progress += 1
                progress_dialog.setValue(progress)
        time.sleep(1)
        progress += 1
        progress_dialog.setValue(progress)
        for town, complexes in town_complex_list:
            self.append_data((town, complexes))

    def progress_canceled(self):
        self.is_progress_canceled = True

    def append_data(self, data: Tuple[Region, List[Complex]]):
        self.data.append(data)
        item = QListWidgetItem(data[0].region_name)
        self.data_list_widget.addItem(item)

    def filtered_data(self):
        result = []
        for town, complex_list in self.data:
            filtered_cs = [c for c in complex_list if self.set_low_hc <= c.total_household_count <= self.set_high_hc]
            result.append((town, filtered_cs))
        return result


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    ex.show()
    ex.set_cities()
    sys.exit(app.exec_())
