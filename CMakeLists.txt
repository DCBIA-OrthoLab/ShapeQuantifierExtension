cmake_minimum_required(VERSION 2.8.9)

project(LongitudinalQuantificationExtension)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_NAME "LongitudinalQuantification")
set(EXTENSION_HOMEPAGE "http://www.slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/LongitudinalQuantification")
set(EXTENSION_CATEGORY "Quantification")
set(EXTENSION_CONTRIBUTORS "Jean-Baptiste Vimort (University of Michigan), Julia Lopinto (University of Michigan), Lucie Macron (University of Michigan),Francois Budin (University of North Carolina), Beatriz Paniagua (University of North Carolina), Juan-Carlos Prieto (University of North Carolina), Lucia Cevidanes (University of Michigan)")
set(EXTENSION_DESCRIPTION "This extension contains different modules that allow the user to either quantify differences between two models or make measurements on the shape of a model.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/jbvimort/LongitudinalQuantificationExtension/master/LongitudinalQuantification/Resources/Icons/LongitudinalQuantification.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/DCBIA-OrthoLab/AnglePlanes-Extension/master/AnglePlanes.png, https://raw.githubusercontent.com/DCBIA-OrthoLab/EasyClip-Extension/master/EasyClip.png, http://https://raw.githubusercontent.com/DCBIA-OrthoLab/MeshStatisticsExtension/master/MeshStatistics/Resources/Icons/MeshStatistics.png, https://raw.githubusercontent.com/DCBIA-OrthoLab/PickAndPaintExtension/master/PickAndPaint/Resources/Icons/PickAndPaint.png, https://raw.githubusercontent.com/DCBIA-OrthoLab/Q3DCExtension/master/Q3DC.png")
set(EXTENSION_DEPENDS "CMFreg, ModelToModelDistance, ShapePopulationViewer")

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(AnglePlanes)
add_subdirectory(EasyClip)
add_subdirectory(LongitudinalQuantification)
add_subdirectory(PythonLibrairies)
add_subdirectory(MeshStatistics)
add_subdirectory(PickAndPaint)
add_subdirectory(Q3DC)

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_CPACK})
