from enum import Enum
import logging

logger = logging.getLogger(__name__)

class PerformanceAttributes(Enum):
    """ ロボットの能力カテゴリを表す列挙型 """
    TRANSPORT = 0  # 運搬能力
    MANUFACTURE = 1  # 加工能力
    MOBILITY = 2  # 移動能力