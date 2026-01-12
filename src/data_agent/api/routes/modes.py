"""
模式管理 API

复用现有的 ModeManager，提供 Web 接口。
"""

from typing import Any, Dict
from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...config.modes import get_mode_manager, MODE_DEFINITIONS

router = APIRouter()


class ModeValue(BaseModel):
    """模式值请求体"""
    value: str


class ModeResponse(BaseModel):
    """模式响应"""
    success: bool
    mode: str
    value: Any
    message: str = ""


@router.get("")
@router.get("/")
async def get_all_modes() -> Dict[str, Any]:
    """
    获取所有模式的当前状态

    返回与 CLI `/modes` 命令相同的信息。
    """
    manager = get_mode_manager()
    modes = manager.get_all()

    # 转换枚举值为字符串
    result = {}
    for key, value in modes.items():
        if isinstance(value, Enum):
            result[key] = value.value
        else:
            result[key] = value

    return {
        "modes": result,
        "definitions": {
            key: {
                "display_name": defn["display_name"],
                "description": defn["description"],
                "allowed_values": defn["allowed_values"],
            }
            for key, defn in MODE_DEFINITIONS.items()
        },
    }


@router.get("/{mode_key}")
async def get_mode(mode_key: str) -> Dict[str, Any]:
    """
    获取指定模式的当前值

    Args:
        mode_key: 模式键名（如 plan, auto, safe, verbose 等）
    """
    if mode_key not in MODE_DEFINITIONS:
        raise HTTPException(status_code=404, detail=f"未知的模式: {mode_key}")

    manager = get_mode_manager()
    value = manager.get(mode_key)

    if isinstance(value, Enum):
        value = value.value

    return {
        "mode": mode_key,
        "value": value,
        "definition": {
            "display_name": MODE_DEFINITIONS[mode_key]["display_name"],
            "description": MODE_DEFINITIONS[mode_key]["description"],
            "allowed_values": MODE_DEFINITIONS[mode_key]["allowed_values"],
        },
    }


@router.post("/{mode_key}")
async def set_mode(mode_key: str, body: ModeValue) -> ModeResponse:
    """
    设置指定模式的值

    Args:
        mode_key: 模式键名（如 plan, auto, safe, verbose 等）
        body: 包含新值的请求体
    """
    if mode_key not in MODE_DEFINITIONS:
        raise HTTPException(status_code=404, detail=f"未知的模式: {mode_key}")

    allowed = MODE_DEFINITIONS[mode_key]["allowed_values"]
    if body.value.lower() not in [v.lower() for v in allowed]:
        raise HTTPException(
            status_code=400,
            detail=f"无效的值: {body.value}，允许的值: {allowed}",
        )

    manager = get_mode_manager()
    success = manager.set(mode_key, body.value)

    if not success:
        raise HTTPException(status_code=500, detail="设置模式失败")

    new_value = manager.get(mode_key)
    if isinstance(new_value, Enum):
        new_value = new_value.value

    return ModeResponse(
        success=True,
        mode=mode_key,
        value=new_value,
        message=f"{MODE_DEFINITIONS[mode_key]['display_name']}已设置为: {new_value}",
    )


@router.post("/{mode_key}/toggle")
async def toggle_mode(mode_key: str) -> ModeResponse:
    """
    切换布尔类型模式

    仅适用于布尔类型的模式（auto, safe, verbose, export）。
    """
    if mode_key not in MODE_DEFINITIONS:
        raise HTTPException(status_code=404, detail=f"未知的模式: {mode_key}")

    # 检查是否为布尔类型模式
    allowed = MODE_DEFINITIONS[mode_key]["allowed_values"]
    if set(allowed) != {"on", "off"}:
        raise HTTPException(
            status_code=400,
            detail=f"模式 {mode_key} 不是布尔类型，无法切换",
        )

    manager = get_mode_manager()
    new_value = manager.toggle(mode_key)

    if new_value is None:
        raise HTTPException(status_code=500, detail="切换模式失败")

    return ModeResponse(
        success=True,
        mode=mode_key,
        value=new_value,
        message=f"{MODE_DEFINITIONS[mode_key]['display_name']}已切换为: {'ON' if new_value else 'OFF'}",
    )


@router.post("/reset")
async def reset_modes() -> Dict[str, Any]:
    """
    重置所有模式为默认值
    """
    manager = get_mode_manager()
    manager.reset_to_defaults()

    return {
        "success": True,
        "message": "所有模式已重置为默认值",
        "modes": manager.get_all(),
    }
