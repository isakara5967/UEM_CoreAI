# core/planning/planning_core.py

from .goal_management import GoalManager
from .task_decomposition import TaskDecomposer
from .action_selection import ActionSelector
from .strategy import StrategyEngine
from .rl_interface import RLPolicyInterface


class PlanningCore:
    """
    UEM planlama çekirdeği.
    Hedef yönetimi, görev parçalama, eylem seçimi, strateji ve RL arayüzünü yönetir.
    Şimdilik tüm alt birimler iskelet formunda yükleniyor.
    """

    def __init__(self):
        self.goal_manager = GoalManager()
        self.task_decomposer = TaskDecomposer()
        self.action_selector = ActionSelector()
        self.strategy_engine = StrategyEngine()
        self.rl_interface = RLPolicyInterface()

        self.initialized = True

    def start(self):
        self.goal_manager.start()
        self.task_decomposer.start()
        self.action_selector.start()
        self.strategy_engine.start()
        self.rl_interface.start()
