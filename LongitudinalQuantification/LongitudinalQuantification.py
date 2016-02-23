from __main__ import vtk, qt, ctk, slicer
import os
import logging

# *************************************************  ********** #
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

        # ------ Preprocessing Collapsible Button ----- #
        self.PreprocessingCollapsibleButton = self.logic.get("PreprocessingCollapsibleButton")
        self.PreprocessingLayout = self.logic.get("PreprocessingLayout")
        self.PreprocessingChoiceComboBox = self.logic.get("PreprocessingChoiceComboBox")

        # ------ Quantification Collapsible Button ----- #
        self.QuantificationCollapsibleButton = self.logic.get("QuantificationCollapsibleButton")
        self.QuantificationLayout = self.logic.get("QuantificationLayout")
        self.QuantificationChoiceComboBox = self.logic.get("QuantificationChoiceComboBox")

        # ------ Analysis Collapsible Button ----- #
        self.AnalysisCollapsibleButton = self.logic.get("AnalysisCollapsibleButton")
        self.AnalysisLayout = self.logic.get("AnalysisLayout")
        self.AnalysisChoiceComboBox = self.logic.get("AnalysisChoiceComboBox")

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

        # ------ Initialisation of variables to know which module is currently used ----- #
        self.curentQuantificationWidget = dict()
        self.curentQuantificationWidget[self.PreprocessingLayout] = None
        self.curentQuantificationWidget[self.QuantificationLayout] = None
        self.curentQuantificationWidget[self.AnalysisLayout] = None

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

        # ------ Preprocessing Collapsible Button ----- #
        self.PreprocessingChoiceComboBox.connect('currentIndexChanged(QString)', self.onPreprocessingSelectionChanged)

        # ------ Quantification Collapsible Button ----- #
        self.QuantificationChoiceComboBox.connect('currentIndexChanged(QString)', self.onQuantificationSelectionChanged)

        # ------ Analysis Collapsible Button ----- #
        self.AnalysisChoiceComboBox.connect('currentIndexChanged(QString)', self.onAnalysisSelectionChanged)

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
        self.PreprocessingChoiceComboBox.setCurrentIndex(0)
        self.QuantificationChoiceComboBox.setCurrentIndex(0)
        self.AnalysisChoiceComboBox.setCurrentIndex(0)

    def onPreprocessingSelectionChanged(self, newModule):
        print "--- onPreprocessingSelectionChanged --- "
        self.moduleChangement(self.PreprocessingLayout, newModule)

    def onQuantificationSelectionChanged(self, newModule):
        print "--- onQuantificationSelectionChanged --- "
        self.moduleChangement(self.QuantificationLayout, newModule)

    def onAnalysisSelectionChanged(self, newModule):
        print "--- onAnalysisSelectionChanged --- "
        self.moduleChangement(self.AnalysisLayout, newModule)

    def moduleChangement(self, layout, newModule):
        if self.curentQuantificationWidget[layout]:
            layout.removeWidget(self.curentQuantificationWidget[layout])
            self.curentQuantificationWidget[layout].hide()
        if newModule == "None":
            self.curentQuantificationWidget[layout] = None
            return
        self.curentQuantificationWidget[layout] = self.ExternalModulesWidgets[newModule]
        layout.addWidget(self.curentQuantificationWidget[layout])
        self.curentQuantificationWidget[layout].show()


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