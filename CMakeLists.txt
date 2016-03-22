cmake_minimum_required(VERSION 2.8.9)

project(LongitudinalQuantificationExtension)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_NAME "LongitudinalQuantification")
set(EXTENSION_HOMEPAGE "http://www.slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/LongitudinalQuantification")
set(EXTENSION_CATEGORY "Quantification")
set(EXTENSION_CONTRIBUTORS "Jean-Baptiste Vimort (University of Michigan)")
set(EXTENSION_DESCRIPTION "TODO")
set(EXTENSION_ICONURL "TODO")
set(EXTENSION_SCREENSHOTURLS "TODO")
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
add_subdirectory(MeshStatistics)
add_subdirectory(PickAndPaint)
add_subdirectory(Q3DC)

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_CPACK})
