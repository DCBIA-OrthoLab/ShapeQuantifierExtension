import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import numpy, csv, os
import json
import time
import math

#
# CalculateDisplacement
#

class DCBIALogic():
    def __init__(self, interface = None):
        self.selectedFidList = None
        self.selectedModel = None
        self.interface = interface

    def get(self, objectName):
        return self.findWidget(self.interface.widget, objectName)

    def findWidget(self, widget, objectName):
        if widget.objectName == objectName:
            return widget
        else:
            for w in widget.children():
                resulting_widget = self.findWidget(w, objectName)
                if resulting_widget:
                    return resulting_widget
            return None

    def UpdateThreeDView(self, landmarkLabel):
        # Update the 3D view on Slicer
        if not self.selectedFidList:
            return
        if not self.selectedModel:
            return
        # print "UpdateThreeDView"
        active = self.selectedFidList
        #deactivate all landmarks
        list = slicer.mrmlScene.GetNodesByClass("vtkMRMLMarkupsFiducialNode")
        end = list.GetNumberOfItems()
        selectedFidReflID = self.findIDFromLabel(active,landmarkLabel)
        for i in range(0,end):
            fidList = list.GetItemAsObject(i)
            landmarkDescription = self.decodeJSON(fidList.GetAttribute("landmarkDescription"))
            for key in landmarkDescription.iterkeys():
                markupsIndex = fidList.GetMarkupIndexByID(key)
                if key != selectedFidReflID:
                    fidList.SetNthMarkupLocked(markupsIndex, True)
                else:
                    fidList.SetNthMarkupLocked(markupsIndex, False)
        displayNode = self.selectedModel.GetModelDisplayNode()
        displayNode.SetScalarVisibility(False)
        if selectedFidReflID != False:
            displayNode.SetScalarVisibility(True)

    def createIntermediateHardenModel(self, model):
        hardenModel = slicer.mrmlScene.GetNodesByName("SurfaceRegistration_" + model.GetName() + "_hardenCopy_" + str(
            slicer.app.applicationPid())).GetItemAsObject(0)
        if hardenModel is None:
            hardenModel = slicer.vtkMRMLModelNode()
        hardenPolyData = vtk.vtkPolyData()
        hardenPolyData.DeepCopy(model.GetPolyData())
        hardenModel.SetAndObservePolyData(hardenPolyData)
        hardenModel.SetName(
            "SurfaceRegistration_" + model.GetName() + "_hardenCopy_" + str(slicer.app.applicationPid()))
        if model.GetParentTransformNode():
            hardenModel.SetAndObserveTransformNodeID(model.GetParentTransformNode().GetID())
        hardenModel.HideFromEditorsOn()
        slicer.mrmlScene.AddNode(hardenModel)
        logic = slicer.vtkSlicerTransformLogic()
        logic.hardenTransform(hardenModel)
        return hardenModel

    def onModelModified(self, obj, event):
        #recompute the harden model
        hardenModel = self.createIntermediateHardenModel(obj)
        obj.SetAttribute("hardenModelID",hardenModel.GetID())
        # for each fiducial list
        list = slicer.mrmlScene.GetNodesByClass("vtkMRMLMarkupsFiducialNode")
        end = list.GetNumberOfItems()
        for i in range(0,end):
            # If landmarks are projected on the modified model
            fidList = list.GetItemAsObject(i)
            if fidList.GetAttribute("connectedModelID"):
                if fidList.GetAttribute("connectedModelID") == obj.GetID():
                    #replace the harden model with the new one
                    fidList.SetAttribute("hardenModelID",hardenModel.GetID())
                    #reproject the fiducials on the new model
                    landmarkDescription = self.decodeJSON(fidList.GetAttribute("landmarkDescription"))
                    for n in range(fidList.GetNumberOfMarkups()):
                        markupID = fidList.GetNthMarkupID(n)
                        if landmarkDescription[markupID]["projection"]["isProjected"] == True:
                            hardenModel = slicer.app.mrmlScene().GetNodeByID(fidList.GetAttribute("hardenModelID"))
                            markupsIndex = fidList.GetMarkupIndexByID(markupID)
                            self.replaceLandmark(hardenModel.GetPolyData(), fidList, markupsIndex,
                                                 landmarkDescription[markupID]["projection"]["closestPointIndex"])
                        fidList.SetAttribute("landmarkDescription",self.encodeJSON(landmarkDescription))

    def ModelChanged(self, inputModelSelector, inputLandmarksSelector):
        inputModel = inputModelSelector.currentNode()
        # if a Model Node is present
        if inputModel:
            self.selectedModel = inputModel
            hardenModel = self.createIntermediateHardenModel(inputModel)
            inputModel.SetAttribute("hardenModelID",hardenModel.GetID())
            modelModifieTagEvent = inputModel.AddObserver(inputModel.TransformModifiedEvent, self.onModelModified)
            inputModel.SetAttribute("modelModifieTagEvent",self.encodeJSON({'modelModifieTagEvent':modelModifieTagEvent}))
            inputLandmarksSelector.setEnabled(True)
        # if no model is selected
        else:
            # Update the fiducial list selector
            inputLandmarksSelector.setCurrentNode(None)
            inputLandmarksSelector.setEnabled(False)

    def isUnderTransform(self, markups):
        if markups.GetParentTransformNode():
            messageBox = ctk.ctkMessageBox()
            messageBox.setWindowTitle(" /!\ WARNING /!\ ")
            messageBox.setIcon(messageBox.Warning)
            messageBox.setText("Your Markup Fiducial Node is currently modified by a transform,"
                               "if you choose to continue the program will apply the transform"
                               "before doing anything else!")
            messageBox.setInformativeText("Do you want to continue?")
            messageBox.setStandardButtons(messageBox.No | messageBox.Yes)
            choice = messageBox.exec_()
            if choice == messageBox.Yes:
                logic = slicer.vtkSlicerTransformLogic()
                logic.hardenTransform(markups)
                return False
            else:
                messageBox.setText(" Node not modified")
                messageBox.setStandardButtons(messageBox.Ok)
                messageBox.setInformativeText("")
                messageBox.exec_()
                return True
        else:
            return False

    def connectedModelChangement(self):
        messageBox = ctk.ctkMessageBox()
        messageBox.setWindowTitle(" /!\ WARNING /!\ ")
        messageBox.setIcon(messageBox.Warning)
        messageBox.setText("The Markup Fiducial Node selected is curently projected on an"
                           "other model, if you chose to continue the fiducials will be  "
                           "reprojected, and this could impact the functioning of other modules")
        messageBox.setInformativeText("Do you want to continue?")
        messageBox.setStandardButtons(messageBox.No | messageBox.Yes)
        choice = messageBox.exec_()
        if choice == messageBox.Yes:
            return True
        else:
            messageBox.setText(" Node not modified")
            messageBox.setStandardButtons(messageBox.Ok)
            messageBox.setInformativeText("")
            messageBox.exec_()
            return False

    def createNewDataStructure(self,landmarks, model, onSurface):
        landmarks.SetAttribute("connectedModelID",model.GetID())
        landmarks.SetAttribute("hardenModelID",model.GetAttribute("hardenModelID"))
        landmarkDescription = dict()
        for n in range(landmarks.GetNumberOfMarkups()):
            markupID = landmarks.GetNthMarkupID(n)
            landmarkDescription[markupID] = dict()
            landmarkLabel = landmarks.GetNthMarkupLabel(n)
            landmarkDescription[markupID]["landmarkLabel"] = landmarkLabel
            landmarkDescription[markupID]["ROIradius"] = 0
            landmarkDescription[markupID]["projection"] = dict()
            if onSurface:
                landmarkDescription[markupID]["projection"]["isProjected"] = True
                hardenModel = slicer.app.mrmlScene().GetNodeByID(landmarks.GetAttribute("hardenModelID"))
                landmarkDescription[markupID]["projection"]["closestPointIndex"] = \
                    self.projectOnSurface(hardenModel, landmarks, markupID)
            else:
                landmarkDescription[markupID]["projection"]["isProjected"] = False
                landmarkDescription[markupID]["projection"]["closestPointIndex"] = None
            landmarkDescription[markupID]["midPoint"] = dict()
            landmarkDescription[markupID]["midPoint"]["definedByThisMarkup"] = list()
            landmarkDescription[markupID]["midPoint"]["isMidPoint"] = False
            landmarkDescription[markupID]["midPoint"]["Point1"] = None
            landmarkDescription[markupID]["midPoint"]["Point2"] = None
        landmarks.SetAttribute("landmarkDescription",self.encodeJSON(landmarkDescription))
        planeDescription = dict()
        landmarks.SetAttribute("planeDescription",self.encodeJSON(planeDescription))
        landmarks.SetAttribute("isClean",self.encodeJSON({"isClean":False}))
        landmarks.SetAttribute("lastTransformID",None)
        landmarks.SetAttribute("arrayName",model.GetName() + "_ROI")

    def changementOfConnectedModel(self,landmarks, model, onSurface):
        landmarks.SetAttribute("connectedModelID",model.GetID())
        landmarks.SetAttribute("hardenModelID",model.GetAttribute("hardenModelID"))
        landmarkDescription = self.decodeJSON(landmarks.GetAttribute("landmarkDescription"))
        for n in range(landmarks.GetNumberOfMarkups()):
            markupID = landmarks.GetNthMarkupID(n)
            if onSurface:
                if landmarkDescription[markupID]["projection"]["isProjected"] == True:
                    hardenModel = slicer.app.mrmlScene().GetNodeByID(landmarks.GetAttribute("hardenModelID"))
                    landmarkDescription[markupID]["projection"]["closestPointIndex"] = \
                        self.projectOnSurface(hardenModel, landmarks, markupID)
            else:
                landmarkDescription[markupID]["projection"]["isProjected"] = False
                landmarkDescription[markupID]["projection"]["closestPointIndex"] = None
            landmarks.SetAttribute("landmarkDescription",self.encodeJSON(landmarkDescription))
        landmarks.SetAttribute("isClean",self.encodeJSON({"isClean":False}))

    def connectLandmarks(self, modelSelector, landmarkSelector, onSurface):
        model = modelSelector.currentNode()
        landmarks = landmarkSelector.currentNode()
        self.selectedFidList = landmarks
        self.selectedModel = model
        if not (model and landmarks):
            return

        if self.isUnderTransform(landmarks):
            landmarkSelector.setCurrentNode(None)
            return
        connectedModelID = landmarks.GetAttribute("connectedModelID")
        try:
            tag = self.decodeJSON(landmarks.GetAttribute("MarkupAddedEventTag"))
            landmarks.RemoveObserver(tag["MarkupAddedEventTag"])
            print "Markups adding observer removed!"
        except:
            pass
        try:
            tag = self.decodeJSON(landmarks.GetAttribute("PointModifiedEventTag"))
            landmarks.RemoveObserver(tag["PointModifiedEventTag"])
            print "Markups moving observer removed!"
        except:
            pass
        try:
            tag = self.decodeJSON(landmarks.GetAttribute("MarkupRemovedEventTag"))
            landmarks.RemoveObserver(tag["MarkupRemovedEventTag"])
            print "Markups removing observers removed!"
        except:
            pass
        if self.interface.moduleName is 'AnglePlanes':
            try:
                tag = self.decodeJSON(landmarks.GetAttribute("UpdatesPlanesEventTag"))
                landmarks.RemoveObserver(tag["UpdatesPlanesEventTag"])
                print "Planes modification observers removed!"
            except:
                pass
        if self.interface.moduleName is 'Q3DC':
            try:
                tag = self.decodeJSON(landmarks.GetAttribute("UpdatesLinesEventTag"))
                landmarks.RemoveObserver(tag["UpdatesLinesEventTag"])
                print "Lines modification observers removed!"
            except:
                pass
        if connectedModelID:
            if connectedModelID != model.GetID():
                if self.connectedModelChangement():
                    self.changementOfConnectedModel(landmarks, model, onSurface)
                else:
                    landmarkSelector.setCurrentNode(None)
                    return
            else:
                landmarks.SetAttribute("hardenModelID",model.GetAttribute("hardenModelID"))
        # creation of the data structure
        else:
            self.createNewDataStructure(landmarks, model, onSurface)
        #update of the landmark Combo Box
        self.updateLandmarkComboBox(landmarks, self.interface.landmarkComboBox, False)
        #adding of listeners
        MarkupAddedEventTag = landmarks.AddObserver(landmarks.MarkupAddedEvent, self.onMarkupAddedEvent)
        landmarks.SetAttribute("MarkupAddedEventTag",self.encodeJSON({"MarkupAddedEventTag":MarkupAddedEventTag}))
        PointModifiedEventTag = landmarks.AddObserver(landmarks.PointModifiedEvent, self.onPointModifiedEvent)
        landmarks.SetAttribute("PointModifiedEventTag",self.encodeJSON({"PointModifiedEventTag":PointModifiedEventTag}))
        MarkupRemovedEventTag = landmarks.AddObserver(landmarks.MarkupRemovedEvent, self.onMarkupRemovedEvent)
        landmarks.SetAttribute("MarkupRemovedEventTag",self.encodeJSON({"MarkupRemovedEventTag":MarkupRemovedEventTag}))
        if self.interface.moduleName is 'AnglePlanes':
            UpdatesPlanesEventTag = landmarks.AddObserver(landmarks.PointModifiedEvent, self.updatePlanesEvent)
            landmarks.SetAttribute("UpdatesPlanesEventTag",self.encodeJSON({"UpdatesPlanesEventTag":UpdatesPlanesEventTag}))
        if self.interface.moduleName is 'Q3DC':
            UpdatesLinesEventTag = landmarks.AddObserver(landmarks.PointModifiedEvent, self.updateLinesEvent)
            landmarks.SetAttribute("UpdatesLinesEventTag",self.encodeJSON({"UpdatesLinesEventTag":UpdatesLinesEventTag}))

    # Called when a landmark is added on a model
    def onMarkupAddedEvent(self, obj, event):
        print "------markup adding-------"
        landmarkDescription = self.decodeJSON(obj.GetAttribute("landmarkDescription"))
        numOfMarkups = obj.GetNumberOfMarkups()
        markupID = obj.GetNthMarkupID(numOfMarkups - 1)
        landmarkDescription[markupID] = dict()
        landmarkLabel = obj.GetNthMarkupLabel(numOfMarkups - 1)
        landmarkDescription[markupID]["landmarkLabel"] = landmarkLabel
        landmarkDescription[markupID]["ROIradius"] = 0
        landmarkDescription[markupID]["projection"] = dict()
        landmarkDescription[markupID]["projection"]["isProjected"] = True
        # The landmark will be projected by onPointModifiedEvent
        landmarkDescription[markupID]["midPoint"] = dict()
        landmarkDescription[markupID]["midPoint"]["definedByThisMarkup"] = list()
        landmarkDescription[markupID]["midPoint"]["isMidPoint"] = False
        landmarkDescription[markupID]["midPoint"]["Point1"] = None
        landmarkDescription[markupID]["midPoint"]["Point2"] = None
        obj.SetAttribute("landmarkDescription",self.encodeJSON(landmarkDescription))
        self.updateAllLandmarkComboBox(obj, markupID)
        self.interface.UpdateInterface()
        self.onPointModifiedEvent(obj,None)

    def updateMidPoint(self, fidList, landmarkID):
        landmarkDescription = self.decodeJSON(fidList.GetAttribute("landmarkDescription"))
        for midPointID in landmarkDescription[landmarkID]["midPoint"]["definedByThisMarkup"]:
            if landmarkDescription[midPointID]["midPoint"]["isMidPoint"]:
                landmark1ID = landmarkDescription[midPointID]["midPoint"]["Point1"]
                landmark2ID = landmarkDescription[midPointID]["midPoint"]["Point2"]
                coord = self.calculateMidPointCoord(fidList, landmark1ID, landmark2ID)
                index = fidList.GetMarkupIndexByID(midPointID)
                fidList.SetNthFiducialPositionFromArray(index, coord)
                if landmarkDescription[midPointID]["projection"]["isProjected"]:
                    hardenModel = slicer.app.mrmlScene().GetNodeByID(fidList.GetAttribute("hardenModelID"))
                    landmarkDescription[midPointID]["projection"]["closestPointIndex"] = \
                        self.projectOnSurface(hardenModel, fidList, midPointID)
                    fidList.SetAttribute("landmarkDescription",self.encodeJSON(landmarkDescription))
                self.updateMidPoint(fidList, midPointID)

    # Called when a landmarks is moved
    def onPointModifiedEvent(self, obj, event):
        print "----onPointModifiedEvent Angle plane-----"
        landmarkDescription = self.decodeJSON(obj.GetAttribute("landmarkDescription"))
        if not landmarkDescription:
            return
        selectedLandmarkID = self.findIDFromLabel(obj, self.interface.landmarkComboBox.currentText)
        # remove observer to make sure, the callback function won't work..
        tag = self.decodeJSON(obj.GetAttribute("PointModifiedEventTag"))
        obj.RemoveObserver(tag["PointModifiedEventTag"])
        if selectedLandmarkID:
            activeLandmarkState = landmarkDescription[selectedLandmarkID]
            if activeLandmarkState["projection"]["isProjected"]:
                hardenModel = slicer.app.mrmlScene().GetNodeByID(obj.GetAttribute("hardenModelID"))
                activeLandmarkState["projection"]["closestPointIndex"] = \
                    self.projectOnSurface(hardenModel, obj, selectedLandmarkID)
                obj.SetAttribute("landmarkDescription",self.encodeJSON(landmarkDescription))
            self.updateMidPoint(obj,selectedLandmarkID)
            self.findROI(obj)
        time.sleep(0.08)
        # Add the observer again
        PointModifiedEventTag = obj.AddObserver(obj.PointModifiedEvent, self.onPointModifiedEvent)
        obj.SetAttribute("PointModifiedEventTag",self.encodeJSON({"PointModifiedEventTag":PointModifiedEventTag}))

    def onMarkupRemovedEvent(self, obj, event):
        print "------markup deleting-------"
        landmarkDescription = self.decodeJSON(obj.GetAttribute("landmarkDescription"))
        IDs = []
        for ID, value in landmarkDescription.iteritems():
            isFound = False
            for n in range(obj.GetNumberOfMarkups()):
                markupID = obj.GetNthMarkupID(n)
                if ID == markupID:
                    isFound = True
            if not isFound:
                IDs.append(ID)
        # for ID in IDs:
        #     self.deleteLandmark(obj, landmarkDescription[ID]["landmarkLabel"])
        #     landmarkDescription.pop(ID,None)
        # obj.SetAttribute("landmarkDescription",self.encodeJSON(landmarkDescription))

    def updatePlanesEvent(self, obj, event):
        for planeControls in self.interface.planeControlsDictionary.values():
            if planeControls.fidlist is obj:
                planeControls.update()

    def updateLinesEvent(self, obj, event):
        if self.interface.line1LAComboBox.currentText != '' and self.interface.line1LBComboBox.currentText != '' \
                and self.interface.line1LAComboBox.currentText != self.interface.line1LBComboBox.currentText :
            # Clear Lines, then define new ones
            if self.interface.renderer1 :
                self.interface.renderer1.RemoveActor(self.interface.actor1)
            self.interface.renderer1, self.interface.actor1 = \
                self.interface.logic.drawLineBetween2Landmark(self.interface.line1LAComboBox.currentText,
                                              self.interface.line1LBComboBox.currentText,
                                              self.interface.fidListComboBoxline1LA.currentNode(),
                                              self.interface.fidListComboBoxline1LB.currentNode())
        if self.interface.line2LAComboBox.currentText != '' and self.interface.line2LBComboBox.currentText != '' \
                and self.interface.line2LAComboBox.currentText != self.interface.line2LBComboBox.currentText :
            if self.interface.renderer2 :
                self.interface.renderer2.RemoveActor(self.interface.actor2)
            self.interface.renderer2, self.interface.actor2 = \
                self.interface.logic.drawLineBetween2Landmark(self.interface.line2LAComboBox.currentText,
                                              self.interface.line2LBComboBox.currentText,
                                              self.interface.fidListComboBoxline2LA.currentNode(),
                                              self.interface.fidListComboBoxline2LB.currentNode())
        if self.interface.lineLAComboBox.currentText != '' and self.interface.lineLBComboBox.currentText != '' \
                and self.interface.lineLAComboBox.currentText != self.interface.lineLBComboBox.currentText :
            if self.interface.renderer3 :
                self.interface.renderer3.RemoveActor(self.interface.actor3)
            self.interface.renderer3, self.interface.actor3 = \
                self.interface.logic.drawLineBetween2Landmark(self.interface.lineLAComboBox.currentText,
                                              self.interface.lineLBComboBox.currentText,
                                              self.interface.fidListComboBoxlineLA.currentNode(),
                                              self.interface.fidListComboBoxlineLB.currentNode())

    def findIDFromLabel(self, fidList, landmarkLabel):
        # find the ID of the markupsNode from the label of a landmark!
        landmarkDescription = self.decodeJSON(fidList.GetAttribute("landmarkDescription"))
        for ID, value in landmarkDescription.iteritems():
            if value["landmarkLabel"] == landmarkLabel:
                return ID
        return None

    def getClosestPointIndex(self, fidNode, inputPolyData, landmarkID):
        landmarkCoord = numpy.zeros(3)
        landmarkCoord[1] = 42
        fidNode.GetNthFiducialPosition(landmarkID, landmarkCoord)
        pointLocator = vtk.vtkPointLocator()
        pointLocator.SetDataSet(inputPolyData)
        pointLocator.AutomaticOn()
        pointLocator.BuildLocator()
        indexClosestPoint = pointLocator.FindClosestPoint(landmarkCoord)
        return indexClosestPoint

    def replaceLandmark(self, inputModelPolyData, fidNode, landmarkID, indexClosestPoint):
        landmarkCoord = [-1, -1, -1]
        inputModelPolyData.GetPoints().GetPoint(indexClosestPoint, landmarkCoord)
        fidNode.SetNthFiducialPositionFromArray(landmarkID,landmarkCoord)

    def projectOnSurface(self, modelOnProject, fidNode, selectedFidReflID):
        if selectedFidReflID:
            markupsIndex = fidNode.GetMarkupIndexByID(selectedFidReflID)
            indexClosestPoint = self.getClosestPointIndex(fidNode, modelOnProject.GetPolyData(), markupsIndex)
            self.replaceLandmark(modelOnProject.GetPolyData(), fidNode, markupsIndex, indexClosestPoint)
            return indexClosestPoint

    def calculateMidPointCoord(self, fidList, landmark1ID, landmark2ID):
        """Set the midpoint when you know the the mrml nodes"""
        landmark1Index = fidList.GetMarkupIndexByID(landmark1ID)
        landmark2Index = fidList.GetMarkupIndexByID(landmark2ID)
        coord1 = [-1, -1, -1]
        coord2 = [-1, -1, -1]
        fidList.GetNthFiducialPosition(landmark1Index, coord1)
        fidList.GetNthFiducialPosition(landmark2Index, coord2)
        midCoord = [-1, -1, -1]
        midCoord[0] = (coord1[0] + coord2[0])/2
        midCoord[1] = (coord1[1] + coord2[1])/2
        midCoord[2] = (coord1[2] + coord2[2])/2
        return midCoord

    def addLandmarkToCombox(self, fidList, combobox, markupID):
        if not fidList:
            return
        landmarkDescription = self.decodeJSON(fidList.GetAttribute("landmarkDescription"))
        combobox.addItem(landmarkDescription[markupID]["landmarkLabel"])

    def updateLandmarkComboBox(self, fidList, combobox, displayMidPoint = True):
        combobox.blockSignals(True)
        combobox.clear()
        if not fidList:
            return
        landmarkDescription = self.decodeJSON(fidList.GetAttribute("landmarkDescription"))
        numOfFid = fidList.GetNumberOfMarkups()
        if numOfFid > 0:
            for i in range(0, numOfFid):
                if displayMidPoint is False:
                    ID = fidList.GetNthMarkupID(i)
                    if not landmarkDescription[ID]["midPoint"]["isMidPoint"]:
                        landmarkLabel = fidList.GetNthMarkupLabel(i)
                        combobox.addItem(landmarkLabel)
                else:
                    landmarkLabel = fidList.GetNthMarkupLabel(i)
                    combobox.addItem(landmarkLabel)
        combobox.setCurrentIndex(combobox.count - 1)
        combobox.blockSignals(False)

    def updateAllLandmarkComboBox(self, fidList, markupID):
        # update of the Combobox that are always updated
        self.updateLandmarkComboBox(fidList, self.interface.landmarkComboBox, False)
        if hasattr(self.interface.logic, 'getComboboxesToUpdate'):
            comboboxesToUpdate = self.interface.logic.getComboboxesToUpdate(fidList, markupID)
            for combobox in comboboxesToUpdate:
                self.addLandmarkToCombox(fidList, combobox, markupID)

    def deleteLandmark(self, fidList, label):
        # update of the Combobox that are always updated
        self.interface.landmarkComboBox.removeItem(self.interface.landmarkComboBox.findText(label))
        if hasattr(self.interface.logic, 'getComboboxesToUpdate'):
            comboboxesToUpdate = self.interface.logic.getComboboxesToUpdate(fidList, markupID)
            for combobox in comboboxesToUpdate:
                combobox.removeItem(combobox.findText(label))

    def GetConnectedVertices(self, connectedVerticesIDList, polyData, pointID):
        # Return IDs of all the vertices that compose the first neighbor.
        cellList = vtk.vtkIdList()
        connectedVerticesIDList.InsertUniqueId(pointID)
        # Get cells that vertex 'pointID' belongs to
        polyData.GetPointCells(pointID, cellList)
        numberOfIds = cellList.GetNumberOfIds()
        for i in range(0, numberOfIds):
            # Get points which compose all cells
            pointIdList = vtk.vtkIdList()
            polyData.GetCellPoints(cellList.GetId(i), pointIdList)
            for j in range(0, pointIdList.GetNumberOfIds()):
                connectedVerticesIDList.InsertUniqueId(pointIdList.GetId(j))
        return connectedVerticesIDList

    def addArrayFromIdList(self, connectedIdList, inputModelNode, arrayName):
        if not inputModelNode:
            return
        inputModelNodePolydata = inputModelNode.GetPolyData()
        pointData = inputModelNodePolydata.GetPointData()
        numberofIds = connectedIdList.GetNumberOfIds()
        hasArrayInt = pointData.HasArray(arrayName)
        if hasArrayInt == 1:  # ROI Array found
            pointData.RemoveArray(arrayName)
        arrayToAdd = vtk.vtkDoubleArray()
        arrayToAdd.SetName(arrayName)
        for i in range(0, inputModelNodePolydata.GetNumberOfPoints()):
            arrayToAdd.InsertNextValue(0.0)
        for i in range(0, numberofIds):
            arrayToAdd.SetValue(connectedIdList.GetId(i), 1.0)
        lut = vtk.vtkLookupTable()
        tableSize = 2
        lut.SetNumberOfTableValues(tableSize)
        lut.Build()
        ID = inputModelNode.GetDisplayNodeID()
        slicer.app.mrmlScene().GetNodeByID(ID)
        displayNode = slicer.app.mrmlScene().GetNodeByID(ID)
        rgb = displayNode.GetColor()
        lut.SetTableValue(0, rgb[0], rgb[1], rgb[2], 1)
        lut.SetTableValue(1, 1.0, 0.0, 0.0, 1)
        arrayToAdd.SetLookupTable(lut)
        pointData.AddArray(arrayToAdd)
        inputModelNodePolydata.Modified()
        return True

    def displayROI(self, inputModelNode, scalarName):
        PolyData = inputModelNode.GetPolyData()
        PolyData.Modified()
        displayNode = inputModelNode.GetModelDisplayNode()
        displayNode.SetScalarVisibility(False)
        disabledModify = displayNode.StartModify()
        displayNode.SetActiveScalarName(scalarName)
        displayNode.SetScalarVisibility(True)
        displayNode.EndModify(disabledModify)

    def defineNeighbor(self, connectedVerticesList, inputModelNodePolyData, indexClosestPoint, distance):
        self.GetConnectedVertices(connectedVerticesList, inputModelNodePolyData, indexClosestPoint)
        if distance > 1:
            for dist in range(1, int(distance)):
                for i in range(0, connectedVerticesList.GetNumberOfIds()):
                    self.GetConnectedVertices(connectedVerticesList, inputModelNodePolyData,
                                              connectedVerticesList.GetId(i))
        return connectedVerticesList

    def findROI(self, fidList):
        hardenModel = slicer.app.mrmlScene().GetNodeByID(fidList.GetAttribute("hardenModelID"))
        connectedModel = slicer.app.mrmlScene().GetNodeByID(fidList.GetAttribute("connectedModelID"))
        landmarkDescription = self.decodeJSON(fidList.GetAttribute("landmarkDescription"))
        arrayName = fidList.GetAttribute("arrayName")
        ROIPointListID = vtk.vtkIdList()
        for key,activeLandmarkState in landmarkDescription.iteritems():
            tempROIPointListID = vtk.vtkIdList()
            if activeLandmarkState["ROIradius"] != 0:
                self.defineNeighbor(tempROIPointListID,
                                    hardenModel.GetPolyData(),
                                    activeLandmarkState["projection"]["closestPointIndex"],
                                    activeLandmarkState["ROIradius"])
            for j in range(0, tempROIPointListID.GetNumberOfIds()):
                ROIPointListID.InsertUniqueId(tempROIPointListID.GetId(j))
        listID = ROIPointListID
        self.addArrayFromIdList(listID, connectedModel, arrayName)
        self.displayROI(connectedModel, arrayName)
        return ROIPointListID

    def warningMessage(self, message):
        messageBox = ctk.ctkMessageBox()
        messageBox.setWindowTitle(" /!\ WARNING /!\ ")
        messageBox.setIcon(messageBox.Warning)
        messageBox.setText(message)
        messageBox.setStandardButtons(messageBox.Ok)
        messageBox.exec_()

    def encodeJSON(self, input):
        encodedString = json.dumps(input)
        encodedString = encodedString.replace('\"', '\'')
        return encodedString

    def decodeJSON(self, input):
        if input:
            input = input.replace('\'','\"')
            return self.byteify(json.loads(input))
        return None

    def byteify(self, input):
        if isinstance(input, dict):
            return {self.byteify(key):self.byteify(value) for key,value in input.iteritems()}
        elif isinstance(input, list):
            return [self.byteify(element) for element in input]
        elif isinstance(input, unicode):
            return input.encode('utf-8')
        else:
            return input