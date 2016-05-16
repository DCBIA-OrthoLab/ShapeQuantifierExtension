import vtk, qt, ctk, slicer
import os
from slicer.ScriptedLoadableModule import *
from slicer.ScriptedLoadableModule import *
import logging
import sys

class PickAndPaint(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        parent.title = "Pick 'n Paint "
        parent.categories = ["Quantification"]
        parent.dependencies = []
        parent.contributors = ["Lucie Macron (University of Michigan), Jean-Baptiste Vimort (University of Michigan)"]
        parent.helpText = """
        Pick 'n Paint tool allows users to select ROIs on a reference model and to propagate it over different time point models.
        """
        parent.acknowledgementText = """
        This work was supported by the National Institues of Dental and Craniofacial Research and Biomedical Imaging and
        Bioengineering of the National Institutes of Health under Award Number R01DE024450
        """
        self.parent = parent

class PickAndPaintWidget(ScriptedLoadableModuleWidget):
    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        print "-------Pick And Paint Widget Setup--------"
        self.moduleName = 'PickAndPaint'
        scriptedModulesPath = eval('slicer.modules.%s.path' % self.moduleName.lower())
        scriptedModulesPath = os.path.dirname(scriptedModulesPath)

        libPath = os.path.join(scriptedModulesPath)
        sys.path.insert(0, libPath)

        # import the external library that contain the functions comon to all DCBIA modules
        import LongitudinalQuantificationCore
        reload(LongitudinalQuantificationCore)

        #reload the logic if there is any change
        self.LongitudinalQuantificationCore = LongitudinalQuantificationCore.LongitudinalQuantificationCore(interface = self)
        self.logic = PickAndPaintLogic(interface=self, LongitudinalQuantificationCore=self.LongitudinalQuantificationCore)
        self.interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")

        # UI setup
        loader = qt.QUiLoader()
        path = os.path.join(scriptedModulesPath, 'Resources', 'UI', '%s.ui' %self.moduleName)
        qfile = qt.QFile(path)
        qfile.open(qt.QFile.ReadOnly)
        widget = loader.load(qfile, self.parent)
        self.layout = self.parent.layout()
        self.widget = widget
        self.layout.addWidget(widget)

        self.inputModelLabel = self.LongitudinalQuantificationCore.get("inputModelLabel")  # this atribute is usefull for Longitudinal quantification extension
        self.inputLandmarksLabel = self.LongitudinalQuantificationCore.get("inputLandmarksLabel")  # this atribute is usefull for Longitudinal quantification extension
        self.inputModelSelector = self.LongitudinalQuantificationCore.get("inputModelSelector")
        self.inputModelSelector.setMRMLScene(slicer.mrmlScene)
        self.inputLandmarksSelector = self.LongitudinalQuantificationCore.get("inputLandmarksSelector")
        self.inputLandmarksSelector.setMRMLScene(slicer.mrmlScene)
        self.inputLandmarksSelector.setEnabled(False) # The "enable" property seems to not be imported from the .ui
        self.loadLandmarksOnSurfacCheckBox = self.LongitudinalQuantificationCore.get("loadLandmarksOnSurfacCheckBox")
        self.landmarksScaleWidget = self.LongitudinalQuantificationCore.get("landmarksScaleWidget")
        self.addLandmarksButton = self.LongitudinalQuantificationCore.get("addLandmarksButton")
        self.surfaceDeplacementCheckBox = self.LongitudinalQuantificationCore.get("surfaceDeplacementCheckBox")
        self.landmarkComboBox = self.LongitudinalQuantificationCore.get("landmarkComboBox")
        self.radiusDefinitionWidget = self.LongitudinalQuantificationCore.get("radiusDefinitionWidget")
        self.cleanerButton = self.LongitudinalQuantificationCore.get("cleanerButton")
        self.correspondentShapes = self.LongitudinalQuantificationCore.get("correspondentShapes")
        self.nonCorrespondentShapes = self.LongitudinalQuantificationCore.get("nonCorrespondentShapes")
        self.propagationInputComboBox = self.LongitudinalQuantificationCore.get("propagationInputComboBox")
        self.propagationInputComboBox.setMRMLScene(slicer.mrmlScene)
        self.propagateButton = self.LongitudinalQuantificationCore.get("propagateButton")

        # ------------------------------------------------------------------------------------
        #                                   CONNECTIONS
        # ------------------------------------------------------------------------------------
        self.inputModelSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onModelChanged)
        self.inputLandmarksSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onLandmarksChanged)
        self.addLandmarksButton.connect('clicked()', self.onAddButton)
        self.cleanerButton.connect('clicked()', self.onCleanButton)
        self.landmarksScaleWidget.connect('valueChanged(double)', self.onLandmarksScaleChanged)
        self.surfaceDeplacementCheckBox.connect('stateChanged(int)', self.onSurfaceDeplacementStateChanged)
        self.landmarkComboBox.connect('currentIndexChanged(QString)', self.onLandmarkComboBoxChanged)
        self.radiusDefinitionWidget.connect('valueChanged(double)', self.onRadiusValueChanged)
        self.propagateButton.connect('clicked()', self.onPropagateButton)


        slicer.mrmlScene.AddObserver(slicer.mrmlScene.EndCloseEvent, self.onCloseScene)

    def enter(self):
        model = self.inputModelSelector.currentNode()
        fidlist = self.inputLandmarksSelector.currentNode()

        if fidlist:
            if fidlist.GetAttribute("connectedModelID") != model.GetID():
                self.inputModelSelector.setCurrentNode(None)
                self.inputLandmarksSelector.setCurrentNode(None)
                self.landmarkComboBox.clear()
        self.UpdateInterface()

        # Checking the names of the fiducials
        list = slicer.mrmlScene.GetNodesByClass("vtkMRMLMarkupsFiducialNode")
        end = list.GetNumberOfItems()
        for i in range(0,end):
            fidList = list.GetItemAsObject(i)
            landmarkDescription = self.LongitudinalQuantificationCore.decodeJSON(fidList.GetAttribute("landmarkDescription"))
            if landmarkDescription:
                for n in range(fidList.GetNumberOfMarkups()):
                    markupID = fidList.GetNthMarkupID(n)
                    markupLabel = fidList.GetNthMarkupLabel(n)
                    landmarkDescription[markupID]["landmarkLabel"] = markupLabel
                fidList.SetAttribute("landmarkDescription",self.LongitudinalQuantificationCore.encodeJSON(landmarkDescription))

    def onCloseScene(self, obj, event):
        list = slicer.mrmlScene.GetNodesByClass("vtkMRMLModelNode")
        end = list.GetNumberOfItems()
        for i in range(0,end):
            model = list.GetItemAsObject(i)
            hardenModel = slicer.mrmlScene.GetNodesByName(model.GetName()).GetItemAsObject(0)
            slicer.mrmlScene.RemoveNode(hardenModel)
        self.radiusDefinitionWidget.value = 0.0
        self.landmarksScaleWidget.value = 2.0
        self.landmarkComboBox.clear()
        self.LongitudinalQuantificationCore.selectedFidList = None
        self.LongitudinalQuantificationCore.selectedModel = None

    def UpdateInterface(self):
        if not self.LongitudinalQuantificationCore.selectedModel:
            return
        activeInput = self.LongitudinalQuantificationCore.selectedModel
        if not self.LongitudinalQuantificationCore.selectedFidList:
            return
        fidList = self.LongitudinalQuantificationCore.selectedFidList
        selectedFidReflID = self.LongitudinalQuantificationCore.findIDFromLabel(fidList, self.landmarkComboBox.currentText)

        if activeInput:
            # Update values on widgets.
            landmarkDescription = self.LongitudinalQuantificationCore.decodeJSON(fidList.GetAttribute("landmarkDescription"))
            if landmarkDescription and selectedFidReflID:
                activeDictLandmarkValue = landmarkDescription[selectedFidReflID]
                self.radiusDefinitionWidget.value = activeDictLandmarkValue["ROIradius"]
                if activeDictLandmarkValue["projection"]["isProjected"]:
                    self.surfaceDeplacementCheckBox.setChecked(True)
                else:
                    self.surfaceDeplacementCheckBox.setChecked(False)
            else:
                self.radiusDefinitionWidget.value = 0.0
            self.LongitudinalQuantificationCore.UpdateThreeDView(self.landmarkComboBox.currentText)


    def onModelChanged(self):
        print "-------Model Changed--------"
        if self.LongitudinalQuantificationCore.selectedModel:
            Model = self.LongitudinalQuantificationCore.selectedModel
            try:
                Model.RemoveObserver(self.LongitudinalQuantificationCore.decodeJSON(self.LongitudinalQuantificationCore.selectedModel.GetAttribute("modelModifieTagEvent")))
            except:
                pass
        self.LongitudinalQuantificationCore.selectedModel = self.inputModelSelector.currentNode()
        self.LongitudinalQuantificationCore.ModelChanged(self.inputModelSelector, self.inputLandmarksSelector)
        self.inputLandmarksSelector.setCurrentNode(None)

    def onLandmarksChanged(self):
        print "-------Landmarks Changed--------"
        if self.inputModelSelector.currentNode():
            self.LongitudinalQuantificationCore.selectedFidList = self.inputLandmarksSelector.currentNode()
            self.LongitudinalQuantificationCore.selectedModel = self.inputModelSelector.currentNode()
            if self.inputLandmarksSelector.currentNode():
                onSurface = self.loadLandmarksOnSurfacCheckBox.isChecked()
                self.LongitudinalQuantificationCore.connectLandmarks(self.inputModelSelector,
                                      self.inputLandmarksSelector,
                                      onSurface)
            else:
                self.landmarkComboBox.clear()

    def onAddButton(self):
        # Add fiducial on the scene.
        # If no input model selected, the addition of fiducial shouldn't be possible.
        selectionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLSelectionNodeSingleton")
        selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLMarkupsFiducialNode")
        if self.LongitudinalQuantificationCore.selectedModel:
            if self.LongitudinalQuantificationCore.selectedFidList:
                selectionNode.SetActivePlaceNodeID(self.LongitudinalQuantificationCore.selectedFidList.GetID())
                self.interactionNode.SetCurrentInteractionMode(1)
            else:
                self.LongitudinalQuantificationCore.warningMessage("Please select a fiducial list")
        else:
            self.LongitudinalQuantificationCore.warningMessage("Please select a model")

    def onLandmarksScaleChanged(self):
        if not self.LongitudinalQuantificationCore.selectedFidList:
            self.LongitudinalQuantificationCore.warningMessage("Please select a fiducial list")
            return
        print "------------Landmark scaled change-----------"
        displayFiducialNode = self.LongitudinalQuantificationCore.selectedFidList.GetMarkupsDisplayNode()
        disabledModify = displayFiducialNode.StartModify()
        displayFiducialNode.SetGlyphScale(self.landmarksScaleWidget.value)
        displayFiducialNode.SetTextScale(self.landmarksScaleWidget.value)
        displayFiducialNode.EndModify(disabledModify)

    def onSurfaceDeplacementStateChanged(self):
        activeInput = self.LongitudinalQuantificationCore.selectedModel
        if not activeInput:
            return
        fidList = self.LongitudinalQuantificationCore.selectedFidList
        if not fidList:
            return
        selectedFidReflID = self.LongitudinalQuantificationCore.findIDFromLabel(fidList, self.landmarkComboBox.currentText)
        isOnSurface = self.surfaceDeplacementCheckBox.isChecked()
        landmarkDescription = self.LongitudinalQuantificationCore.decodeJSON(fidList.GetAttribute("landmarkDescription"))
        if isOnSurface:
            hardenModel = slicer.app.mrmlScene().GetNodeByID(fidList.GetAttribute("hardenModelID"))
            landmarkDescription[selectedFidReflID]["projection"]["isProjected"] = True
            landmarkDescription[selectedFidReflID]["projection"]["closestPointIndex"] =\
                self.LongitudinalQuantificationCore.projectOnSurface(hardenModel, fidList, selectedFidReflID)
        else:
            landmarkDescription[selectedFidReflID]["projection"]["isProjected"] = False
            landmarkDescription[selectedFidReflID]["projection"]["closestPointIndex"] = None
            landmarkDescription[selectedFidReflID]["ROIradius"] = 0
        fidList.SetAttribute("landmarkDescription",self.LongitudinalQuantificationCore.encodeJSON(landmarkDescription))


    def onLandmarkComboBoxChanged(self):
        print "-------- ComboBox changement --------"
        self.UpdateInterface()

    def onRadiusValueChanged(self):
        print "--------- ROI radius modification ----------"
        fidList = self.LongitudinalQuantificationCore.selectedFidList
        if not fidList:
            return
        selectedFidReflID = self.LongitudinalQuantificationCore.findIDFromLabel(fidList, self.landmarkComboBox.currentText)
        if selectedFidReflID:
            landmarkDescription = self.LongitudinalQuantificationCore.decodeJSON(fidList.GetAttribute("landmarkDescription"))
            activeLandmarkState = landmarkDescription[selectedFidReflID]
            activeLandmarkState["ROIradius"] = self.radiusDefinitionWidget.value
            if not activeLandmarkState["projection"]["isProjected"]:
                self.surfaceDeplacementCheckBox.setChecked(True)
                hardenModel = slicer.app.mrmlScene().GetNodeByID(fidList.GetAttribute("hardenModelID"))
                landmarkDescription[selectedFidReflID]["projection"]["isProjected"] = True
                landmarkDescription[selectedFidReflID]["projection"]["closestPointIndex"] =\
                    self.LongitudinalQuantificationCore.projectOnSurface(hardenModel, fidList, selectedFidReflID)
            fidList.SetAttribute("landmarkDescription",self.LongitudinalQuantificationCore.encodeJSON(landmarkDescription))
            self.LongitudinalQuantificationCore.findROI(fidList)

    def onCleanButton(self):
        messageBox = ctk.ctkMessageBox()
        messageBox.setWindowTitle(" /!\ WARNING /!\ ")
        messageBox.setIcon(messageBox.Warning)
        messageBox.setText("Your model is about to be modified")
        messageBox.setInformativeText("Do you want to continue?")
        messageBox.setStandardButtons(messageBox.No | messageBox.Yes)
        choice = messageBox.exec_()
        if choice == messageBox.Yes:
            selectedLandmark = self.landmarkComboBox.currentText
            self.logic.cleanMesh(selectedLandmark)
            self.onRadiusValueChanged()
        else:
            messageBox.setText(" Region not modified")
            messageBox.setStandardButtons(messageBox.Ok)
            messageBox.setInformativeText("")
            messageBox.exec_()

    def onPropagationInputComboBoxCheckedNodesChanged(self):
        if not self.inputModelSelector.currentNode():
            return
        if not self.inputLandmarksSelector.currentNode():
            return
        modelToPropList = self.propagationInputComboBox.checkedNodes()
        finalList = list()
        for model in modelToPropList:
            if model.GetID() != self.inputModelSelector.currentNode().GetID():
                finalList.append(model.GetID())
        self.inputLandmarksSelector.currentNode().SetAttribute("modelToPropList",self.LongitudinalQuantificationCore.encodeJSON({"modelToPropList":finalList}))

    def onPropagateButton(self):
        print " ------------------------------------ onPropagateButton -------------------------------------- "
        # verifications
        if not self.inputModelSelector.currentNode():
            return
        if not self.inputLandmarksSelector.currentNode():
            return
        # recueration of the useful data
        model = self.inputModelSelector.currentNode()
        fidList = self.inputLandmarksSelector.currentNode()
        modelToPropList = self.propagationInputComboBox.checkedNodes()
        modelToPropIDList = list()
        for modelToProp in modelToPropList:
            if modelToProp.GetID() != model.GetID():
                modelToPropIDList.append(modelToProp.GetID())
        # verification if the list is not empty
        if len(modelToPropIDList) is 0:
            self.LongitudinalQuantificationCore.warningMessage("Please select at list one model for propagation")
            return

        # propagation
        isSourceModelClean = self.LongitudinalQuantificationCore.decodeJSON(model.GetAttribute("isClean"))
        hardenModel = self.LongitudinalQuantificationCore.createIntermediateHardenModel(model)
        model.SetAttribute("hardenModelID",hardenModel.GetID())
        arrayName = fidList.GetAttribute("arrayName")
        for modelToPropagateID in modelToPropIDList:
            modelToPropagate = slicer.mrmlScene.GetNodeByID(modelToPropagateID)
            isModelToPropagateClean = self.LongitudinalQuantificationCore.decodeJSON(modelToPropagate.GetAttribute("isClean"))

            if self.correspondentShapes.isChecked() and (isSourceModelClean != isModelToPropagateClean):
                self.LongitudinalQuantificationCore.warningMessage("caution, some models seams to not be "
                                               "clean wereath while some others "
                                               "are, it could make a bad propagation!")
            hardenModel = self.LongitudinalQuantificationCore.createIntermediateHardenModel(modelToPropagate)
            modelToPropagate.SetAttribute("hardenModelID",hardenModel.GetID())
            if self.correspondentShapes.isChecked():
                fidList.SetAttribute("typeOfPropagation","correspondentShapes")
                self.logic.propagateCorrespondent(model, modelToPropagate, arrayName)
            else:
                fidList.SetAttribute("typeOfPropagation","nonCorrespondentShapes")
                self.logic.propagateNonCorrespondent(fidList, modelToPropagate)
        self.UpdateInterface()



