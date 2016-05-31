import os
from __main__ import vtk, qt, ctk, slicer
import logging
import numpy
import pickle
from math import *
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import sys


class ModelAddedClass(VTKObservationMixin):
    def __init__(self, anglePlanes):
        VTKObservationMixin.__init__(self)
        self.addObserver(slicer.mrmlScene, slicer.vtkMRMLScene.NodeAddedEvent, self.nodeAddedCallback)
        self.addObserver(slicer.mrmlScene, slicer.vtkMRMLScene.NodeRemovedEvent, self.nodeRemovedCallback)
        self.anglePlanes = anglePlanes

    @vtk.calldata_type(vtk.VTK_OBJECT)
    def nodeAddedCallback(self, caller, eventId, callData):
        if isinstance(callData, slicer.vtkMRMLModelNode):
            callData.AddObserver(callData.DisplayModifiedEvent, self.anglePlanes.onChangeModelDisplay)
            self.addObserver(callData, callData.PolyDataModifiedEvent, self.onModelNodePolyDataModified)
            self.anglePlanes.updateOnSurfaceCheckBoxes()

    @vtk.calldata_type(vtk.VTK_OBJECT)
    def nodeRemovedCallback(self, caller, eventId, callData):
        if isinstance(callData, slicer.vtkMRMLModelNode):
            self.removeObserver(callData, callData.PolyDataModifiedEvent, self.onModelNodePolyDataModified)
            callData.RemoveObservers(callData.DisplayModifiedEvent)
            self.anglePlanes.updateOnSurfaceCheckBoxes()
        if isinstance(callData, slicer.vtkMRMLMarkupsFiducialNode):
            name = callData.GetName()
            planeid = name[len('P'):]
            name = "Plane " + planeid
            if name in self.anglePlanes.planeControlsDictionary.keys():
                self.anglePlanes.RemoveManualPlane(planeid)

    def onModelNodePolyDataModified(self, caller, eventId):
        pass

class AnglePlanes(ScriptedLoadableModule):
    def __init__(self, parent):

        ScriptedLoadableModule.__init__(self, parent)
        parent.title = "Angle Planes"
        parent.categories = ["Quantification"]
        parent.dependencies = []
        parent.contributors = ["Julia Lopinto", "Juan Carlos Prieto", "Francois Budin", "Jean-Baptiste Vimort"]
        parent.helpText = """
            This Module is used to calculate the angle between two planes by using the normals.
            The user gets the choice to use two planes which are already implemented on Slicer
            or they can define a plane by using landmarks (at least 3 landmarks).
            Plane can also be saved to be reused for other models.
            This is an alpha version of the module.
            It can't be used for the moment.
            """

        parent.acknowledgementText = """
            This work was supported by the National
            Institutes of Dental and Craniofacial Research
            and Biomedical Imaging and Bioengineering of
            the National Institutes of Health under Award
            Number R01DE024450.
            """

        self.parent = parent

