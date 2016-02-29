from __main__ import vtk, qt, ctk, slicer
import os
import logging

# ********************************************** #
# **************** Useful class **************** #
# ********************************************** #

class ExternalModuleTab():
    def __init__(self):
        self.collapsibleButton = None
        self.layout = None
        self.choiceComboBox = None
        self.currentModule = None
        self.currentComboboxIndex = None

    def hideCurrentModule(self):
        if self.currentModule:
            self.layout.removeWidget(self.currentModule)
            self.currentModule.hide()
            self.choiceComboBox.setCurrentIndex(0)

    def deleteCurrentModule(self):
        self.hideCurrentModule()
        self.currentModule = None
        self.currentComboboxIndex = 0

    def showCurrentModule(self):
        if self.currentModule:
            print self.currentModule
            print self.currentComboboxIndex
            self.layout.addWidget(self.currentModule)
            self.currentModule.show()
            self.choiceComboBox.setCurrentIndex(self.currentComboboxIndex)

    def setCurrentModule(self, widget, index):
        self.currentModule = widget
        self.currentComboboxIndex = index
        self.showCurrentModule()

# ************************************************************* #
# **************** Longitudinal Quantification **************** #
# ************************************************************* #

class LongitudinalQuantification(slicer.ScriptedLoadableModule.ScriptedLoadableModule):
    def __init__(self, parent):

        slicer.ScriptedLoadableModule.ScriptedLoadableModule.__init__(self, parent)
        parent.title = "Longitudinal Quantification"
        parent.categories = ["Quantification"]
        parent.dependencies = []
        parent.contributors = ["Jean-Baptiste Vimort"]
        parent.helpText = """
            TODO
            """

        parent.acknowledgementText = """
            This work was supported by the National
            Institutes of Dental and Craniofacial Research
            and Biomedical Imaging and Bioengineering of
            the National Institutes of Health under Award
            Number R01DE024450.
            """

        self.parent = parent

# ******************************************************************* #
# **************** Longitudinal Quantification Widget *************** #
# ******************************************************************* #