class PickAndPaintLogic(ScriptedLoadableModuleLogic):
    def __init__(self, interface, LongitudinalQuantificationCore):
        self.LongitudinalQuantificationCore = LongitudinalQuantificationCore
        self.interface = interface

    def cleanerAndTriangleFilter(self, inputModel):
        cleanerPolydata = vtk.vtkCleanPolyData()
        cleanerPolydata.SetInputData(inputModel.GetPolyData())
        cleanerPolydata.Update()
        triangleFilter = vtk.vtkTriangleFilter()
        triangleFilter.SetInputData(cleanerPolydata.GetOutput())
        triangleFilter.Update()
        inputModel.SetAndObservePolyData(triangleFilter.GetOutput())

    def cleanMesh(self, selectedLandmark):
        activeInput = self.LongitudinalQuantificationCore.selectedModel
        fidList = self.LongitudinalQuantificationCore.selectedFidList
        hardenModel = slicer.app.mrmlScene().GetNodeByID(activeInput.GetAttribute("hardenModelID"))
        if activeInput:
            # Clean the mesh with vtkCleanPolyData cleaner and vtkTriangleFilter:
            self.cleanerAndTriangleFilter(activeInput)
            self.cleanerAndTriangleFilter(hardenModel)
            # Define the new ROI:
            selectedLandmarkID = self.LongitudinalQuantificationCore.findIDFromLabel(fidList, selectedLandmark)
            if selectedLandmarkID:
                landmarkDescription = self.LongitudinalQuantificationCore.decodeJSON(fidList.GetAttribute("landmarkDescription"))
                landmarkDescription[selectedLandmarkID]["projection"]["closestPointIndex"] =\
                    self.LongitudinalQuantificationCore.projectOnSurface(hardenModel, fidList, selectedLandmarkID)
                fidList.SetAttribute("landmarkDescription",self.LongitudinalQuantificationCore.encodeJSON(landmarkDescription))
            fidList.SetAttribute("isClean",self.LongitudinalQuantificationCore.encodeJSON({"isClean":True}))
            connectedModel = slicer.app.mrmlScene().GetNodeByID(fidList.GetAttribute("connectedModelID"))
            connectedModel.SetAttribute("isClean",self.LongitudinalQuantificationCore.encodeJSON({"isClean":True}))


    def propagateCorrespondent(self, referenceInputModel, propagatedInputModel, arrayName):
        referencePointData = referenceInputModel.GetPolyData().GetPointData()
        propagatedPointData = propagatedInputModel.GetPolyData().GetPointData()
        arrayToPropagate = referencePointData.GetArray(arrayName)
        if arrayToPropagate:

            if propagatedPointData.GetArray(arrayName): # Array already exists
                propagatedPointData.RemoveArray(arrayName)
            propagatedPointData.AddArray(arrayToPropagate)
            self.LongitudinalQuantificationCore.displayROI(propagatedInputModel, arrayName)
        else:
            print " NO ROI ARRAY FOUND. PLEASE DEFINE ONE BEFORE."
            return

    def propagateNonCorrespondent(self, fidList, modelToPropagate):
        print modelToPropagate.GetAttribute("hardenModelID")
        hardenModel = slicer.app.mrmlScene().GetNodeByID(modelToPropagate.GetAttribute("hardenModelID"))
        landmarkDescription = self.LongitudinalQuantificationCore.decodeJSON(fidList.GetAttribute("landmarkDescription"))
        arrayName = fidList.GetAttribute("arrayName")
        ROIPointListID = vtk.vtkIdList()
        for key,activeLandmarkState in landmarkDescription.iteritems():
            tempROIPointListID = vtk.vtkIdList()
            markupsIndex = fidList.GetMarkupIndexByID(key)
            indexClosestPoint = self.LongitudinalQuantificationCore.getClosestPointIndex(fidList,modelToPropagate.GetPolyData(),markupsIndex)
            if activeLandmarkState["ROIradius"] != 0:
                self.LongitudinalQuantificationCore.defineNeighbor(tempROIPointListID,
                                    hardenModel.GetPolyData(),
                                    indexClosestPoint,
                                    activeLandmarkState["ROIradius"])
            for j in range(0, tempROIPointListID.GetNumberOfIds()):
                ROIPointListID.InsertUniqueId(tempROIPointListID.GetId(j))
        listID = ROIPointListID
        self.LongitudinalQuantificationCore.addArrayFromIdList(listID, modelToPropagate, arrayName)
        self.LongitudinalQuantificationCore.displayROI(modelToPropagate, arrayName)

