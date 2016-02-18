from __main__ import vtk, qt, ctk, slicer
import os
import logging


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


class LongitudinalQuantificationWidget(slicer.ScriptedLoadableModule.ScriptedLoadableModuleWidget):

    def setup(self):
        print "----- Longitudinal Quantification widget setup -----"

        # ------------------------------------------------------------------------------ #
        # ---------------- Setup and initialisation of global variables ---------------- #
        # ------------------------------------------------------------------------------ #

        # ------ Initialisation of Longitudinal quantification and its logic ----- #
        slicer.ScriptedLoadableModule.ScriptedLoadableModuleWidget.setup(self)
        self.logic = LongitudinalQuantificationLogic(self)

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

        # ------ Creation of a dictionary that will contain the widgets of all the modules ----- #
        self.ExternalModulesWidgets = dict()
        self.ExternalModulesWidgets["Angle Planes"] = slicer.modules.AnglePlanesWidget.widget
        self.ExternalModulesWidgets["Easy Clip"] = slicer.modules.EasyClipWidget.widget
        #self.ExternalModulesWidgets["Mesh Statistics"] = slicer.modules.MeshStatisticsWidget.widget
        self.ExternalModulesWidgets["Model to Model Distance"] = slicer.modules.modeltomodeldistance.widgetRepresentation()
        self.ExternalModulesWidgets["Pick and Paint"] = slicer.modules.PickAndPaintWidget.widget
        self.ExternalModulesWidgets["Q3DC"] = slicer.modules.Q3DCWidget.widget
        self.ExternalModulesWidgets["Surface Registration"] = slicer.modules.SurfaceRegistrationWidget.widget

        # ------ Initialisation of variables to know wich module is currently used ----- #
        self.curentQuantificationWidget = None

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

        # ------ Quantification Collapsible Button ----- #
        self.QuantificationCollapsibleButton = self.logic.get("QuantificationCollapsibleButton")
        self.QuantificationLayout = self.logic.get("QuantificationLayout")
        self.QuantificationCoiceComboBox = self.logic.get("QuantificationCoiceComboBox")

        # ------ Analisis Collapsible Button ----- #
        self.AnalysisCollapsibleButton = self.logic.get("AnalysisCollapsibleButton")

        # --------------------------------------------- #
        # ---------------- Connections ---------------- #
        # --------------------------------------------- #

        # ------ Scene Collapsible Button ----- #

        # ------ Quantification Collapsible Button ----- #
        self.QuantificationCoiceComboBox.connect('currentIndexChanged(QString)', self.onQuantificationSelectionChanged)

        # ------ Analisis Collapsible Button ----- #
        slicer.mrmlScene.AddObserver(slicer.mrmlScene.EndCloseEvent, self.onCloseScene)

    # function called each time that the user "enter" in Longitudinal Quantification interface
    def enter(self):
        print "---- Enter Longitudinal Quantification ---- "
        pass

    # function called each time that the user "exit" in Longitudinal Quantification interface
    def exit(self):
        print "---- Exit Longitudinal Quantification ---- "
        pass

    # function called each time that the scene is closed (if Longitudinal Quantification has been initialized)
    def onCloseScene(self, obj, event):
        print "---- Close Longitudinal Quantification ---- "
        pass

    def onQuantificationSelectionChanged(self, module):
        print "--- onQuantificationSelectionChanged --- "
        if self.curentQuantificationWidget:
            self.QuantificationLayout.removeWidget(self.curentQuantificationWidget)
        if module == "None":
            self.curentQuantificationWidget = None
            return
        self.curentQuantificationWidget = self.ExternalModulesWidgets[module]
        self.QuantificationLayout.addWidget(self.ExternalModulesWidgets[module])

class LongitudinalQuantificationLogic(slicer.ScriptedLoadableModule.ScriptedLoadableModuleLogic):

    # --------------------------------------------------- #
    # ----------- Initialisation of the logic ----------- #
    # --------------------------------------------------- #
    def __init__(self, interface):
        print "----- Longitudinal Quantification logic init -----"
        self.interface = interface

    # -------------------------------------------------------- #
    # ----------- Connection of the User Interface ----------- #
    # -------------------------------------------------------- #

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