class LongitudinalQuantificationWidget(slicer.ScriptedLoadableModule.ScriptedLoadableModuleWidget):

    # ************************************************ #
    # ---------------- Initialisation ---------------- #
    # ************************************************ #

    def setup(self):
        print "----- Longitudinal Quantification widget setup -----"

        # ------ Initialisation of Longitudinal quantification and its logic ----- #
        slicer.ScriptedLoadableModule.ScriptedLoadableModuleWidget.setup(self)
        self.logic = LongitudinalQuantificationLogic(self)

        # ---------------------------------------------------------------- #
        # ---------------- Definition of the UI interface ---------------- #
        # ---------------------------------------------------------------- #

        # ------------ Loading of the .ui file ---------- #

        loader = qt.QUiLoader()
        moduleName = 'LongitudinalQuantification'
        scriptedModulesPath = eval('slicer.modules.%s.path' % moduleName.lower())
        scriptedModulesPath = os.path.dirname(scriptedModulesPath)
        path = os.path.join(scriptedModulesPath, 'Resources', 'UI', '%s.ui' %moduleName)

        qfile = qt.QFile(path)
        qfile.open(qt.QFile.ReadOnly)
        widget = loader.load(qfile, self.parent)
        self.layout = self.parent.layout()
        self.widget = widget
        self.layout.addWidget(widget)

        # ------ Scene Collapsible Button ----- #
        self.SceneCollapsibleButton = self.logic.get("SceneCollapsibleButton")
        treeView = self.logic.get("treeView")
        treeView.setMRMLScene(slicer.app.mrmlScene())
        treeView.sceneModel().setHorizontalHeaderLabels(["Models"])
        treeView.sortFilterProxyModel().nodeTypes = ['vtkMRMLModelNode','vtkMRMLMarkupsFiducialNode']
        treeView.header().setVisible(False)
        self.autoChangeLayout = self.logic.get("autoChangeLayout")
        self.computeBox = self.logic.get("computeBox")

        # ------ Step Group Box ----- #
        self.Model1RadioButton = self.logic.get("Model1RadioButton")
        self.Model1RadioButton.hide()
        self.Model2RadioButton = self.logic.get("Model2RadioButton")
        self.Model2RadioButton.hide()
        self.PreviousStepPushButton = self.logic.get("PreviousStepPushButton")
        self.NextStepPushButton = self.logic.get("NextStepPushButton")
        self.logic.get("verticalLayout_4").setAlignment(0x84)
        self.logic.get("verticalLayout_5").setAlignment(0x84)

        # ------ Data selection Collapsible Button ----- #
        self.DataSelectionCollapsibleButton = self.logic.get("DataSelectionCollapsibleButton")
        self.SingleModelRadioButton = self.logic.get("SingleModelRadioButton")
        self.TwoModelsRadioButton = self.logic.get("TwoModelsRadioButton")
        self.logic.get("verticalLayout_6").setAlignment(0x84)
        self.logic.get("verticalLayout_7").setAlignment(0x84)
        self.Model1groupBox = self.logic.get("Model1groupBox")
        self.Model1MRMLNodeComboBox = self.logic.get("Model1MRMLNodeComboBox")
        self.Model1MRMLNodeComboBox.setMRMLScene(slicer.mrmlScene)
        self.FidList1MRMLNodeComboBox = self.logic.get("FidList1MRMLNodeComboBox")
        self.FidList1MRMLNodeComboBox.setMRMLScene(slicer.mrmlScene)
        self.Model2groupBox = self.logic.get("Model2groupBox")
        self.Model2MRMLNodeComboBox = self.logic.get("Model2MRMLNodeComboBox")
        self.Model2MRMLNodeComboBox.setMRMLScene(slicer.mrmlScene)
        self.FidList2MRMLNodeComboBox = self.logic.get("FidList2MRMLNodeComboBox")
        self.FidList2MRMLNodeComboBox.setMRMLScene(slicer.mrmlScene)

        self.ExternalModuleTabDict = dict()
        # ------ Preprocessing Collapsible Button ----- #
        self.ExternalModuleTabDict["Preprocessing"] = ExternalModuleTab()
        self.ExternalModuleTabDict["Preprocessing"].collapsibleButton = self.logic.get("PreprocessingCollapsibleButton")
        self.ExternalModuleTabDict["Preprocessing"].layout = self.logic.get("PreprocessingLayout")
        self.ExternalModuleTabDict["Preprocessing"].choiceComboBox = self.logic.get("PreprocessingChoiceComboBox")

        # ------ Quantification Collapsible Button ----- #
        self.ExternalModuleTabDict["Quantification"] = ExternalModuleTab()
        self.ExternalModuleTabDict["Quantification"].collapsibleButton = self.logic.get("QuantificationCollapsibleButton")
        self.ExternalModuleTabDict["Quantification"].layout = self.logic.get("QuantificationLayout")
        self.ExternalModuleTabDict["Quantification"].choiceComboBox = self.logic.get("QuantificationChoiceComboBox")

        # ------ Analysis Collapsible Button ----- #
        self.ExternalModuleTabDict["Analysis"] = ExternalModuleTab()
        self.ExternalModuleTabDict["Analysis"].collapsibleButton = self.logic.get("AnalysisCollapsibleButton")
        self.ExternalModuleTabDict["Analysis"].layout = self.logic.get("AnalysisLayout")
        self.ExternalModuleTabDict["Analysis"].choiceComboBox = self.logic.get("AnalysisChoiceComboBox")

        # ------------------------------------------------------------------------------ #
        # ---------------- Setup and initialisation of global variables ---------------- #
        # ------------------------------------------------------------------------------ #

        # ------ Initialisation of the other modules is Slicer, if that's not already done ----- #
        if not hasattr(slicer.modules, 'AnglePlanesWidget'):
            slicer.modules.angleplanes.createNewWidgetRepresentation()
        if not hasattr(slicer.modules, 'EasyClipWidget'):
            slicer.modules.easyclip.createNewWidgetRepresentation()
        if not hasattr(slicer.modules, 'MeshStatisticsWidget'):
            slicer.modules.meshstatistics.createNewWidgetRepresentation()
        if not hasattr(slicer.modules, 'PickAndPaintWidget'):
            slicer.modules.pickandpaint.createNewWidgetRepresentation()
        if not hasattr(slicer.modules, 'Q3DCWidget'):
            slicer.modules.q3dc.createNewWidgetRepresentation()
        if not hasattr(slicer.modules, 'SurfaceRegistrationWidget'):
            slicer.modules.surfaceregistration.createNewWidgetRepresentation()

        # ------ Creation of a dictionary that will contain the pythons modules ----- #
        self.ExternalPythonModules = dict()
        self.ExternalPythonModules["Angle Planes"] = slicer.modules.AnglePlanesWidget
        self.ExternalPythonModules["Easy Clip"] = slicer.modules.EasyClipWidget
        self.ExternalPythonModules["Mesh Statistics"] = slicer.modules.MeshStatisticsWidget
        self.ExternalPythonModules["Pick and Paint"] = slicer.modules.PickAndPaintWidget
        self.ExternalPythonModules["Q3DC"] = slicer.modules.Q3DCWidget
        self.ExternalPythonModules["Surface Registration"] = slicer.modules.SurfaceRegistrationWidget

        # ------ Creation of a dictionary that will contain the CLI modules ----- #
        self.ExternalCLIModules = dict()
        self.ExternalCLIModules["Model to Model Distance"] = slicer.modules.modeltomodeldistance
        self.ExternalCLIModules["Shape Population Viewer"] = slicer.modules.launcher

        # ------ Creation of a dictionary that will contain the widgets of all the modules ----- #
        self.ExternalModulesWidgets = dict()
        for key, value in self.ExternalPythonModules.iteritems():
            self.ExternalModulesWidgets[key] = value.widget
        for key, value in self.ExternalCLIModules.iteritems():
            self.ExternalModulesWidgets[key] = value.widgetRepresentation()

        # ------ Setup of the external modules ------ #
        # Hiding of the scene tabs and the input tabs in
        # all the external modules to avoid redundancies
        # and make this module as clear and simple as possible

        for key, value in self.ExternalPythonModules.iteritems():
            if hasattr(value, 'SceneCollapsibleButton'):
                value.SceneCollapsibleButton.hide()
            if hasattr(value, 'inputModelLabel'):
                value.inputModelLabel.hide()
                value.inputLandmarksLabel.hide()
                value.inputModelSelector.hide()
                value.inputLandmarksSelector.hide()
                value.loadLandmarksOnSurfacCheckBox.hide()
            elif hasattr(value, 'InputCollapsibleButton'):
                value.InputCollapsibleButton.hide()

        # --------------------------------------------- #
        # ---------------- Connections ---------------- #
        # --------------------------------------------- #

        # ------ Scene Collapsible Button ----- #
        self.SceneCollapsibleButton.\
            connect('clicked()', lambda: self.onSelectedCollapsibleButtonChanged(self.SceneCollapsibleButton))

        # ------ Data selection Collapsible Button ----- #
        self.DataSelectionCollapsibleButton.\
            connect('clicked()', lambda: self.onSelectedCollapsibleButtonChanged(self.DataSelectionCollapsibleButton))
        self.SingleModelRadioButton.connect('clicked()', lambda: self.onNumberOfModelForMeasureChange(True))
        self.TwoModelsRadioButton.connect('clicked()', lambda: self.onNumberOfModelForMeasureChange(False))
        self.Model1MRMLNodeComboBox.connect('currentNodeChanged(vtkMRMLNode*)', self.propagateInputModel1)
        self.FidList1MRMLNodeComboBox.connect('currentNodeChanged(vtkMRMLNode*)', self.propagateInputFidList1)
        self.Model2MRMLNodeComboBox.connect('currentNodeChanged(vtkMRMLNode*)', self.propagateInputModel2)
        self.FidList2MRMLNodeComboBox.connect('currentNodeChanged(vtkMRMLNode*)', self.propagateInputFidList2)

        # ------ Eternal Modules Selections Collapsible Buttons ----- #
        for key, ExternalModule in self.ExternalModuleTabDict.iteritems():
            ExternalModule.collapsibleButton.connect('clicked()',
                                                     lambda currentCollapsibleButton = ExternalModule.collapsibleButton:
                                                     self.onSelectedCollapsibleButtonChanged(currentCollapsibleButton))
            ExternalModule.choiceComboBox.connect('currentIndexChanged(QString)',
                                                  lambda newModule, currentCombobox = ExternalModule.choiceComboBox:
                                                  self.onExternalModuleChangement(newModule, currentCombobox))

        # ------ Closing of the scene -----#
        slicer.mrmlScene.AddObserver(slicer.mrmlScene.EndCloseEvent, self.onCloseScene)

    # ******************************************* #
    # ---------------- Algorithm ---------------- #
    # ******************************************* #

    # function called each time that the user "enter" in Longitudinal Quantification interface
    def enter(self):
        print "---- Enter Longitudinal Quantification ---- "

    # function called each time that the user "exit" in Longitudinal Quantification interface
    def exit(self):
        print "---- Exit Longitudinal Quantification ---- "

    # function called each time that the scene is closed (if Longitudinal Quantification has been initialized)
    def onCloseScene(self, obj, event):
        print "---- Close Longitudinal Quantification ---- "
        for ExtModTab in self.ExternalModuleTabDict.itervalues():
            ExtModTab.choiceComboBox.setCurrentIndex(0)

    # ---------- switching of Tab ----------- #
    # Only one tab can be display at the same time, so when one tab is opened
    # all the other tabs are closed by this function
    def onSelectedCollapsibleButtonChanged(self, selectedCollapsibleButton):
        self.SceneCollapsibleButton.setChecked(False)
        self.DataSelectionCollapsibleButton.setChecked(False)
        for ExternalModule in self.ExternalModuleTabDict.itervalues():
            ExternalModule.collapsibleButton.setChecked(False)
        print selectedCollapsibleButton
        selectedCollapsibleButton.setChecked(True)

    # ---------- switching of External Module ----------- #
    # This function hide all the external widgets if they are displayed
    # And show the new external module given in argument
    def ExternalModuleChangement(self, newModule):
        for ExtModTab in self.ExternalModuleTabDict.itervalues():
            ExtModTab.choiceComboBox.blockSignals(True)
            ExtModTab.clean()
            if newModule is "None":
                ExtModTab.choiceComboBox.blockSignals(False)
                continue
            if ExtModTab.belongToThisTab(newModule):
                ExtModTab.setWidget(self.ExternalModulesWidgets[newModule])
            ExtModTab.choiceComboBox.blockSignals(False)

    # ---------- Data Selection ---------- #
    # This function show/enable or hide/disable the different inputs depending
    # if the user check measurement on a single model or between two models
    def onNumberOfModelForMeasureChange(self, isSingleModelMeasurement):
        if isSingleModelMeasurement:
            self.Model2groupBox.setEnabled(False)
            self.Model1RadioButton.hide()
            self.Model2RadioButton.hide()
        else:
            self.Model2groupBox.setEnabled(True)
            self.Model2MRMLNodeComboBox.setEnabled(True)
            self.FidList2MRMLNodeComboBox.setEnabled(True)
            self.Model1RadioButton.show()
            self.Model2RadioButton.show()

    # This function propagate the model1 selected in the input tab to all the external modules
    def propagateInputModel1(self, newModel):
        for key, value in self.ExternalPythonModules.iteritems():
            if hasattr(value, 'inputModelSelector'):
                value.inputModelSelector.setCurrentNode(newModel)
            elif hasattr(value, 'inputFixedModelSelector'):
                value.inputFixedModelSelector.setCurrentNode(newModel)

    # This function propagate the Fiducial List 1 selected in the input tab to all the external modules
    def propagateInputFidList1(self, newModel):
        for key, value in self.ExternalPythonModules.iteritems():
            if hasattr(value, 'inputLandmarksSelector'):
                value.inputLandmarksSelector.setCurrentNode(newModel)
            elif hasattr(value, 'inputMovingModelSelector'):
                value.inputMovingModelSelector.setCurrentNode(newModel)

    # This function propagate the model2 selected in the input tab to all the external modules
    def propagateInputModel2(self, newModel):
        for key, value in self.ExternalPythonModules.iteritems():
            if hasattr(value, 'inputModelSelector'):
                value.inputModelSelector.setCurrentNode(newModel)
            elif hasattr(value, 'inputMovingModelSelector'):
                value.inputMovingModelSelector.setCurrentNode(newModel)

    # This function propagate the Fiducial List 2 selected in the input tab to all the external modules
    def propagateInputFidList2(self, newModel):
        for key, value in self.ExternalPythonModules.iteritems():
            if hasattr(value, 'inputLandmarksSelector'):
                value.inputLandmarksSelector.setCurrentNode(newModel)
            elif hasattr(value, 'inputMovingLandmarksSelector'):
                value.inputMovingLandmarksSelector.setCurrentNode(newModel)



