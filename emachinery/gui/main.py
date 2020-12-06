# https://www.youtube.com/watch?v=2C5VnE9wPhk
# background-color: rgb(255, 255, 255)

import pkg_resources # to include resource file: mainWindow.ui # https://stackoverflow.com/questions/6028000/how-to-read-a-static-file-from-inside-a-python-package/20885799
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.uic import loadUi

from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT as NavigationToolbar)

import numpy as np
import random

from collections import OrderedDict
import json

from emachinery.utils.conversion import ElectricMachinery
from emachinery.jsons import ACMInfo
from emachinery.gui.stylesheet.toggle_stylesheet import toggle_stylesheet

# Promoted Widgets: use these two absolute imports to replace the relative imports in mainWindow.py for uploading to PyPI
# from emachinery.gui.consolewidget import ConsoleWidget
# from emachinery.gui.mplwidget import MplWidget

from emachinery.gui.mainWindow import Ui_MainWindow

from PyQt5 import QtCore, QtGui, QtWidgets

import re

class EmachineryWidget(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        ''' generate file path within package
        '''
        # __name__ in case you're within the package
        # - otherwise it would be 'lidtk' in this example as it is the package name
        path = 'mainWindow_v2.ui'  # always use slash
        filepath = pkg_resources.resource_filename(__name__, path)

        ''' load ui or import ui class
        '''
        try:
            print('CJH: plan A to load .ui file.')
            self.ui = loadUi(filepath, self) # baseinstance=self
        except ModuleNotFoundError as e:
            raise e
            print(str(e))
            print('CJH: will use plan B now.')
            self.ui = Ui_MainWindow()
            self.ui.setupUi(self)
        except Exception as e:
            raise e

        '''tab: Name Plate Data
        '''
        self.mj = ACMInfo.MotorJson().d
        self.ui.comboBox_MachineName.addItems(self.mj.keys())
        self.ui.comboBox_MachineName.activated.connect(self.update_namePlateData)
        self.update_namePlateData()

        def get_motor_dict(mj):
            motor = mj["SEW400W (SF60B04030C2004)"]["基本参数"]

            n_pp = motor["极对数 [1]"]
            R    = motor["电机线电阻 [Ohm]"]/2
            L    = motor["电机D轴线电感 [mH]"]/2*1e-3
            KE   = motor["转矩常数 [Nm/Arms]"] / 1.5 / n_pp * 1.414
            J_s  = motor["转动惯量 [kg.cm^2]"]*1e-4
            IN   = motor["额定电流 [Arms]"]
            PW   = motor["额定功率 [Watt]"]
            RPM  = motor["额定转速 [rpm]"]

            motor_dict = dict()
            motor_dict['n_pp'] = n_pp
            motor_dict['Rs'] = R
            motor_dict['Ld'] = L
            motor_dict['Lq'] = L
            motor_dict['KE'] = KE
            motor_dict['J_s'] = J_s
            motor_dict['IN'] = IN
            motor_dict['PW'] = PW
            motor_dict['RPM'] = RPM

            CL_TS = 1/20e3
            VL_TS = 4*CL_TS # if modified, need to change SPEED_LOOP_CEILING in ACMConfig.h as well

            motor_dict['CL_TS'] = CL_TS
            motor_dict['VL_TS'] = VL_TS

            motor_dict['JLoadRatio'] = JLoadRatio = 0.16 # 0.16 # 3 [%]
            motor_dict['Tload'] = TLoad = 0.0 # 0.05 # [Nm]
            motor_dict['ViscousCoeff'] = B = 0.7e-4


        '''tab_2: Plots
        '''
        # update plot
        self.ui.pushButton_getSignal.clicked.connect(self.update_graph)
        # undate model
        self.ui.pushButton_updateModel.clicked.connect(self.update_emy)

        # Matplotlib navigation bar to: self or tabWidget
        self.toolbar = NavigationToolbar(self.ui.MplWidget.canvas, self)
            # self.addToolBar(self.toolbar) # add to mainWindow
        self.ui.verticalLayout_inTab2.addWidget(self.toolbar) # add to tab 2 only

        '''tab_3: FEA-based Optimization
        '''
        try:
            path = self.lineEdit_path2boptPython.text()
            with open(path+'/codes3/machine_specifications.json', 'r', encoding='utf-8') as f:
                self.bopt_fea_config_dict = json.load(f, object_pairs_hook=OrderedDict) # https://stackoverflow.com/questions/10844064/items-in-json-object-are-out-of-order-using-json-dumps/23820416
            self.ui.comboBox_MachineSpec.addItems(self.bopt_fea_config_dict.keys())
            self.ui.comboBox_MachineSpec.activated.connect(self.update_machineSpec)
            self.update_machineSpec()
            with open(path+'/codes3/machine_simulation.json', 'r', encoding='utf-8') as f:
                self.bopt_machine_spec_dict = json.load(f, object_pairs_hook=OrderedDict) # https://stackoverflow.com/questions/10844064/items-in-json-object-are-out-of-order-using-json-dumps/23820416
            self.ui.comboBox_FEAConfig.addItems(self.bopt_machine_spec_dict.keys())
            self.ui.comboBox_FEAConfig.activated.connect(self.update_FEAConfig)
            self.update_FEAConfig()
        except:
            print('[Warn] Skip FEA-based Optimization')
            pass

        '''tab_4: C-based Simulation
        '''
        self.path2acmsimc = self.lineEdit_path2acmsimc.text()
        self.ui.pushButton_runCBasedSimulation.clicked.connect(self.runCBasedSimulation)

        # Read in ACM Plot Settings
        with open(self.ui.lineEdit_path2ACMPlotLabels.text(), 'r') as f:
            self.ui.plainTextEdit_ACMPlotLabels.clear()
            self.ui.plainTextEdit_ACMPlotLabels.appendPlainText(f.read())
        with open(self.ui.lineEdit_path2ACMPlotSignals.text(), 'r') as f:
            self.ui.plainTextEdit_ACMPlotDetails.clear()
            self.ui.plainTextEdit_ACMPlotDetails.appendPlainText(f.read())

        '''tab_5: ACMPlot
        '''
        self.ui.pushButton_ACMPlotHere.clicked.connect(self.update_ACMPlot)
        self.bool_import_ACMPlot = False
        # Matplotlib navigation bar to: self or tabWidget
        self.toolbar = NavigationToolbar(self.ui.MplWidget.canvas, self)
        self.ui.verticalLayout_CBSMplToolBar.addWidget(self.toolbar) # add to tab 2 only


        '''menu
        '''
        # Style sheet
        self.ui.actionDark.triggered.connect(lambda: toggle_stylesheet("QDarkStyleSheet.qss")) # need to use "./stylesheet/QDarkStyleSheet.qss" if pkg_resources is not used in toggle_stylesheet.py
        self.ui.actionLight.triggered.connect(lambda: toggle_stylesheet(""))

        '''MainWindow
        '''
        self.setWindowTitle("Figure: Electric Machinery")

        '''
        todo
        '''
        # Recover last input
        # self.lineEdit_npp.textChanged[str].connect(self.doSomething)
        # read in c header file and figure out what are the possible labels

    def runCBasedSimulation(self):

        def savePlotSettings():
            with open(self.ui.lineEdit_path2ACMPlotLabels.text(), 'w') as f:
                f.write(self.ui.plainTextEdit_ACMPlotLabels.toPlainText())
            with open(self.ui.lineEdit_path2ACMPlotSignals.text(), 'w') as f:
                f.write(self.ui.plainTextEdit_ACMPlotDetails.toPlainText())

            # #define DATA_LABELS
            labels = [el.strip() for el in self.ui.plainTextEdit_ACMPlotLabels.toPlainText().split('\n') if el.strip()!='']
            # avoid using ',' or ';' in label, because comma will be interpreted as new column by pandas
            # labels = [el.replace(',','|') for el in labels]
            self.list__label = labels
            # print(labels)

            details = self.ui.plainTextEdit_ACMPlotDetails.toPlainText()
            # print(details)

            # 每个通道有几条信号？
            self.list__number_of_traces_per_subplot = []
            for detail in [el.strip() for el in self.ui.plainTextEdit_ACMPlotDetails.toPlainText().split('\n') if el.strip()!='']:
                number_of_traces_per_subplot = len( [el.strip() for el in detail.split(',') if el.strip()!=''] )
                self.list__number_of_traces_per_subplot.append(number_of_traces_per_subplot)

            # #define DATA_DETAILS
            details = [el.strip() for el in re.split('\n|,', details) if el.strip()!='']
            self.list__detail = details
            # print(details)

            with open(self.path2acmsimc+'/c/utility.c', 'r', encoding='utf-8') as f:
                new_line = []
                for line in f.readlines():
                    if   '#define DATA_LABELS '  in line: new_line.append(rf'#define DATA_LABELS "{",".join(details)}\n"' +'\n')
                    elif '#define DATA_DETAILS ' in line: new_line.append(rf'#define DATA_DETAILS {",".join(details)}' +'\n')
                    elif '#define DATA_FORMAT '  in line: new_line.append(rf'#define DATA_FORMAT "{("%g,"*len(details))[:-1]}\n"' +'\n')
                    else: new_line.append(line)
            with open(self.path2acmsimc+'/c/utility.c', 'w', encoding='utf-8') as f:
                f.writelines(new_line)

        savePlotSettings()
        os.system(f"cd /d {self.path2acmsimc}/c && gmake main && start cmd /c main")
        self.update_ACMPlot()

    def update_ACMPlot(self):
        if(not self.bool_import_ACMPlot):
            sys.path.append(self.path2acmsimc)
            import ACMPlot

        df_info, df_profiles, no_samples, no_traces = ACMPlot.get_data_frame(self.path2acmsimc)

        time = np.arange(1, no_samples+1) * df_info['DOWN_SAMPLE'].values[0] * df_info['CL_TS'].values[0]

        # adjust height per number of traces
        self.MplWidget_ACMPlot.setMinimumSize(QtCore.QSize(500, 200*no_traces))

        self.ui.MplWidget_ACMPlot.canvas.figure.clf()
        trace_counter = 0
        number_of_subplot = len(self.list__number_of_traces_per_subplot)
        # for i, key in enumerate(df_profiles.keys()):
        # for i, key in enumerate(self.list__label):
        for i, number_of_traces_per_subplot in enumerate(self.list__number_of_traces_per_subplot):
            ax = self.ui.MplWidget_ACMPlot.canvas.figure.add_subplot(number_of_subplot*100+11+i)

            for j in range(number_of_traces_per_subplot):
                key = self.list__detail[trace_counter]
                signal = df_profiles[key]
                trace_counter += 1
                ax.plot(time, signal, '-.', lw=1, label=key)
            ax.set_ylabel(self.list__label[i])
            ax.legend(loc='lower center')
        ax.set_xlabel('Time [s]')
        axes = self.ui.MplWidget_ACMPlot.canvas.figure.get_axes()
        self.ui.MplWidget_ACMPlot.canvas.draw()

    def update_FEAConfig(self):
        pass

    def update_machineSpec(self):
        pass

    def update_namePlateData(self):
        motor_dict = self.get_motor(self.ui.comboBox_MachineName.currentText())
        self.ui.lineEdit_npp         .setText(str(motor_dict['n_pp']))
        self.ui.lineEdit_RatedCurrent.setText(str(motor_dict['IN']))
        self.ui.lineEdit_RatedPower  .setText(str(motor_dict['PW']))
        self.ui.lineEdit_RatedSpeed  .setText(str(motor_dict['RPM']))

    def update_emy(self):
        self.emy = ElectricMachinery( NUMBER_OF_POLE_PAIRS  = int  (self.ui.lineEdit_npp.text()),
                                      RATED_CURRENT_RMS     = float(self.ui.lineEdit_RatedCurrent.text()),
                                      RATED_POWER_WATT      = float(self.ui.lineEdit_RatedPower.text()),
                                      RATED_SPEED_RPM       = float(self.ui.lineEdit_RatedSpeed.text()),
            )
        self.ui.ConsoleWidget.push_vars({
            'emy': self.emy
            })
        self.ui.label_pushedVariables.setText('emy')

    def get_motor(self, motor_name="SEW400W (SF60B04030C2004)"):
        motor = self.mj[motor_name]["基本参数"]

        n_pp = motor["极对数 [1]"]
        R    = motor["电机线电阻 [Ohm]"]/2
        L    = motor["电机D轴线电感 [mH]"]/2*1e-3
        KT   = motor["转矩常数 [Nm/Arms]"] * 1.414
        KE   = motor["转矩常数 [Nm/Arms]"] / 1.5 / n_pp * 1.414
        J_s  = motor["转动惯量 [kg.cm^2]"]*1e-4
        IN   = motor["额定电流 [Arms]"]
        PW   = motor["额定功率 [Watt]"]
        RPM  = motor["额定转速 [rpm]"]

        motor_dict = dict()
        motor_dict['n_pp'] = n_pp
        motor_dict['Rs'] = R
        motor_dict['Ld'] = L
        motor_dict['Lq'] = L
        motor_dict['KE'] = KE
        motor_dict['J_s'] = J_s
        motor_dict['IN'] = IN
        motor_dict['PW'] = PW
        motor_dict['RPM'] = RPM

        CL_TS = 1/20e3
        VL_TS = 4*CL_TS # if modified, need to change SPEED_LOOP_CEILING in ACMConfig.h as well

        motor_dict['JLoadRatio']   = JLoadRatio = 0.4 # 0.16 # 3 [%]
        motor_dict['Tload']        = TLoad      = 0.0*0.07 # 0.05 # [Nm]
        motor_dict['ViscousCoeff'] = B = 0.7e-4
        return motor_dict

    def update_graph(self):
        if self.ui.MplWidget.canvas.axes is None:
           self.ui.MplWidget.canvas.axes = self.ui.MplWidget.canvas.figure.add_subplot(111)

        fs = 500
        f = random.randint(1, 100)
        ts = 1/fs
        length_of_signal = 100
        t = np.linspace(0,1,length_of_signal)
        
        cosinus_signal = np.cos(2*np.pi*f*t)
        sinus_signal = np.sin(2*np.pi*f*t)

        self.ui.MplWidget.canvas.axes.clear()
        self.ui.MplWidget.canvas.axes.plot(t, cosinus_signal)
        self.ui.MplWidget.canvas.axes.plot(t, sinus_signal)
        self.ui.MplWidget.canvas.axes.legend(('cosinus', 'sinus'),loc='upper right')
        self.ui.MplWidget.canvas.axes.set_title('Cosinus - Sinus Signal')
        self.ui.MplWidget.canvas.draw()

def main():
    app = QApplication([])
    window = EmachineryWidget()
    window.show()
    app.exec_()

if __name__ == '__main__':
    import os, sys
    print(os.path.dirname(os.path.realpath(__file__)))
    main()