class AnglePlanesWidget(ScriptedLoadableModuleWidget):
    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        print "-------Angle Planes Widget Setup-------"
        self.moduleName = 'AnglePlanes'
        scriptedModulesPath = eval('slicer.modules.%s.path' % self.moduleName.lower())
        scriptedModulesPath = os.path.dirname(scriptedModulesPath)

        libPath = os.path.join(scriptedModulesPath)
        sys.path.insert(0, libPath)

        # import the external library that contain the functions comon to all DCBIA modules
        import ShapeQuantifierCore
        reload(ShapeQuantifierCore)

        self.ShapeQuantifierCore = ShapeQuantifierCore.ShapeQuantifierCore(interface = self)
        self.logic = AnglePlanesLogic(interface=self, ShapeQuantifierCore=self.ShapeQuantifierCore)
        self.planeControlsId = 0
        self.planeControlsDictionary = {}
        self.planeCollection = vtk.vtkPlaneCollection()
        self.ignoredNodeNames = ('Red Volume Slice', 'Yellow Volume Slice', 'Green Volume Slice')
        self.colorSliceVolumes = dict()
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

        #--------------------------- Scene --------------------------#
        self.SceneCollapsibleButton = self.ShapeQuantifierCore.get("SceneCollapsibleButton") # this atribute is usefull for Shape Quantifier extension
        treeView = self.ShapeQuantifierCore.get("treeView")
        treeView.setMRMLScene(slicer.app.mrmlScene())
        treeView.sceneModel().setHorizontalHeaderLabels(["Models"])
        treeView.sortFilterProxyModel().nodeTypes = ['vtkMRMLModelNode']
        treeView.header().setVisible(False)
        self.autoChangeLayout = self.ShapeQuantifierCore.get("autoChangeLayout")
        self.computeBox = self.ShapeQuantifierCore.get("computeBox")
        # -------------------------------Manage planes---------------------------------
        self.inputModelLabel = self.ShapeQuantifierCore.get("inputModelLabel")  # this atribute is usefull for Shape Quantifier extension
        self.inputLandmarksLabel = self.ShapeQuantifierCore.get("inputLandmarksLabel")  # this atribute is usefull for Shape Quantifier extension
        self.CollapsibleButton = self.ShapeQuantifierCore.get("CollapsibleButton")
        self.managePlanesFormLayout = self.ShapeQuantifierCore.get("managePlanesFormLayout")
        self.inputModelSelector = self.ShapeQuantifierCore.get("inputModelSelector")
        self.inputModelSelector.setMRMLScene(slicer.mrmlScene)
        self.inputLandmarksSelector = self.ShapeQuantifierCore.get("inputLandmarksSelector")
        self.inputLandmarksSelector.setMRMLScene(slicer.mrmlScene)
        self.inputLandmarksSelector.setEnabled(False) # The "enable" property seems to not be imported from the .ui
        self.loadLandmarksOnSurfacCheckBox = self.ShapeQuantifierCore.get("loadLandmarksOnSurfacCheckBox")
        self.addPlaneButton = self.ShapeQuantifierCore.get("addPlaneButton")
        self.landmarkComboBox = self.ShapeQuantifierCore.get("landmarkComboBox")
        self.surfaceDeplacementCheckBox = self.ShapeQuantifierCore.get("surfaceDeplacementCheckBox")
        # ----------------- Compute Mid Point -------------
        self.midPointGroupBox = self.ShapeQuantifierCore.get("midPointGroupBox")
        self.selectPlaneForMidPoint = self.ShapeQuantifierCore.get("selectPlaneForMidPoint")
        self.landmarkComboBox1MidPoint = self.ShapeQuantifierCore.get("landmarkComboBox1MidPoint")
        self.landmarkComboBox2MidPoint = self.ShapeQuantifierCore.get("landmarkComboBox2MidPoint")
        self.midPointOnSurfaceCheckBox = self.ShapeQuantifierCore.get("midPointOnSurfaceCheckBox")
        self.defineMiddlePointButton = self.ShapeQuantifierCore.get("defineMiddlePointButton")
        # -------- Choose planes ------------
        self.CollapsibleButtonPlane = self.ShapeQuantifierCore.get("CollapsibleButtonPlane")
        self.planeComboBox1 = self.ShapeQuantifierCore.get("planeComboBox1")
        self.planeComboBox2 = self.ShapeQuantifierCore.get("planeComboBox2")
        # -------- Calculate angles between planes ------------
        self.CollapsibleButton2 = self.ShapeQuantifierCore.get("CollapsibleButton2")
        self.results = self.ShapeQuantifierCore.get("results")
        self.tableResult = self.ShapeQuantifierCore.get("tableResult")
        self.getAngle_RL = qt.QLabel("0")
        self.getAngle_RL.setStyleSheet('QLabel{qproperty-alignment:AlignCenter;}')
        self.getAngle_SI = qt.QLabel("0")
        self.getAngle_SI.setStyleSheet('QLabel{qproperty-alignment:AlignCenter;}')
        self.getAngle_AP = qt.QLabel("0")
        self.getAngle_AP.setStyleSheet('QLabel{qproperty-alignment:AlignCenter;}')
        self.getAngle_RL_comp = qt.QLabel("0")
        self.getAngle_RL_comp.setStyleSheet('QLabel{qproperty-alignment:AlignCenter;}')
        self.getAngle_SI_comp = qt.QLabel("0")
        self.getAngle_SI_comp.setStyleSheet('QLabel{qproperty-alignment:AlignCenter;}')
        self.getAngle_AP_comp = qt.QLabel("0")
        self.getAngle_AP_comp.setStyleSheet('QLabel{qproperty-alignment:AlignCenter;}')
        self.tableResult.setColumnWidth(1, 180)
        self.tableResult.setCellWidget(0, 0, self.getAngle_RL)
        self.tableResult.setCellWidget(0, 1, self.getAngle_RL_comp)
        self.tableResult.setCellWidget(1, 0, self.getAngle_SI)
        self.tableResult.setCellWidget(1, 1, self.getAngle_SI_comp)
        self.tableResult.setCellWidget(2, 0, self.getAngle_AP)
        self.tableResult.setCellWidget(2, 1, self.getAngle_AP_comp)
        # -------------------------------- PLANES --------------------------------#
        self.CollapsibleButton3 = self.ShapeQuantifierCore.get("CollapsibleButton3")
        self.save = self.ShapeQuantifierCore.get("save")
        self.read = self.ShapeQuantifierCore.get("read")
        #-------------------------------- CONNECTIONS --------------------------------#
        self.computeBox.connect('clicked()', self.onComputeBox)
        self.inputModelSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onModelChanged)
        self.inputLandmarksSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onLandmarksChanged)
        self.planeComboBox1.connect('currentIndexChanged(QString)', self.valueComboBox)
        self.planeComboBox2.connect('currentIndexChanged(QString)', self.valueComboBox)
        self.addPlaneButton.connect('clicked()', self.addNewPlane)
        self.landmarkComboBox.connect('currentIndexChanged(QString)', self.UpdateInterface)
        self.surfaceDeplacementCheckBox.connect('stateChanged(int)', self.onSurfaceDeplacementStateChanged)
        self.selectPlaneForMidPoint.connect('currentIndexChanged(int)', self.onChangeMiddlePointFiducialNode)
        self.defineMiddlePointButton.connect('clicked()', self.onAddMidPoint)
        self.results.connect('clicked()', self.angleValue)
        self.save.connect('clicked(bool)', self.onSavePlanes)
        self.read.connect('clicked(bool)', self.onReadPlanes)

        slicer.mrmlScene.AddObserver(slicer.mrmlScene.EndCloseEvent, self.onCloseScene)

        for i in self.getPositionOfModelNodes(False):
            modelnode = slicer.mrmlScene.GetNthNodeByClass(i, "vtkMRMLModelNode")
            modelnode.AddObserver(modelnode.DisplayModifiedEvent, self.onChangeModelDisplay)
        ModelAddedClass(self)

        # ------------------------------ INITIALISATION ---------------------------------
        self.fillColorsComboBox(self.planeComboBox1)
        self.fillColorsComboBox(self.planeComboBox2)
        self.planeComboBox1.setCurrentIndex(0)
        self.planeComboBox2.setCurrentIndex(0)
        self.valueComboBox()

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
            landmarkDescription = self.ShapeQuantifierCore.decodeJSON(fidList.GetAttribute("landmarkDescription"))
            if landmarkDescription:
                for n in range(fidList.GetNumberOfMarkups()):
                    markupID = fidList.GetNthMarkupID(n)
                    markupLabel = fidList.GetNthMarkupLabel(n)
                    landmarkDescription[markupID]["landmarkLabel"] = markupLabel
                print landmarkDescription
                fidList.SetAttribute("landmarkDescription",self.ShapeQuantifierCore.encodeJSON(landmarkDescription))

        onSurface = self.loadLandmarksOnSurfacCheckBox.isChecked()
        self.ShapeQuantifierCore.connectLandmarks(self.inputModelSelector,
                              self.inputLandmarksSelector,
                              onSurface)

    def UpdateInterface(self):
        self.ShapeQuantifierCore.UpdateThreeDView(self.landmarkComboBox.currentText)

    def onModelChanged(self):
        print "-------Model Changed--------"
        if self.ShapeQuantifierCore.selectedModel:
            Model = self.ShapeQuantifierCore.selectedModel
            try:
                Model.RemoveObserver(self.ShapeQuantifierCore.decodeJSON(self.ShapeQuantifierCore.selectedModel.GetAttribute("modelModifieTagEvent")))
            except:
                pass
        self.ShapeQuantifierCore.selectedModel = self.inputModelSelector.currentNode()
        self.ShapeQuantifierCore.ModelChanged(self.inputModelSelector, self.inputLandmarksSelector)
        self.inputLandmarksSelector.setCurrentNode(None)
        self.addPlaneButton.setEnabled(False)

    def onLandmarksChanged(self):
        print "-------Landmarks Changed--------"
        if self.inputModelSelector.currentNode():
            self.ShapeQuantifierCore.FidList = self.inputLandmarksSelector.currentNode()
            self.ShapeQuantifierCore.selectedFidList = self.inputLandmarksSelector.currentNode()
            self.ShapeQuantifierCore.selectedModel = self.inputModelSelector.currentNode()
            if self.inputLandmarksSelector.currentNode():
                onSurface = self.loadLandmarksOnSurfacCheckBox.isChecked()
                self.ShapeQuantifierCore.connectLandmarks(self.inputModelSelector,
                                      self.inputLandmarksSelector,
                                      onSurface)
                self.addPlaneButton.setEnabled(True)
            else:
                self.addPlaneButton.setEnabled(False)
                self.landmarkComboBox.clear()

    def onSurfaceDeplacementStateChanged(self):
        activeInput = self.ShapeQuantifierCore.selectedModel
        if not activeInput:
            return
        fidList = self.ShapeQuantifierCore.selectedFidList
        if not fidList:
            return
        selectedFidReflID = self.ShapeQuantifierCore.findIDFromLabel(fidList, self.landmarkComboBox.currentText)
        isOnSurface = self.surfaceDeplacementCheckBox.isChecked()
        landmarkDescription = self.ShapeQuantifierCore.decodeJSON(fidList.GetAttribute("landmarkDescription"))
        if isOnSurface:
            hardenModel = slicer.app.mrmlScene().GetNodeByID(fidList.GetAttribute("hardenModelID"))
            landmarkDescription[selectedFidReflID]["projection"]["isProjected"] = True
            landmarkDescription[selectedFidReflID]["projection"]["closestPointIndex"] =\
                self.ShapeQuantifierCore.projectOnSurface(hardenModel, fidList, selectedFidReflID)
        else:
            landmarkDescription[selectedFidReflID]["projection"]["isProjected"] = False
            landmarkDescription[selectedFidReflID]["projection"]["closestPointIndex"] = None
            landmarkDescription[selectedFidReflID]["ROIradius"] = 0
        fidList.SetAttribute("landmarkDescription",self.ShapeQuantifierCore.encodeJSON(landmarkDescription))

    def onChangeMiddlePointFiducialNode(self):
        key = self.selectPlaneForMidPoint.currentText
        if key is "":
            return
        plane = self.planeControlsDictionary[key]
        fidList = plane.fidlist
        self.ShapeQuantifierCore.updateLandmarkComboBox(fidList, self.landmarkComboBox1MidPoint)
        self.ShapeQuantifierCore.updateLandmarkComboBox(fidList, self.landmarkComboBox2MidPoint)

    def onChangeModelDisplay(self, obj, event):
        self.updateOnSurfaceCheckBoxes()

    def fillColorsComboBox(self, planeComboBox):
        planeComboBox.clear()
        planeComboBox.addItem("None")
        planeComboBox.addItem("Red")
        planeComboBox.addItem("Yellow")
        planeComboBox.addItem("Green")
        try:
            for x in self.planeControlsDictionary.keys():
                if self.planeControlsDictionary[x].PlaneIsDefined():
                    planeComboBox.addItem(x)
        except NameError:
            print "exept in fillColorsComboBox"

    def updateOnSurfaceCheckBoxes(self):
        numberOfVisibleModels = len(self.getPositionOfModelNodes(True))
        if numberOfVisibleModels > 0:
            self.computeBox.setDisabled(False)
        else:
            self.computeBox.setDisabled(True)

    def getPositionOfModelNodes(self, onlyVisible):
        numNodes = slicer.mrmlScene.GetNumberOfNodesByClass("vtkMRMLModelNode")
        positionOfNodes = list()
        for i in range(0, numNodes):
            node = slicer.mrmlScene.GetNthNodeByClass(i, "vtkMRMLModelNode")
            if node.GetName() in self.ignoredNodeNames:
                continue
            if onlyVisible is True and node.GetDisplayVisibility() == 0:
                continue
            positionOfNodes.append(i)
        return positionOfNodes

    def addNewPlane(self, keyLoad=-1):
        print "------- New plane created -------"
        if keyLoad != -1:
            self.planeControlsId = keyLoad
        else:
            self.planeControlsId += 1
        planeControls = AnglePlanesWidgetPlaneControl(self,
                                                      self.planeControlsId,
                                                      self.planeCollection,
                                                      self.inputLandmarksSelector.currentNode())
        self.managePlanesFormLayout.addWidget(planeControls.widget)
        key = "Plane " + str(self.planeControlsId)
        self.planeControlsDictionary[key] = planeControls
        self.updatePlanesComboBoxes()
        self.midPointGroupBox.setDisabled(False)
        self.selectPlaneForMidPoint.addItem(key)

    def RemoveManualPlane(self, id):
        print "--- Remove a plan ---"
        key = "Plane " + str(id)
        # If the plane has already been removed (for example, when removing this plane in this function,
        # the callback on removing the nodes will be called, and therefore this function will be called again
        # We need to not do anything the second time this function is called for the same plane
        if key not in self.planeControlsDictionary.keys():
            print "Key error"
            return
        if self.planeComboBox1.currentText == key:
            self.planeComboBox1.setCurrentIndex(0)
        if self.planeComboBox2.currentText == key:
            self.planeComboBox2.setCurrentIndex(0)
        planeControls = self.planeControlsDictionary[key]
        self.managePlanesFormLayout.removeWidget(planeControls.widget)
        planeControls.widget.hide()
        planeControls.deleteLater()
        planeControls.remove()
        self.planeControlsDictionary.pop(key)
        self.addPlaneButton.setDisabled(False)
        if len(self.planeControlsDictionary.keys()) == 0:
            self.midPointGroupBox.setDisabled(True)
            self.midPointGroupBox.collapsed = True
        self.updatePlanesComboBoxes()
        self.valueComboBox()
        if self.selectPlaneForMidPoint.findText(key) > -1:
            self.selectPlaneForMidPoint.removeItem(self.selectPlaneForMidPoint.findText(key))

    def onComputeBox(self):
        positionOfVisibleNodes = self.getPositionOfModelNodes(True)
        if len(positionOfVisibleNodes) == 0:
            return
        try:
            maxValue = slicer.sys.float_info.max
        except:
            maxValue = self.logic.sys.float_info.max
        bound = [maxValue, -maxValue, maxValue, -maxValue, maxValue, -maxValue]
        for i in positionOfVisibleNodes:
            node = slicer.mrmlScene.GetNthNodeByClass(i, "vtkMRMLModelNode")
            model = self.ShapeQuantifierCore.createIntermediateHardenModel(node)
            polydata = model.GetPolyData()
            if polydata is None or not hasattr(polydata, "GetBounds"):
                continue
            tempbound = polydata.GetBounds()
            bound[0] = min(bound[0], tempbound[0])
            bound[2] = min(bound[2], tempbound[2])
            bound[4] = min(bound[4], tempbound[4])

            bound[1] = max(bound[1], tempbound[1])
            bound[3] = max(bound[3], tempbound[3])
            bound[5] = max(bound[5], tempbound[5])
        # --------------------------- Box around the model --------------------------#
        dim = []
        origin = []
        for x in range(0, 3):
            dim.append(bound[x * 2 + 1] - bound[x * 2])
            origin.append(bound[x * 2] + dim[x] / 2)
            dim[x] *= 1.1
        # ---------definition of planes for clipping around the bounding box ---------#
        self.planeCollection = vtk.vtkPlaneCollection()
        self.planeXmin = vtk.vtkPlane()
        self.planeXmin.SetOrigin(bound[0],bound[2],bound[4])
        self.planeXmin.SetNormal(1,0,0)
        self.planeCollection.AddItem(self.planeXmin)
        self.planeYmin = vtk.vtkPlane()
        self.planeYmin.SetOrigin(bound[0],bound[2],bound[4])
        self.planeYmin.SetNormal(0,1,0)
        self.planeCollection.AddItem(self.planeYmin)
        self.planeZmin = vtk.vtkPlane()
        self.planeZmin.SetOrigin(bound[0],bound[2],bound[4])
        self.planeZmin.SetNormal(0,0,1)
        self.planeCollection.AddItem(self.planeZmin)
        self.planeXmax = vtk.vtkPlane()
        self.planeXmax.SetOrigin(bound[1],bound[3],bound[5])
        self.planeXmax.SetNormal(-1,0,0)
        self.planeCollection.AddItem(self.planeXmax)
        self.planeYmax = vtk.vtkPlane()
        self.planeYmax.SetOrigin(bound[1],bound[3],bound[5])
        self.planeYmax.SetNormal(0,-1,0)
        self.planeCollection.AddItem(self.planeYmax)
        self.planeZmax = vtk.vtkPlane()
        self.planeZmax.SetOrigin(bound[1],bound[3],bound[5])
        self.planeZmax.SetNormal(0,0,-1)
        self.planeCollection.AddItem(self.planeZmax)
        # print self.planeCollection
        dictColors = {'Red': 32, 'Yellow': 15, 'Green': 1}
        for x in dictColors.keys():
            sampleVolumeNode = self.CreateNewNode(x, dictColors[x], dim, origin)
            compNode = slicer.util.getNode('vtkMRMLSliceCompositeNode' + x)
            compNode.SetLinkedControl(False)
            compNode.SetBackgroundVolumeID(sampleVolumeNode.GetID())
            # print "set background" + x
        lm = slicer.app.layoutManager()
        #Reset and fit 2D-views
        lm.resetSliceViews()
        for x in dictColors.keys():
            logic = lm.sliceWidget(x)
            node = logic.mrmlSliceNode()
            node.SetSliceResolutionMode(node.SliceResolutionMatch2DView)
            logic.fitSliceToBackground()
        #Reset pink box around models
        for i in range(0, lm.threeDViewCount):
            threeDView = lm.threeDWidget(i).threeDView()
            threeDView.resetFocalPoint()
            #Reset camera in 3D view to center the models and position the camera so that all actors can be seen
            threeDView.renderWindow().GetRenderers().GetFirstRenderer().ResetCamera()

    def CreateNewNode(self, colorName, color, dim, origin):
        # we add a pseudo-random number to the name of our empty volume to avoid the risk of having a volume called
        #  exactly the same by the user which could be confusing. We could also have used slicer.app.sessionId()
        if colorName not in self.colorSliceVolumes.keys():
            VolumeName = "AnglePlanes_EmptyVolume_" + str(slicer.app.applicationPid()) + "_" + colorName
            # Do NOT set the spacing and the origin of imageData (vtkImageData)
            # The spacing and the origin should only be set in the vtkMRMLScalarVolumeNode!!!!!!
            # We only create an image of 1 voxel (as we only use it to color the planes
            imageData = vtk.vtkImageData()
            imageData.SetDimensions(1, 1, 1)
            imageData.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, 1)
            imageData.SetScalarComponentFromDouble(0, 0, 0, 0, color)
            if hasattr(slicer, 'vtkMRMLLabelMapVolumeNode'):
                sampleVolumeNode = slicer.vtkMRMLLabelMapVolumeNode()
            else:
                sampleVolumeNode = slicer.vtkMRMLScalarVolumeNode()
            sampleVolumeNode = slicer.mrmlScene.AddNode(sampleVolumeNode)
            sampleVolumeNode.SetName(VolumeName)
            labelmapVolumeDisplayNode = slicer.vtkMRMLLabelMapVolumeDisplayNode()
            slicer.mrmlScene.AddNode(labelmapVolumeDisplayNode)
            colorNode = slicer.util.getNode('GenericAnatomyColors')
            labelmapVolumeDisplayNode.SetAndObserveColorNodeID(colorNode.GetID())
            sampleVolumeNode.SetAndObserveImageData(imageData)
            sampleVolumeNode.SetAndObserveDisplayNodeID(labelmapVolumeDisplayNode.GetID())
            labelmapVolumeDisplayNode.VisibilityOn()
            self.colorSliceVolumes[colorName] = sampleVolumeNode.GetID()
        sampleVolumeNode = slicer.mrmlScene.GetNodeByID(self.colorSliceVolumes[colorName])
        sampleVolumeNode.HideFromEditorsOn()
        sampleVolumeNode.SetOrigin(origin[0], origin[1], origin[2])
        sampleVolumeNode.SetSpacing(dim[0], dim[1], dim[2])
        if not hasattr(slicer, 'vtkMRMLLabelMapVolumeNode'):
            sampleVolumeNode.SetLabelMap(1)
        sampleVolumeNode.SetHideFromEditors(True)
        sampleVolumeNode.SetSaveWithScene(False)
        return sampleVolumeNode

    def onAddMidPoint(self):
        key = self.selectPlaneForMidPoint.currentText
        plane = self.planeControlsDictionary[key]
        fidList = plane.fidlist
        if not fidList:
            self.ShapeQuantifierCore.warningMessage("Fiducial list problem.")
        landmark1ID = self.ShapeQuantifierCore.findIDFromLabel(fidList,self.landmarkComboBox1MidPoint.currentText)
        landmark2ID = self.ShapeQuantifierCore.findIDFromLabel(fidList,self.landmarkComboBox2MidPoint.currentText)
        coord = self.ShapeQuantifierCore.calculateMidPointCoord(fidList, landmark1ID, landmark2ID)
        fidList.AddFiducial(coord[0],coord[1],coord[2])
        fidList.SetNthFiducialSelected(fidList.GetNumberOfMarkups() - 1, False)
        # update of the data structure
        landmarkDescription = self.ShapeQuantifierCore.decodeJSON(fidList.GetAttribute("landmarkDescription"))
        numOfMarkups = fidList.GetNumberOfMarkups()
        markupID = fidList.GetNthMarkupID(numOfMarkups - 1)
        landmarkDescription[landmark1ID]["midPoint"]["definedByThisMarkup"].append(markupID)
        landmarkDescription[landmark2ID]["midPoint"]["definedByThisMarkup"].append(markupID)
        landmarkDescription[markupID]["midPoint"]["isMidPoint"] = True
        landmarkDescription[markupID]["midPoint"]["Point1"] = landmark1ID
        landmarkDescription[markupID]["midPoint"]["Point2"] = landmark2ID
        landmarkDescription[markupID]["projection"]["isProjected"] = False
        landmarkDescription[markupID]["projection"]["closestPointIndex"] = None
        if self.midPointOnSurfaceCheckBox.isChecked():
            landmarkDescription[markupID]["projection"]["isProjected"] = True
            hardenModel = slicer.app.mrmlScene().GetNodeByID(fidList.GetAttribute("hardenModelID"))
            landmarkDescription[markupID]["projection"]["closestPointIndex"] = \
                self.ShapeQuantifierCore.projectOnSurface(hardenModel, fidList, markupID)
        else:
            landmarkDescription[markupID]["projection"]["isProjected"] = False
        fidList.SetAttribute("landmarkDescription",self.ShapeQuantifierCore.encodeJSON(landmarkDescription))
        self.ShapeQuantifierCore.interface.UpdateInterface()
        self.ShapeQuantifierCore.updateLandmarkComboBox(fidList, self.landmarkComboBox, False)
        fidList.SetNthFiducialPositionFromArray(numOfMarkups - 1, coord)

    def onCloseScene(self, obj, event):
        self.colorSliceVolumes = dict()
        self.planeControlsId = 0
        list = slicer.mrmlScene.GetNodesByClass("vtkMRMLModelNode")
        end = list.GetNumberOfItems()
        for i in range(0,end):
            model = list.GetItemAsObject(i)
            hardenModel = slicer.mrmlScene.GetNodesByName(model.GetName()).GetItemAsObject(0)
            slicer.mrmlScene.RemoveNode(hardenModel)
        keys = self.planeControlsDictionary.keys()
        for x in keys:
            self.RemoveManualPlane(x[len('Plane '):])
        self.planeControlsDictionary = dict()
        self.addPlaneButton.setDisabled(True)
        self.getAngle_RL.setText("0")
        self.getAngle_RL_comp.setText("0")
        self.getAngle_SI.setText("0")
        self.getAngle_SI_comp.setText("0")
        self.getAngle_AP.setText("0")
        self.getAngle_AP_comp.setText("0")
        self.landmarkComboBox.clear()

    def angleValue(self):
        self.valueComboBox()
        self.getAngle_RL.setText(self.logic.angle_degre_RL)
        self.getAngle_RL_comp.setText(self.logic.angle_degre_RL_comp)
        self.getAngle_SI.setText(self.logic.angle_degre_SI)
        self.getAngle_SI_comp.setText(self.logic.angle_degre_SI_comp)
        self.getAngle_AP.setText(self.logic.angle_degre_AP)
        self.getAngle_AP_comp.setText(self.logic.angle_degre_AP_comp)

    def setFirstItemInComboBoxNotGivenString(self, comboBox, oldString, noThisString):
        if comboBox.findText(oldString) == -1:
            comboBox.setCurrentIndex(1)
        else:
            comboBox.setCurrentIndex(comboBox.findText(oldString))

    def updatePlanesComboBoxes(self):
        print "---- update plane combobox ----"
        self.planeComboBox1.blockSignals(True)
        self.planeComboBox2.blockSignals(True)
        colorPlane1 = self.planeComboBox1.currentText
        colorPlane2 = self.planeComboBox2.currentText
        # Reset Combo boxes
        self.fillColorsComboBox(self.planeComboBox1)
        self.fillColorsComboBox(self.planeComboBox2)
        if colorPlane1 != "None":
            self.planeComboBox2.removeItem(self.planeComboBox2.findText(colorPlane1))
        if colorPlane2 != "None":
            self.planeComboBox1.removeItem(self.planeComboBox1.findText(colorPlane2))
        self.setFirstItemInComboBoxNotGivenString(self.planeComboBox1, colorPlane1, colorPlane2)
        self.setFirstItemInComboBoxNotGivenString(self.planeComboBox2, colorPlane2, colorPlane1)
        self.planeComboBox1.blockSignals(False)
        self.planeComboBox2.blockSignals(False)

    def valueComboBox(self):
        self.updatePlanesComboBoxes()
        # Hide everything before showing what is necessary
        for x in self.logic.ColorNodeCorrespondence.keys():
            compNode = slicer.util.getNode('vtkMRMLSliceCompositeNode' + x)
            compNode.SetLinkedControl(False)
            slice = slicer.mrmlScene.GetNodeByID(self.logic.ColorNodeCorrespondence[x])
            slice.SetWidgetVisible(False)
            slice.SetSliceVisible(False)
        colorPlane1 = self.planeComboBox1.currentText
        colorPlane2 = self.planeComboBox2.currentText
        self.defineAngle(colorPlane1, colorPlane2)

    def defineAngle(self, colorPlane1, colorPlane2):
        print "--- defineAngle ---"
        # print colorPlane1
        if colorPlane1 != "None":
            if colorPlane1 in self.logic.ColorNodeCorrespondence:
                slice1 = slicer.util.getNode(self.logic.ColorNodeCorrespondence[colorPlane1])
                self.logic.getMatrix(slice1)
                slice1.SetWidgetVisible(True)
                slice1.SetSliceVisible(True)
                matrix1 = self.logic.getMatrix(slice1)
                normal1 = self.logic.defineNormal(matrix1)
            else:
                normal1 = self.planeControlsDictionary[colorPlane1].normal
        else:
            return
        # print colorPlane2
        if colorPlane2 != "None":
            if colorPlane2 in self.logic.ColorNodeCorrespondence:
                slice2 = slicer.util.getNode(self.logic.ColorNodeCorrespondence[colorPlane2])
                self.logic.getMatrix(slice2)
                slice2.SetWidgetVisible(True)
                slice2.SetSliceVisible(True)
                matrix2 = self.logic.getMatrix(slice2)
                normal2 = self.logic.defineNormal(matrix2)
            else:
                normal2 = self.planeControlsDictionary[colorPlane2].normal
        else:
            return
        print "normal 1"
        print normal1
        print "normal 2"
        print normal2
        self.logic.getAngle(normal1, normal2)

    def onSavePlanes(self):
        self.logic.savePlanes()

    def onReadPlanes(self):
        self.logic.readPlanes()
        self.onComputeBox()

