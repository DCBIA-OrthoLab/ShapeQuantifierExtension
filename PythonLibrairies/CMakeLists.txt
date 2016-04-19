set(
  MODULE_NAME LongitudinalQuantificationCore)

set(
  MODULE_PYTHON_SCRIPTS
  LongitudinalQuantificationCore.py)

slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS})