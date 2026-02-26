"""Base tool interface. All mock tools must inherit from BaseTool."""

from abc import ABC, abstractmethod

from app.schemas.models import ToolDefinition


class BaseTool(ABC):
    """工具基类接口。所有模拟工具必须继承此类。"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称标识符（snake_case）。"""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """工具功能说明。"""
        ...

    @abstractmethod
    def execute(self, **kwargs) -> dict:
        """执行工具操作。返回结果字典。"""
        ...

    @abstractmethod
    def _get_parameters(self) -> dict:
        """返回参数描述字典。"""
        ...

    def get_definition(self) -> ToolDefinition:
        """返回工具元信息，供管理 API 使用。"""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self._get_parameters(),
        )