# ******************************************************************* #
# **************** Longitudinal Quantification Logic **************** #
# ******************************************************************* #

class LongitudinalQuantificationLogic(slicer.ScriptedLoadableModule.ScriptedLoadableModuleLogic):

    # ************************************************ #
    # ---------------- Initialisation ---------------- #
    # ************************************************ #

    def __init__(self, interface):
        print "----- Longitudinal Quantification logic init -----"
        self.interface = interface

    # ******************************************* #
    # ---------------- Algorithm ---------------- #
    # ******************************************* #

    # ----------- Connection of the User Interface ----------- #
    # This function will look for an object with the given name in the UI and return it.
    def get(self, objectName):
        return self.findWidget(self.interface.widget, objectName)

    # This function will recursively look into all the object of the UI and compare it to
    # the given name, if it never find it will return "None"
    def findWidget(self, widget, objectName):
        if widget.objectName == objectName:
            return widget
        else:
            for w in widget.children():
                resulting_widget = self.findWidget(w, objectName)
                if resulting_widget:
                    return resulting_widget
            return None


# ****************************************************************** #
# **************** Longitudinal Quantification Test **************** #
# ****************************************************************** #

class LongitudinalQuantificationTest(slicer.ScriptedLoadableModule.ScriptedLoadableModuleTest):
    def __init__(self):
        print "----- Longitudinal Quantification test init -----"

    def setUp(self):
        print "----- Longitudinal Quantification test setup -----"
        # reset the state - clear scene
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        # run all tests needed
        self.delayDisplay("Clear the scene")
        self.setUp()
        self.delayDisplay("Download and load datas")
        self.downloaddata()

    def downloaddata(self):
        import urllib
        downloads = (
            ('http://slicer.kitware.com/midas3/download?items=213632', '01.vtk', slicer.util.loadModel),
            ('http://slicer.kitware.com/midas3/download?items=213633', '02.vtk', slicer.util.loadModel),
        )
        for url, name, loader in downloads:
            filePath = slicer.app.temporaryPath + '/' + name
            print filePath
            if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
                logging.info('Requesting download %s from %s...\n' % (name, url))
                urllib.urlretrieve(url, filePath)
            if loader:
                logging.info('Loading %s...' % (name,))
                loader(filePath)

        layoutManager = slicer.app.layoutManager()
        threeDWidget = layoutManager.threeDWidget(0)
        threeDView = threeDWidget.threeDView()
        threeDView.resetFocalPoint()