class PickAndPaintTest(ScriptedLoadableModuleTest):
    def setUp(self):
        self.widget = slicer.modules.PickAndPaintWidget
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        self.delayDisplay("Clear the scene")
        self.setUp()
        self.delayDisplay("Download and load datas")
        self.downloaddata()
        self.delayDisplay("Starting the tests")

        test_sample_LC_T1 = slicer.mrmlScene.GetNodesByName("test_sample_LC_T1").GetItemAsObject(0)
        test_sample_LC_T2 = slicer.mrmlScene.GetNodesByName("test_sample_LC_T2").GetItemAsObject(0)
        test_sample_LC_T3 = slicer.mrmlScene.GetNodesByName("test_sample_LC_T3").GetItemAsObject(0)
        test_sample_LC_T1_with_ROI = slicer.mrmlScene.GetNodesByName("test_sample_LC_T1_with_ROI").GetItemAsObject(0)
        test_sample_LC_T2_with_correspondent_ROI = slicer.mrmlScene.GetNodesByName("test_sample_LC_T2_with_correspondent_ROI").GetItemAsObject(0)
        test_sample_LC_T3_with_correspondent_ROI = slicer.mrmlScene.GetNodesByName("test_sample_LC_T3_with_correspondent_ROI").GetItemAsObject(0)
        test_sample_LC_T2_with_non_correspondent_ROI = slicer.mrmlScene.GetNodesByName("test_sample_LC_T2_with_non_correspondent_ROI").GetItemAsObject(0)
        test_sample_LC_T3_with_non_correspondent_ROI = slicer.mrmlScene.GetNodesByName("test_sample_LC_T3_with_non_correspondent_ROI").GetItemAsObject(0)

        self.delayDisplay("Test1: definition of a ROI")

        self.assertTrue(self.test_DefinitionOfROI( test_sample_LC_T1, test_sample_LC_T1_with_ROI,"FiducialsT1",
                                               [[2.10738791, -4.83934865, 36.13066709],
                                                [12.2914279, 15.31336608, 32.52167858],
                                                [18.12651635, 6.39560101, 31.4412528]]))

        self.delayDisplay("Test2: non correspondent propagation")
        self.delayDisplay("Test2 - 1: propagation from T1 to T2")
        self.assertTrue(self.test_nonCorrespondentpropagation( test_sample_LC_T1,
                                                   test_sample_LC_T2,
                                                   test_sample_LC_T2_with_non_correspondent_ROI))
        self.delayDisplay("Test2 - 2: propagation from T1 to T3")
        self.assertTrue(self.test_nonCorrespondentpropagation( test_sample_LC_T1,
                                                   test_sample_LC_T3,
                                                   test_sample_LC_T3_with_non_correspondent_ROI))

        self.delayDisplay("Test3: correspondent propagation")
        self.delayDisplay("Test2 - 1: propagation from T1 to T2")
        self.assertTrue(self.test_correspondentpropagation( test_sample_LC_T1,
                                                   test_sample_LC_T2,
                                                   test_sample_LC_T2_with_correspondent_ROI))
        self.delayDisplay("Test2 - 2: propagation from T1 to T3")
        self.assertTrue(self.test_correspondentpropagation( test_sample_LC_T1,
                                                   test_sample_LC_T3,
                                                   test_sample_LC_T3_with_correspondent_ROI))
        self.delayDisplay("Test2 - 3: propagation from T2 to T3")
        self.assertTrue(self.test_correspondentpropagation( test_sample_LC_T2,
                                                   test_sample_LC_T3,
                                                   test_sample_LC_T3_with_correspondent_ROI))

        self.delayDisplay('All tests passed!')

    def downloaddata(self):
        import urllib
        downloads = (
            ('http://slicer.kitware.com/midas3/download?items=239999', 'test_sample_LC_T1.vtk', slicer.util.loadModel),
            ('http://slicer.kitware.com/midas3/download?items=239996', 'test_sample_LC_T2.vtk', slicer.util.loadModel),
            ('http://slicer.kitware.com/midas3/download?items=239993', 'test_sample_LC_T3.vtk', slicer.util.loadModel),
            ('http://slicer.kitware.com/midas3/download?items=240000', 'test_sample_LC_T1_with_ROI.vtk', slicer.util.loadModel),
            ('http://slicer.kitware.com/midas3/download?items=239997', 'test_sample_LC_T2_with_non_correspondent_ROI.vtk', slicer.util.loadModel),
            ('http://slicer.kitware.com/midas3/download?items=239998', 'test_sample_LC_T2_with_correspondent_ROI.vtk', slicer.util.loadModel),
            ('http://slicer.kitware.com/midas3/download?items=239994', 'test_sample_LC_T3_with_non_correspondent_ROI.vtk', slicer.util.loadModel),
            ('http://slicer.kitware.com/midas3/download?items=239995', 'test_sample_LC_T3_with_correspondent_ROI.vtk', slicer.util.loadModel),
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

    def test_DefinitionOfROI(self, Model, FinalModel, FidNodeName, PointsCoords):

        self.delayDisplay("Definition of a FOI on " + Model.GetName())

        widget = slicer.modules.PickAndPaintWidget
        widget.inputModelSelector.setCurrentNode(Model)
        self.inputMarkupsFiducial = slicer.vtkMRMLMarkupsFiducialNode()
        self.inputMarkupsFiducial.SetName(FidNodeName)
        slicer.mrmlScene.AddNode(self.inputMarkupsFiducial)
        widget.inputLandmarksSelector.setCurrentNode(self.inputMarkupsFiducial)
        for point in PointsCoords:
            self.inputMarkupsFiducial.AddFiducial(point[0], point[1], point[2])
            widget.LongitudinalQuantificationCore.onPointModifiedEvent(self.inputMarkupsFiducial,None)
            widget.radiusDefinitionWidget.value = 3.0

        return self.compare_ROIS(self.inputMarkupsFiducial, Model, FinalModel)

    def test_nonCorrespondentpropagation(self, modelToPropagate, model, finalModel):

        widget = slicer.modules.PickAndPaintWidget
        widget.inputModelSelector.setCurrentNode(modelToPropagate)
        widget.nonCorrespondentShapes.setChecked(True)
        widget.propagationInputComboBox.setCheckState(model, 2)
        widget.propagateButton.click()

        widget.propagationInputComboBox.setCheckState(model, 0)

        return self.compare_ROIS(self.inputMarkupsFiducial, model, finalModel)

    def test_correspondentpropagation(self, modelToPropagate, model, finalModel):

        widget = slicer.modules.PickAndPaintWidget
        widget.inputModelSelector.setCurrentNode(modelToPropagate)
        widget.correspondentShapes.setChecked(True)
        widget.propagationInputComboBox.setCheckState(model, 2)
        widget.propagateButton.click()

        widget.propagationInputComboBox.setCheckState(model, 0)

        return self.compare_ROIS(self.inputMarkupsFiducial, model, finalModel)

    def compare_ROIS(self, fidlist, model1, model2):
        ROI1 = model1.GetPolyData().GetPointData().GetArray(fidlist.GetAttribute("arrayName"))
        ROI2 = model2.GetPolyData().GetPointData().GetArray(fidlist.GetAttribute("arrayName"))
        for i in range(0, 1002):
            if ROI1.GetTuple(i)[0] != ROI2.GetTuple(i)[0]:
                print ROI1.GetTuple(i)
                print ROI2.GetTuple(i)
                return False
        return True