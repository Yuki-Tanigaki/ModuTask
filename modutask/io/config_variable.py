class PropertyVariable:
    TASK: str = 'task'
    TASK_DEPENDENCY: str = 'task_dependency'
    MODULE_TYPE: str = 'module_type'
    MODULE: str = 'module'
    ROBOT_TYPE: str = 'robot_type'
    ROBOT: str = 'robot'
    SCENARIO: str = 'risk_scenario'
    TASK_PRIORITY: str = 'task_priority'

class TaskVariable:
    CLASS: str = 'class'
    REQUIRED_PERFORMANCE: str = 'required_performance'

class ModuleVariable:
    TYPE: str = 'module_type'
    STATE: str = 'state'

class RobotTypeVariable:
    REQUIRED_MODULES: str = 'required_modules'
    PERFORMANCE: str = 'performance'

class RobotVariable:
    TYPE: str = 'robot_type'
    COMPONENT: str = 'component'

class Variable:
    PROPERTY = PropertyVariable
    TASK = TaskVariable
    MODULE = ModuleVariable
    ROBOT_TYPE = RobotTypeVariable
    ROBOT = RobotVariable