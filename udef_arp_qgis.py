# -*- coding: utf-8 -*-
"""
/***************************************************************************
UDef-ARP Plugin for QGIS

A modified version of the UDef-ARP repository [https://github.com/ClarkCGA/UDef-ARP]
that enables the tool to be fully integrated into QGIS as a plugin

Created using the Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-04-01
        copyright            : (C) 2024 by Eli Simonson
        email                : esimonson@clarku.edu
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

# Import libraries
import sys
import os
import os.path
from pathlib import Path, PureWindowsPath

from osgeo import gdal
import numpy as np

# QGIS imports
from qgis.core import (
    QgsMessageLog, QgsProject, Qgis, QgsMapLayerProxyModel,
    QgsRasterLayer, QgsVectorLayer
)
from qgis.PyQt.QtCore import (
    QSettings, QTranslator, QCoreApplication, QUrl, Qt
)
from qgis.PyQt.QtGui import (
    QFontDatabase, QIcon, QFont, QDesktopServices, QColor
)
from qgis.PyQt.QtWidgets import (
    QAction, QFileDialog, QApplication, QWidget, QProgressDialog, QMessageBox
)
from qgis.PyQt import uic, QtWidgets
from qgis.gui import QgsMapLayerComboBox

# Custom imports
from .resources import *
from .allocation_tool import AllocationTool
from .vulnerability_map import VulnerabilityMap
from .model_evaluation import ModelEvaluation

# GDAL exceptions
gdal.UseExceptions()

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS0, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'data\\intro_screen.ui'))
FORM_CLASS1, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'data\\rmt_fit_cal_screen_Dev.ui'))
FORM_CLASS2, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'data\\at_fit_cal_screen_Dev.ui'))
FORM_CLASS3, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'data\\mct_fit_cal_screen_Dev.ui'))
FORM_CLASS4, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'data\\rmt_pre_cnf_screen_Dev.ui'))
FORM_CLASS5, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'data\\at_pre_cnf_screen_Dev.ui'))
FORM_CLASS6, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'data\\mct_pre_cnf_screen_Dev.ui'))
FORM_CLASS7, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'data\\rmt_fit_hrp_screen_Dev.ui'))
FORM_CLASS8, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'data\\at_fit_hrp_screen_Dev.ui'))
FORM_CLASS9, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'data\\rmt_pre_vp_screen_Dev.ui'))
FORM_CLASS10, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'data\\at_pre_vp_screen_Dev.ui'))

# Define the style sheet for the combo box
style_sheet = """
    /* Set text color to black */
    color: black;
    
    /* Set background color to white and border color to black */
    background-color: white;
    border: 1px solid #c0c0c0; /* light grey border color */
    
    /* Set hover color to blue */
    selection-background-color: #add8e6;
