"""工具注册表 — 自动发现并注册所有 BaseTool 子类。"""

import importlib
import pkgutil
from pathlib import Path

from app.agent.tools.base import BaseTool
from app.schemas.models import ToolDefinition

# 工具实例注册表
_tool_registry: dict[str, BaseTool] = {}


def get_tool(name: str) -> BaseTool | None:
    """按名称查找工具。"""
    return _tool_registry.get(name)


def get_all_tools() -> list[BaseTool]:
    """获取全部已注册工具实例。"""
    return list(_tool_registry.values())


def get_tool_definitions() -> list[ToolDefinition]:
    """获取全部工具元信息。"""
    return [tool.get_definition() for tool in _tool_registry.values()]


# 自动导入当前目录下所有模块（排除 base），触发工具类定义
_package_dir = Path(__file__).parent
for _, _module_name, _ in pkgutil.iter_modules([str(_package_dir)]):
    if _module_name != "base":
        importlib.import_module(f".{_module_name}", __package__)

# 导入完成后，扫描 BaseTool 子类并注册具体实现（此时 __abstractmethods__ 已正确设置）
for _cls in BaseTool.__subclasses__():
    if not getattr(_cls, "__abstractmethods__", None):
        _instance = _cls()
        _tool_registry[_instance.name] = _instance