# This widget controls each of the planes that are added to the interface.
# The widget contains its own logic, i.e. an object of AnglePlanesLogic.
# Each plane contains a separate fiducial list. The planes are named P1, P2, ..., PN. The landmarks are named
# P1-1, P1-2, P1-N.
class AnglePlanesWidgetPlaneControl(qt.QFrame):
    def __init__(self, anglePlanes, id, planeCollection, fidlist):
        # ------------- variables -------------------
        self.anglePlanes = anglePlanes
        self.planeCollection = planeCollection
        self.id = id
        self.fidlist = fidlist
        self.actor = vtk.vtkActor()
        self.normal = None
        # -------------- interface -------------------
        qt.QFrame.__init__(self)
        # UI setup
        loader = qt.QUiLoader()
        moduleName = 'AnglePlanes'
        scriptedModulesPath = eval('slicer.modules.%s.path' % moduleName.lower())
        scriptedModulesPath = os.path.dirname(scriptedModulesPath)
        path = os.path.join(scriptedModulesPath, 'Resources', 'UI', 'PlaneControl.ui')
        qfile = qt.QFile(path)
        widget = loader.load(qfile)
        self.widget = widget
        # self.anglePlanes.layout.addWidget(widget)

        self.planeLabel = self.anglePlanes.ShapeQuantifierCore.findWidget(self.widget, "planeLabel")
        self.planeLabel.setText('Plane ' + str(id) + ":")
        self.addFiducialButton = self.anglePlanes.ShapeQuantifierCore.findWidget(self.widget, "addFiducialButton")
        self.landmark1ComboBox = self.anglePlanes.ShapeQuantifierCore.findWidget(self.widget, "landmark1ComboBox")
        self.landmark2ComboBox = self.anglePlanes.ShapeQuantifierCore.findWidget(self.widget, "landmark2ComboBox")
        self.landmark3ComboBox = self.anglePlanes.ShapeQuantifierCore.findWidget(self.widget, "landmark3ComboBox")
        self.slideOpacity = self.anglePlanes.ShapeQuantifierCore.findWidget(self.widget, "slideOpacity")
        self.AdaptToBoundingBoxCheckBox = self.anglePlanes.ShapeQuantifierCore.findWidget(self.widget, "AdaptToBoundingBoxCheckBox")
        self.HidePlaneCheckBox = self.anglePlanes.ShapeQuantifierCore.findWidget(self.widget, "HidePlaneCheckBox")
        self.removePlaneButton = self.anglePlanes.ShapeQuantifierCore.findWidget(self.widget, "removePlaneButton")
        # connections
        self.addFiducialButton.connect('clicked()', self.addLandMarkClicked)
        self.landmark1ComboBox.connect('currentIndexChanged(QString)', self.placePlaneClicked)
        self.landmark2ComboBox.connect('currentIndexChanged(QString)', self.placePlaneClicked)
        self.landmark3ComboBox.connect('currentIndexChanged(QString)', self.placePlaneClicked)
        self.slideOpacity.connect('valueChanged(double)', self.placePlaneClicked)
        self.AdaptToBoundingBoxCheckBox.connect('stateChanged(int)', self.onBBox)
        self.AdaptToBoundingBoxCheckBox.connect('stateChanged(int)',self.placePlaneClicked)
        self.HidePlaneCheckBox.connect('stateChanged(int)', self.update)
        self.removePlaneButton.connect('clicked(bool)', self.onRemove)
        # fiducial list for the plane
        self.anglePlanes.ShapeQuantifierCore.updateLandmarkComboBox(self.fidlist, self.landmark1ComboBox)
        self.anglePlanes.ShapeQuantifierCore.updateLandmarkComboBox(self.fidlist, self.landmark2ComboBox)
        self.anglePlanes.ShapeQuantifierCore.updateLandmarkComboBox(self.fidlist, self.landmark3ComboBox)


    def PlaneIsDefined(self):
        landmark1 = self.anglePlanes.ShapeQuantifierCore.findIDFromLabel(self.fidlist, self.landmark1ComboBox.currentText)
        landmark2 = self.anglePlanes.ShapeQuantifierCore.findIDFromLabel(self.fidlist, self.landmark2ComboBox.currentText)
        landmark3 = self.anglePlanes.ShapeQuantifierCore.findIDFromLabel(self.fidlist, self.landmark3ComboBox.currentText)
        if landmark1 and landmark2 and landmark3:
            if landmark1 != landmark2 \
                    and landmark3 != landmark2 \
                    and landmark3 != landmark1:
                return True
        return False

    def onRemove(self):
        self.anglePlanes.RemoveManualPlane(self.id)

    def getFiducials(self):

        listCoord = list()

        coord = numpy.zeros(3)
        self.fidlist.GetNthFiducialPosition(int(self.landmark1ComboBox.currentIndex) - 1, coord)
        listCoord.append(coord)

        self.fidlist.GetNthFiducialPosition(int(self.landmark2ComboBox.currentIndex) - 1, coord)
        listCoord.append(coord)

        self.fidlist.GetNthFiducialPosition(int(self.landmark3ComboBox.currentIndex) - 1, coord)
        listCoord.append(coord)

        return listCoord

    def placePlaneClicked(self):
        self.anglePlanes.valueComboBox()
        self.update()

    def onBBox(self):
        self.anglePlanes.onComputeBox()
        self.update()

    def update(self):
        self.planeCollection = self.anglePlanes.planeCollection
        if self.PlaneIsDefined():
            if self.HidePlaneCheckBox.isChecked():
                self.normal = self.anglePlanes.logic.planeLandmarks(self.fidlist,
                                          self.landmark1ComboBox.currentText, self.landmark2ComboBox.currentText,
                                          self.landmark3ComboBox.currentText, self.normal,
                                          self.AdaptToBoundingBoxCheckBox,
                                          0, self.planeCollection, self.actor)
            else:
                self.normal = self.anglePlanes.logic.planeLandmarks(self.fidlist,
                                          self.landmark1ComboBox.currentText, self.landmark2ComboBox.currentText,
                                          self.landmark3ComboBox.currentText, self.normal,
                                          self.AdaptToBoundingBoxCheckBox,
                                          self.slideOpacity.value, self.planeCollection, self.actor)

    def addLandMarkClicked(self):
        print "Add landmarks"
        self.anglePlanes.inputModelSelector.setCurrentNode(slicer.app.mrmlScene().GetNodeByID(self.fidlist.GetAttribute("connectedModelID")))
        self.anglePlanes.inputLandmarksSelector.setCurrentNode(self.fidlist)
        # Place landmarks in the 3D scene
        selectionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLSelectionNodeSingleton")
        selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLMarkupsFiducialNode")
        selectionNode.SetActivePlaceNodeID(self.fidlist.GetID())
        # print selectionNode
        interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
        interactionNode.SetCurrentInteractionMode(1)
        # To select multiple points in the 3D view, we want to have to click
        # on the "place fiducial" button multiple times
        placeModePersistence = 0
        interactionNode.SetPlaceModePersistence(placeModePersistence)

    def remove(self):
        renderer = list()
        renderWindow = list()
        layoutManager = slicer.app.layoutManager()
        for i in range(0, layoutManager.threeDViewCount):
            threeDWidget = layoutManager.threeDWidget(i)
            threeDView = threeDWidget.threeDView()
            renderWindow.append(threeDView.renderWindow())
            renderers = renderWindow[i].GetRenderers()
            renderer.append(renderers.GetFirstRenderer())
            renderer[i].RemoveViewProp(self.actor)
            renderWindow[i].AddRenderer(renderer[i])
            renderer[i].Render()
        self.actor.RemoveAllObservers()
        self.actor = None