"""

######################################################################################################

class IntroScreen(QtWidgets.QDialog, FORM_CLASS0):
    def __init__(self, parent=None):
        """Constructor."""
        super(IntroScreen, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS0.
        self.setupUi(self)
        # Connect functions to the UI
        self.connect_signals()

    def connect_signals(self):
        self.Fit_Cal_button.clicked.connect(self.gotofitcal)
        self.Pre_Cnf_button.clicked.connect(self.gotoprecnf)
        self.Fit_Hrp_button.clicked.connect(self.gotofithrp)
        self.Pre_VP_button.clicked.connect(self.gotoprevp)
        self.doc_button.clicked.connect(self.openDocument)
        
    def gotofitcal(self):
        rmt_fit_cal = RMT_FIT_CAL_SCREEN()
        stacked_widget.addWidget(rmt_fit_cal)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def gotoprecnf(self):
        rmt_pre_cnf = RMT_PRE_CNF_SCREEN()
        stacked_widget.addWidget(rmt_pre_cnf)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def gotofithrp(self):
        rmt_fit_hrp = RMT_FIT_HRP_SCREEN()
        stacked_widget.addWidget(rmt_fit_hrp)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def gotoprevp(self):
        rmt_pre_vp = RMT_PRE_VP_SCREEN()
        stacked_widget.addWidget(rmt_pre_vp)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def openDocument(self):
        pdf_path = os.path.join(os.path.dirname(__file__), 'doc\\UDef-ARP_Introduction.pdf')
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

######################################################################################################
        
class RMT_FIT_CAL_SCREEN(QtWidgets.QDialog, FORM_CLASS1):
    def __init__(self, parent=None):
        """Constructor."""
        super(RMT_FIT_CAL_SCREEN, self).__init__(parent)
        # Store the initial directory path
        self.initial_directory = os.getcwd()
        # Set up the user interface from Designer through FORM_CLASS1.
        self.setupUi(self)
        # Workspace handling
        if central_data_store.directory is not None and self.folder_entry is not None:
            self.directory = central_data_store.directory
            self.folder_entry.setText(str(central_data_store.directory))
        if central_data_store.directory is not None and self.folder_entry_2 is not None:
            self.directory_2 = central_data_store.directory
            self.folder_entry_2.setText(str(central_data_store.directory))
            
        self.AT_button2.clicked.connect(self.gotoat2)
        self.Intro_button2.clicked.connect(self.gotointro2)
        self.MCT_button2.clicked.connect(self.gotomct2)

        # Tab 1 Widgets
        self.doc_button = self.tab1.findChild(QWidget, "doc_button")
        self.select_folder_button = self.tab1.findChild(QWidget, "select_folder_button")
        self.deforestation_hrp_button = self.tab1.findChild(QWidget, "deforestation_hrp_button")
        self.mask_button = self.tab1.findChild(QWidget, "mask_button")
        self.fd_button = self.tab1.findChild(QWidget, "fd_button")
        self.calculate_button2 = self.tab1.findChild(QWidget, "calculate_button2")
        self.ok_button2 = self.tab1.findChild(QWidget, "ok_button2")
        
        # Tab 2 Widgets
        self.doc_button_2 = self.tab2.findChild(QWidget, "doc_button_2")
        self.select_folder_button_2 = self.tab2.findChild(QWidget, "select_folder_button_2")
        self.mask_button_2 = self.tab2.findChild(QWidget, "mask_button_2")
        self.fmask_button_2 = self.tab2.findChild(QWidget, "fmask_button_2")
        self.fd_button_2 = self.tab2.findChild(QWidget, "fd_button_2")
        self.ok_button2_2 = self.tab2.findChild(QWidget, "ok_button2_2")

        # Connect Tab 1 Widgets to Functions
        self.doc_button.clicked.connect(self.openDocument)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.deforestation_hrp_button.clicked.connect(lambda: self.selectRaster(self.deforestation_hrp_entry, 'Map of Deforestation in the HRP'))
        self.mask_button.clicked.connect(lambda: self.selectRaster(self.mask_entry, 'Mask of Study Area'))
        self.fd_button.clicked.connect(lambda: self.selectRaster(self.comboBox, 'Map of Distance from the Forest Edge in CAL'))
        self.calculate_button2.clicked.connect(self.process_data2_nrt)
        self.ok_button2.clicked.connect(self.process_data2)

        # Connect Tab 2 Widgets to Functions
        self.doc_button_2.clicked.connect(self.openDocument_2)
        self.select_folder_button_2.clicked.connect(self.select_working_directory_2)
        self.mask_button_2.clicked.connect(lambda: self.selectRaster(self.mask_entry_2, 'Mask of Study Area'))
        self.fmask_button_2.clicked.connect(lambda: self.selectRaster(self.fmask_entry_2, 'Mask of Forest Area'))
        self.fd_button_2.clicked.connect(lambda: self.selectRaster(self.in_fn_entry_2, 'Map of Empirical transition potential for CAL'))
        self.ok_button2_2.clicked.connect(self.process_data2_2)

        # Create Class Attributes
        self.vulnerability_map = VulnerabilityMap()
        self.vulnerability_map.progress_updated.connect(self.update_progress)
        self.directory = None
        self.in_fn = None
        self.deforestation_hrp = None
        self.mask = None
        self.NRT = None
        if central_data_store.NRT is not None:
            self.nrt_entry.setText(str(central_data_store.NRT))
        self.n_classes = None
        self.out_fn = None
        self.out_fn_entry.setPlaceholderText('e.g., Acre_Vulnerability_CAL.tif')
        self.directory_2 = None
        self.mask_2 = None
        self.fmask_2 = None
        self.in_fn_2 = None
        self.out_fn_2 = None
        self.n_classes_2 = None
        self.out_fn_entry_2.setPlaceholderText('e.g., Acre_Vulnerability_CAL.tif')

        # Provide intitial settings for each comboBox
        self.comboBox.setStyleSheet(style_sheet)
        self.deforestation_hrp_entry.setStyleSheet(style_sheet)
        self.mask_entry.setStyleSheet(style_sheet)
        self.mask_entry_2.setStyleSheet(style_sheet)
        self.fmask_entry_2.setStyleSheet(style_sheet)
        self.in_fn_entry_2.setStyleSheet(style_sheet)

        self.comboBox.setCurrentIndex(-1)
        self.deforestation_hrp_entry.setCurrentIndex(-1)
        self.mask_entry.setCurrentIndex(-1)
        self.mask_entry_2.setCurrentIndex(-1)
        self.fmask_entry_2.setCurrentIndex(-1)
        self.in_fn_entry_2.setCurrentIndex(-1)
        
        self.comboBox.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.deforestation_hrp_entry.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.mask_entry.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.mask_entry_2.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.fmask_entry_2.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.in_fn_entry_2.setFilters(QgsMapLayerProxyModel.RasterLayer)

    def gotoat2(self):
        os.chdir(self.initial_directory)
        at2 = AT_FIT_CAL_SCREEN()
        stacked_widget.addWidget(at2)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def gotomct2(self):
        os.chdir(self.initial_directory)
        mct2 = MCT_FIT_CAL_SCREEN()
        stacked_widget.addWidget(mct2)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def gotointro2(self):
        os.chdir(self.initial_directory)
        intro2 = IntroScreen()
        stacked_widget.addWidget(intro2)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def openDocument(self):
        pdf_path = os.path.join(os.path.dirname(__file__), "doc\\TestFitVM.pdf")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def openDocument_2(self):
        pdf_path = os.path.join(os.path.dirname(__file__), "doc\\TestFitVM.pdf")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path = Path(data_folder)
        self.directory = str(data_folder_path)
        self.folder_entry.setText(self.directory)
        self.folder_entry_2.setText(self.directory)
        central_data_store.directory = self.directory

    def selectRaster(self, comboBox, string):
        """
        Opening the raster layer file and adding the path to the combobox
        on end of the list with comboBox items.

        :param comboBox: Qt combobox.
        :type comboBox: QComboBox
        """
        rast_path = QFileDialog.getOpenFileName(self, string)
        index = comboBox.currentIndex()
        comboBox.setAdditionalItems([rast_path[0]])
        ind = comboBox.count() - 1
        comboBox.setCurrentIndex(ind)

    def select_working_directory_2(self):
        data_folder_2 = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path_2 = Path(data_folder_2)
        self.directory_2 = str(data_folder_path_2)
        self.folder_entry_2.setText(self.directory_2)
        self.folder_entry.setText(self.directory_2)
        central_data_store.directory = self.directory_2

    def get_image_resolution(self,image):
        # Set up a GDAL dataset
        in_ds = gdal.Open(image)
        # Set up a GDAL band
        P = in_ds.GetGeoTransform()[1]
        # Create Numpy Array1
        return P

    def get_image_dimensions(self, image):
        dataset = gdal.Open(image)
        cols = dataset.RasterXSize
        rows = dataset.RasterYSize
        return rows, cols

    def get_image_datatype(self, image):
        in_ds = gdal.Open(image)
        in_band = in_ds.GetRasterBand(1)
        datatype = gdal.GetDataTypeName(in_band.DataType)
        return datatype

    def get_image_max_min(self, image):
        in_ds = gdal.Open(image)
        in_band = in_ds.GetRasterBand(1)
        min, max= in_band.ComputeRasterMinMax()
        return min, max

    def find_unique_values(self, arr, limit=2):
        unique_values = set()
        for value in np.nditer(arr):
            unique_values.add(value.item())
            if len(unique_values) > limit:
                return False
        return True

    def check_binary_map(self, in_fn):
        '''
        Check if input image is binary map
        :param in_fn: input image
        :return: True if the file is a binary map, False otherwise
        '''
        file_extension = in_fn.split('.')[-1].lower()
        file_name, _ = os.path.splitext(in_fn)
        if file_extension == 'rst':
            with open(file_name + '.rdc', 'r') as read_file:
                rdc_content = read_file.read().lower()
                byte_or_integer_binary = "data type   : byte" in rdc_content or (
                        "data type   : integer" in rdc_content and "min. value  : 0" in rdc_content and "max. value  : 1" in rdc_content)
                float_binary = "data type   : real" in rdc_content and "min. value  : 0.0000000" in rdc_content and "max. value  : 1.0000000" in rdc_content
        elif file_extension == 'tif':
            datatype = self.get_image_datatype(in_fn)
            min_val, max_val = self.get_image_max_min(in_fn)
            byte_or_integer_binary = datatype in ['Byte', 'CInt16', 'CInt32', 'Int16', 'Int32', 'UInt16',
                                                      'UInt32'] and max_val == 1 and min_val == 0
            float_binary = datatype in ['Float32', 'Float64', 'CFloat32', 'CFloat64'] and max_val == 1.0000000 and min_val == 0.0000000

        if byte_or_integer_binary or (float_binary):
            # For float_binary, use find_unique_values function to check if data only have two unique values [0.0000000, 1.0000000].
            if float_binary:
                in_ds = gdal.Open(in_fn)
                in_band = in_ds.GetRasterBand(1)
                arr = in_band.ReadAsArray()
                # If more than two unique values are found, it's not a binary map, return False.
                if not self.find_unique_values(arr, 2):
                    return False
            # Binary map: byte_or_integer_binary or float_binary with two unique values [0.0000000, 1.0000000], it returns True.
            return True
        # For any other scenario, it returns False.
        return False

    def process_data2_nrt(self):
        try: 
            self.in_fn = self.comboBox.currentLayer().source()
        except Exception:
            self.in_fn = self.comboBox.currentText() 
        try:
            self.deforestation_hrp = self.deforestation_hrp_entry.currentLayer().source()
        except Exception:
            self.deforestation_hrp = self.deforestation_hrp_entry.currentText()
        try:
            self.mask = self.mask_entry.currentLayer().source()
        except Exception:
            self.mask = self.mask_entry.currentText()
            
        images = [self.in_fn, self.deforestation_hrp, self.mask]

        # Check if all images have the same resolution
        resolutions = [self.get_image_resolution(img) for img in images]
        if len(set(resolutions)) != 1:
            QMessageBox.critical(None, "Error", "All the input raster images must have the same spatial resolution!")
            return

        directory = self.folder_entry.text()

        # Check if all images have the same number of rows and columns
        dimensions = [self.get_image_dimensions(img) for img in images]
        if len(set(dimensions)) != 1:
            QMessageBox.critical(None, "Error",
                                 "All the input raster images must have the same number of rows and columns!")
            return

        if not self.in_fn or not self.deforestation_hrp or not self.mask:
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        if not self.check_binary_map(self.deforestation_hrp):
            QMessageBox.critical(None, "Error",
                                 "'MAP OF DEFORESTATION IN THE HRP' must be a binary map (0 and 1) where the 1’s indicate deforestation.")
            return

        if not self.check_binary_map(self.mask):
            QMessageBox.critical(None, "Error",
                                 "'MASK OF THE JURISDICTION' must be a binary map (0 and 1) where the 1’s indicate jurisdiction.")
            return

        # Show "Processing" message
        processing_message = "Calculating NRT..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Calculating")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.vulnerability_map.set_working_directory(directory)
            NRT = self.vulnerability_map.nrt_calculation(self.in_fn, self.deforestation_hrp, self.mask)
            # Update the central data store
            central_data_store.NRT = NRT

            QMessageBox.information(self, "Processing Completed", f"Processing completed!\nNRT is: {NRT}")

            self.nrt_entry.setText(str(NRT))

            self.progressDialog.close()

        except Exception as e:
            self.progressDialog.close()
            QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def process_data2(self):
        try: 
            self.in_fn = self.comboBox.currentLayer().source()
        except Exception:
            self.in_fn = self.comboBox.currentText()
            
        if not self.in_fn:
            QMessageBox.critical(self, "Error", "Please select  the input file!")
            return

        NRT = self.nrt_entry.text()
        if not NRT:
            QMessageBox.critical(self, "Error", "Please enter the NRT value!")
            return
        try:
            self.NRT = int(NRT)
            if (self.NRT <= 0):
                QMessageBox.critical(self, "Error", "NRT value should be larger than 0!")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "NRT value should be a valid number!")
            return

        directory = self.folder_entry.text()

        n_classes = int(29)
        if not n_classes:
            QMessageBox.critical(self, "Error", "Please enter the number of classes!")
            return
        try:
            self.n_classes = int(n_classes)
            if (self.n_classes <= 0):
                QMessageBox.critical(self, "Error", "Number of classes should be larger than 0!")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "Number of classes value should be a valid number!")
            return

        out_fn = self.out_fn_entry.text()
        if not out_fn:
            QMessageBox.critical(self, "Error", "Please enter the name of Vulnerability Map in CAL!")
            return

        # Check if the out_fn has the correct file extension
        if not (out_fn.endswith('.tif') or out_fn.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Vulnerability Map in CAL!")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.vulnerability_map.set_working_directory(directory)
            mask_arr = self.vulnerability_map.geometric_classification(self.in_fn, NRT, n_classes)
            self.vulnerability_map.array_to_image(self.in_fn, out_fn, mask_arr, gdal.GDT_Int16, -1)
            self.vulnerability_map.replace_ref_system(self.in_fn, out_fn)

            if self.checkBox.isChecked():
                basename = os.path.splitext(os.path.basename(out_fn))[0]
                layer = QgsRasterLayer(out_fn, basename)
                layer.setDataSource(os.path.join(directory, out_fn), basename, 'gdal')
                QgsProject.instance().addMapLayer(layer)

            QMessageBox.information(self, "Processing Completed", "Processing completed!")

            self.progressDialog.close()

        except Exception as e:
            self.progressDialog.close()
            QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")


    def process_data2_2(self):
        try: 
            self.in_fn_2 = self.in_fn_entry_2.currentLayer().source()
        except Exception:
            self.in_fn_2 = self.in_fn_entry_2.currentText() 
        try:
            self.mask_2 = self.mask_entry_2.currentLayer().source()
        except Exception:
            self.mask_2 = self.mask_entry_2.currentText()
        try:
            self.fmask_2 = self.fmask_entry_2.currentLayer().source()
        except Exception:
            self.fmask_2 = self.fmask_entry_2.currentText()
        
        images = [self.in_fn_2, self.mask_2, self.fmask_2]

        # Check if all images have the same resolution
        resolutions = [self.get_image_resolution(img) for img in images]
        if len(set(resolutions)) != 1:
            QMessageBox.critical(None, "Error", "All the input raster images must have the same spatial resolution!")
            return

        # Check if all images have the same number of rows and columns
        dimensions = [self.get_image_dimensions(img) for img in images]
        if len(set(dimensions)) != 1:
            QMessageBox.critical(None, "Error",
                                 "All the input raster images must have the same number of rows and columns!")
            return

        if not self.in_fn_2 or not self.mask_2 or not self.fmask_2:
            QMessageBox.critical(self, "Error", "Please select  the input file!")
            return
        n_classes_2 = int(30)
        directory_2 = self.folder_entry_2.text()
        out_fn_2 = self.out_fn_entry_2.text()
        if not out_fn_2:
            QMessageBox.critical(self, "Error", "Please enter the name of Vulnerability Map in CAL!")
            return

        # Check if the out_fn has the correct file extension
        if not (out_fn_2.endswith('.tif') or out_fn_2.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Vulnerability Map in CAL!")
            return

        if not self.check_binary_map(self.fmask_2):
            QMessageBox.critical(None, "Error",
                                 "'MASK OF FOREST AREAS IN THE CAL' must be a binary map (0 and 1) where the 1’s indicate forest areas.")
            return

        if not self.check_binary_map(self.mask_2):
            QMessageBox.critical(None, "Error",
                                 "'MASK OF THE NON-EXCLUDED JURISDICTION' must be a binary map (0 and 1) where the 1’s indicate areas inside the jurisdiction.")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.vulnerability_map.set_working_directory(directory_2)
            mask_arr = self.vulnerability_map.geometric_classification_alternative(self.in_fn_2, n_classes_2, self.mask_2, self.fmask_2)
            self.vulnerability_map.array_to_image(self.in_fn_2, out_fn_2, mask_arr, gdal.GDT_Int16, -1)
            self.vulnerability_map.replace_ref_system(self.in_fn_2, out_fn_2)

            if self.checkBox_2.isChecked():
                basename = os.path.splitext(os.path.basename(out_fn_2))[0]
                layer = QgsRasterLayer(out_fn_2, basename)
                layer.setDataSource(os.path.join(directory_2, out_fn_2), basename, 'gdal')
                QgsProject.instance().addMapLayer(layer)

            QMessageBox.information(self, "Processing Completed", "Processing completed!")

            self.progressDialog.close()

        except Exception as e:
            self.progressDialog.close()
            QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")
            
    def update_progress(self, value):
        # Update QProgressDialog with the new value
        if self.progressDialog is not None:
            self.progressDialog.setValue(value)

######################################################################################################
        
class AT_FIT_CAL_SCREEN(QtWidgets.QDialog, FORM_CLASS2):
    def __init__(self, parent=None):
        """Constructor."""
        super(AT_FIT_CAL_SCREEN, self).__init__(parent)
        # Store the initial directory path
        self.initial_directory = os.getcwd()
        # Set up the user interface from Designer through FORM_CLASS2.
        self.setupUi(self)
        # Workspace handling
        if central_data_store.directory is not None and self.folder_entry is not None:
            self.directory = central_data_store.directory
            self.folder_entry.setText(str(central_data_store.directory))
        self.Intro_button3.clicked.connect(self.gotointro3)
        self.RMT_button3.clicked.connect(self.gotormt3)
        self.MCT_button3.clicked.connect(self.gotomct3)
        self.doc_button.clicked.connect(self.openDocument)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.municipality_button.clicked.connect(lambda: self.selectRaster(self.municipality_entry, 'Map of Administrative Divisions'))
        self.risk30_hrp_button.clicked.connect(lambda: self.selectRaster(self.risk30_hrp_entry, 'Vulnerability Map in CAL'))
        self.deforestation_hrp_button.clicked.connect(lambda: self.selectRaster(self.deforestation_hrp_entry, 'Map of Deforestation in the CAL'))
        
        self.ok_button3.clicked.connect(self.process_data3)
        self.allocation_tool = AllocationTool()
        # Connect the progress_updated signal to the update_progress method
        self.allocation_tool.progress_updated.connect(self.update_progress)
        self.directory = None
        self.risk30_hrp = None
        self.municipality = None
        self.deforestation_hrp = None
        self.out_fn1 = None
        self.out_fn2 = None
        self.csv_name = None
        self.image1_entry.setPlaceholderText('e.g., Acre_Modeling_Region_CAL.tif')
        self.csv_entry.setPlaceholderText('e.g., Relative_Frequency_Table_CAL.csv')
        self.image2_entry.setPlaceholderText('e.g., Acre_Fitted_Density_Map_CAL.tif')
        self.setWindowTitle("JNR Integrated Risk/Allocation Tool")

        # Provide intitial settings for each comboBox
        self.municipality_entry.setStyleSheet(style_sheet)
        self.deforestation_hrp_entry.setStyleSheet(style_sheet)
        self.risk30_hrp_entry.setStyleSheet(style_sheet)
        
        self.municipality_entry.setCurrentIndex(-1)
        self.deforestation_hrp_entry.setCurrentIndex(-1)
        self.risk30_hrp_entry.setCurrentIndex(-1)
        
        self.municipality_entry.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.deforestation_hrp_entry.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.risk30_hrp_entry.setFilters(QgsMapLayerProxyModel.RasterLayer)

    def gotormt3(self):
        os.chdir(self.initial_directory)
        rmt3 = RMT_FIT_CAL_SCREEN()
        stacked_widget.addWidget(rmt3)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def gotointro3(self):
        os.chdir(self.initial_directory)
        intro3 = IntroScreen()
        stacked_widget.addWidget(intro3)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def gotomct3(self):
        os.chdir(self.initial_directory)
        mct3 = MCT_FIT_CAL_SCREEN()
        stacked_widget.addWidget(mct3)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def openDocument(self):
        pdf_path = os.path.join(os.path.dirname(__file__), "doc\\TestFitAM.pdf")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path = Path(data_folder)
        self.directory = str(data_folder_path)
        self.folder_entry.setText(self.directory)
        central_data_store.directory = self.directory

    def selectRaster(self, comboBox, string):
        """
        Opening the raster layer file and adding the path to the combobox
        on end of the list with comboBox items.

        :param comboBox: Qt combobox.
        :type comboBox: QComboBox
        """
        rast_path = QFileDialog.getOpenFileName(self, string)
        index = comboBox.currentIndex()
        comboBox.setAdditionalItems([rast_path[0]])
        ind = comboBox.count() - 1
        comboBox.setCurrentIndex(ind)

    def get_image_resolution(self, image):
        # Set up a GDAL dataset
        in_ds = gdal.Open(image)
        # Set up a GDAL band
        P = in_ds.GetGeoTransform()[1]
        # Create Numpy Array1
        return P

    def get_image_dimensions(self, image):
        dataset = gdal.Open(image)
        cols = dataset.RasterXSize
        rows = dataset.RasterYSize
        return rows, cols

    def get_image_datatype(self, image):
        in_ds = gdal.Open(image)
        in_band = in_ds.GetRasterBand(1)
        datatype = gdal.GetDataTypeName(in_band.DataType)
        return datatype

    def get_image_max_min(self, image):
        in_ds = gdal.Open(image)
        in_band = in_ds.GetRasterBand(1)
        min, max= in_band.ComputeRasterMinMax()
        return min, max

    def find_unique_values(self, arr, limit=2):
        unique_values = set()
        for value in np.nditer(arr):
            unique_values.add(value.item())
            if len(unique_values) > limit:
                return False
        return True

    def check_binary_map(self, in_fn):
        '''
        Check if input image is binary map
        :param in_fn: input image
        :return: True if the file is a binary map, False otherwise
        '''
        file_extension = in_fn.split('.')[-1].lower()
        file_name, _ = os.path.splitext(in_fn)
        if file_extension == 'rst':
            with open(file_name + '.rdc', 'r') as read_file:
                rdc_content = read_file.read().lower()
                byte_or_integer_binary = "data type   : byte" in rdc_content or (
                        "data type   : integer" in rdc_content and "min. value  : 0" in rdc_content and "max. value  : 1" in rdc_content)
                float_binary = "data type   : real" in rdc_content and "min. value  : 0.0000000" in rdc_content and "max. value  : 1.0000000" in rdc_content
        elif file_extension == 'tif':
            datatype = self.get_image_datatype(in_fn)
            min_val, max_val = self.get_image_max_min(in_fn)
            byte_or_integer_binary = datatype in ['Byte', 'CInt16', 'CInt32', 'Int16', 'Int32', 'UInt16',
                                                      'UInt32'] and max_val == 1 and min_val == 0
            float_binary = datatype in ['Float32', 'Float64', 'CFloat32', 'CFloat64'] and max_val == 1.0000000 and min_val == 0.0000000

        if byte_or_integer_binary or (float_binary):
            # For float_binary, use find_unique_values function to check if data only have two unique values [0.0000000, 1.0000000].
            if float_binary:
                in_ds = gdal.Open(in_fn)
                in_band = in_ds.GetRasterBand(1)
                arr = in_band.ReadAsArray()
                # If more than two unique values are found, it's not a binary map, return False.
                if not self.find_unique_values(arr, 2):
                    return False
            # Binary map: byte_or_integer_binary or float_binary with two unique values [0.0000000, 1.0000000], it returns True.
            return True
        # For any other scenario, it returns False.
        return False

    def process_data3(self):
        try: 
            self.risk30_hrp = self.risk30_hrp_entry.currentLayer().source()
        except Exception:
            self.risk30_hrp = self.risk30_hrp_entry.currentText() 
        try:
            self.municipality = self.municipality_entry.currentLayer().source()
        except Exception:
            self.municipality = self.municipality_entry.currentText()
        try:
            self.deforestation_hrp = self.deforestation_hrp_entry.currentLayer().source()
        except Exception:
            self.deforestation_hrp = self.deforestation_hrp_entry.currentText()
            
        images = [self.risk30_hrp, self.municipality, self.deforestation_hrp]

        # Check if all images have the same resolution
        resolutions = [self.get_image_resolution(img) for img in images]
        if len(set(resolutions)) != 1:
            QMessageBox.critical(None, "Error", "All the input raster images must have the same spatial resolution!")
            return

        # Check if all images have the same number of rows and columns
        dimensions = [self.get_image_dimensions(img) for img in images]
        if len(set(dimensions)) != 1:
            QMessageBox.critical(None, "Error",
                                 "All the input raster images must have the same number of rows and columns!")
            return

        if not self.risk30_hrp or not self.municipality or not self.deforestation_hrp:
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        directory = self.folder_entry.text()

        out_fn1 = self.image1_entry.text()
        if not out_fn1:
            QMessageBox.critical(self, "Error", "Please enter the name for Modeling Region Map in CAL!")
            return

        if not (out_fn1.endswith('.tif') or out_fn1.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name for Modeling Region Map in CAL!")
            return

        csv_name = self.csv_entry.text()
        if not csv_name:
            QMessageBox.critical(self, "Error", "Please enter the name for the Relative Frequency Table!")
            return

        if not (csv_name.endswith('.csv')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .csv extension in the name of Relative Frequency Table!")
            return

        out_fn2 = self.image2_entry.text()
        if not out_fn2:
            QMessageBox.critical(self, "Error", "Please enter the name for Fitted Density Map in the CAL!")
            return

        if not (out_fn2.endswith('.tif') or out_fn2.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name for Fitted Density Map in the CAL!")
            return

        if not self.check_binary_map(self.deforestation_hrp):
            QMessageBox.critical(None, "Error",
                                 "'MAP OF DEFORESTATION IN THE CAL' must be a binary map (0 and 1) where the 1’s indicate deforestation.")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.allocation_tool.execute_workflow_fit(directory, self.risk30_hrp,
                                                        self.municipality,self.deforestation_hrp, csv_name,
                                                        out_fn1,out_fn2)
            QMessageBox.information(self, "Processing Completed", "Processing completed!")
            self.progressDialog.close()

            if self.checkBox.isChecked():
                csv_basename = os.path.splitext(os.path.basename(csv_name))[0]
                basename1 = os.path.splitext(os.path.basename(out_fn1))[0]
                basename2 = os.path.splitext(os.path.basename(out_fn2))[0]
                csv_layer = QgsVectorLayer(csv_name, csv_basename, "ogr")
                layer1 = QgsRasterLayer(out_fn1, basename1)
                layer2 = QgsRasterLayer(out_fn2, basename2)
                layer1.setDataSource(os.path.join(directory, out_fn1), basename1, 'gdal')
                layer2.setDataSource(os.path.join(directory, out_fn2), basename2, 'gdal')
                #csv_layer.setDataSource(os.path.join(directory,csv_name), "UTF-8", "x", ";")
                QgsProject.instance().addMapLayer(layer1)
                QgsProject.instance().addMapLayer(layer2)
                QgsProject.instance().addMapLayer(csv_layer)

        except Exception as e:
             self.progressDialog.close()
             QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def update_progress(self, value):
        # Update QProgressDialog with the new value
        if self.progressDialog is not None:
            self.progressDialog.setValue(value)
         
######################################################################################################

class MCT_FIT_CAL_SCREEN(QtWidgets.QDialog, FORM_CLASS3):
    def __init__(self, parent=None):
        """Constructor."""
        super(MCT_FIT_CAL_SCREEN, self).__init__(parent)
        # Store the initial directory path
        self.initial_directory = os.getcwd()
        # Set up the user interface from Designer through FORM_CLASS3.
        self.setupUi(self)
        # Workspace handling
        if central_data_store.directory is not None and self.folder_entry is not None:
            self.directory = central_data_store.directory
            self.folder_entry.setText(str(central_data_store.directory))
        self.AT_button4.clicked.connect(self.gotoat4)
        self.Intro_button4.clicked.connect(self.gotointro4)
        self.RMT_button4.clicked.connect(self.gotormt4)
        self.doc_button.clicked.connect(self.openDocument)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.mask_button.clicked.connect(lambda: self.selectRaster(self.mask_entry, 'Mask of Study Area'))
        self.deforestation_hrp_button.clicked.connect(lambda: self.selectRaster(self.deforestation_hrp_entry, 'Map of Deforestation in the CAL'))
        self.density_button.clicked.connect(lambda: self.selectRaster(self.density_entry, 'Deforestation Density Map'))
        
        self.ok_button.clicked.connect(self.process_data4)
        self.model_evaluation = ModelEvaluation()
        self.model_evaluation.progress_updated.connect(self.update_progress)
        self.directory = None
        self.mask = None
        self.deforestation_hrp = None
        self.density = None
        self.grid_area = None
        self.grid_area_entry.setPlaceholderText('Type default 100000 or other number')
        self.title = None
        self.out_fn = None
        self.out_fn_entry.setPlaceholderText('e.g., Plot_CAL.png')
        self.raster_fn = None
        self.raster_fn_entry.setPlaceholderText('e.g., Acre_Residuals_CAL.tif')
        self.xmax = None
        self.xmax = None
        self.setWindowTitle("JNR Integrated Risk/Allocation Tool")

        # Provide intitial settings for each comboBox
        self.mask_entry.setStyleSheet(style_sheet)
        self.deforestation_hrp_entry.setStyleSheet(style_sheet)
        self.density_entry.setStyleSheet(style_sheet)
        
        self.mask_entry.setCurrentIndex(-1)
        self.deforestation_hrp_entry.setCurrentIndex(-1)
        self.density_entry.setCurrentIndex(-1)
        
        self.mask_entry.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.deforestation_hrp_entry.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.density_entry.setFilters(QgsMapLayerProxyModel.RasterLayer)

    def gotoat4(self):
        os.chdir(self.initial_directory)
        at4 = AT_FIT_CAL_SCREEN()
        stacked_widget.addWidget(at4)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def gotointro4(self):
        os.chdir(self.initial_directory)
        intro4 = IntroScreen()
        stacked_widget.addWidget(intro4)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def gotormt4(self):
        os.chdir(self.initial_directory)
        rmt4 = RMT_FIT_CAL_SCREEN()
        stacked_widget.addWidget(rmt4)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def openDocument(self):
        pdf_path = os.path.join(os.path.dirname(__file__), "doc\\TestFitMA.pdf")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path = Path(data_folder)
        self.directory = str(data_folder_path)
        self.folder_entry.setText(self.directory)
        central_data_store.directory = self.directory

    def selectRaster(self, comboBox, string):
        """
        Opening the raster layer file and adding the path to the combobox
        on end of the list with comboBox items.

        :param comboBox: Qt combobox.
        :type comboBox: QComboBox
        """
        rast_path = QFileDialog.getOpenFileName(self, string)
        index = comboBox.currentIndex()
        comboBox.setAdditionalItems([rast_path[0]])
        ind = comboBox.count() - 1
        comboBox.setCurrentIndex(ind)

    def get_image_resolution(self, image):
        # Set up a GDAL dataset
        in_ds = gdal.Open(image)
        # Set up a GDAL band
        P = in_ds.GetGeoTransform()[1]
        # Create Numpy Array1
        return P

    def get_image_dimensions(self, image):
        dataset = gdal.Open(image)
        cols = dataset.RasterXSize
        rows = dataset.RasterYSize
        return rows, cols

    def get_image_datatype(self, image):
        in_ds = gdal.Open(image)
        in_band = in_ds.GetRasterBand(1)
        datatype = gdal.GetDataTypeName(in_band.DataType)
        return datatype

    def get_image_max_min(self, image):
        in_ds = gdal.Open(image)
        in_band = in_ds.GetRasterBand(1)
        min, max= in_band.ComputeRasterMinMax()
        return min, max

    def find_unique_values(self, arr, limit=2):
        unique_values = set()
        for value in np.nditer(arr):
            unique_values.add(value.item())
            if len(unique_values) > limit:
                return False
        return True

    def check_binary_map(self, in_fn):
        '''
        Check if input image is binary map
        :param in_fn: input image
        :return: True if the file is a binary map, False otherwise
        '''
        file_extension = in_fn.split('.')[-1].lower()
        file_name, _ = os.path.splitext(in_fn)
        if file_extension == 'rst':
            with open(file_name + '.rdc', 'r') as read_file:
                rdc_content = read_file.read().lower()
                byte_or_integer_binary = "data type   : byte" in rdc_content or (
                        "data type   : integer" in rdc_content and "min. value  : 0" in rdc_content and "max. value  : 1" in rdc_content)
                float_binary = "data type   : real" in rdc_content and "min. value  : 0.0000000" in rdc_content and "max. value  : 1.0000000" in rdc_content
        elif file_extension == 'tif':
            datatype = self.get_image_datatype(in_fn)
            min_val, max_val = self.get_image_max_min(in_fn)
            byte_or_integer_binary = datatype in ['Byte', 'CInt16', 'CInt32', 'Int16', 'Int32', 'UInt16',
                                                      'UInt32'] and max_val == 1 and min_val == 0
            float_binary = datatype in ['Float32', 'Float64', 'CFloat32', 'CFloat64'] and max_val == 1.0000000 and min_val == 0.0000000

        if byte_or_integer_binary or (float_binary):
            # For float_binary, use find_unique_values function to check if data only have two unique values [0.0000000, 1.0000000].
            if float_binary:
                in_ds = gdal.Open(in_fn)
                in_band = in_ds.GetRasterBand(1)
                arr = in_band.ReadAsArray()
                # If more than two unique values are found, it's not a binary map, return False.
                if not self.find_unique_values(arr, 2):
                    return False
            # Binary map: byte_or_integer_binary or float_binary with two unique values [0.0000000, 1.0000000], it returns True.
            return True
        # For any other scenario, it returns False.
        return False

    def process_data4(self):
        try: 
            self.mask = self.mask_entry.currentLayer().source()
        except Exception:
            self.mask = self.mask_entry.currentText() 
        try:
            self.deforestation_hrp = self.deforestation_hrp_entry.currentLayer().source()
        except Exception:
            self.deforestation_hrp = self.deforestation_hrp_entry.currentText()
        try:
            self.density = self.density_entry.currentLayer().source()
        except Exception:
            self.density = self.density_entry.currentText()
            
        images = [self.mask, self.deforestation_hrp, self.density]

        # Check if all images have the same resolution
        resolutions = [self.get_image_resolution(img) for img in images]
        if len(set(resolutions)) != 1:
            QMessageBox.critical(None, "Error", "All the input raster images must have the same spatial resolution!")
            return

        # Check if all images have the same number of rows and columns
        dimensions = [self.get_image_dimensions(img) for img in images]
        if len(set(dimensions)) != 1:
            QMessageBox.critical(None, "Error",
                                 "All the input raster images must have the same number of rows and columns!")
            return

        if not self.mask or not self.deforestation_hrp or not self.density :
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        grid_area = self.grid_area_entry.text()
        if not grid_area:
            QMessageBox.critical(self, "Error", "Please enter the thiessen polygon grid area value!")
            return
        try:
            self.grid_area = float(grid_area)
            if not (0 < self.grid_area):
                QMessageBox.critical(self, "Error", "Thiessen polygon grid area value should larger than 0!")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "Thiessen polygon grid area value should be a valid number!")
            return


        xmax = self.xmax_entry.text()
        if xmax.lower() != "default":
            try:
                xmax = float(xmax)
                if xmax <= 0:
                    raise ValueError("The plot x-axis limit should be larger than 0!")
            except ValueError:
                QMessageBox.critical(self, "Error", "The plot x-axis limit should be a valid number or 'Default'!")
                return

        ymax = self.ymax_entry.text()
        if ymax.lower() != "default":
            try:
                ymax = float(ymax)
                if ymax <= 0:
                    raise ValueError("The plot y-axis limit should be larger than 0!")
            except ValueError:
                QMessageBox.critical(self, "Error", "The plot y-axis limit should be a valid number or 'Default'!")
                return

        title = self.title_entry.text()
        if not title:
            QMessageBox.critical(self, "Error", "Please enter the title of plot!")
            return

        directory = self.folder_entry.text()

        out_fn = self.out_fn_entry.text()
        if not out_fn:
            QMessageBox.critical(self, "Error", "Please enter the name of plot!")
            return

        # Check if the out_fn has the correct file extension
        if not (out_fn.endswith('.png') or out_fn.endswith('.jpg') or out_fn.endswith('.pdf') or out_fn.endswith(
                '.svg') or out_fn.endswith('.eps') or out_fn.endswith('.ps') or out_fn.endswith('.tif')):
            QMessageBox.critical(self, "Error",
                                 "Please enter extension(.png/.jpg/.pdf/.svg/.eps/.ps/.tif) in the name of plot!")
            return

        raster_fn = self.raster_fn_entry.text()
        if not raster_fn:
            QMessageBox.critical(self, "Error", "Please enter the name for Residual Map!")
            return

        if not (raster_fn.endswith('.tif') or raster_fn.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Residual Map!")
            return

        if not self.check_binary_map(self.mask):
            QMessageBox.critical(None, "Error",
                                 "'MASK OF THE NON-EXCLUDED JURISDICTION' must be a binary map (0 and 1) where the 1’s indicate areas inside the jurisdiction.")
            return

        if not self.check_binary_map(self.deforestation_hrp):
            QMessageBox.critical(None, "Error",
                                 "'MAP OF DEFORESTATION IN THE CAL' must be a binary map (0 and 1) where the 1’s indicate deforestation.")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.model_evaluation.set_working_directory(directory)
            self.model_evaluation.create_mask_polygon(self.mask)
            clipped_gdf = self.model_evaluation.create_thiessen_polygon(self.grid_area, self.mask,self.density, self.deforestation_hrp, out_fn,raster_fn)
            self.model_evaluation.replace_ref_system(self.mask, raster_fn)
            self.model_evaluation.create_plot(grid_area,clipped_gdf, title, out_fn, xmax, ymax)
            self.model_evaluation.remove_temp_files()

            if self.checkBox.isChecked():
                basename = os.path.splitext(os.path.basename(raster_fn))[0]
                layer = QgsRasterLayer(raster_fn, basename)
                layer.setDataSource(os.path.join(directory, raster_fn), basename, 'gdal')
                QgsProject.instance().addMapLayer(layer)

            QMessageBox.information(self, "Processing Completed", "Processing completed!")
            self.progressDialog.close()

        except Exception as e:
             self.progressDialog.close()
             QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def update_progress(self, value):
        # Update QProgressDialog with the new value
        if self.progressDialog is not None:
            self.progressDialog.setValue(value)

######################################################################################################
        
class RMT_PRE_CNF_SCREEN(QtWidgets.QDialog, FORM_CLASS4):
    def __init__(self, parent=None):
        """Constructor."""
        super(RMT_PRE_CNF_SCREEN, self).__init__(parent)
        # Store the initial directory path
        self.initial_directory = os.getcwd()
        # Set up the user interface from Designer through FORM_CLASS4.
        self.setupUi(self)
        # Workspace handling
        if central_data_store.directory is not None and self.folder_entry is not None:
            self.directory = central_data_store.directory
            self.folder_entry.setText(str(central_data_store.directory))
        if central_data_store.directory is not None and self.folder_entry_2 is not None:
            self.directory_2 = central_data_store.directory
            self.folder_entry_2.setText(str(central_data_store.directory))
        self.AT_button2.clicked.connect(self.gotoat2)
        self.Intro_button2.clicked.connect(self.gotointro2)
        self.MCT_button2.clicked.connect(self.gotomct2)
        self.doc_button = self.tab1.findChild(QWidget, "doc_button")
        self.select_folder_button = self.tab1.findChild(QWidget, "select_folder_button")
        self.fd_button = self.tab1.findChild(QWidget, "fd_button")
        self.ok_button2 = self.tab1.findChild(QWidget, "ok_button2")

        self.doc_button_2 = self.tab2.findChild(QWidget, "doc_button_2")
        self.select_folder_button_2 = self.tab2.findChild(QWidget, "select_folder_button_2")
        self.mask_button_2 = self.tab2.findChild(QWidget, "mask_button_2")
        self.fmask_button_2 = self.tab2.findChild(QWidget, "fmask_button_2")
        self.fd_button_2 = self.tab2.findChild(QWidget, "fd_button_2")
        self.ok_button2_2 = self.tab2.findChild(QWidget, "ok_button2_2")

        self.doc_button.clicked.connect(self.openDocument)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.fd_button.clicked.connect(lambda: self.selectRaster(self.in_fn_entry, 'Map of Distance from the Forest Edge in CNF'))
        self.ok_button2.clicked.connect(self.process_data2)

        self.doc_button_2.clicked.connect(self.openDocument_2)
        self.select_folder_button_2.clicked.connect(self.select_working_directory_2)
        self.fd_button_2.clicked.connect(lambda: self.selectRaster(self.in_fn_entry_2, 'Map of Empirical transition potential for CNF'))
        self.fmask_button_2.clicked.connect(lambda: self.selectRaster(self.fmask_entry_2, 'Mask of Forest Area'))
        self.mask_button_2.clicked.connect(lambda: self.selectRaster(self.mask_entry_2, 'Mask of Study Area'))
        self.ok_button2_2.clicked.connect(self.process_data2_2)

        self.vulnerability_map = VulnerabilityMap()
        self.vulnerability_map.progress_updated.connect(self.update_progress)
        self.directory = None
        self.in_fn = None
        self.NRT = None
        # Use NRT from the data store
        if central_data_store.NRT is not None:
            self.nrt_entry.setText(str(central_data_store.NRT))
        self.n_classes = None
        self.out_fn = None
        self.out_fn_entry.setPlaceholderText('e.g., Acre_Vulnerability_CNF.tif')

        self.directory_2 = None
        self.mask_2 = None
        self.fmask_2 = None
        self.in_fn_2 = None
        self.out_fn_2 = None
        self.n_classes_2 = None
        self.out_fn_entry_2.setPlaceholderText('e.g., Acre_Vulnerability_CNF.tif')

        self.setWindowTitle("JNR Integrated Risk/Allocation Tool")

        # Provide intitial settings for each comboBox
        self.in_fn_entry.setStyleSheet(style_sheet)
        self.in_fn_entry_2.setStyleSheet(style_sheet)
        self.fmask_entry_2.setStyleSheet(style_sheet)
        self.mask_entry_2.setStyleSheet(style_sheet)
        
        self.in_fn_entry.setCurrentIndex(-1)
        self.in_fn_entry_2.setCurrentIndex(-1)
        self.fmask_entry_2.setCurrentIndex(-1)
        self.mask_entry_2.setCurrentIndex(-1)
        
        self.in_fn_entry.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.in_fn_entry_2.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.fmask_entry_2.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.mask_entry_2.setFilters(QgsMapLayerProxyModel.RasterLayer)

    def gotoat2(self):
        os.chdir(self.initial_directory)
        at2 = AT_PRE_CNF_SCREEN()
        stacked_widget.addWidget(at2)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def gotomct2(self):
        os.chdir(self.initial_directory)
        mct2 = MCT_PRE_CNF_SCREEN()
        stacked_widget.addWidget(mct2)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def gotointro2(self):
        os.chdir(self.initial_directory)
        intro2 = IntroScreen()
        stacked_widget.addWidget(intro2)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def openDocument(self):
        pdf_path = os.path.join(os.path.dirname(__file__), "doc\\TestPreVM.pdf")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def openDocument_2(self):
        pdf_path = os.path.join(os.path.dirname(__file__), "doc\\TestPreVM.pdf")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path = Path(data_folder)
        self.directory = str(data_folder_path)
        self.folder_entry.setText(self.directory)
        self.folder_entry_2.setText(self.directory)
        central_data_store.directory = self.directory
        
    def selectRaster(self, comboBox, string):
        """
        Opening the raster layer file and adding the path to the combobox
        on end of the list with comboBox items.

        :param comboBox: Qt combobox.
        :type comboBox: QComboBox
        """
        rast_path = QFileDialog.getOpenFileName(self, string)
        index = comboBox.currentIndex()
        comboBox.setAdditionalItems([rast_path[0]])
        ind = comboBox.count() - 1
        comboBox.setCurrentIndex(ind)

    def select_working_directory_2(self):
        data_folder_2 = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path_2 = Path(data_folder_2)
        self.directory_2 = str(data_folder_path_2)
        self.folder_entry_2.setText(self.directory_2)
        self.folder_entry.setText(self.directory_2)
        central_data_store.directory = self.directory_2

    def process_data2(self):
        try: 
            self.in_fn = self.in_fn_entry.currentLayer().source()
        except Exception:
            self.in_fn = self.in_fn_entry.currentText()
            
        if not self.in_fn:
            QMessageBox.critical(self, "Error", "Please select the input file!")
            return

        NRT = self.nrt_entry.text()
        if not NRT:
            QMessageBox.critical(self, "Error", "Please enter the NRT value!")
            return
        try:
            self.NRT = int(NRT)
            if (self.NRT <= 0):
                QMessageBox.critical(self, "Error", "NRT value should be larger than 0!")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "NRT value should be a valid number!")
            return

        n_classes = int(29)
        if not n_classes:
            QMessageBox.critical(self, "Error", "Please enter the number of classes!")
            return
        try:
            self.n_classes = int(n_classes)
            if (self.n_classes <= 0):
                QMessageBox.critical(self, "Error", "Number of classes should be larger than 0!")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "Number of classes value should be a valid number!")
            return

        directory = self.folder_entry.text()

        out_fn = self.out_fn_entry.text()
        if not out_fn:
            QMessageBox.critical(self, "Error", "Please enter the name of Vulnerability Map in CNF!")
            return

        if not (out_fn.endswith('.tif') or out_fn.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Vulnerability Map in CNF!")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.vulnerability_map.set_working_directory(directory)
            mask_arr = self.vulnerability_map.geometric_classification(self.in_fn, NRT, n_classes)
            self.vulnerability_map.array_to_image(self.in_fn, out_fn, mask_arr, gdal.GDT_Int16, -1)
            self.vulnerability_map.replace_ref_system(self.in_fn, out_fn)

            if self.checkBox.isChecked():
                basename = os.path.splitext(os.path.basename(out_fn))[0]
                layer = QgsRasterLayer(out_fn, basename)
                layer.setDataSource(os.path.join(directory, out_fn), basename, 'gdal')
                QgsProject.instance().addMapLayer(layer)

            QMessageBox.information(self, "Processing Completed", "Processing completed!")
            self.progressDialog.close()

        except Exception as e:
            self.progressDialog.close()
            QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def get_image_resolution(self, image):
        # Set up a GDAL dataset
        in_ds = gdal.Open(image)
        # Set up a GDAL band
        P = in_ds.GetGeoTransform()[1]
        # Create Numpy Array1
        return P

    def get_image_dimensions(self, image):
        dataset = gdal.Open(image)
        cols = dataset.RasterXSize
        rows = dataset.RasterYSize
        return rows, cols

    def get_image_datatype(self, image):
        in_ds = gdal.Open(image)
        in_band = in_ds.GetRasterBand(1)
        datatype = gdal.GetDataTypeName(in_band.DataType)
        return datatype

    def get_image_max_min(self, image):
        in_ds = gdal.Open(image)
        in_band = in_ds.GetRasterBand(1)
        min, max= in_band.ComputeRasterMinMax()
        return min, max

    def find_unique_values(self, arr, limit=2):
        unique_values = set()
        for value in np.nditer(arr):
            unique_values.add(value.item())
            if len(unique_values) > limit:
                return False
        return True

    def check_binary_map(self, in_fn):
        '''
        Check if input image is binary map
        :param in_fn: input image
        :return: True if the file is a binary map, False otherwise
        '''
        file_extension = in_fn.split('.')[-1].lower()
        file_name, _ = os.path.splitext(in_fn)
        if file_extension == 'rst':
            with open(file_name + '.rdc', 'r') as read_file:
                rdc_content = read_file.read().lower()
                byte_or_integer_binary = "data type   : byte" in rdc_content or (
                        "data type   : integer" in rdc_content and "min. value  : 0" in rdc_content and "max. value  : 1" in rdc_content)
                float_binary = "data type   : real" in rdc_content and "min. value  : 0.0000000" in rdc_content and "max. value  : 1.0000000" in rdc_content
        elif file_extension == 'tif':
            datatype = self.get_image_datatype(in_fn)
            min_val, max_val = self.get_image_max_min(in_fn)
            byte_or_integer_binary = datatype in ['Byte', 'CInt16', 'CInt32', 'Int16', 'Int32', 'UInt16',
                                                      'UInt32'] and max_val == 1 and min_val == 0
            float_binary = datatype in ['Float32', 'Float64', 'CFloat32', 'CFloat64'] and max_val == 1.0000000 and min_val == 0.0000000

        if byte_or_integer_binary or (float_binary):
            # For float_binary, use find_unique_values function to check if data only have two unique values [0.0000000, 1.0000000].
            if float_binary:
                in_ds = gdal.Open(in_fn)
                in_band = in_ds.GetRasterBand(1)
                arr = in_band.ReadAsArray()
                # If more than two unique values are found, it's not a binary map, return False.
                if not self.find_unique_values(arr, 2):
                    return False
            # Binary map: byte_or_integer_binary or float_binary with two unique values [0.0000000, 1.0000000], it returns True.
            return True
        # For any other scenario, it returns False.
        return False

    def process_data2_2(self):
        try: 
            self.in_fn_2 = self.in_fn_entry_2.currentLayer().source()
        except Exception:
            self.in_fn_2 = self.in_fn_entry_2.currentText() 
        try:
            self.mask_2 = self.mask_entry_2.currentLayer().source()
        except Exception:
            self.mask_2 = self.mask_entry_2.currentText()
        try:
            self.fmask_2 = self.fmask_entry_2.currentLayer().source()
        except Exception:
            self.fmask_2 = self.fmask_entry_2.currentText()
            
        images = [self.in_fn_2, self.mask_2, self.fmask_2]

        # Check if all images have the same resolution
        resolutions = [self.get_image_resolution(img) for img in images]
        if len(set(resolutions)) != 1:
            QMessageBox.critical(None, "Error", "All the input raster images must have the same spatial resolution!")
            return

        # Check if all images have the same number of rows and columns
        dimensions = [self.get_image_dimensions(img) for img in images]
        if len(set(dimensions)) != 1:
            QMessageBox.critical(None, "Error",
                                 "All the input raster images must have the same number of rows and columns!")
            return

        if not self.in_fn_2 or not self.mask_2 or not self.fmask_2:
            QMessageBox.critical(self, "Error", "Please select  the input file!")
            return
        n_classes_2 = int(30)
        directory_2 = self.folder_entry_2.text()
        out_fn_2 = self.out_fn_entry_2.text()
        if not out_fn_2:
            QMessageBox.critical(self, "Error", "Please enter the name of Vulnerability Map in CNF!")
            return

        # Check if the out_fn has the correct file extension
        if not (out_fn_2.endswith('.tif') or out_fn_2.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Vulnerability Map in CNF!")
            return

        if not self.check_binary_map(self.fmask_2):
            QMessageBox.critical(None, "Error",
                                 "'MASK OF FOREST AREAS IN THE CNF' must be a binary map (0 and 1) where the 1’s indicate forest areas.")
            return

        if not self.check_binary_map(self.mask_2):
            QMessageBox.critical(None, "Error",
                                 "'MASK OF THE NON-EXCLUDED JURISDICTION' must be a binary map (0 and 1) where the 1’s indicate areas inside the jurisdiction.")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.vulnerability_map.set_working_directory(directory_2)
            mask_arr = self.vulnerability_map.geometric_classification_alternative(self.in_fn_2, n_classes_2,
                                                                                   self.mask_2, self.fmask_2)
            self.vulnerability_map.array_to_image(self.in_fn_2, out_fn_2, mask_arr, gdal.GDT_Int16, -1)
            self.vulnerability_map.replace_ref_system(self.in_fn_2, out_fn_2)

            if self.checkBox_2.isChecked():
                basename = os.path.splitext(os.path.basename(out_fn_2))[0]
                layer = QgsRasterLayer(out_fn_2, basename)
                layer.setDataSource(os.path.join(directory_2, out_fn_2), basename, 'gdal')
                QgsProject.instance().addMapLayer(layer)

            QMessageBox.information(self, "Processing Completed", "Processing completed!")

            self.progressDialog.close()

        except Exception as e:
            self.progressDialog.close()
            QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def update_progress(self, value):
        # Update QProgressDialog with the new value
        if self.progressDialog is not None:
            self.progressDialog.setValue(value)

######################################################################################################
        
class AT_PRE_CNF_SCREEN(QtWidgets.QDialog, FORM_CLASS5):
    def __init__(self, parent=None):
        """Constructor."""
        super(AT_PRE_CNF_SCREEN, self).__init__(parent)
        # Store the initial directory path
        self.initial_directory = os.getcwd()
        # Set up the user interface from Designer through FORM_CLASS5.
        self.setupUi(self)
        if central_data_store.directory is not None and self.folder_entry is not None:
            self.directory = central_data_store.directory
            self.folder_entry.setText(str(central_data_store.directory))
        self.Intro_button3.clicked.connect(self.gotointro3)
        self.RMT_button3.clicked.connect(self.gotormt3)
        self.MCT_button3.clicked.connect(self.gotomct3)
        self.doc_button.clicked.connect(self.openDocument)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.municipality_button.clicked.connect(lambda: self.selectRaster(self.municipality_entry, 'Map of Administrative Divisions'))
        self.csv_button.clicked.connect(self.select_csv)
        self.risk30_vp_button.clicked.connect(lambda: self.selectRaster(self.risk30_vp_entry, 'Vulnerability Map in CNF'))
        self.deforestation_cnf_button.clicked.connect(lambda: self.selectRaster(self.deforestation_cnf_entry, 'Map of Deforestation in CNF'))
        self.ok_button3.clicked.connect(self.process_data3)
        self.allocation_tool = AllocationTool()
        self.allocation_tool.progress_updated.connect(self.update_progress)
        self.directory = None
        self.csv = None
        self.municipality = None
        self.risk30_vp = None
        self.deforestation_cnf = None
        self.max_iterations = None
        self.image1 = None
        self.image2 = None
        self.iteration_entry.setPlaceholderText('The suggestion max iteration number is 5')
        self.image1_entry.setPlaceholderText('e.g., Acre_Prediction_Modeling_Region_CNF.tif')
        self.image2_entry.setPlaceholderText('e.g., Acre_Adjucted_Density_Map_CNF.tif')
        self.setWindowTitle("JNR Integrated Risk/Allocation Tool")

        # Provide intitial settings for each comboBox
        self.municipality_entry.setStyleSheet(style_sheet)
        self.risk30_vp_entry.setStyleSheet(style_sheet)
        self.deforestation_cnf_entry.setStyleSheet(style_sheet)
        
        self.municipality_entry.setCurrentIndex(-1)
        self.risk30_vp_entry.setCurrentIndex(-1)
        self.deforestation_cnf_entry.setCurrentIndex(-1)
        
        self.municipality_entry.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.risk30_vp_entry.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.deforestation_cnf_entry.setFilters(QgsMapLayerProxyModel.RasterLayer)

    def gotormt3(self):
        os.chdir(self.initial_directory)
        rmt3 = RMT_PRE_CNF_SCREEN()
        stacked_widget.addWidget(rmt3)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def gotointro3(self):
        os.chdir(self.initial_directory)
        intro3 = IntroScreen()
        stacked_widget.addWidget(intro3)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def gotomct3(self):
        os.chdir(self.initial_directory)
        mct3 = MCT_PRE_CNF_SCREEN()
        stacked_widget.addWidget(mct3)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def openDocument(self):
        pdf_path = os.path.join(os.path.dirname(__file__), "doc\\TestPreAM.pdf")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path = Path(data_folder)
        self.directory = str(data_folder_path)
        self.folder_entry.setText(self.directory)
        central_data_store.directory = self.directory

    def selectRaster(self, comboBox, string):
        """
        Opening the raster layer file and adding the path to the combobox
        on end of the list with comboBox items.

        :param comboBox: Qt combobox.
        :type comboBox: QComboBox
        """
        rast_path = QFileDialog.getOpenFileName(self, string)
        index = comboBox.currentIndex()
        comboBox.setAdditionalItems([rast_path[0]])
        ind = comboBox.count() - 1
        comboBox.setCurrentIndex(ind)

    def select_csv(self):
        file_path1, _ = QFileDialog.getOpenFileName(self, "CAL Relative Frequency Table (.csv)")
        if file_path1:
            self.csv = file_path1
            self.csv_entry.setText(file_path1.split('/')[-1])

    def get_image_resolution(self, image):
        # Set up a GDAL dataset
        in_ds = gdal.Open(image)
        # Set up a GDAL band
        P = in_ds.GetGeoTransform()[1]
        # Create Numpy Array1
        return P

    def get_image_dimensions(self, image):
        dataset = gdal.Open(image)
        cols = dataset.RasterXSize
        rows = dataset.RasterYSize
        return rows, cols

    def get_image_datatype(self, image):
        in_ds = gdal.Open(image)
        in_band = in_ds.GetRasterBand(1)
        datatype = gdal.GetDataTypeName(in_band.DataType)
        return datatype

    def get_image_max_min(self, image):
        in_ds = gdal.Open(image)
        in_band = in_ds.GetRasterBand(1)
        min, max= in_band.ComputeRasterMinMax()
        return min, max

    def find_unique_values(self, arr, limit=2):
        unique_values = set()
        for value in np.nditer(arr):
            unique_values.add(value.item())
            if len(unique_values) > limit:
                return False
        return True

    def check_binary_map(self, in_fn):
        '''
        Check if input image is binary map
        :param in_fn: input image
        :return: True if the file is a binary map, False otherwise
        '''
        file_extension = in_fn.split('.')[-1].lower()
        file_name, _ = os.path.splitext(in_fn)
        if file_extension == 'rst':
            with open(file_name + '.rdc', 'r') as read_file:
                rdc_content = read_file.read().lower()
                byte_or_integer_binary = "data type   : byte" in rdc_content or (
                        "data type   : integer" in rdc_content and "min. value  : 0" in rdc_content and "max. value  : 1" in rdc_content)
                float_binary = "data type   : real" in rdc_content and "min. value  : 0.0000000" in rdc_content and "max. value  : 1.0000000" in rdc_content
        elif file_extension == 'tif':
            datatype = self.get_image_datatype(in_fn)
            min_val, max_val = self.get_image_max_min(in_fn)
            byte_or_integer_binary = datatype in ['Byte', 'CInt16', 'CInt32', 'Int16', 'Int32', 'UInt16',
                                                      'UInt32'] and max_val == 1 and min_val == 0
            float_binary = datatype in ['Float32', 'Float64', 'CFloat32', 'CFloat64'] and max_val == 1.0000000 and min_val == 0.0000000

        if byte_or_integer_binary or (float_binary):
            # For float_binary, use find_unique_values function to check if data only have two unique values [0.0000000, 1.0000000].
            if float_binary:
                in_ds = gdal.Open(in_fn)
                in_band = in_ds.GetRasterBand(1)
                arr = in_band.ReadAsArray()
                # If more than two unique values are found, it's not a binary map, return False.
                if not self.find_unique_values(arr, 2):
                    return False
            # Binary map: byte_or_integer_binary or float_binary with two unique values [0.0000000, 1.0000000], it returns True.
            return True
        # For any other scenario, it returns False.
        return False

    def process_data3(self):
        try: 
            self.risk30_vp = self.risk30_vp_entry.currentLayer().source()
        except Exception:
            self.risk30_vp = self.risk30_vp_entry.currentText() 
        try:
            self.municipality = self.municipality_entry.currentLayer().source()
        except Exception:
            self.municipality = self.municipality_entry.currentText()
        try:
            self.deforestation_cnf = self.deforestation_cnf_entry.currentLayer().source()
        except Exception:
            self.deforestation_cnf = self.deforestation_cnf_entry.currentText()
            
        images = [self.municipality, self.deforestation_cnf, self.risk30_vp]

        # Check if all images have the same resolution
        resolutions = [self.get_image_resolution(img) for img in images]
        if len(set(resolutions)) != 1:
            QMessageBox.critical(None, "Error", "All the input raster images must have the same spatial resolution!")
            return

        # Check if all images have the same number of rows and columns
        dimensions = [self.get_image_dimensions(img) for img in images]
        if len(set(dimensions)) != 1:
            QMessageBox.critical(None, "Error",
                                 "All the input raster images must have the same number of rows and columns!")
            return

        if not self.municipality or not self.csv or not self.deforestation_cnf or not self.risk30_vp:
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        directory = self.folder_entry.text()

        out_fn1 = self.image1_entry.text()
        if not out_fn1:
            QMessageBox.critical(self, "Error", "Please enter the name of Prediction Modeling Region Map in CNF!")
            return

        if not (out_fn1.endswith('.tif') or out_fn1.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Prediction Modeling Region Map in CNF!")
            return

        out_fn2 = self.image2_entry.text()
        if not out_fn2:
            QMessageBox.critical(self, "Error", "Please enter the name of Adjusted Prediction Density Map in CNF!")
            return

        if not (out_fn2.endswith('.tif') or out_fn2.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Adjusted Prediction Density Map in CNF!")
            return

        max_iterations = self.iteration_entry.text()
        if not max_iterations:
            QMessageBox.critical(self, "Error", "Please enter the max iterations! The suggestion number is 5.")
            return
        try:
            self.max_iterations = int(max_iterations)
        except ValueError:
            QMessageBox.critical(self, "Error", "Max iteration value should be a valid number!")
            return

        if not self.check_binary_map(self.deforestation_cnf):
            QMessageBox.critical(None, "Error",
                                 "'MAP OF DEFORESTATION IN THE CNF' must be a binary map (0 and 1) where the 1’s indicate deforestation.")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            id_difference = self.allocation_tool.execute_workflow_cnf(directory,
                                                            self.max_iterations, self.csv,
                                                            self.municipality,
                                                            self.deforestation_cnf,
                                                            self.risk30_vp, out_fn1,
                                                            out_fn2)
            if self.checkBox.isChecked():
                basename1 = os.path.splitext(os.path.basename(out_fn1))[0]
                basename2 = os.path.splitext(os.path.basename(out_fn2))[0]
                layer1 = QgsRasterLayer(out_fn1, basename1)
                layer2 = QgsRasterLayer(out_fn2, basename2)
                layer1.setDataSource(os.path.join(directory, out_fn1), basename1, 'gdal')
                layer2.setDataSource(os.path.join(directory, out_fn2), basename2, 'gdal')
                QgsProject.instance().addMapLayer(layer1)
                QgsProject.instance().addMapLayer(layer2)
                
            if id_difference.size > 0:
                QMessageBox.warning(self, " Warning ", f"Modeling Region ID {','.join(map(str, id_difference))} do not exist in the Calculation Period. A new CSV has been created for the CAL where relative frequencies for missing bins have been estimated from corresponding vulnerability zones over the entire jurisdiction.")
            QMessageBox.information(self, "Processing Completed", "Processing completed!")
            self.progressDialog.close()

        except Exception as e:
             self.progressDialog.close()
             QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def update_progress(self, value):
        # Update QProgressDialog with the new value
        if self.progressDialog is not None:
            self.progressDialog.setValue(value)

######################################################################################################
        
class MCT_PRE_CNF_SCREEN(QtWidgets.QDialog, FORM_CLASS6):
    def __init__(self, parent=None):
        """Constructor."""
        super(MCT_PRE_CNF_SCREEN, self).__init__(parent)
        # Store the initial directory path
        self.initial_directory = os.getcwd()
        # Set up the user interface from Designer through FORM_CLASS6.
        self.setupUi(self)
        if central_data_store.directory is not None and self.folder_entry is not None:
            self.directory = central_data_store.directory
            self.folder_entry.setText(str(central_data_store.directory))
        self.AT_button4.clicked.connect(self.gotoat4)
        self.Intro_button4.clicked.connect(self.gotointro4)
        self.RMT_button4.clicked.connect(self.gotormt4)
        self.doc_button.clicked.connect(self.openDocument)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.mask_button.clicked.connect(lambda: self.selectRaster(self.mask_entry, 'Mask of Study Area'))
        self.fmask_button.clicked.connect(lambda: self.selectRaster(self.fmask_entry, 'Mask of Forest Area'))
        self.deforestation_cal_button.clicked.connect(lambda: self.selectRaster(self.deforestation_cal_entry, 'Actual Deforestation Map in CAL'))
        self.deforestation_hrp_button.clicked.connect(lambda: self.selectRaster(self.deforestation_hrp_entry, 'Actual Deforestation Map in CNF'))
        self.density_button.clicked.connect(lambda: self.selectRaster(self.density_entry, 'Adjusted Prediction Density Map in CNF'))
        self.ok_button.clicked.connect(self.process_data4)
        self.model_evaluation = ModelEvaluation()
        self.model_evaluation.progress_updated.connect(self.update_progress)
        self.directory = None
        self.mask = None
        self.fmask = None
        self.deforestation_cal = None
        self.deforestation_hrp = None
        self.density = None
        self.grid_area = None
        self.grid_area_entry.setPlaceholderText('Type default 100000 or other number')
        self.title = None
        self.out_fn = None
        self.out_fn_def = None
        self.raster_fn = None
        self.out_fn_entry.setPlaceholderText('e.g., Plot_CNF.png')
        self.out_fn_def_entry.setPlaceholderText('e.g., Acre_Def_Review.tif')
        self.raster_fn_entry.setPlaceholderText('e.g., Acre_Residuals_CNF.tif')
        self.setWindowTitle("JNR Integrated Risk/Allocation Tool")

        # Provide intitial settings for each comboBox
        self.mask_entry.setStyleSheet(style_sheet)
        self.fmask_entry.setStyleSheet(style_sheet)
        self.deforestation_cal_entry.setStyleSheet(style_sheet)
        self.deforestation_hrp_entry.setStyleSheet(style_sheet)
        self.density_entry.setStyleSheet(style_sheet)
        
        self.mask_entry.setCurrentIndex(-1)
        self.fmask_entry.setCurrentIndex(-1)
        self.deforestation_cal_entry.setCurrentIndex(-1)
        self.deforestation_hrp_entry.setCurrentIndex(-1)
        self.density_entry.setCurrentIndex(-1)
        
        self.mask_entry.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.fmask_entry.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.deforestation_cal_entry.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.deforestation_hrp_entry.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.density_entry.setFilters(QgsMapLayerProxyModel.RasterLayer)

    def gotoat4(self):
        os.chdir(self.initial_directory)
        at4 = AT_PRE_CNF_SCREEN()
        stacked_widget.addWidget(at4)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def gotointro4(self):
        os.chdir(self.initial_directory)
        intro4 = IntroScreen()
        stacked_widget.addWidget(intro4)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def gotormt4(self):
        os.chdir(self.initial_directory)
        rmt4 = RMT_PRE_CNF_SCREEN()
        stacked_widget.addWidget(rmt4)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def openDocument(self):
        pdf_path = os.path.join(os.path.dirname(__file__), "doc\\TestPreMA.pdf")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path = Path(data_folder)
        self.directory = str(data_folder_path)
        self.folder_entry.setText(self.directory)
        central_data_store.directory = self.directory

    def selectRaster(self, comboBox, string):
        """
        Opening the raster layer file and adding the path to the combobox
        on end of the list with comboBox items.

        :param comboBox: Qt combobox.
        :type comboBox: QComboBox
        """
        rast_path = QFileDialog.getOpenFileName(self, string)
        index = comboBox.currentIndex()
        comboBox.setAdditionalItems([rast_path[0]])
        ind = comboBox.count() - 1
        comboBox.setCurrentIndex(ind)

    def get_image_resolution(self, image):
        # Set up a GDAL dataset
        in_ds = gdal.Open(image)
        # Set up a GDAL band
        P = in_ds.GetGeoTransform()[1]
        # Create Numpy Array1
        return P

    def get_image_dimensions(self, image):
        dataset = gdal.Open(image)
        cols = dataset.RasterXSize
        rows = dataset.RasterYSize
        return rows, cols

    def get_image_datatype(self, image):
        in_ds = gdal.Open(image)
        in_band = in_ds.GetRasterBand(1)
        datatype = gdal.GetDataTypeName(in_band.DataType)
        return datatype

    def get_image_max_min(self, image):
        in_ds = gdal.Open(image)
        in_band = in_ds.GetRasterBand(1)
        min, max= in_band.ComputeRasterMinMax()
        return min, max

    def find_unique_values(self, arr, limit=2):
        unique_values = set()
        for value in np.nditer(arr):
            unique_values.add(value.item())
            if len(unique_values) > limit:
                return False
        return True

    def check_binary_map(self, in_fn):
        '''
        Check if input image is binary map
        :param in_fn: input image
        :return: True if the file is a binary map, False otherwise
        '''
        file_extension = in_fn.split('.')[-1].lower()
        file_name, _ = os.path.splitext(in_fn)
        if file_extension == 'rst':
            with open(file_name + '.rdc', 'r') as read_file:
                rdc_content = read_file.read().lower()
                byte_or_integer_binary = "data type   : byte" in rdc_content or (
                        "data type   : integer" in rdc_content and "min. value  : 0" in rdc_content and "max. value  : 1" in rdc_content)
                float_binary = "data type   : real" in rdc_content and "min. value  : 0.0000000" in rdc_content and "max. value  : 1.0000000" in rdc_content
        elif file_extension == 'tif':
            datatype = self.get_image_datatype(in_fn)
            min_val, max_val = self.get_image_max_min(in_fn)
            byte_or_integer_binary = datatype in ['Byte', 'CInt16', 'CInt32', 'Int16', 'Int32', 'UInt16',
                                                      'UInt32'] and max_val == 1 and min_val == 0
            float_binary = datatype in ['Float32', 'Float64', 'CFloat32', 'CFloat64'] and max_val == 1.0000000 and min_val == 0.0000000

        if byte_or_integer_binary or (float_binary):
            # For float_binary, use find_unique_values function to check if data only have two unique values [0.0000000, 1.0000000].
            if float_binary:
                in_ds = gdal.Open(in_fn)
                in_band = in_ds.GetRasterBand(1)
                arr = in_band.ReadAsArray()
                # If more than two unique values are found, it's not a binary map, return False.
                if not self.find_unique_values(arr, 2):
                    return False
            # Binary map: byte_or_integer_binary or float_binary with two unique values [0.0000000, 1.0000000], it returns True.
            return True
        # For any other scenario, it returns False.
        return False

    def process_data4(self):
        try: 
            self.mask = self.mask_entry.currentLayer().source()
        except Exception:
            self.mask = self.mask_entry.currentText()
        try: 
            self.fmask = self.fmask_entry.currentLayer().source()
        except Exception:
            self.fmask = self.fmask_entry.currentText() 
        try:
            self.deforestation_cal = self.deforestation_cal_entry.currentLayer().source()
        except Exception:
            self.deforestation_cal = self.deforestation_cal_entry.currentText()
        try:
            self.deforestation_hrp = self.deforestation_hrp_entry.currentLayer().source()
        except Exception:
            self.deforestation_hrp = self.deforestation_hrp_entry.currentText()
        try: 
            self.density = self.density_entry.currentLayer().source()
        except Exception:
            self.density = self.density_entry.currentText()

        images = [self.mask, self.fmask, self.deforestation_cal, self.deforestation_hrp, self.density]

        # Check if all images have the same resolution
        resolutions = [self.get_image_resolution(img) for img in images]
        if len(set(resolutions)) != 1:
            QMessageBox.critical(None, "Error", "All the input raster images must have the same spatial resolution!")
            return

        # Check if all images have the same number of rows and columns
        dimensions = [self.get_image_dimensions(img) for img in images]
        if len(set(dimensions)) != 1:
            QMessageBox.critical(None, "Error",
                                 "All the input raster images must have the same number of rows and columns!")
            return

        if not self.mask or not self.fmask or not self.deforestation_cal or not self.deforestation_hrp or not self.density :
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        grid_area = self.grid_area_entry.text()
        if not grid_area:
            QMessageBox.critical(self, "Error", "Please enter the thiessen polygon grid area value!")
            return
        try:
            self.grid_area = float(grid_area)
            if not (0 < self.grid_area):
                QMessageBox.critical(self, "Error", "Thiessen polygon grid area value should larger than 0!")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "Thiessen polygon grid area value should be a valid number!")
            return

        xmax = self.xmax_entry.text()
        if xmax.lower() != "default":
            try:
                xmax = float(xmax)
                if xmax <= 0:
                    raise ValueError("The plot x-axis limit should be larger than 0!")
            except ValueError:
                QMessageBox.critical(self, "Error", "The plot x-axis limit should be a valid number or 'Default'!")
                return

        ymax = self.ymax_entry.text()
        if ymax.lower() != "default":
            try:
                ymax = float(ymax)
                if ymax <= 0:
                    raise ValueError("The plot y-axis limit should be larger than 0!")
            except ValueError:
                QMessageBox.critical(self, "Error", "The plot y-axis limit should be a valid number or 'Default'!")
                return

        title = self.title_entry.text()
        if not title:
            QMessageBox.critical(self, "Error", "Please enter the title of plot!")
            return

        directory = self.folder_entry.text()

        out_fn = self.out_fn_entry.text()
        if not out_fn:
            QMessageBox.critical(self, "Error", "Please enter the name used for the plot, performace chart and assessment polygons!")
            return

        # Check if the out_fn has the correct file extension
        if not (out_fn.endswith('.png') or out_fn.endswith('.jpg') or out_fn.endswith('.pdf') or out_fn.endswith(
                '.svg') or out_fn.endswith('.eps') or out_fn.endswith('.ps') or out_fn.endswith('.tif')):
            QMessageBox.critical(self, "Error",
                                 "Please enter extension(.png/.jpg/.pdf/.svg/.eps/.ps/.tif) in the name of plot!")
            return

        raster_fn = self.raster_fn_entry.text()
        if not raster_fn:
            QMessageBox.critical(self, "Error", "Please enter the name for Residual Map!")
            return

        if not (raster_fn.endswith('.tif') or raster_fn.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Residual Map!")
            return

        out_fn_def = self.out_fn_def_entry.text()
        if not out_fn_def:
            QMessageBox.critical(self, "Error", "Please enter the name for Combined Deforestation Reference Map!")
            return

        if not (out_fn_def.endswith('.tif') or out_fn_def.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Combined Deforestation Reference Map!")
            return

        if not self.check_binary_map(self.mask):
            QMessageBox.critical(None, "Error",
                                 "'MASK OF THE NON-EXCLUDED JURISDICTION' must be a binary map (0 and 1) where the 1’s indicate areas inside the jurisdiction.")
            return

        if not self.check_binary_map(self.deforestation_hrp):
            QMessageBox.critical(None, "Error",
                                 "'MAP OF DEFORESTATION IN THE CNF' must be a binary map (0 and 1) where the 1’s indicate deforestation.")
            return

        if not self.check_binary_map(self.deforestation_cal):
            QMessageBox.critical(None, "Error",
                                 "'MAP OF DEFORESTATION IN THE CAL' must be a binary map (0 and 1) where the 1’s indicate deforestation.")
            return

        if not self.check_binary_map(self.fmask):
            QMessageBox.critical(None, "Error",
                                 "'MASK OF FOREST AREAS IN THE CAL' must be a binary map (0 and 1) where the 1’s indicate forest areas.")
            return


        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.model_evaluation.set_working_directory(directory)
            self.model_evaluation.create_mask_polygon(self.mask)
            clipped_gdf = self.model_evaluation.create_thiessen_polygon(self.grid_area, self.mask, self.density,
                                                                             self.deforestation_hrp, out_fn, raster_fn)
            self.model_evaluation.replace_ref_system(self.mask, raster_fn)
            self.model_evaluation.create_deforestation_map(self.fmask, self.deforestation_cal, self.deforestation_hrp,
                                                           out_fn_def)
            self.model_evaluation.replace_ref_system(self.fmask, out_fn_def)
            self.model_evaluation.replace_legend(out_fn_def)
            self.model_evaluation.create_plot(grid_area,clipped_gdf, title, out_fn, xmax, ymax)
            self.model_evaluation.remove_temp_files()

            if self.checkBox.isChecked():
                basename1 = os.path.splitext(os.path.basename(raster_fn))[0]
                basename2 = os.path.splitext(os.path.basename(out_fn_def))[0]
                layer1 = QgsRasterLayer(raster_fn, basename1)
                layer2 = QgsRasterLayer(out_fn_def, basename2)
                layer1.setDataSource(os.path.join(directory, raster_fn), basename1, 'gdal')
                layer2.setDataSource(os.path.join(directory, out_fn_def), basename2, 'gdal')
                QgsProject.instance().addMapLayer(layer1)
                QgsProject.instance().addMapLayer(layer2)

            QMessageBox.information(self, "Processing Completed", "Processing completed!")
            self.progressDialog.close()

        except Exception as e:
             self.progressDialog.close()
             QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def update_progress(self, value):
        # Update QProgressDialog with the new value
        if self.progressDialog is not None:
            self.progressDialog.setValue(value)

######################################################################################################
        
class RMT_FIT_HRP_SCREEN(QtWidgets.QDialog, FORM_CLASS7):
    def __init__(self, parent=None):
        """Constructor."""
        super(RMT_FIT_HRP_SCREEN, self).__init__(parent)
        # Store the initial directory path
        self.initial_directory = os.getcwd()
        # Set up the user interface from Designer through FORM_CLASS7.
        self.setupUi(self)
        if central_data_store.directory is not None and self.folder_entry is not None:
            self.directory = central_data_store.directory
            self.folder_entry.setText(str(central_data_store.directory))
        if central_data_store.directory is not None and self.folder_entry_2 is not None:
            self.directory_2 = central_data_store.directory
            self.folder_entry_2.setText(str(central_data_store.directory))
        self.AT_button2.clicked.connect(self.gotoat2)
        self.Intro_button2.clicked.connect(self.gotointro2)

        self.doc_button = self.tab1.findChild(QWidget, "doc_button")
        self.select_folder_button = self.tab1.findChild(QWidget, "select_folder_button")
        self.fd_button = self.tab1.findChild(QWidget, "fd_button")
        self.ok_button2 = self.tab1.findChild(QWidget, "ok_button2")

        self.doc_button_2 = self.tab2.findChild(QWidget, "doc_button_2")
        self.select_folder_button_2 = self.tab2.findChild(QWidget, "select_folder_button_2")
        self.mask_button_2 = self.tab2.findChild(QWidget, "mask_button_2")
        self.fmask_button_2 = self.tab2.findChild(QWidget, "fmask_button_2")
        self.fd_button_2 = self.tab2.findChild(QWidget, "fd_button_2")
        self.ok_button2_2 = self.tab2.findChild(QWidget, "ok_button2_2")

        self.doc_button.clicked.connect(self.openDocument)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.fd_button.clicked.connect(lambda: self.selectRaster(self.in_fn_entry, 'Map of Distance from the Forest Edge in HRP'))
        self.ok_button2.clicked.connect(self.process_data2)

        self.doc_button_2.clicked.connect(self.openDocument_2)
        self.select_folder_button_2.clicked.connect(self.select_working_directory_2)
        self.fd_button_2.clicked.connect(lambda: self.selectRaster(self.in_fn_entry_2, 'Map of Empirical transition potential for HRP'))
        self.fmask_button_2.clicked.connect(lambda: self.selectRaster(self.fmask_entry_2, 'Mask of Forest Area'))
        self.mask_button_2.clicked.connect(lambda: self.selectRaster(self.mask_entry_2, 'Mask of Study Area'))
        self.ok_button2_2.clicked.connect(self.process_data2_2)

        self.vulnerability_map = VulnerabilityMap()
        self.vulnerability_map.progress_updated.connect(self.update_progress)
        self.directory = None
        self.in_fn = None
        self.NRT = None
        if central_data_store.NRT is not None:
            self.nrt_entry.setText(str(central_data_store.NRT))
        self.n_classes = None
        self.out_fn = None
        self.out_fn_entry.setPlaceholderText('e.g., Acre_Vulnerability_HRP.tif')

        self.directory_2 = None
        self.mask_2 = None
        self.fmask_2 = None
        self.in_fn_2 = None
        self.out_fn_2 = None
        self.n_classes_2 = None
        self.out_fn_entry_2.setPlaceholderText('e.g., Acre_Vulnerability_HRP.tif')

        self.setWindowTitle("JNR Integrated Risk/Allocation Tool")

        # Provide intitial settings for each comboBox
        self.in_fn_entry.setStyleSheet(style_sheet)
        self.in_fn_entry_2.setStyleSheet(style_sheet)
        self.fmask_entry_2.setStyleSheet(style_sheet)
        self.mask_entry_2.setStyleSheet(style_sheet)
        
        self.in_fn_entry.setCurrentIndex(-1)
        self.in_fn_entry_2.setCurrentIndex(-1)
        self.fmask_entry_2.setCurrentIndex(-1)
        self.mask_entry_2.setCurrentIndex(-1)
        
        self.in_fn_entry.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.in_fn_entry_2.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.fmask_entry_2.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.mask_entry_2.setFilters(QgsMapLayerProxyModel.RasterLayer)

    def gotoat2(self):
        os.chdir(self.initial_directory)
        at2 = AT_FIT_HRP_SCREEN()
        stacked_widget.addWidget(at2)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def gotointro2(self):
        os.chdir(self.initial_directory)
        intro2 = IntroScreen()
        stacked_widget.addWidget(intro2)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def openDocument(self):
        pdf_path = os.path.join(os.path.dirname(__file__), "doc\\AppFitVM.pdf")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def openDocument_2(self):
        pdf_path = os.path.join(os.path.dirname(__file__), "doc\\AppFitVM.pdf")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path = Path(data_folder)
        self.directory = str(data_folder_path)
        self.folder_entry.setText(self.directory)
        self.folder_entry_2.setText(self.directory)
        central_data_store.directory = self.directory

    def selectRaster(self, comboBox, string):
        """
        Opening the raster layer file and adding the path to the combobox
        on end of the list with comboBox items.

        :param comboBox: Qt combobox.
        :type comboBox: QComboBox
        """
        rast_path = QFileDialog.getOpenFileName(self, string)
        index = comboBox.currentIndex()
        comboBox.setAdditionalItems([rast_path[0]])
        ind = comboBox.count() - 1
        comboBox.setCurrentIndex(ind)

    def select_working_directory_2(self):
        data_folder_2 = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path_2 = Path(data_folder_2)
        self.directory_2 = str(data_folder_path_2)
        self.folder_entry_2.setText(self.directory_2)
        self.folder_entry.setText(self.directory_2)
        central_data_store.directory = self.directory_2

    def process_data2(self):
        try: 
            self.in_fn = self.in_fn_entry.currentLayer().source()
        except Exception:
            self.in_fn = self.in_fn_entry.currentText()
            
        if not self.in_fn:
            QMessageBox.critical(self, "Error", "Please select the input file!")
            return

        NRT = self.nrt_entry.text()
        if not NRT:
            QMessageBox.critical(self, "Error", "Please enter the NRT value!")
            return
        try:
            self.NRT = int(NRT)
            if (self.NRT <= 0):
                QMessageBox.critical(self, "Error", "NRT value should be larger than 0!")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "NRT value should be a valid number!")
            return

        n_classes = int(29)
        if not n_classes:
            QMessageBox.critical(self, "Error", "Please enter the number of classes!")
            return
        try:
            self.n_classes = int(n_classes)
            if (self.n_classes <= 0):
                QMessageBox.critical(self, "Error", "Number of classes should be larger than 0!")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "Number of classes value should be a valid number!")
            return

        directory = self.folder_entry.text()

        out_fn = self.out_fn_entry.text()
        if not out_fn:
            QMessageBox.critical(self, "Error", "Please enter the name of Vulnerability Map in HRP!")
            return

        if not (out_fn.endswith('.tif') or out_fn.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Vulnerability Map in HRP!")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.vulnerability_map.set_working_directory(directory)
            mask_arr = self.vulnerability_map.geometric_classification(self.in_fn, NRT, n_classes)
            self.vulnerability_map.array_to_image(self.in_fn, out_fn, mask_arr, gdal.GDT_Int16, -1)
            self.vulnerability_map.replace_ref_system(self.in_fn, out_fn)

            if self.checkBox.isChecked():
                basename = os.path.splitext(os.path.basename(out_fn))[0]
                layer = QgsRasterLayer(out_fn, basename)
                layer.setDataSource(os.path.join(directory, out_fn), basename, 'gdal')
                QgsProject.instance().addMapLayer(layer)

            QMessageBox.information(self, "Processing Completed", "Processing completed!")
            self.progressDialog.close()

        except Exception as e:
            self.progressDialog.close()
            QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def get_image_resolution(self, image):
        # Set up a GDAL dataset
        in_ds = gdal.Open(image)
        # Set up a GDAL band
        P = in_ds.GetGeoTransform()[1]
        # Create Numpy Array1
        return P

    def get_image_dimensions(self, image):
        dataset = gdal.Open(image)
        cols = dataset.RasterXSize
        rows = dataset.RasterYSize
        return rows, cols

    def get_image_datatype(self, image):
        in_ds = gdal.Open(image)
        in_band = in_ds.GetRasterBand(1)
        datatype = gdal.GetDataTypeName(in_band.DataType)
        return datatype

    def get_image_max_min(self, image):
        in_ds = gdal.Open(image)
        in_band = in_ds.GetRasterBand(1)
        min, max= in_band.ComputeRasterMinMax()
        return min, max

    def find_unique_values(self, arr, limit=2):
        unique_values = set()
        for value in np.nditer(arr):
            unique_values.add(value.item())
            if len(unique_values) > limit:
                return False
        return True

    def check_binary_map(self, in_fn):
        '''
        Check if input image is binary map
        :param in_fn: input image
        :return: True if the file is a binary map, False otherwise
        '''
        file_extension = in_fn.split('.')[-1].lower()
        file_name, _ = os.path.splitext(in_fn)
        if file_extension == 'rst':
            with open(file_name + '.rdc', 'r') as read_file:
                rdc_content = read_file.read().lower()
                byte_or_integer_binary = "data type   : byte" in rdc_content or (
                        "data type   : integer" in rdc_content and "min. value  : 0" in rdc_content and "max. value  : 1" in rdc_content)
                float_binary = "data type   : real" in rdc_content and "min. value  : 0.0000000" in rdc_content and "max. value  : 1.0000000" in rdc_content
        elif file_extension == 'tif':
            datatype = self.get_image_datatype(in_fn)
            min_val, max_val = self.get_image_max_min(in_fn)
            byte_or_integer_binary = datatype in ['Byte', 'CInt16', 'CInt32', 'Int16', 'Int32', 'UInt16',
                                                      'UInt32'] and max_val == 1 and min_val == 0
            float_binary = datatype in ['Float32', 'Float64', 'CFloat32', 'CFloat64'] and max_val == 1.0000000 and min_val == 0.0000000

        if byte_or_integer_binary or (float_binary):
            # For float_binary, use find_unique_values function to check if data only have two unique values [0.0000000, 1.0000000].
            if float_binary:
                in_ds = gdal.Open(in_fn)
                in_band = in_ds.GetRasterBand(1)
                arr = in_band.ReadAsArray()
                # If more than two unique values are found, it's not a binary map, return False.
                if not self.find_unique_values(arr, 2):
                    return False
            # Binary map: byte_or_integer_binary or float_binary with two unique values [0.0000000, 1.0000000], it returns True.
            return True
        # For any other scenario, it returns False.
        return False

    def process_data2_2(self):
        try: 
            self.in_fn_2 = self.in_fn_entry_2.currentLayer().source()
        except Exception:
            self.in_fn_2 = self.in_fn_entry_2.currentText() 
        try:
            self.mask_2 = self.mask_entry_2.currentLayer().source()
        except Exception:
            self.mask_2 = self.mask_entry_2.currentText()
        try:
            self.fmask_2 = self.fmask_entry_2.currentLayer().source()
        except Exception:
            self.fmask_2 = self.fmask_entry_2.currentText()
            
        images = [self.in_fn_2, self.mask_2, self.fmask_2]

        # Check if all images have the same resolution
        resolutions = [self.get_image_resolution(img) for img in images]
        if len(set(resolutions)) != 1:
            QMessageBox.critical(None, "Error", "All the input raster images must have the same spatial resolution!")
            return

        # Check if all images have the same number of rows and columns
        dimensions = [self.get_image_dimensions(img) for img in images]
        if len(set(dimensions)) != 1:
            QMessageBox.critical(None, "Error",
                                 "All the input raster images must have the same number of rows and columns!")
            return

        if not self.in_fn_2 or not self.mask_2 or not self.fmask_2:
            QMessageBox.critical(self, "Error", "Please select  the input file!")
            return
        n_classes_2 = int(30)
        directory_2 = self.folder_entry_2.text()
        out_fn_2 = self.out_fn_entry_2.text()
        if not out_fn_2:
            QMessageBox.critical(self, "Error", "Please enter the name of Vulnerability Map in HRP!")
            return

        # Check if the out_fn has the correct file extension
        if not (out_fn_2.endswith('.tif') or out_fn_2.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Vulnerability Map in HRP!")
            return

        if not self.check_binary_map(self.mask_2):
            QMessageBox.critical(None, "Error",
                                 "'MASK OF THE NON-EXCLUDED JURISDICTION' must be a binary map (0 and 1) where the 1’s indicate areas inside the jurisdiction.")
            return

        if not self.check_binary_map(self.fmask_2):
            QMessageBox.critical(None, "Error",
                                 "'MASK OF FOREST AREAS IN THE HRP' must be a binary map (0 and 1) where the 1’s indicate forest areas.")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.vulnerability_map.set_working_directory(directory_2)
            mask_arr = self.vulnerability_map.geometric_classification_alternative(self.in_fn_2, n_classes_2,
                                                                                   self.mask_2, self.fmask_2)
            self.vulnerability_map.array_to_image(self.in_fn_2, out_fn_2, mask_arr, gdal.GDT_Int16, -1)
            self.vulnerability_map.replace_ref_system(self.in_fn_2, out_fn_2)

            if self.checkBox_2.isChecked():
                basename = os.path.splitext(os.path.basename(out_fn_2))[0]
                layer = QgsRasterLayer(out_fn_2, basename)
                layer.setDataSource(os.path.join(directory_2, out_fn_2), basename, 'gdal')
                QgsProject.instance().addMapLayer(layer)

            QMessageBox.information(self, "Processing Completed", "Processing completed!")

            self.progressDialog.close()

        except Exception as e:
            self.progressDialog.close()
            QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def update_progress(self, value):
        # Update QProgressDialog with the new value
        if self.progressDialog is not None:
            self.progressDialog.setValue(value)

######################################################################################################
        
class AT_FIT_HRP_SCREEN(QtWidgets.QDialog, FORM_CLASS8):
    def __init__(self, parent=None):
        """Constructor."""
        super(AT_FIT_HRP_SCREEN, self).__init__(parent)
        # Store the initial directory path
        self.initial_directory = os.getcwd()
        # Set up the user interface from Designer through FORM_CLASS8.
        self.setupUi(self)
        if central_data_store.directory is not None and self.folder_entry is not None:
            self.directory = central_data_store.directory
            self.folder_entry.setText(str(central_data_store.directory))
        self.Intro_button3.clicked.connect(self.gotointro3)
        self.RMT_button3.clicked.connect(self.gotormt3)
        self.doc_button.clicked.connect(self.openDocument)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.municipality_button.clicked.connect(lambda: self.selectRaster(self.municipality_entry, 'Map of Administrative Divisions'))
        self.risk30_hrp_button.clicked.connect(lambda: self.selectRaster(self.risk30_hrp_entry, 'Vulnerability Map in HRP'))
        self.deforestation_hrp_button.clicked.connect(lambda: self.selectRaster(self.deforestation_hrp_entry, 'Map of Deforestation in the HRP'))
        self.ok_button3.clicked.connect(self.process_data3)
        self.allocation_tool = AllocationTool()
        self.allocation_tool.progress_updated.connect(self.update_progress)
        self.directory = None
        self.risk30_hrp = None
        self.municipality = None
        self.deforestation_hrp = None
        self.out_fn1 = None
        self.out_fn2 = None
        self.csv_name = None
        self.image1_entry.setPlaceholderText('e.g., Acre_Modeling_Region_HRP.tif')
        self.csv_entry.setPlaceholderText('e.g., Relative_Frequency_Table_HRP.csv')
        self.image2_entry.setPlaceholderText('e.g., Acre_Fitted_Density_Map_HRP.tif')

        self.setWindowTitle("JNR Integrated Risk/Allocation Tool")

        # Provide intitial settings for each comboBox
        self.municipality_entry.setStyleSheet(style_sheet)
        self.risk30_hrp_entry.setStyleSheet(style_sheet)
        self.deforestation_hrp_entry.setStyleSheet(style_sheet)
        
        self.municipality_entry.setCurrentIndex(-1)
        self.risk30_hrp_entry.setCurrentIndex(-1)
        self.deforestation_hrp_entry.setCurrentIndex(-1)
        
        self.municipality_entry.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.risk30_hrp_entry.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.deforestation_hrp_entry.setFilters(QgsMapLayerProxyModel.RasterLayer)

    def gotormt3(self):
        os.chdir(self.initial_directory)
        rmt3 = RMT_FIT_HRP_SCREEN()
        stacked_widget.addWidget(rmt3)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def gotointro3(self):
        os.chdir(self.initial_directory)
        intro3 = IntroScreen()
        stacked_widget.addWidget(intro3)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def openDocument(self):
        pdf_path = os.path.join(os.path.dirname(__file__), "doc\\AppFitAM.pdf")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path = Path(data_folder)
        self.directory = str(data_folder_path)
        self.folder_entry.setText(self.directory)
        central_data_store.directory = self.directory

    def selectRaster(self, comboBox, string):
        """
        Opening the raster layer file and adding the path to the combobox
        on end of the list with comboBox items.

        :param comboBox: Qt combobox.
        :type comboBox: QComboBox
        """
        rast_path = QFileDialog.getOpenFileName(self, string)
        index = comboBox.currentIndex()
        comboBox.setAdditionalItems([rast_path[0]])
        ind = comboBox.count() - 1
        comboBox.setCurrentIndex(ind)

    def get_image_resolution(self, image):
        # Set up a GDAL dataset
        in_ds = gdal.Open(image)
        # Set up a GDAL band
        P = in_ds.GetGeoTransform()[1]
        # Create Numpy Array1
        return P

    def get_image_dimensions(self, image):
        dataset = gdal.Open(image)
        cols = dataset.RasterXSize
        rows = dataset.RasterYSize
        return rows, cols

    def get_image_datatype(self, image):
        in_ds = gdal.Open(image)
        in_band = in_ds.GetRasterBand(1)
        datatype = gdal.GetDataTypeName(in_band.DataType)
        return datatype

    def get_image_max_min(self, image):
        in_ds = gdal.Open(image)
        in_band = in_ds.GetRasterBand(1)
        min, max= in_band.ComputeRasterMinMax()
        return min, max

    def find_unique_values(self, arr, limit=2):
        unique_values = set()
        for value in np.nditer(arr):
            unique_values.add(value.item())
            if len(unique_values) > limit:
                return False
        return True

    def check_binary_map(self, in_fn):
        '''
        Check if input image is binary map
        :param in_fn: input image
        :return: True if the file is a binary map, False otherwise
        '''
        file_extension = in_fn.split('.')[-1].lower()
        file_name, _ = os.path.splitext(in_fn)
        if file_extension == 'rst':
            with open(file_name + '.rdc', 'r') as read_file:
                rdc_content = read_file.read().lower()
                byte_or_integer_binary = "data type   : byte" in rdc_content or (
                        "data type   : integer" in rdc_content and "min. value  : 0" in rdc_content and "max. value  : 1" in rdc_content)
                float_binary = "data type   : real" in rdc_content and "min. value  : 0.0000000" in rdc_content and "max. value  : 1.0000000" in rdc_content
        elif file_extension == 'tif':
            datatype = self.get_image_datatype(in_fn)
            min_val, max_val = self.get_image_max_min(in_fn)
            byte_or_integer_binary = datatype in ['Byte', 'CInt16', 'CInt32', 'Int16', 'Int32', 'UInt16',
                                                      'UInt32'] and max_val == 1 and min_val == 0
            float_binary = datatype in ['Float32', 'Float64', 'CFloat32', 'CFloat64'] and max_val == 1.0000000 and min_val == 0.0000000

        if byte_or_integer_binary or (float_binary):
            # For float_binary, use find_unique_values function to check if data only have two unique values [0.0000000, 1.0000000].
            if float_binary:
                in_ds = gdal.Open(in_fn)
                in_band = in_ds.GetRasterBand(1)
                arr = in_band.ReadAsArray()
                # If more than two unique values are found, it's not a binary map, return False.
                if not self.find_unique_values(arr, 2):
                    return False
            # Binary map: byte_or_integer_binary or float_binary with two unique values [0.0000000, 1.0000000], it returns True.
            return True
        # For any other scenario, it returns False.
        return False

    def process_data3(self):
        try: 
            self.risk30_hrp = self.risk30_hrp_entry.currentLayer().source()
        except Exception:
            self.risk30_hrp = self.risk30_hrp_entry.currentText() 
        try:
            self.municipality = self.municipality_entry.currentLayer().source()
        except Exception:
            self.municipality = self.municipality_entry.currentText()
        try:
            self.deforestation_hrp = self.deforestation_hrp_entry.currentLayer().source()
        except Exception:
            self.deforestation_hrp = self.deforestation_hrp_entry.currentText()
            
        images = [self.risk30_hrp, self.municipality, self.deforestation_hrp]

        # Check if all images have the same resolution
        resolutions = [self.get_image_resolution(img) for img in images]
        if len(set(resolutions)) != 1:
            QMessageBox.critical(None, "Error", "All the input raster images must have the same spatial resolution!")
            return

        # Check if all images have the same number of rows and columns
        dimensions = [self.get_image_dimensions(img) for img in images]
        if len(set(dimensions)) != 1:
            QMessageBox.critical(None, "Error",
                                 "All the input raster images must have the same number of rows and columns!")
            return
        if not self.risk30_hrp or not self.municipality or not self.deforestation_hrp:
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        directory = self.folder_entry.text()

        out_fn1 = self.image1_entry.text()
        if not out_fn1:
            QMessageBox.critical(self, "Error", "Please enter the name for Modeling Region Map in HRP!")
            return

        if not (out_fn1.endswith('.tif') or out_fn1.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name for Modeling Region Map in HRP!")
            return

        csv_name = self.csv_entry.text()
        if not csv_name:
            QMessageBox.critical(self, "Error", "Please enter the name for the Relative Frequency Table!")
            return

        if not (csv_name.endswith('.csv')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .csv extension in the name of Relative Frequency Table!")
            return

        out_fn2 = self.image2_entry.text()
        if not out_fn2:
            QMessageBox.critical(self, "Error", "Please enter the name for Fitted Density Map in the HRP!")
            return

        if not (out_fn2.endswith('.tif') or out_fn2.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Fitted Density Map in the HRP!")
            return

        if not self.check_binary_map(self.deforestation_hrp):
            QMessageBox.critical(None, "Error",
                                 "'MAP OF DEFORESTATION IN THE HRP' must be a binary map (0 and 1) where the 1’s indicate deforestation.")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.allocation_tool.execute_workflow_fit(directory, self.risk30_hrp,
                                                        self.municipality,self.deforestation_hrp, csv_name,
                                                        out_fn1,out_fn2)

            if self.checkBox.isChecked():
                basename1 = os.path.splitext(os.path.basename(out_fn1))[0]
                basename2 = os.path.splitext(os.path.basename(out_fn2))[0]
                layer1 = QgsRasterLayer(out_fn1, basename1)
                layer2 = QgsRasterLayer(out_fn2, basename2)
                layer1.setDataSource(os.path.join(directory, out_fn1), basename1, 'gdal')
                layer2.setDataSource(os.path.join(directory, out_fn2), basename2, 'gdal')
                QgsProject.instance().addMapLayer(layer1)
                QgsProject.instance().addMapLayer(layer2)
                
            QMessageBox.information(self, "Processing Completed", "Processing completed!")
            self.progressDialog.close()

        except Exception as e:
             self.progressDialog.close()
             QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def update_progress(self, value):
        # Update QProgressDialog with the new value
        if self.progressDialog is not None:
            self.progressDialog.setValue(value)

######################################################################################################
        
class RMT_PRE_VP_SCREEN(QtWidgets.QDialog, FORM_CLASS9):
    def __init__(self, parent=None):
        """Constructor."""
        super(RMT_PRE_VP_SCREEN, self).__init__(parent)
        # Store the initial directory path
        self.initial_directory = os.getcwd()
        # Set up the user interface from Designer through FORM_CLASS9.
        self.setupUi(self)
        if central_data_store.directory is not None and self.folder_entry is not None:
            self.directory = central_data_store.directory
            self.folder_entry.setText(str(central_data_store.directory))
        if central_data_store.directory is not None and self.folder_entry_2 is not None:
            self.directory_2 = central_data_store.directory
            self.folder_entry_2.setText(str(central_data_store.directory))
        self.AT_button2.clicked.connect(self.gotoat2)
        self.Intro_button2.clicked.connect(self.gotointro2)

        self.doc_button = self.tab1.findChild(QWidget, "doc_button")
        self.select_folder_button = self.tab1.findChild(QWidget, "select_folder_button")
        self.fd_button = self.tab1.findChild(QWidget, "fd_button")
        self.ok_button2 = self.tab1.findChild(QWidget, "ok_button2")

        self.doc_button_2 = self.tab2.findChild(QWidget, "doc_button_2")
        self.select_folder_button_2 = self.tab2.findChild(QWidget, "select_folder_button_2")
        self.mask_button_2 = self.tab2.findChild(QWidget, "mask_button_2")
        self.fmask_button_2 = self.tab2.findChild(QWidget, "fmask_button_2")
        self.fd_button_2 = self.tab2.findChild(QWidget, "fd_button_2")
        self.ok_button2_2 = self.tab2.findChild(QWidget, "ok_button2_2")

        self.doc_button.clicked.connect(self.openDocument)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.fd_button.clicked.connect(lambda: self.selectRaster(self.in_fn_entry, 'Map of Distance from the Forest Edge in VP'))
        self.ok_button2.clicked.connect(self.process_data2)

        self.doc_button_2.clicked.connect(self.openDocument_2)
        self.select_folder_button_2.clicked.connect(self.select_working_directory_2)
        self.fd_button_2.clicked.connect(lambda: self.selectRaster(self.in_fn_entry_2, 'Map of Empirical transition potential for VP'))
        self.fmask_button_2.clicked.connect(lambda: self.selectRaster(self.fmask_entry_2, 'Mask of Forest Area'))
        self.mask_button_2.clicked.connect(lambda: self.selectRaster(self.mask_entry_2, 'Mask of Study Area'))
        self.ok_button2_2.clicked.connect(self.process_data2_2)

        self.vulnerability_map = VulnerabilityMap()
        self.vulnerability_map.progress_updated.connect(self.update_progress)
        self.directory = None
        self.in_fn = None
        self.NRT = None
        if central_data_store.NRT is not None:
            self.nrt_entry.setText(str(central_data_store.NRT))
        self.n_classes = None
        self.out_fn = None
        self.out_fn_entry.setPlaceholderText('e.g., Acre_Vulnerability_VP.tif')

        self.directory_2 = None
        self.mask_2 = None
        self.fmask_2 = None
        self.in_fn_2 = None
        self.out_fn_2 = None
        self.n_classes_2 = None
        self.out_fn_entry_2.setPlaceholderText('e.g., Acre_Vulnerability_VP.tif')

        self.setWindowTitle("JNR Integrated Risk/Allocation Tool")

        # Provide intitial settings for each comboBox
        self.in_fn_entry.setStyleSheet(style_sheet)
        self.in_fn_entry_2.setStyleSheet(style_sheet)
        self.fmask_entry_2.setStyleSheet(style_sheet)
        self.mask_entry_2.setStyleSheet(style_sheet)
        
        self.in_fn_entry.setCurrentIndex(-1)
        self.in_fn_entry_2.setCurrentIndex(-1)
        self.fmask_entry_2.setCurrentIndex(-1)
        self.mask_entry_2.setCurrentIndex(-1)
        
        self.in_fn_entry.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.in_fn_entry_2.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.fmask_entry_2.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.mask_entry_2.setFilters(QgsMapLayerProxyModel.RasterLayer)

    def gotoat2(self):
        os.chdir(self.initial_directory)
        at2 = AT_PRE_VP_SCREEN()
        stacked_widget.addWidget(at2)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def gotointro2(self):
        os.chdir(self.initial_directory)
        intro2 = IntroScreen()
        stacked_widget.addWidget(intro2)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def openDocument(self):
        pdf_path = os.path.join(os.path.dirname(__file__), "doc\\AppPreVM.pdf")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def openDocument_2(self):
        pdf_path = os.path.join(os.path.dirname(__file__), "doc\\AppPreVM.pdf")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path = Path(data_folder)
        self.directory = str(data_folder_path)
        self.folder_entry.setText(self.directory)
        self.folder_entry_2.setText(self.directory)
        central_data_store.directory = self.directory

    def selectRaster(self, comboBox, string):
        """
        Opening the raster layer file and adding the path to the combobox
        on end of the list with comboBox items.

        :param comboBox: Qt combobox.
        :type comboBox: QComboBox
        """
        rast_path = QFileDialog.getOpenFileName(self, string)
        index = comboBox.currentIndex()
        comboBox.setAdditionalItems([rast_path[0]])
        ind = comboBox.count() - 1
        comboBox.setCurrentIndex(ind)

    def select_working_directory_2(self):
        data_folder_2 = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path_2 = Path(data_folder_2)
        self.directory_2 = str(data_folder_path_2)
        self.folder_entry_2.setText(self.directory_2)
        self.folder_entry.setText(self.directory_2)
        central_data_store.directory = self.directory_2

    def process_data2(self):
        try: 
            self.in_fn = self.in_fn_entry.currentLayer().source()
        except Exception:
            self.in_fn = self.in_fn_entry.currentText()
            
        if not self.in_fn:
            QMessageBox.critical(self, "Error", "Please select the input file!")
            return

        NRT = self.nrt_entry.text()
        if not NRT:
            QMessageBox.critical(self, "Error", "Please enter the NRT value!")
            return
        try:
            self.NRT = int(NRT)
            if (self.NRT <= 0):
                QMessageBox.critical(self, "Error", "NRT value should be larger than 0!")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "NRT value should be a valid number!")
            return

        n_classes = int(29)
        if not n_classes:
            QMessageBox.critical(self, "Error", "Please enter the number of classes!")
            return
        try:
            self.n_classes = int(n_classes)
            if (self.n_classes <= 0):
                QMessageBox.critical(self, "Error", "Number of classes should be larger than 0!")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "Number of classes value should be a valid number!")
            return

        directory = self.folder_entry.text()

        out_fn = self.out_fn_entry.text()
        if not out_fn:
            QMessageBox.critical(self, "Error", "Please enter the name of Vulnerability Map in VP!")
            return

        if not (out_fn.endswith('.tif') or out_fn.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Vulnerability Map in VP!")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.vulnerability_map.set_working_directory(directory)
            mask_arr = self.vulnerability_map.geometric_classification(self.in_fn, NRT, n_classes)
            self.vulnerability_map.array_to_image(self.in_fn, out_fn, mask_arr, gdal.GDT_Int16, -1)
            self.vulnerability_map.replace_ref_system(self.in_fn, out_fn)

            if self.checkBox.isChecked():
                basename = os.path.splitext(os.path.basename(out_fn))[0]
                layer = QgsRasterLayer(out_fn, basename)
                layer.setDataSource(os.path.join(directory, out_fn), basename, 'gdal')
                QgsProject.instance().addMapLayer(layer)

            QMessageBox.information(self, "Processing Completed", "Processing completed!")
            self.progressDialog.close()

        except Exception as e:
            self.progressDialog.close()
            QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def get_image_resolution(self, image):
        # Set up a GDAL dataset
        in_ds = gdal.Open(image)
        # Set up a GDAL band
        P = in_ds.GetGeoTransform()[1]
        # Create Numpy Array1
        return P

    def get_image_dimensions(self, image):
        dataset = gdal.Open(image)
        cols = dataset.RasterXSize
        rows = dataset.RasterYSize
        return rows, cols

    def get_image_datatype(self, image):
        in_ds = gdal.Open(image)
        in_band = in_ds.GetRasterBand(1)
        datatype = gdal.GetDataTypeName(in_band.DataType)
        return datatype

    def get_image_max_min(self, image):
        in_ds = gdal.Open(image)
        in_band = in_ds.GetRasterBand(1)
        min, max= in_band.ComputeRasterMinMax()
        return min, max

    def find_unique_values(self, arr, limit=2):
        unique_values = set()
        for value in np.nditer(arr):
            unique_values.add(value.item())
            if len(unique_values) > limit:
                return False
        return True

    def check_binary_map(self, in_fn):
        '''
        Check if input image is binary map
        :param in_fn: input image
        :return: True if the file is a binary map, False otherwise
        '''
        file_extension = in_fn.split('.')[-1].lower()
        file_name, _ = os.path.splitext(in_fn)
        if file_extension == 'rst':
            with open(file_name + '.rdc', 'r') as read_file:
                rdc_content = read_file.read().lower()
                byte_or_integer_binary = "data type   : byte" in rdc_content or (
                        "data type   : integer" in rdc_content and "min. value  : 0" in rdc_content and "max. value  : 1" in rdc_content)
                float_binary = "data type   : real" in rdc_content and "min. value  : 0.0000000" in rdc_content and "max. value  : 1.0000000" in rdc_content
        elif file_extension == 'tif':
            datatype = self.get_image_datatype(in_fn)
            min_val, max_val = self.get_image_max_min(in_fn)
            byte_or_integer_binary = datatype in ['Byte', 'CInt16', 'CInt32', 'Int16', 'Int32', 'UInt16',
                                                      'UInt32'] and max_val == 1 and min_val == 0
            float_binary = datatype in ['Float32', 'Float64', 'CFloat32', 'CFloat64'] and max_val == 1.0000000 and min_val == 0.0000000

        if byte_or_integer_binary or (float_binary):
            # For float_binary, use find_unique_values function to check if data only have two unique values [0.0000000, 1.0000000].
            if float_binary:
                in_ds = gdal.Open(in_fn)
                in_band = in_ds.GetRasterBand(1)
                arr = in_band.ReadAsArray()
                # If more than two unique values are found, it's not a binary map, return False.
                if not self.find_unique_values(arr, 2):
                    return False
            # Binary map: byte_or_integer_binary or float_binary with two unique values [0.0000000, 1.0000000], it returns True.
            return True
        # For any other scenario, it returns False.
        return False

    def process_data2_2(self):
        try: 
            self.in_fn_2 = self.in_fn_entry_2.currentLayer().source()
        except Exception:
            self.in_fn_2 = self.in_fn_entry_2.currentText() 
        try:
            self.mask_2 = self.mask_entry_2.currentLayer().source()
        except Exception:
            self.mask_2 = self.mask_entry_2.currentText()
        try:
            self.fmask_2 = self.fmask_entry_2.currentLayer().source()
        except Exception:
            self.fmask_2 = self.fmask_entry_2.currentText()
            
        images = [self.in_fn_2, self.mask_2, self.fmask_2]

        # Check if all images have the same resolution
        resolutions = [self.get_image_resolution(img) for img in images]
        if len(set(resolutions)) != 1:
            QMessageBox.critical(None, "Error", "All the input raster images must have the same spatial resolution!")
            return

        # Check if all images have the same number of rows and columns
        dimensions = [self.get_image_dimensions(img) for img in images]
        if len(set(dimensions)) != 1:
            QMessageBox.critical(None, "Error",
                                 "All the input raster images must have the same number of rows and columns!")
            return

        if not self.in_fn_2 or not self.mask_2 or not self.fmask_2:
            QMessageBox.critical(self, "Error", "Please select  the input file!")
            return
        n_classes_2 = int(30)
        directory_2 = self.folder_entry_2.text()
        out_fn_2 = self.out_fn_entry_2.text()
        if not out_fn_2:
            QMessageBox.critical(self, "Error", "Please enter the name of Vulnerability Map in VP!")
            return

        # Check if the out_fn has the correct file extension
        if not (out_fn_2.endswith('.tif') or out_fn_2.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Vulnerability Map in VP!")
            return

        if not self.check_binary_map(self.mask_2):
            QMessageBox.critical(None, "Error",
                                 "'MASK OF THE NON-EXCLUDED JURISDICTION' must be a binary map (0 and 1) where the 1’s indicate areas inside the jurisdiction.")
            return

        if not self.check_binary_map(self.fmask_2):
            QMessageBox.critical(None, "Error",
                                 "'MASK OF FOREST AREAS IN THE VP' must be a binary map (0 and 1) where the 1’s indicate forest areas.")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.vulnerability_map.set_working_directory(directory_2)
            mask_arr = self.vulnerability_map.geometric_classification_alternative(self.in_fn_2, n_classes_2,
                                                                                   self.mask_2, self.fmask_2)
            self.vulnerability_map.array_to_image(self.in_fn_2, out_fn_2, mask_arr, gdal.GDT_Int16, -1)
            self.vulnerability_map.replace_ref_system(self.in_fn_2, out_fn_2)

            if self.checkBox_2.isChecked():
                basename = os.path.splitext(os.path.basename(out_fn_2))[0]
                layer = QgsRasterLayer(out_fn_2, basename)
                layer.setDataSource(os.path.join(directory_2, out_fn_2), basename, 'gdal')
                QgsProject.instance().addMapLayer(layer)

            QMessageBox.information(self, "Processing Completed", "Processing completed!")

            self.progressDialog.close()

        except Exception as e:
            self.progressDialog.close()
            QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def update_progress(self, value):
        # Update QProgressDialog with the new value
        if self.progressDialog is not None:
            self.progressDialog.setValue(value)


######################################################################################################
        
class AT_PRE_VP_SCREEN(QtWidgets.QDialog, FORM_CLASS10):
    def __init__(self, parent=None):
        """Constructor."""
        super(AT_PRE_VP_SCREEN, self).__init__(parent)
        # Store the initial directory path
        self.initial_directory = os.getcwd()
        # Set up the user interface from Designer through FORM_CLASS10.
        self.setupUi(self)
        if central_data_store.directory is not None and self.folder_entry is not None:
            self.directory = central_data_store.directory
            self.folder_entry.setText(str(central_data_store.directory))
        self.Intro_button3.clicked.connect(self.gotointro3)
        self.RMT_button3.clicked.connect(self.gotormt3)
        self.doc_button.clicked.connect(self.openDocument)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.municipality_button.clicked.connect(lambda: self.selectRaster(self.municipality_entry, 'Map of Administrative Divisions'))
        self.csv_button.clicked.connect(self.select_csv)
        self.risk30_vp_button.clicked.connect(lambda: self.selectRaster(self.risk30_vp_entry, 'Vulnerability Map in VP'))
        self.ok_button3.clicked.connect(self.process_data3)
        self.allocation_tool = AllocationTool()
        # Connect the progress_updated signal to the update_progress method
        self.allocation_tool.progress_updated.connect(self.update_progress)
        self.directory = None
        self.csv = None
        self.municipality = None
        self.risk30_vp = None
        self.expected_deforestation = None
        self.max_iterations = None
        self.time = None
        self.image1 = None
        self.image2 = None
        self.iteration_entry.setPlaceholderText('The suggestion max iteration number is 5')
        self.image1_entry.setPlaceholderText('e.g., Acre_Prediction_Modeling_Region_VP.tif')
        self.image2_entry.setPlaceholderText('e.g., Acre_Adjucted_Density_Map_VP.tif')
        self.setWindowTitle("JNR Integrated Risk/Allocation Tool")

        # Provide intitial settings for each comboBox
        self.municipality_entry.setStyleSheet(style_sheet)
        self.risk30_vp_entry.setStyleSheet(style_sheet)
        
        self.municipality_entry.setCurrentIndex(-1)
        self.risk30_vp_entry.setCurrentIndex(-1)
        
        self.municipality_entry.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.risk30_vp_entry.setFilters(QgsMapLayerProxyModel.RasterLayer)

    def gotormt3(self):
        os.chdir(self.initial_directory)
        rmt3 = RMT_PRE_VP_SCREEN()
        stacked_widget.addWidget(rmt3)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def gotointro3(self):
        os.chdir(self.initial_directory)
        intro3 = IntroScreen()
        stacked_widget.addWidget(intro3)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

    def openDocument(self):
        pdf_path = os.path.join(os.path.dirname(__file__), "doc\\AppPreAM.pdf")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path = Path(data_folder)
        self.directory = str(data_folder_path)
        self.folder_entry.setText(self.directory)
        central_data_store.directory = self.directory

    def selectRaster(self, comboBox, string):
        """
        Opening the raster layer file and adding the path to the combobox
        on end of the list with comboBox items.

        :param comboBox: Qt combobox.
        :type comboBox: QComboBox
        """
        rast_path = QFileDialog.getOpenFileName(self, string)
        index = comboBox.currentIndex()
        comboBox.setAdditionalItems([rast_path[0]])
        ind = comboBox.count() - 1
        comboBox.setCurrentIndex(ind)

    def select_csv(self):
        file_path1, _ = QFileDialog.getOpenFileName(self, "HRP Relative Frequency Table (.csv)")
        if file_path1:
            self.csv = file_path1
            self.csv_entry.setText(file_path1.split('/')[-1])

    def get_image_resolution(self, image):
        # Set up a GDAL dataset
        in_ds = gdal.Open(image)
        # Set up a GDAL band
        P = in_ds.GetGeoTransform()[1]
        # Create Numpy Array1
        return P

    def get_image_dimensions(self, image):
        dataset = gdal.Open(image)
        cols = dataset.RasterXSize
        rows = dataset.RasterYSize
        return rows, cols

    def process_data3(self):
        try: 
            self.risk30_vp = self.risk30_vp_entry.currentLayer().source()
        except Exception:
            self.risk30_vp = self.risk30_vp_entry.currentText() 
        try:
            self.municipality = self.municipality_entry.currentLayer().source()
        except Exception:
            self.municipality = self.municipality_entry.currentText()
            
        images = [self.municipality, self.risk30_vp]

        # Check if all images have the same resolution
        resolutions = [self.get_image_resolution(img) for img in images]
        if len(set(resolutions)) != 1:
            QMessageBox.critical(None, "Error", "All the input raster images must have the same spatial resolution!")
            return

        # Check if all images have the same number of rows and columns
        dimensions = [self.get_image_dimensions(img) for img in images]
        if len(set(dimensions)) != 1:
            QMessageBox.critical(None, "Error",
                                 "All the input raster images must have the same number of rows and columns!")
            return
        if not self.csv or not self.municipality or not self.risk30_vp:
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        expected_deforestation = self.expected_entry.text()
        if not expected_deforestation:
            QMessageBox.critical(self, "Error", "Please enter the expected deforestation value!")
            return
        try:
            self.expected_deforestation = float(expected_deforestation)
        except ValueError:
            QMessageBox.critical(self, "Error", "Expected deforestation value should be a valid number!")
            return

        directory = self.folder_entry.text()

        out_fn1 = self.image1_entry.text()
        if not out_fn1:
            QMessageBox.critical(self, "Error", "Please enter the name of Prediction Modeling Region Map in VP!")
            return

        if not (out_fn1.endswith('.tif') or out_fn1.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Prediction Modeling Region Map in VP!")
            return

        out_fn2 = self.image2_entry.text()
        if not out_fn2:
            QMessageBox.critical(self, "Error", "Please enter the name of Adjusted Prediction Density Map in VP!")
            return

        if not (out_fn2.endswith('.tif') or out_fn2.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Adjusted Prediction Density Map in VP!")
            return

        max_iterations = self.iteration_entry.text()
        if not max_iterations:
            QMessageBox.critical(self, "Error", "Please enter the max iterations! The suggestion number is 5.")
            return
        try:
            self.max_iterations = int(max_iterations)
        except ValueError:
            QMessageBox.critical(self, "Error", "Max iteration value should be a valid number!")
            return

        time = self.year_entry.text()
        if not time:
            QMessageBox.critical(self, "Error", "Please enter the number of years in the VP! ")
            return
        try:
            self.time = int(time)
        except ValueError:
            QMessageBox.critical(self, "Error", "The number of years in the VP should be a valid number!")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            id_difference = self.allocation_tool.execute_workflow_vp(directory, self.max_iterations,
                                                                           self.csv,
                                                                           self.municipality,
                                                                           self.expected_deforestation,
                                                                           self.risk30_vp, out_fn1,out_fn2,
                                                                           self.time)

            if self.checkBox.isChecked():
                basename1 = os.path.splitext(os.path.basename(out_fn1))[0]
                basename2 = os.path.splitext(os.path.basename(out_fn2))[0]
                layer1 = QgsRasterLayer(out_fn1, basename1)
                layer2 = QgsRasterLayer(out_fn2, basename2)
                layer1.setDataSource(os.path.join(directory, out_fn1), basename1, 'gdal')
                layer2.setDataSource(os.path.join(directory, out_fn2), basename2, 'gdal')
                QgsProject.instance().addMapLayer(layer1)
                QgsProject.instance().addMapLayer(layer2)

            if id_difference.size > 0:
                QMessageBox.warning(self, " Warning ", f"Modeling Region ID {','.join(map(str, id_difference))} do not exist in the Historical Reference Period. A new CSV has been created for the HRP where relative frequencies for missing bins have been estimated from corresponding vulnerability zones over the entire jurisdiction.")

            QMessageBox.information(self, "Processing Completed", "Processing completed!")
            self.progressDialog.close()

        except Exception as e:
             self.progressDialog.close()
             QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def update_progress(self, value):
        # Update QProgressDialog with the new value
        if self.progressDialog is not None:
            self.progressDialog.setValue(value)


######################################################################################################
######################################################################################################
######################################################################################################
            
# CLASS FOR THE PLUGIN ITSELF. HERE WE TELL QGIS HOW TO INITIALIZE THE PLUGIN.
class UDef_ARP_QGIS:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'TestUI_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&UDef-ARP Plugin')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('TestUI', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        #icon_path = ':/plugins/test_ui/icon.png'
        icon_path = f'{self.plugin_dir}/VCS.png'
        self.add_action(
            icon_path,
            text=self.tr(u'UDef-ARP Plugin'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&UDef-ARP Plugin'),
                action)
            self.iface.removeToolBarIcon(action)
            

    def run(self):
        """Run method that performs all the real work"""
        #if self.first_start:
        self.first_start = False

        # Create and add the first dialog
        self.dlg = IntroScreen() 
        stacked_widget.addWidget(self.dlg)
        stacked_widget.setCurrentIndex(stacked_widget.currentIndex() + 1)

        # Show the stacked widget
        stacked_widget.setFixedHeight(1000)
        stacked_widget.setFixedWidth(1800)
        stacked_widget.show()

######################################################################################################

# Define a central data store
class CentralDataStore:
    def __init__(self):
        self.NRT = None
        self.directory = None

# DEFINE GLOBAL OBJECTS OUTSIDE OF CLASS OBJECTS
central_data_store = CentralDataStore()
stacked_widget = QtWidgets.QStackedWidget()
