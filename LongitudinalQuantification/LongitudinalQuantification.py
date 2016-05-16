from __main__ import vtk, qt, ctk, slicer
import os
import sys
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
            if hasattr(self.currentModule, 'widget'):
                self.layout.removeWidget(self.currentModule.widget)
                self.currentModule.widget.hide()
            else:
                self.layout.removeWidget(self.currentModule.widgetRepresentation())
                self.currentModule.widgetRepresentation().hide()
            self.choiceComboBox.setCurrentIndex(0)

    def deleteCurrentModule(self):
        self.hideCurrentModule()
        self.currentModule = None
        self.currentComboboxIndex = 0

    def showCurrentModule(self):
        if self.currentModule:
            if hasattr(self.currentModule, 'widget'):
                self.layout.addWidget(self.currentModule.widget)
                self.currentModule.widget.show()
            else:
                self.layout.addWidget(self.currentModule.widgetRepresentation())
                self.currentModule.widgetRepresentation().show()
            if hasattr(self.currentModule, 'enter'):
                self.currentModule.enter()
            self.choiceComboBox.setCurrentIndex(self.currentComboboxIndex)

    def setCurrentModule(self, module, index):
        self.deleteCurrentModule()
        self.currentModule = module
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
        slicer.ScriptedLoadableModule.ScriptedLoadableModuleWidget.setup(self)
        print "----- Longitudinal Quantification widget setup -----"
        self.moduleName = 'LongitudinalQuantification'
        scriptedModulesPath = eval('slicer.modules.%s.path' % self.moduleName.lower())
        scriptedModulesPath = os.path.dirname(scriptedModulesPath)

        libPath = os.path.join(scriptedModulesPath)
        sys.path.insert(0, libPath)

        # import the external library that contain the functions comon to all DCBIA modules
        import LongitudinalQuantificationCore
        reload(LongitudinalQuantificationCore)

        # ------ Initialisation of Longitudinal quantification and its logic ----- #
        self.LongitudinalQuantificationCore = LongitudinalQuantificationCore.LongitudinalQuantificationCore(interface = self)
        self.logic = LongitudinalQuantificationLogic(self, self.LongitudinalQuantificationCore)

        # ---------------------------------------------------------------- #
        # ---------------- Definition of the UI interface ---------------- #
        # ---------------------------------------------------------------- #

        # ------------ Loading of the .ui file ---------- #

        loader = qt.QUiLoader()
        path = os.path.join(scriptedModulesPath, 'Resources', 'UI', '%s.ui' %self.moduleName)
        qfile = qt.QFile(path)
        qfile.open(qt.QFile.ReadOnly)
        widget = loader.load(qfile, self.parent)
        self.layout = self.parent.layout()
        self.widget = widget
        self.layout.addWidget(widget)

        # ------ Scene Collapsible Button ----- #
        self.SceneCollapsibleButton = self.LongitudinalQuantificationCore.get("SceneCollapsibleButton")
        treeView = self.LongitudinalQuantificationCore.get("treeView")
        treeView.setMRMLScene(slicer.app.mrmlScene())
        treeView.sortFilterProxyModel().nodeTypes = ['vtkMRMLModelNode','vtkMRMLMarkupsFiducialNode']
        sceneModel = treeView.sceneModel()
        sceneModel.colorColumn = 1
        sceneModel.opacityColumn = 2
        treeViewHeader = treeView.header()
        treeViewHeader.setVisible(False)
        treeViewHeader.setStretchLastSection(False)
        treeViewHeader.setResizeMode(sceneModel.nameColumn,qt.QHeaderView.Stretch)
        treeViewHeader.setResizeMode(sceneModel.colorColumn,qt.QHeaderView.ResizeToContents)
        treeViewHeader.setResizeMode(sceneModel.opacityColumn,qt.QHeaderView.ResizeToContents)
        self.computeBoxPushButton = self.LongitudinalQuantificationCore.get("computeBoxPushButton")

        # ------ Step Group Box ----- #
        self.ModelRadioGroupBox = self.LongitudinalQuantificationCore.get("ModelRadioGroupBox")
        self.ModelRadioGroupBox.hide()
        self.Model1RadioButton = self.LongitudinalQuantificationCore.get("Model1RadioButton")
        self.LongitudinalQuantificationCore.get("verticalLayout_4").setAlignment(0x84)
        self.Model2RadioButton = self.LongitudinalQuantificationCore.get("Model2RadioButton")
        self.LongitudinalQuantificationCore.get("verticalLayout_5").setAlignment(0x84)

        # ------ Data selection Collapsible Button ----- #
        self.DataSelectionCollapsibleButton = self.LongitudinalQuantificationCore.get("DataSelectionCollapsibleButton")
        self.SingleModelRadioButton = self.LongitudinalQuantificationCore.get("SingleModelRadioButton")
        self.TwoModelsRadioButton = self.LongitudinalQuantificationCore.get("TwoModelsRadioButton")
        self.LongitudinalQuantificationCore.get("verticalLayout_6").setAlignment(0x84)
        self.LongitudinalQuantificationCore.get("verticalLayout_7").setAlignment(0x84)
        self.Model1groupBox = self.LongitudinalQuantificationCore.get("Model1groupBox")
        self.Model1MRMLNodeComboBox = self.LongitudinalQuantificationCore.get("Model1MRMLNodeComboBox")
        self.Model1MRMLNodeComboBox.setMRMLScene(slicer.mrmlScene)
        self.FidList1MRMLNodeComboBox = self.LongitudinalQuantificationCore.get("FidList1MRMLNodeComboBox")
        self.FidList1MRMLNodeComboBox.setMRMLScene(slicer.mrmlScene)
        self.Model2groupBox = self.LongitudinalQuantificationCore.get("Model2groupBox")
        self.Model2MRMLNodeComboBox = self.LongitudinalQuantificationCore.get("Model2MRMLNodeComboBox")
        self.Model2MRMLNodeComboBox.setMRMLScene(slicer.mrmlScene)
        self.FidList2MRMLNodeComboBox = self.LongitudinalQuantificationCore.get("FidList2MRMLNodeComboBox")
        self.FidList2MRMLNodeComboBox.setMRMLScene(slicer.mrmlScene)

        self.ExternalModuleTabDict = dict()
        # ------ Eternal Modules Selections ----- #
        listOfTab = ["Preprocessing","Quantification","Analysis"]
        for tab in listOfTab:
            self.ExternalModuleTabDict[tab] = ExternalModuleTab()
            self.ExternalModuleTabDict[tab].collapsibleButton = self.LongitudinalQuantificationCore.get(tab + "CollapsibleButton")
            self.ExternalModuleTabDict[tab].layout = self.LongitudinalQuantificationCore.get(tab + "Layout")
            self.ExternalModuleTabDict[tab].choiceComboBox = self.LongitudinalQuantificationCore.get(tab + "ChoiceComboBox")

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

        # ------ Creation of a dictionary that will contain all the modules ----- #
        self.ExternalModulesDict = dict(self.ExternalPythonModules, **self.ExternalCLIModules)

        # ------ Setup of the external Python modules ------ #
        # Hiding of the scene tabs and the input tabs in
        # all the external modules to avoid redundancies
        # and make this module as clear and simple as possible

            #This part of the setup is now made in the enter function

        # ------ Setup of the external CLI modules ------ #
        # Setting the size to the good value

        for key, value in self.ExternalCLIModules.iteritems():
            value.widgetRepresentation().setSizePolicy(1,1)
            value.widgetRepresentation().adjustSize()

        # --------------------------------------------- #
        # ---------------- Connections ---------------- #
        # --------------------------------------------- #

        # ------ Scene Collapsible Button ----- #
        self.SceneCollapsibleButton.\
            connect('clicked()', lambda: self.onSelectedCollapsibleButtonChanged(self.SceneCollapsibleButton))
        self.computeBoxPushButton.connect('clicked()', self.ExternalModulesDict["Easy Clip"].onComputeBox)

        # ------ Step Group Box ----- #
        self.Model1RadioButton.connect('clicked()', self.propagationOfInputDataToExternalModules)
        self.Model2RadioButton.connect('clicked()', self.propagationOfInputDataToExternalModules)

        # ------ Data selection Collapsible Button ----- #
        self.DataSelectionCollapsibleButton.\
            connect('clicked()', lambda: self.onSelectedCollapsibleButtonChanged(self.DataSelectionCollapsibleButton))
        self.SingleModelRadioButton.connect('clicked()', lambda: self.onNumberOfModelForMeasureChange(True))
        self.TwoModelsRadioButton.connect('clicked()', lambda: self.onNumberOfModelForMeasureChange(False))
        self.Model1MRMLNodeComboBox.connect('currentNodeChanged(vtkMRMLNode*)', self.propagationOfInputDataToExternalModules)
        self.FidList1MRMLNodeComboBox.connect('currentNodeChanged(vtkMRMLNode*)', self.propagationOfInputDataToExternalModules)
        self.Model2MRMLNodeComboBox.connect('currentNodeChanged(vtkMRMLNode*)', self.propagationOfInputDataToExternalModules)
        self.FidList2MRMLNodeComboBox.connect('currentNodeChanged(vtkMRMLNode*)', self.propagationOfInputDataToExternalModules)

        # ------ Eternal Modules Selections ----- #
        for key, ExternalModule in self.ExternalModuleTabDict.iteritems():
            ExternalModule.collapsibleButton.connect('clicked()',
                                                     lambda currentCollapsibleButton = ExternalModule.collapsibleButton:
                                                     self.onSelectedCollapsibleButtonChanged(currentCollapsibleButton))
            ExternalModule.choiceComboBox.connect('currentIndexChanged(QString)',
                                                  lambda newModule, currentCombobox = ExternalModule.choiceComboBox:
                                                  self.onExternalModuleChangement(newModule, currentCombobox))

        # ------ Closing of the scene -----#
        slicer.mrmlScene.AddObserver(slicer.mrmlScene.EndCloseEvent, self.onCloseScene)
        self.enter()

    # ******************************************* #
    # ---------------- Algorithm ---------------- #
    # ******************************************* #

    def onReload(self):
        slicer.util.reloadScriptedModule(self.moduleName)
        for key, value in self.ExternalPythonModules.iteritems():
            slicer.util.reloadScriptedModule(value.moduleName)

    # function called each time that the user "enter" in Longitudinal Quantification interface
    def enter(self):
        print "---- Enter Longitudinal Quantification ---- "
        # Hiding the input selection of each module when entering in Longitudinal quantification
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
                value.ModelLabel.hide()
                value.fixedModel.hide()
                value.movingModel.hide()
        for key, ExternalModule in self.ExternalModuleTabDict.iteritems():
            if not ExternalModule.collapsibleButton.collapsed:
                ExternalModule.showCurrentModule()

    # function called each time that the user "exit" in Longitudinal Quantification interface
    def exit(self):
        print "---- Exit Longitudinal Quantification ---- "
        # Showing the input selection of each module when exiting Longitudinal quantification
        # This allow the user to normaly use the modules without Longitudinal Quantification
        for key, value in self.ExternalPythonModules.iteritems():
            if hasattr(value, 'SceneCollapsibleButton'):
                value.SceneCollapsibleButton.show()
            if hasattr(value, 'inputModelLabel'):
                value.inputModelLabel.show()
                value.inputLandmarksLabel.show()
                value.inputModelSelector.show()
                value.inputLandmarksSelector.show()
                value.loadLandmarksOnSurfacCheckBox.show()
            elif hasattr(value, 'InputCollapsibleButton'):
                value.InputCollapsibleButton.show()
                value.ModelLabel.show()
                value.fixedModel.show()
                value.movingModel.show()
            value.layout.addWidget(value.widget)

    # function called each time that the scene is closed (if Longitudinal Quantification has been initialized)
    def onCloseScene(self, obj, event):
        print "---- Close Longitudinal Quantification ---- "
        for ExtModTab in self.ExternalModuleTabDict.itervalues():
            ExtModTab.choiceComboBox.setCurrentIndex(0)

    # ---------- switching of Tab ----------- #
    # Only one tab can be display at the same time, so when one tab is opened
    # all the other tabs are closed by this function
    def onSelectedCollapsibleButtonChanged(self, selectedCollapsibleButton):
        print "--- on Selected Collapsible Button Changed ---"
        if selectedCollapsibleButton.isChecked():
            self.SceneCollapsibleButton.setChecked(False)
            self.DataSelectionCollapsibleButton.setChecked(False)
            for ExtModTab in self.ExternalModuleTabDict.itervalues():
                ExtModTab.choiceComboBox.blockSignals(True)
                if ExtModTab.collapsibleButton is selectedCollapsibleButton:
                    ExtModTab.showCurrentModule()
                else:
                    ExtModTab.collapsibleButton.setChecked(False)
                    ExtModTab.hideCurrentModule()
                ExtModTab.choiceComboBox.blockSignals(False)
            selectedCollapsibleButton.setChecked(True)
            self.propagationOfInputDataToExternalModules()

    # ---------- switching of External Module ----------- #
    # This function hide all the external widgets if they are displayed
    # And show the new external module given in argument
    def onExternalModuleChangement(self, newModule, currentCombobox):
        print "--- on External Module Changement ---"
        for ExtModTab in self.ExternalModuleTabDict.itervalues():
            ExtModTab.choiceComboBox.blockSignals(True)
            if ExtModTab.choiceComboBox is currentCombobox:
                if newModule != "None":
                    ExtModTab.setCurrentModule(self.ExternalModulesDict[newModule], currentCombobox.currentIndex)
                else:
                    ExtModTab.deleteCurrentModule()
            else:
                ExtModTab.hideCurrentModule()
            ExtModTab.choiceComboBox.blockSignals(False)
        self.propagationOfInputDataToExternalModules()

    # ---------- Data Selection ---------- #
    # This function show/enable or hide/disable the different inputs depending
    # if the user check measurement on a single model or between two models
    def onNumberOfModelForMeasureChange(self, isSingleModelMeasurement):
        if isSingleModelMeasurement:
            self.Model2groupBox.setEnabled(False)
            self.ModelRadioGroupBox.hide()
            self.Model1RadioButton.setChecked(True)
            self.ExternalModuleTabDict["Preprocessing"].choiceComboBox.removeItem(2)
        else:
            self.Model2groupBox.setEnabled(True)
            self.ModelRadioGroupBox.show()
            self.Model2MRMLNodeComboBox.setEnabled(True)
            self.FidList2MRMLNodeComboBox.setEnabled(True)
            self.ExternalModuleTabDict["Preprocessing"].choiceComboBox.addItem("Surface Registration")
        self.propagationOfInputDataToExternalModules()

    # This function propagate the inputs selected in the input tab the selected external module
    def propagationOfInputDataToExternalModules(self):
        print "--- Propagation of input data to external Modules ---"
        inputModel1 = self.Model1MRMLNodeComboBox.currentNode()
        inputFidList1 = self.FidList1MRMLNodeComboBox.currentNode()
        inputModel2 = self.Model2MRMLNodeComboBox.currentNode()
        inputFidList2 = self.FidList2MRMLNodeComboBox.currentNode()
        for ExtModTab in self.ExternalModuleTabDict.itervalues():
            if ExtModTab.choiceComboBox.currentIndex != 0:
                if self.SingleModelRadioButton.isChecked():
                    if hasattr(ExtModTab.currentModule, 'inputModelSelector'):
                        ExtModTab.currentModule.inputModelSelector.setCurrentNode(None)
                        ExtModTab.currentModule.inputModelSelector.setCurrentNode(inputModel1)
                        ExtModTab.currentModule.inputLandmarksSelector.setCurrentNode(inputFidList1)
                elif self.TwoModelsRadioButton.isChecked():
                    if self.Model1RadioButton.isChecked():
                        if hasattr(ExtModTab.currentModule, 'inputModelSelector'):
                            ExtModTab.currentModule.inputModelSelector.setCurrentNode(None)
                            ExtModTab.currentModule.inputModelSelector.setCurrentNode(inputModel1)
                            ExtModTab.currentModule.inputLandmarksSelector.setCurrentNode(inputFidList1)
                    elif self.Model2RadioButton.isChecked():
                        if hasattr(ExtModTab.currentModule, 'inputModelSelector'):
                            ExtModTab.currentModule.inputModelSelector.setCurrentNode(None)
                            ExtModTab.currentModule.inputModelSelector.setCurrentNode(inputModel2)
                            ExtModTab.currentModule.inputLandmarksSelector.setCurrentNode(inputFidList2)
                    if hasattr(ExtModTab.currentModule, 'inputFixedModelSelector'):
                        ExtModTab.currentModule.inputFixedModelSelector.setCurrentNode(None)
                        ExtModTab.currentModule.inputFixedModelSelector.setCurrentNode(inputModel1)
                        ExtModTab.currentModule.inputMovingModelSelector.setCurrentNode(None)
                        ExtModTab.currentModule.inputMovingModelSelector.setCurrentNode(inputModel2)
                        ExtModTab.currentModule.inputFixedLandmarksSelector.setCurrentNode(inputFidList1)
                        ExtModTab.currentModule.inputMovingLandmarksSelector.setCurrentNode(inputFidList2)
                        if self.Model1RadioButton.isChecked():
                            ExtModTab.currentModule.fixedModel.setChecked(True)
                            ExtModTab.currentModule.onFixedModelRadio()
                        if self.Model2RadioButton.isChecked():
                            ExtModTab.currentModule.movingModel.setChecked(True)
                            ExtModTab.currentModule.onMovingModelRadio()

