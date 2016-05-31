set(
  MODULE_NAME ShapeQuantifierCore)

set(
  MODULE_PYTHON_SCRIPTS
  ShapeQuantifierCore.py)

slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS})