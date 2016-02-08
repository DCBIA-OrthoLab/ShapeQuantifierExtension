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
        print "Longitudinal Quantification widget setup"
        slicer.ScriptedLoadableModule.ScriptedLoadableModuleWidget.setup(self)
        self.logic = LongitudinalQuantificationLogic()

        slicer.mrmlScene.AddObserver(slicer.mrmlScene.EndCloseEvent, self.onCloseScene)

    # function called each time that the user "enter" in Longitudinal Quantification interface
    def enter(self):
        pass

    # function called each time that the user "exit" in Longitudinal Quantification interface
    def exit(self):
        pass

    # function called each time that the scene is closed (if Longitudinal Quantification has been initialized)
    def onCloseScene(self, obj, event):
        pass


class LongitudinalQuantificationLogic(slicer.ScriptedLoadableModule.ScriptedLoadableModuleLogic):
    def __init__(self):
        print "Longitudinal Quantification logic init"


class LongitudinalQuantificationTest(slicer.ScriptedLoadableModule.ScriptedLoadableModuleTest):
    def __init__(self):
        print "Longitudinal Quantification test init"

    def setUp(self):
        print "Longitudinal Quantification test setup"
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