class AnglePlanesLogic(ScriptedLoadableModuleLogic):
    try:
        slicer.sys
    except:
        import sys

    def __init__(self, interface = None, ShapeQuantifierCore = None):
        self.ColorNodeCorrespondence = {'Red': 'vtkMRMLSliceNodeRed',
                                        'Yellow': 'vtkMRMLSliceNodeYellow',
                                        'Green': 'vtkMRMLSliceNodeGreen'}
        self.interface = interface
        self.ShapeQuantifierCore = ShapeQuantifierCore

    def getComboboxesToUpdate(self, fidList):
        comboboxesToUpdate = list()
        for planeControls in self.interface.planeControlsDictionary.values():
            if planeControls.fidlist is fidList:
                comboboxesToUpdate.append(planeControls.landmark1ComboBox)
                comboboxesToUpdate.append(planeControls.landmark2ComboBox)
                comboboxesToUpdate.append(planeControls.landmark3ComboBox)
        key = self.interface.selectPlaneForMidPoint.currentText
        if key != '':
            plane = self.interface.planeControlsDictionary[key]
            midFidList = plane.fidlist
            if midFidList == fidList:
                comboboxesToUpdate.append(self.interface.landmarkComboBox1MidPoint)
                comboboxesToUpdate.append(self.interface.landmarkComboBox2MidPoint)
        return comboboxesToUpdate

    def getMatrix(self, slice):
        # print "--- get Matrix ---"
        self.mat = slice.GetSliceToRAS()
        # print self.mat
        # Matrix with the elements of SliceToRAS
        m = numpy.matrix([[self.mat.GetElement(0, 0), self.mat.GetElement(0, 1), self.mat.GetElement(0, 2), self.mat.GetElement(0, 3)],
                          [self.mat.GetElement(1, 0), self.mat.GetElement(1, 1), self.mat.GetElement(1, 2), self.mat.GetElement(1, 3)],
                          [self.mat.GetElement(2, 0), self.mat.GetElement(2, 1), self.mat.GetElement(2, 2), self.mat.GetElement(2, 3)],
                          [self.mat.GetElement(3, 0), self.mat.GetElement(3, 1), self.mat.GetElement(3, 2), self.mat.GetElement(3, 3)]])
        # print m
        return m

    def defineNormal(self, matrix):
        # print "--- defineNormal ---"
        # Normal vector to the Red slice:
        n_vector = numpy.matrix([[0], [0], [1], [1]])

        # point on the Red slice:
        A = numpy.matrix([[0], [0], [0], [1]])

        normalVector = matrix * n_vector
        # print "n : \n", normalVector
        A = matrix * A

        normalVector1 = normalVector

        normalVector1[0] = normalVector[0] - A[0]
        normalVector1[1] = normalVector[1] - A[1]
        normalVector1[2] = normalVector[2] - A[2]

        # print normalVector1

        return normalVector1

    def getAngle(self, normalVect1, normalVect2):
        # print "--- getAngle ---"
        norm1 = sqrt(
            normalVect1[0] * normalVect1[0] + normalVect1[1] * normalVect1[1] + normalVect1[2] * normalVect1[2])
        # print "norme 1: \n", norm1
        norm2 = sqrt(
            normalVect2[0] * normalVect2[0] + normalVect2[1] * normalVect2[1] + normalVect2[2] * normalVect2[2])
        # print "norme 2: \n", norm2


        scalar_product = (
            normalVect1[0] * normalVect2[0] + normalVect1[1] * normalVect2[1] + normalVect1[2] * normalVect2[2])
        # print "scalar product : \n", scalar_product

        angle = acos(scalar_product / (norm1 * norm2))

        # print "radian angle : ", angle

        angle_degree = angle * 180 / pi
        # print "Angle in degree", angle_degree


        norm1_RL = sqrt(normalVect1[1] * normalVect1[1] + normalVect1[2] * normalVect1[2])
        # print "norme RL: \n", norm1_RL
        norm2_RL = sqrt(normalVect2[1] * normalVect2[1] + normalVect2[2] * normalVect2[2])
        # print "norme RL: \n", norm2_RL

        if (norm1_RL == 0 or norm2_RL == 0):
            self.angle_degre_RL = 0
            self.angle_degre_RL_comp = 0
        else:
            scalar_product_RL = (normalVect1[1] * normalVect2[1] + normalVect1[2] * normalVect2[2])
            # print "scalar product : \n", scalar_product_RL
            inter = scalar_product_RL / (norm1_RL * norm2_RL)
            if inter >= [[ 0.99999]]:
                angleRL = 0
            else:
                angleRL = acos(inter)
            # print "radian angle : ", angleRL

            self.angle_degre_RL = angleRL * 180 / pi
            self.angle_degre_RL = round(self.angle_degre_RL, 2)
            # print self.angle_degre_RL
            self.angle_degre_RL_comp = 180 - self.angle_degre_RL

        norm1_SI = sqrt(normalVect1[0] * normalVect1[0] + normalVect1[1] * normalVect1[1])
        # print "norme1_SI : \n", norm1_SI
        norm2_SI = sqrt(normalVect2[0] * normalVect2[0] + normalVect2[1] * normalVect2[1])
        # print "norme2_SI : \n", norm2_SI

        if (norm1_SI == 0 or norm2_SI == 0):
            self.angle_degre_SI = 0
            self.angle_degre_SI_comp = 0
        else:
            scalar_product_SI = (normalVect1[0] * normalVect2[0] + normalVect1[1] * normalVect2[1])
            # print "scalar product_SI : \n", scalar_product_SI

            inter = scalar_product_SI / (norm1_SI * norm2_SI)
            if inter >= [[ 0.99999]]:
                angleSI = 0
            else:
                angleSI = acos(inter)
            # print "radian angle : ", angleSI

            self.angle_degre_SI = angleSI * 180 / pi
            self.angle_degre_SI = round(self.angle_degre_SI, 2)
            # print self.angle_degre_SI
            self.angle_degre_SI_comp = 180 - self.angle_degre_SI
            # print self.angle_degre_SI_comp

        norm1_AP = sqrt(normalVect1[0] * normalVect1[0] + normalVect1[2] * normalVect1[2])
        # print "norme1_SI : \n", norm1_AP
        norm2_AP = sqrt(normalVect2[0] * normalVect2[0] + normalVect2[2] * normalVect2[2])
        # print "norme2_SI : \n", norm2_AP

        if (norm1_AP == 0 or norm2_AP == 0):
            self.angle_degre_AP = 0
            self.angle_degre_AP_comp = 0
        else:
            scalar_product_AP = (normalVect1[0] * normalVect2[0] + normalVect1[2] * normalVect2[2])
            # print "scalar product_SI : \n", scalar_product_AP

            # print "VALUE :", scalar_product_AP/(norm1_AP*norm2_AP)
            inter = scalar_product_AP / (norm1_AP * norm2_AP)
            if inter >= [[ 0.99999]]:
                angleAP = 0
            else:
                angleAP = acos(inter)

            # print "radian angle : ", angleAP

            self.angle_degre_AP = angleAP * 180 / pi
            self.angle_degre_AP = round(self.angle_degre_AP, 2)
            # print self.angle_degre_AP
            self.angle_degre_AP_comp = 180 - self.angle_degre_AP

    def normalLandmarks(self, GA, GB):
        # print "--- normalLandmarks ---"
        Vn = numpy.matrix([[0], [0], [0]])
        Vn[0] = GA[1] * GB[2] - GA[2] * GB[1]
        Vn[1] = GA[2] * GB[0] - GA[0] * GB[2]
        Vn[2] = GA[0] * GB[1] - GA[1] * GB[0]

        # print "Vn = ",Vn

        norm_Vn = sqrt(Vn[0] * Vn[0] + Vn[1] * Vn[1] + Vn[2] * Vn[2])

        # print "norm_Vn = ",norm_Vn

        Normal = Vn / norm_Vn

        # print "N = ",Normal

        return Normal

    def planeLandmarks(self, fidList, Landmark1Label, Landmark2Label, Landmark3Label, Normal,
                       AdaptToBoundingBoxCheckBox, sliderOpacity, planeCollection, actor):
        # print "--- planeLandmarks ---"
        # Limit the number of 3 landmarks to define a plane
        # Keep the coordinates of the landmarks
        landmark1ID = self.ShapeQuantifierCore.findIDFromLabel(fidList, Landmark1Label)
        landmark2ID = self.ShapeQuantifierCore.findIDFromLabel(fidList, Landmark2Label)
        landmark3ID = self.ShapeQuantifierCore.findIDFromLabel(fidList, Landmark3Label)

        if not (landmark1ID and landmark2ID and landmark3ID):
            # print "landmark not defined"
            return

        if AdaptToBoundingBoxCheckBox.isChecked():
            slider = 10000
        else:
            slider = 1

        coord = numpy.zeros(3)
        landmark1Index = fidList.GetMarkupIndexByID(landmark1ID)
        fidList.GetNthFiducialPosition(landmark1Index, coord)
        # print "Landmark1Value: ", coord
        r1 = coord[0]
        a1 = coord[1]
        s1 = coord[2]
        landmark2Index = fidList.GetMarkupIndexByID(landmark2ID)
        fidList.GetNthFiducialPosition(landmark2Index, coord)
        # print "Landmark2Value: ", coord
        r2 = coord[0]
        a2 = coord[1]
        s2 = coord[2]
        landmark3Index = fidList.GetMarkupIndexByID(landmark3ID)
        fidList.GetNthFiducialPosition(landmark3Index, coord)
        # print "Landmark3Value: ", coord
        r3 = coord[0]
        a3 = coord[1]
        s3 = coord[2]

        points = vtk.vtkPoints()
        if points.GetNumberOfPoints() == 0:
            points.InsertNextPoint(r1, a1, s1)
            points.InsertNextPoint(r2, a2, s2)
            points.InsertNextPoint(r3, a3, s3)
        else:
            points.SetPoint(0, r1, a1, s1)
            points.SetPoint(1, r2, a2, s2)
            points.SetPoint(2, r3, a3, s3)
        # print "points ", points

        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points)

        centerOfMass = vtk.vtkCenterOfMass()
        centerOfMass.SetInputData(polydata)
        centerOfMass.SetUseScalarsAsWeights(False)
        centerOfMass.Update()

        G = centerOfMass.GetCenter()

        # print "Center of mass = ",G

        A = (r1, a1, s1)
        B = (r2, a2, s2)
        C = (r3, a3, s3)

        # Vector GA
        GA = numpy.matrix([[0.0], [0.0], [0.0]])
        GA[0] = A[0] - G[0]
        GA[1] = A[1] - G[1]
        GA[2] = A[2] - G[2]

        # print "GA = ", GA

        # Vector BG
        GB = numpy.matrix([[0.0], [0.0], [0.0]])
        GB[0] = B[0] - G[0]
        GB[1] = B[1] - G[1]
        GB[2] = B[2] - G[2]

        # print "GB = ", GB

        # Vector CG
        GC = numpy.matrix([[0.0], [0.0], [0.0]])
        GC[0] = C[0] - G[0]
        GC[1] = C[1] - G[1]
        GC[2] = C[2] - G[2]

        # print "GC = ", GC

        normal = self.normalLandmarks(GA, GB)

        D = numpy.matrix([[0.0], [0.0], [0.0]])
        E = numpy.matrix([[0.0], [0.0], [0.0]])
        F = numpy.matrix([[0.0], [0.0], [0.0]])

        D[0] = slider * GA[0] + G[0]
        D[1] = slider * GA[1] + G[1]
        D[2] = slider * GA[2] + G[2]

        # print "Slider value : ", slider

        # print "D = ",D

        E[0] = slider * GB[0] + G[0]
        E[1] = slider * GB[1] + G[1]
        E[2] = slider * GB[2] + G[2]

        # print "E = ",E

        F[0] = slider * GC[0] + G[0]
        F[1] = slider * GC[1] + G[1]
        F[2] = slider * GC[2] + G[2]

        # print "F = ",F

        planeSource = vtk.vtkPlaneSource()
        planeSource.SetNormal(normal[0], normal[1], normal[2])

        planeSource.SetOrigin(D[0], D[1], D[2])
        planeSource.SetPoint1(E[0], E[1], E[2])
        planeSource.SetPoint2(F[0], F[1], F[2])

        planeSource.Update()

        if AdaptToBoundingBoxCheckBox.isChecked():
            clipper = vtk.vtkClipClosedSurface()
            clipper.SetClippingPlanes(planeCollection)
            clipper.SetInputData(planeSource.GetOutput())
            clipper.Update()
            plane = clipper.GetOutput()
        else:
            plane = planeSource.GetOutput()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(plane)
        mapper.Update()

        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0, 0.4, 0.8)
        actor.GetProperty().SetOpacity(sliderOpacity)

        renderer = list()
        renderWindow = list()
        layoutManager = slicer.app.layoutManager()
        for i in range(0, layoutManager.threeDViewCount):
            threeDWidget = layoutManager.threeDWidget(i)
            threeDView = threeDWidget.threeDView()
            renderWindow.append(threeDView.renderWindow())
            renderers = renderWindow[i].GetRenderers()
            renderer.append(renderers.GetFirstRenderer())
            renderer[i].AddViewProp(actor)
            renderWindow[i].AddRenderer(renderer[i])
            renderer[i].Render()
            renderWindow[i].Render()
        return normal

    def savePlanes(self, filename=None):
        tempDictionary = {}
        for key in self.ColorNodeCorrespondence:
            slice = slicer.util.getNode(self.ColorNodeCorrespondence[key])
            print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            print key
            print slice
            print self.getMatrix(slice)
            print "____________________________________________________"
            tempDictionary[key] = self.getMatrix(slice).tolist()
        if filename is None:
            filename = qt.QFileDialog.getSaveFileName(parent=self.interface, caption='Save file')
        if filename != "":
            fileObj = open(filename, "wb")
            pickle.dump(tempDictionary, fileObj)
            fileObj.close()

    def readPlanes(self, filename=None):
        if filename is None:
            filename = qt.QFileDialog.getOpenFileName(parent=self.interface, caption='Open file')
        if filename != "":
            fileObj = open(filename, "rb")
            tempDictionary = pickle.load(fileObj)
            for key in self.ColorNodeCorrespondence:
                node = slicer.mrmlScene.GetNodeByID(self.ColorNodeCorrespondence[key])
                matList = tempDictionary[key]
                matNode = node.GetSliceToRAS()
                for col in range(0, len(matList)):
                    for row in range(0, len(matList[col])):
                        matNode.SetElement(col, row, matList[col][row])
            fileObj.close()

