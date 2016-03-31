import vtk, qt, ctk, slicer
import os
from slicer.ScriptedLoadableModule import *
import numpy
import time
from slicer.ScriptedLoadableModule import *
import json
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

        libPath = os.path.join(scriptedModulesPath, '..', 'PythonLibrairies')
        sys.path.insert(0, libPath)

        # import the external library that contain the functions comon to all DCBIA modules
        import DCBIALogic
        reload(DCBIALogic)

        #reload the logic if there is any change
        self.DCBIALogic = DCBIALogic.DCBIALogic(self)
        self.logic = PickAndPaintLogic(interface=self, DCBIALogic=self.DCBIALogic)
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

        self.inputModelLabel = self.DCBIALogic.get("inputModelLabel")  # this atribute is usefull for Longitudinal quantification extension
        self.inputLandmarksLabel = self.DCBIALogic.get("inputLandmarksLabel")  # this atribute is usefull for Longitudinal quantification extension
        self.inputModelSelector = self.DCBIALogic.get("inputModelSelector")
        self.inputModelSelector.setMRMLScene(slicer.mrmlScene)
        self.inputLandmarksSelector = self.DCBIALogic.get("inputLandmarksSelector")
        self.inputLandmarksSelector.setMRMLScene(slicer.mrmlScene)
        self.inputLandmarksSelector.setEnabled(False) # The "enable" property seems to not be imported from the .ui
        self.loadLandmarksOnSurfacCheckBox = self.DCBIALogic.get("loadLandmarksOnSurfacCheckBox")
        self.landmarksScaleWidget = self.DCBIALogic.get("landmarksScaleWidget")
        self.addLandmarksButton = self.DCBIALogic.get("addLandmarksButton")
        self.surfaceDeplacementCheckBox = self.DCBIALogic.get("surfaceDeplacementCheckBox")
        self.landmarkComboBox = self.DCBIALogic.get("landmarkComboBox")
        self.radiusDefinitionWidget = self.DCBIALogic.get("radiusDefinitionWidget")
        self.cleanerButton = self.DCBIALogic.get("cleanerButton")
        self.correspondentShapes = self.DCBIALogic.get("correspondentShapes")
        self.nonCorrespondentShapes = self.DCBIALogic.get("nonCorrespondentShapes")
        self.propagationInputComboBox = self.DCBIALogic.get("propagationInputComboBox")
        self.propagationInputComboBox.setMRMLScene(slicer.mrmlScene)
        self.propagateButton = self.DCBIALogic.get("propagateButton")

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
            landmarkDescription = self.DCBIALogic.decodeJSON(fidList.GetAttribute("landmarkDescription"))
            if landmarkDescription:
                for n in range(fidList.GetNumberOfMarkups()):
                    markupID = fidList.GetNthMarkupID(n)
                    markupLabel = fidList.GetNthMarkupLabel(n)
                    landmarkDescription[markupID]["landmarkLabel"] = markupLabel
                fidList.SetAttribute("landmarkDescription",self.DCBIALogic.encodeJSON(landmarkDescription))

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
        self.DCBIALogic.selectedFidList = None
        self.DCBIALogic.selectedModel = None

    def UpdateInterface(self):
        if not self.DCBIALogic.selectedModel:
            return
        activeInput = self.DCBIALogic.selectedModel
        if not self.DCBIALogic.selectedFidList:
            return
        fidList = self.DCBIALogic.selectedFidList
        selectedFidReflID = self.DCBIALogic.findIDFromLabel(fidList, self.landmarkComboBox.currentText)

        if activeInput:
            # Update values on widgets.
            landmarkDescription = self.DCBIALogic.decodeJSON(fidList.GetAttribute("landmarkDescription"))
            if landmarkDescription and selectedFidReflID:
                activeDictLandmarkValue = landmarkDescription[selectedFidReflID]
                self.radiusDefinitionWidget.value = activeDictLandmarkValue["ROIradius"]
                if activeDictLandmarkValue["projection"]["isProjected"]:
                    self.surfaceDeplacementCheckBox.setChecked(True)
                else:
                    self.surfaceDeplacementCheckBox.setChecked(False)
            else:
                self.radiusDefinitionWidget.value = 0.0
            self.DCBIALogic.UpdateThreeDView(self.landmarkComboBox.currentText)


    def onModelChanged(self):
        print "-------Model Changed--------"
        if self.DCBIALogic.selectedModel:
            Model = self.DCBIALogic.selectedModel
            try:
                Model.RemoveObserver(self.DCBIALogic.decodeJSON(self.DCBIALogic.selectedModel.GetAttribute("modelModifieTagEvent")))
            except:
                pass
        self.DCBIALogic.selectedModel = self.inputModelSelector.currentNode()
        self.DCBIALogic.ModelChanged(self.inputModelSelector, self.inputLandmarksSelector)
        self.inputLandmarksSelector.setCurrentNode(None)

    def onLandmarksChanged(self):
        print "-------Landmarks Changed--------"
        if self.inputModelSelector.currentNode():
            self.DCBIALogic.selectedFidList = self.inputLandmarksSelector.currentNode()
            self.DCBIALogic.selectedModel = self.inputModelSelector.currentNode()
            if self.inputLandmarksSelector.currentNode():
                onSurface = self.loadLandmarksOnSurfacCheckBox.isChecked()
                self.DCBIALogic.connectLandmarks(self.inputModelSelector,
                                      self.inputLandmarksSelector,
                                      onSurface)
            else:
                self.landmarkComboBox.clear()

    def onAddButton(self):
        # Add fiducial on the scene.
        # If no input model selected, the addition of fiducial shouldn't be possible.
        selectionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLSelectionNodeSingleton")
        selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLMarkupsFiducialNode")
        if self.DCBIALogic.selectedModel:
            if self.DCBIALogic.selectedFidList:
                selectionNode.SetActivePlaceNodeID(self.DCBIALogic.selectedFidList.GetID())
                self.interactionNode.SetCurrentInteractionMode(1)
            else:
                self.DCBIALogic.warningMessage("Please select a fiducial list")
        else:
            self.DCBIALogic.warningMessage("Please select a model")

    def onLandmarksScaleChanged(self):
        if not self.DCBIALogic.selectedFidList:
            self.DCBIALogic.warningMessage("Please select a fiducial list")
            return
        print "------------Landmark scaled change-----------"
        displayFiducialNode = self.DCBIALogic.selectedFidList.GetMarkupsDisplayNode()
        disabledModify = displayFiducialNode.StartModify()
        displayFiducialNode.SetGlyphScale(self.landmarksScaleWidget.value)
        displayFiducialNode.SetTextScale(self.landmarksScaleWidget.value)
        displayFiducialNode.EndModify(disabledModify)

    def onSurfaceDeplacementStateChanged(self):
        activeInput = self.DCBIALogic.selectedModel
        if not activeInput:
            return
        fidList = self.DCBIALogic.selectedFidList
        if not fidList:
            return
        selectedFidReflID = self.DCBIALogic.findIDFromLabel(fidList, self.landmarkComboBox.currentText)
        isOnSurface = self.surfaceDeplacementCheckBox.isChecked()
        landmarkDescription = self.DCBIALogic.decodeJSON(fidList.GetAttribute("landmarkDescription"))
        if isOnSurface:
            hardenModel = slicer.app.mrmlScene().GetNodeByID(fidList.GetAttribute("hardenModelID"))
            landmarkDescription[selectedFidReflID]["projection"]["isProjected"] = True
            landmarkDescription[selectedFidReflID]["projection"]["closestPointIndex"] =\
                self.DCBIALogic.projectOnSurface(hardenModel, fidList, selectedFidReflID)
        else:
            landmarkDescription[selectedFidReflID]["projection"]["isProjected"] = False
            landmarkDescription[selectedFidReflID]["projection"]["closestPointIndex"] = None
            landmarkDescription[selectedFidReflID]["ROIradius"] = 0
        fidList.SetAttribute("landmarkDescription",self.DCBIALogic.encodeJSON(landmarkDescription))


    def onLandmarkComboBoxChanged(self):
        print "-------- ComboBox changement --------"
        self.UpdateInterface()

    def onRadiusValueChanged(self):
        print "--------- ROI radius modification ----------"
        fidList = self.DCBIALogic.selectedFidList
        if not fidList:
            return
        selectedFidReflID = self.DCBIALogic.findIDFromLabel(fidList, self.landmarkComboBox.currentText)
        if selectedFidReflID:
            landmarkDescription = self.DCBIALogic.decodeJSON(fidList.GetAttribute("landmarkDescription"))
            activeLandmarkState = landmarkDescription[selectedFidReflID]
            activeLandmarkState["ROIradius"] = self.radiusDefinitionWidget.value
            if not activeLandmarkState["projection"]["isProjected"]:
                self.surfaceDeplacementCheckBox.setChecked(True)
                hardenModel = slicer.app.mrmlScene().GetNodeByID(fidList.GetAttribute("hardenModelID"))
                landmarkDescription[selectedFidReflID]["projection"]["isProjected"] = True
                landmarkDescription[selectedFidReflID]["projection"]["closestPointIndex"] =\
                    self.DCBIALogic.projectOnSurface(hardenModel, fidList, selectedFidReflID)
            fidList.SetAttribute("landmarkDescription",self.DCBIALogic.encodeJSON(landmarkDescription))
            self.DCBIALogic.findROI(fidList)

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
        self.inputLandmarksSelector.currentNode().SetAttribute("modelToPropList",self.DCBIALogic.encodeJSON({"modelToPropList":finalList}))

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
            self.DCBIALogic.warningMessage("Please select at list one model for propagation")
            return

        # propagation
        isSourceModelClean = self.DCBIALogic.decodeJSON(model.GetAttribute("isClean"))
        hardenModel = self.DCBIALogic.createIntermediateHardenModel(model)
        model.SetAttribute("hardenModelID",hardenModel.GetID())
        arrayName = fidList.GetAttribute("arrayName")
        for modelToPropagateID in modelToPropIDList:
            modelToPropagate = slicer.mrmlScene.GetNodeByID(modelToPropagateID)
            isModelToPropagateClean = self.DCBIALogic.decodeJSON(modelToPropagate.GetAttribute("isClean"))

            if self.correspondentShapes.isChecked() and (isSourceModelClean != isModelToPropagateClean):
                self.DCBIALogic.warningMessage("caution, some models seams to not be "
                                               "clean wereath while some others "
                                               "are, it could make a bad propagation!")
            self.logic.cleanerAndTriangleFilter(modelToPropagate)
            hardenModel = self.DCBIALogic.createIntermediateHardenModel(modelToPropagate)
            modelToPropagate.SetAttribute("hardenModelID",hardenModel.GetID())
            if self.correspondentShapes.isChecked():
                fidList.SetAttribute("typeOfPropagation","correspondentShapes")
                self.logic.propagateCorrespondent(model, modelToPropagate, arrayName)
            else:
                fidList.SetAttribute("typeOfPropagation","nonCorrespondentShapes")
                self.logic.propagateNonCorrespondent(fidList, modelToPropagate)
        self.UpdateInterface()



