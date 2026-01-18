"""
配置文件 Schema 定义

使用 Pydantic 进行配置验证和类型安全。
支持 YAML 配置文件定义子代理、工具、LLM 等。
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class LLMProfile(BaseModel):
    """LLM 配置 Profile"""

    model: str = Field(default="deepseek-chat", description="模型名称")
    base_url: Optional[str] = Field(default=None, description="API 基础 URL，为空则使用全局配置")
    api_key: Optional[str] = Field(default=None, description="API 密钥，为空则使用全局配置")
    temperature: float = Field(default=0.7, ge=0, le=2, description="生成温度")
    max_tokens: Optional[int] = Field(default=None, description="最大 token 数")


class LLMConfig(BaseModel):
    """LLM 总配置"""

    default: LLMProfile = Field(default_factory=LLMProfile, description="默认 LLM 配置")
    profiles: Dict[str, LLMProfile] = Field(
        default_factory=dict, description="命名的 LLM 配置，供子代理引用"
    )


class BuiltinToolsConfig(BaseModel):
    """内置工具开关配置"""

    sql_tools: bool = Field(default=True, description="启用 SQL 工具组")
    python_tools: bool = Field(default=True, description="启用 Python 工具组")
    ml_tools: bool = Field(default=True, description="启用机器学习工具组")
    graph_tools: bool = Field(default=True, description="启用图分析工具组")


class ExternalToolConfig(BaseModel):
    """外部工具配置"""

    module: str = Field(..., description="Python 模块路径")
    tools: List[str] = Field(default_factory=list, description="要导入的工具名称列表")


class ToolsConfig(BaseModel):
    """工具配置"""

    builtin: BuiltinToolsConfig = Field(
        default_factory=BuiltinToolsConfig, description="内置工具开关"
    )
    aliases: Dict[str, str] = Field(default_factory=dict, description="工具别名映射")
    external: List[ExternalToolConfig] = Field(
        default_factory=list, description="外部工具注册列表"
    )


class SubAgentConfig(BaseModel):
    """子代理配置"""

    description: str = Field(..., description="子代理功能描述，用于协调者分配任务")
    llm: str = Field(default="default", description="使用的 LLM profile 名称")
    tools: List[str] = Field(default_factory=list, description="可用工具名称列表")
    prompt_file: Optional[str] = Field(default=None, description="外部提示词文件路径")
    system_prompt: Optional[str] = Field(default=None, description="内联系统提示词")
    middleware: List[str] = Field(default_factory=list, description="中间件列表")

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("description 不能为空")
        return v


class CoordinatorConfig(BaseModel):
    """协调者配置"""

    llm: str = Field(default="default", description="使用的 LLM profile 名称")
    prompt_file: Optional[str] = Field(default=None, description="外部提示词文件路径")
    system_prompt: Optional[str] = Field(default=None, description="内联系统提示词")
    use_default_prompt: bool = Field(default=True, description="是否使用默认提示词")


class HotReloadConfig(BaseModel):
    """热重载配置"""

    enabled: bool = Field(default=False, description="是否启用热重载")
    watch_paths: List[str] = Field(default_factory=list, description="要监听的路径列表")
    debounce_ms: int = Field(default=1000, ge=100, description="防抖延迟（毫秒）")


class AgentSystemConfig(BaseModel):
    """Agent 系统总配置"""

    version: str = Field(default="1.0", description="配置版本")
    llm: LLMConfig = Field(default_factory=LLMConfig, description="LLM 配置")
    tools: ToolsConfig = Field(default_factory=ToolsConfig, description="工具配置")
    subagents: Dict[str, SubAgentConfig] = Field(
        default_factory=dict, description="子代理配置字典"
    )
    coordinator: CoordinatorConfig = Field(
        default_factory=CoordinatorConfig, description="协调者配置"
    )
    hot_reload: HotReloadConfig = Field(
        default_factory=HotReloadConfig, description="热重载配置"
    )

    def get_llm_profile(self, name: str) -> LLMProfile:
        """
        获取 LLM Profile

        Args:
            name: profile 名称，"default" 返回默认配置

        Returns:
            LLMProfile 配置对象
        """
        if name == "default":
            return self.llm.default
        return self.llm.profiles.get(name, self.llm.default)

    def get_all_tool_names(self) -> List[str]:
        """获取所有配置中引用的工具名称"""
        tools = set()
        for subagent in self.subagents.values():
            tools.update(subagent.tools)
        return list(tools)