class AnglePlanesTest(ScriptedLoadableModuleTest):
    def setUp(self):
        # reset the state - clear scene
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        # run all tests needed
        self.delayDisplay("Clear the scene")
        self.setUp()
        self.delayDisplay("Download and load datas")
        self.downloaddata()
        self.delayDisplay("Starting the tests")

        self.delayDisplay("Test1: test save and load Planes")
        self.assertTrue(self.test_SaveLoad_Planes())

        self.delayDisplay("Test2: test adding Planes")
        self.assertTrue(self.test_AddingPlane( "test_sample_LC_T1", "FiducialsT1", "Plane 1",
                                               [[2.10738791, -4.83934865, 36.13066709],
                                                [12.2914279, 15.31336608, 32.52167858],
                                                [18.12651635, 6.39560101, 31.4412528]]))
        self.assertTrue(self.test_AddingPlane( "test_sample_LC_T2", "FiducialsT2", "Plane 2",
                                               [[11.72863443, 14.01486727, 32.8596916],
                                                [7.82101916, 8.1821128, 36.84962826],
                                                [18.10934698, 6.67499921, 32.57312822]]))
        self.assertTrue(self.test_AddingPlane( "test_sample_LC_T3", "FiducialsT3", "Plane 3",
                                               [[19.24090905, 8.41699664, 31.0460558],
                                                [4.99470106, 4.70245687, 34.3911743],
                                                [13.82451733, 14.960671, 30.78424719]]))

        self.delayDisplay("Test3: test of the interactions with the planes")
        self.assertTrue(self.test_interactions())

        self.delayDisplay("Test4: test of angles between planes")
        self.assertTrue(self.test_AngleResult(4, 5, [158.68, 135.63, 168.65]))
        self.assertTrue(self.test_AngleResult(6, 5, [169.23, 178.06, 166.27]))
        self.assertTrue(self.test_AngleResult(5, 4, [10.54, 46.31, 2.38]))
        self.assertTrue(self.test_AngleResult(1, 5, [19.98, 0.0, 24.44]))
        self.assertTrue(self.test_AngleResult(2, 3, [0.0, 174.29, 103.09]))
        self.assertTrue(self.test_AngleResult(3, 4, [99.21, 130.6, 0.0]))

        self.delayDisplay('All tests passed!')

    def downloaddata(self):
        import urllib
        downloads = (
            ('http://slicer.kitware.com/midas3/download?items=239999', 'test_sample_LC_T1.vtk', slicer.util.loadModel),
            ('http://slicer.kitware.com/midas3/download?items=239996', 'test_sample_LC_T2.vtk', slicer.util.loadModel),
            ('http://slicer.kitware.com/midas3/download?items=239993', 'test_sample_LC_T3.vtk', slicer.util.loadModel),
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

    def test_SaveLoad_Planes(self):

        widget = slicer.modules.AnglePlanesWidget

        self.delayDisplay('Saving planes')
        widget.logic.savePlanes("test.p")

        self.delayDisplay('Loading planes')
        widget.logic.readPlanes("test.p")
        return True

    def test_AddingPlane(self, ModelName, FidNodeNampe, PlaneName, PlanePointsCoords):

        self.delayDisplay("Adding " + PlaneName + " to " + ModelName)

        widget = slicer.modules.AnglePlanesWidget
        widget.inputModelSelector.setCurrentNode(
            slicer.mrmlScene.GetNodesByName(ModelName).GetItemAsObject(0))
        inputMarkupsFiducial = slicer.vtkMRMLMarkupsFiducialNode()
        inputMarkupsFiducial.SetName(FidNodeNampe)
        slicer.mrmlScene.AddNode(inputMarkupsFiducial)
        widget.inputLandmarksSelector.setCurrentNode(inputMarkupsFiducial)
        widget.addNewPlane()
        plane = widget.planeControlsDictionary[PlaneName]
        for point in PlanePointsCoords:
            inputMarkupsFiducial.AddFiducial(point[0], point[1], point[2])
            widget.ShapeQuantifierCore.onPointModifiedEvent(inputMarkupsFiducial,None)
        plane.landmark1ComboBox.setCurrentIndex(0)
        plane.landmark2ComboBox.setCurrentIndex(1)
        plane.landmark3ComboBox.setCurrentIndex(2)

        return True

    def test_AngleResult(self, Plane1Index, Plane2Index, Angles):

        widget = slicer.modules.AnglePlanesWidget
        widget.planeComboBox1.setCurrentIndex(0)
        widget.planeComboBox2.setCurrentIndex(0)
        widget.planeComboBox1.setCurrentIndex(Plane1Index)
        widget.planeComboBox2.setCurrentIndex(Plane2Index)

        self.delayDisplay("Test angle between " + widget.planeComboBox1.currentText
                          + " and " + widget.planeComboBox2.currentText)
        widget.angleValue()

        test = widget.logic.angle_degre_RL != Angles[0] or\
               widget.logic.angle_degre_SI != Angles[1] or\
               widget.logic.angle_degre_AP != Angles[2]

        if test:
            print "", "Angle", "Complementary"
            print "R-L-View", widget.logic.angle_degre_RL,widget.logic.angle_degre_RL != Angles[0]
            print "S-I-View", widget.logic.angle_degre_SI,widget.logic.angle_degre_SI != Angles[1]
            print "A-P-View", widget.logic.angle_degre_AP,widget.logic.angle_degre_AP != Angles[2]
            self.delayDisplay('Test Failure!')
            return False

        else:
            return True


    def test_interactions(self):

        widget = slicer.modules.AnglePlanesWidget

        for plane in widget.planeControlsDictionary:
            widget.planeControlsDictionary[plane].HidePlaneCheckBox.setChecked(True)
            widget.planeControlsDictionary[plane].HidePlaneCheckBox.setChecked(False)
            widget.planeControlsDictionary[plane].AdaptToBoundingBoxCheckBox.setChecked(True)

        return True