# ******************************************************************* #
# **************** Longitudinal Quantification Logic **************** #
# ******************************************************************* #

class LongitudinalQuantificationLogic(slicer.ScriptedLoadableModule.ScriptedLoadableModuleLogic):

    # ************************************************ #
    # ---------------- Initialisation ---------------- #
    # ************************************************ #

    def __init__(self, interface, LongitudinalQuantificationCore):
        print "----- Longitudinal Quantification logic init -----"
        self.interface = interface
        self.LongitudinalQuantificationCore = LongitudinalQuantificationCore

# ****************************************************************** #
# **************** Longitudinal Quantification Test **************** #
# ****************************************************************** #

class LongitudinalQuantificationTest(slicer.ScriptedLoadableModule.ScriptedLoadableModuleTest):

    # ******************************************************** #
    # ---------------- Setup / initialisation ---------------- #
    # ******************************************************** #

    def setUp(self):
        print "----- Longitudinal Quantification test setup -----"
        # reset the state - clear scene
        self.delayDisplay("Clear the scene")
        slicer.mrmlScene.Clear(0)

        self.widget = slicer.modules.LongitudinalQuantificationWidget
        self.logic = self.widget.logic
        self.LongitudinalQuantificationCore = self.widget.LongitudinalQuantificationCore

    def runTest(self):
        # run all tests needed
        self.setUp()

        self.delayDisplay("Starting the test of LongitudinalQuantificationCore")
        self.TestCore()

        self.delayDisplay("Starting the test of AnglePlanes")
        slicer.modules.AnglePlanesInstance.runTest()

        self.delayDisplay("Starting the test of EasyClip")
        slicer.modules.EasyClipInstance.runTest()

        self.delayDisplay("Starting the test of PickAndPaint")
        slicer.modules.PickAndPaintInstance.runTest()

        self.delayDisplay("Starting the test of Q3DC")
        slicer.modules.Q3DCInstance.runTest()

        self.delayDisplay("Starting the test of MeshStatistics")
        slicer.modules.MeshStatisticsInstance.runTest()

        self.delayDisplay("All test passed!")

    # ************************************************************************ #
    # ---------------- Test of LongitudinalQuantificationCore ---------------- #
    # ************************************************************************ #

    def TestCore(self):
        self.setUp()
        self.delayDisplay(' Starting tests ')

        self.delayDisplay(' Test getClosestPointIndex Function ')
        self.assertTrue(self.testGetClosestPointIndexFunction())

        self.delayDisplay(' Test replaceLandmark Function ')
        self.assertTrue( self.testReplaceLandmarkFunction() )

        self.delayDisplay(' Test DefineNeighbors Function ')
        self.assertTrue( self.testDefineNeighborsFunction() )

        self.delayDisplay(' Test addArrayFromIdList Function ')
        self.assertTrue( self.testAddArrayFromIdListFunction() )

        self.delayDisplay(' Tests Passed! ')


    def testGetClosestPointIndexFunction(self):
        sphereModel = self.defineSphere()
        slicer.mrmlScene.AddNode(sphereModel)
        closestPointIndexList = list()
        polyData = sphereModel.GetPolyData()
        markupsLogic = self.defineMarkupsLogic()


        closestPointIndexList.append(self.LongitudinalQuantificationCore.getClosestPointIndex(slicer.mrmlScene.GetNodeByID(markupsLogic.GetActiveListID()),
                                                                polyData,
                                                                0))
        closestPointIndexList.append(self.LongitudinalQuantificationCore.getClosestPointIndex(slicer.mrmlScene.GetNodeByID(markupsLogic.GetActiveListID()),
                                                                polyData,
                                                                1))
        closestPointIndexList.append(self.LongitudinalQuantificationCore.getClosestPointIndex(slicer.mrmlScene.GetNodeByID(markupsLogic.GetActiveListID()),
                                                                polyData,
                                                                2))

        if closestPointIndexList[0] != 9 or closestPointIndexList[1] != 35 or closestPointIndexList[2] != 1:
            return False
        return True

    def testReplaceLandmarkFunction(self):
        print ' Test replaceLandmark Function '
        sphereModel = self.defineSphere()
        polyData = sphereModel.GetPolyData()
        markupsLogic = self.defineMarkupsLogic()
        listCoordinates = list()
        listCoordinates.append([55.28383255004883, 55.28383255004883, 62.34897994995117])
        listCoordinates.append([-68.93781280517578, -68.93781280517578, -22.252094268798828])
        listCoordinates.append([0.0, 0.0, -100.0])
        closestPointIndexList = [9, 35, 1]
        coord = [-1, -1, -1]
        for i in range(0, slicer.mrmlScene.GetNodeByID(markupsLogic.GetActiveListID()).GetNumberOfFiducials() ):
            self.LongitudinalQuantificationCore.replaceLandmark(polyData, slicer.mrmlScene.GetNodeByID(markupsLogic.GetActiveListID()),
                                  i,
                                  closestPointIndexList[i])
            slicer.mrmlScene.GetNodeByID(markupsLogic.GetActiveListID()).GetNthFiducialPosition(i, coord)
            if coord != listCoordinates[i]:
                print i, ' - Failed '
                return False
            else:
                print i, ' - Passed! '
        return True

    def testDefineNeighborsFunction(self):
        sphereModel = self.defineSphere()
        polyData = sphereModel.GetPolyData()
        closestPointIndexList = [9, 35, 1]
        connectedVerticesReferenceList = list()
        connectedVerticesReferenceList.append([9, 2, 3, 8, 10, 15, 16])
        connectedVerticesReferenceList.append(
            [35, 28, 29, 34, 36, 41, 42, 21, 22, 27, 23, 30, 33, 40, 37, 43, 47, 48, 49])
        connectedVerticesReferenceList.append(
            [1, 7, 13, 19, 25, 31, 37, 43, 49, 6, 48, 12, 18, 24, 30, 36, 42, 5, 47, 41, 11, 17, 23, 29, 35])
        connectedVerticesTestedList = list()

        for i in range(0, 3):
            inter = vtk.vtkIdList()
            self.LongitudinalQuantificationCore.defineNeighbor(inter,
                                 polyData,
                                 closestPointIndexList[i],
                                 i + 1)
            connectedVerticesTestedList.append(inter)
            list1 = list()
            for j in range(0, connectedVerticesTestedList[i].GetNumberOfIds()):
                list1.append(int(connectedVerticesTestedList[i].GetId(j)))
            connectedVerticesTestedList[i] = list1
            if connectedVerticesTestedList[i] != connectedVerticesReferenceList[i]:
                print "test ",i ," AddArrayFromIdList: failed"
                return False
            else:
                print "test ",i ," AddArrayFromIdList: succeed"
        return True

    def testAddArrayFromIdListFunction(self):
        sphereModel = self.defineSphere()
        polyData = sphereModel.GetPolyData()
        closestPointIndexList = [9, 35, 1]
        for i in range(0, 3):
            inter = vtk.vtkIdList()
            self.LongitudinalQuantificationCore.defineNeighbor(inter, polyData, closestPointIndexList[i], i + 1)
            self.LongitudinalQuantificationCore.addArrayFromIdList(inter,
                                     sphereModel,
                                     'Test_' + str(i + 1))
            if polyData.GetPointData().HasArray('Test_' + str(i + 1)) != 1:
                print "test ",i ," AddArrayFromIdList: failed"
                return False
            else:
                print "test ",i ," AddArrayFromIdList: succeed"
        return True

    def defineSphere(self):
        sphereSource = vtk.vtkSphereSource()
        sphereSource.SetRadius(100.0)
        model = slicer.vtkMRMLModelNode()
        model.SetAndObservePolyData(sphereSource.GetOutput())
        modelDisplay = slicer.vtkMRMLModelDisplayNode()
        modelDisplay.SetColor(0.5,0.5,0.5)
        slicer.mrmlScene.AddNode(modelDisplay)
        model.SetAndObserveDisplayNodeID(modelDisplay.GetID())
        modelDisplay.SetInputPolyDataConnection(sphereSource.GetOutputPort())
        return model

    def defineMarkupsLogic(self):
        slicer.mrmlScene.Clear(0)
        markupsLogic = slicer.modules.markups.logic()
        markupsLogic.AddFiducial(58.602, 41.692, 62.569)
        markupsLogic.AddFiducial(-59.713, -67.347, -19.529)
        markupsLogic.AddFiducial(-10.573, -3.036, -93.381)
        return markupsLogic