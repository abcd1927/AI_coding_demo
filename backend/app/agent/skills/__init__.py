"""Skill 注册表 — 自动扫描 skills/ 目录的 .md 文件并注册为 SkillDefinition。"""

from pathlib import Path

from app.schemas.models import SkillDefinition

# Skill 实例注册表
_skill_registry: dict[str, SkillDefinition] = {}


def _load_skills() -> None:
    """扫描当前目录下所有 .md 文件，解析并注册为 SkillDefinition。"""
    skills_dir = Path(__file__).parent
    for md_file in sorted(skills_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        skill_id = md_file.stem  # 文件名去掉 .md 后缀
        lines = content.strip().splitlines()
        # 第一行（去掉 # 前缀）作为名称
        name = lines[0].lstrip("#").strip() if lines else skill_id
        # 第一个非空非标题行作为描述
        description = ""
        for line in lines[1:]:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                description = stripped
                break
        _skill_registry[skill_id] = SkillDefinition(
            skill_id=skill_id,
            name=name,
            description=description,
            content=content,
        )


def get_skill(skill_id: str) -> SkillDefinition | None:
    """按 skill_id 查找 Skill。"""
    return _skill_registry.get(skill_id)


def get_all_skills() -> list[SkillDefinition]:
    """获取全部已注册 Skill。"""
    return list(_skill_registry.values())


# 模块加载时自动扫描并注册
_load_skills()