class PickAndPaintLogic(ScriptedLoadableModuleLogic):
    def __init__(self, interface, DCBIALogic):
        self.DCBIALogic = DCBIALogic
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
        activeInput = self.DCBIALogic.selectedModel
        fidList = self.DCBIALogic.selectedFidList
        hardenModel = slicer.app.mrmlScene().GetNodeByID(activeInput.GetAttribute("hardenModelID"))
        if activeInput:
            # Clean the mesh with vtkCleanPolyData cleaner and vtkTriangleFilter:
            self.cleanerAndTriangleFilter(activeInput)
            self.cleanerAndTriangleFilter(hardenModel)
            # Define the new ROI:
            selectedLandmarkID = self.DCBIALogic.findIDFromLabel(fidList, selectedLandmark)
            if selectedLandmarkID:
                landmarkDescription = self.DCBIALogic.decodeJSON(fidList.GetAttribute("landmarkDescription"))
                landmarkDescription[selectedLandmarkID]["projection"]["closestPointIndex"] =\
                    self.DCBIALogic.projectOnSurface(hardenModel, fidList, selectedLandmarkID)
                fidList.SetAttribute("landmarkDescription",self.DCBIALogic.encodeJSON(landmarkDescription))
            fidList.SetAttribute("isClean",self.DCBIALogic.encodeJSON({"isClean":True}))
            connectedModel = slicer.app.mrmlScene().GetNodeByID(fidList.GetAttribute("connectedModelID"))
            connectedModel.SetAttribute("isClean",self.DCBIALogic.encodeJSON({"isClean":True}))


    def propagateCorrespondent(self, referenceInputModel, propagatedInputModel, arrayName):
        referencePointData = referenceInputModel.GetPolyData().GetPointData()
        propagatedPointData = propagatedInputModel.GetPolyData().GetPointData()
        arrayToPropagate = referencePointData.GetArray(arrayName)
        if arrayToPropagate:

            if propagatedPointData.GetArray(arrayName): # Array already exists
                propagatedPointData.RemoveArray(arrayName)
            propagatedPointData.AddArray(arrayToPropagate)
            self.DCBIALogic.displayROI(propagatedInputModel, arrayName)
        else:
            print " NO ROI ARRAY FOUND. PLEASE DEFINE ONE BEFORE."
            return

    def propagateNonCorrespondent(self, fidList, modelToPropagate):
        print modelToPropagate.GetAttribute("hardenModelID")
        hardenModel = slicer.app.mrmlScene().GetNodeByID(modelToPropagate.GetAttribute("hardenModelID"))
        landmarkDescription = self.DCBIALogic.decodeJSON(fidList.GetAttribute("landmarkDescription"))
        arrayName = fidList.GetAttribute("arrayName")
        ROIPointListID = vtk.vtkIdList()
        for key,activeLandmarkState in landmarkDescription.iteritems():
            tempROIPointListID = vtk.vtkIdList()
            markupsIndex = fidList.GetMarkupIndexByID(key)
            indexClosestPoint = self.DCBIALogic.getClosestPointIndex(fidList,modelToPropagate.GetPolyData(),markupsIndex)
            if activeLandmarkState["ROIradius"] != 0:
                self.DCBIALogic.defineNeighbor(tempROIPointListID,
                                    hardenModel.GetPolyData(),
                                    indexClosestPoint,
                                    activeLandmarkState["ROIradius"])
            for j in range(0, tempROIPointListID.GetNumberOfIds()):
                ROIPointListID.InsertUniqueId(tempROIPointListID.GetId(j))
        listID = ROIPointListID
        self.DCBIALogic.addArrayFromIdList(listID, modelToPropagate, arrayName)
        self.DCBIALogic.displayROI(modelToPropagate, arrayName)

class PickAndPaintTest(ScriptedLoadableModuleTest):
    def setUp(self):
        self.widget = slicer.modules.PickAndPaintWidget
        slicer.mrmlScene.Clear(0)

    def runTest(self):
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


        closestPointIndexList.append(self.widget.DCBIALogic.getClosestPointIndex(slicer.mrmlScene.GetNodeByID(markupsLogic.GetActiveListID()),
                                                                polyData,
                                                                0))
        closestPointIndexList.append(self.widget.DCBIALogic.getClosestPointIndex(slicer.mrmlScene.GetNodeByID(markupsLogic.GetActiveListID()),
                                                                polyData,
                                                                1))
        closestPointIndexList.append(self.widget.DCBIALogic.getClosestPointIndex(slicer.mrmlScene.GetNodeByID(markupsLogic.GetActiveListID()),
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
            self.widget.DCBIALogic.replaceLandmark(polyData, slicer.mrmlScene.GetNodeByID(markupsLogic.GetActiveListID()),
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
            self.widget.DCBIALogic.defineNeighbor(inter,
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
            self.widget.DCBIALogic.defineNeighbor(inter, polyData, closestPointIndexList[i], i + 1)
            self.widget.DCBIALogic.addArrayFromIdList(inter,
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