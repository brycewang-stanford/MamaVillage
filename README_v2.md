# MamaVillage v2.0 - 现代化农村育儿社群模拟系统

基于 **LangGraph + LangChain** 的现代化多智能体社交模拟系统，用于研究中国农村地区妈妈群体的知识分享和互助行为。

## 🎯 项目概述

MamaVillage v2.0 模拟了一个由农村妈妈和奶奶组成的社群，她们通过智能手机、微信群和抖音等数字平台分享育儿知识、寻求帮助和提供支持。

### 核心特性

- 🏗️ **现代化架构**: 基于 LangGraph StateGraph 的工作流引擎
- 🤖 **智能Agent系统**: 使用 LangChain Agent 框架的类型安全Agent
- 🧠 **先进记忆系统**: LangChain Memory + SQLite 的混合记忆架构
- 🔄 **状态驱动工作流**: observe → plan → act → reflect 循环
- 📊 **类型安全**: 基于 Pydantic 的完整类型系统
- 🎭 **真实角色模拟**: 基于实地调研的农村妈妈角色设计

## 🚀 快速开始

### 1. 环境配置

```bash
# 创建虚拟环境
python -m venv mama_village_env
source mama_village_env/bin/activate  # Linux/Mac
# 或 mama_village_env\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置API密钥

创建 `.env` 文件：

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
DATABASE_PATH=memory/memory.sqlite
```

### 3. 运行系统

```bash
# 使用新的v2.0系统
python run_new.py

# 或运行系统测试
python test_new_system.py
```

## 🏗️ 系统架构

### 核心模块结构

```
core/
├── state.py              # 状态管理和数据模型
├── agent_profile.py      # Agent配置文件系统
├── agent.py              # Agent核心类和LangChain集成
├── workflow.py           # LangGraph工作流引擎
├── memory_system.py      # 记忆系统和持久化
└── __init__.py           # 模块导出
```

### Agent配置文件

```
agents/
├── mama_xiaoli.json      # 年轻妈妈：小李
├── mama_li.json          # 年轻妈妈：李丽
├── grandma_zhang.json    # 资深奶奶：张奶奶
└── ...                   # 更多Agent配置
```

## 🤖 Agent系统设计

### Agent角色类型

- **年轻妈妈** (`年轻妈妈`): 90后新手妈妈，善用数字工具
- **有经验妈妈** (`有经验的妈妈`): 有多个孩子的妈妈
- **奶奶** (`奶奶`): 60后传统智慧持有者
- **社工** (`社工`): 专业支持人员

### Agent配置示例

```json
{
  "id": "mama_xiaoli",
  "name": "小李",
  "age": 28,
  "education": "高中",
  "role": "年轻妈妈",
  "personality": {
    "traits": ["细心", "好学", "容易焦虑"],
    "digital_habits": {
      "video_preferences": ["育儿知识", "辅食制作"],
      "preferred_platforms": ["抖音", "快手"]
    }
  },
  "language_style": {
    "common_phrases": ["哎呀", "真的吗"],
    "emoji_usage": "频繁使用😊😘🤱"
  }
}
```

## 🔄 工作流引擎

基于 LangGraph StateGraph 的 **observe → plan → act → reflect** 循环：

### 工作流节点

1. **select_agent**: 选择活跃Agent
2. **observe**: 环境感知和社交观察
3. **plan**: 基于LangChain的智能计划生成
4. **execute**: 行动执行（对话、学习、育儿）
5. **reflect**: 经验反思和记忆更新
6. **process_results**: 结果处理和状态更新

### 状态管理

使用 Pydantic 模型确保类型安全：

```python
class WorkflowState(BaseModel):
    simulation_state: SimulationState
    current_agent_id: Optional[str]
    node_outputs: Dict[str, NodeOutput]
    # ...
```

## 🧠 记忆系统

### 混合记忆架构

- **短期记忆**: LangChain ConversationSummaryBufferMemory
- **长期记忆**: SQLite + 语义搜索准备
- **对话历史**: 完整的互动记录
- **Agent状态**: 实时的Agent状态追踪

### 记忆类型

```python
class MemoryType(str, Enum):
    OBSERVATION = "observation"    # 环境观察
    PLAN = "plan"                 # 计划制定
    ACTION = "action"             # 行动执行
    REFLECTION = "reflection"     # 经验反思
    CONVERSATION = "conversation" # 对话互动
    LEARNING = "learning"         # 学习收获
    CONCERN = "concern"           # 担忧记录
```

## 📊 数据模型

### 核心数据结构

```python
# 对话模型
class Conversation(BaseModel):
    from_agent: str
    to_agent: Optional[str]  # None = 群聊
    message: str
    conversation_type: ConversationType
    timestamp: datetime

# 记忆模型
class Memory(BaseModel):
    agent_id: str
    content: str
    memory_type: MemoryType
    importance: int  # 1-10
    timestamp: datetime
```

## 🎮 使用方式

### 交互模式命令

```bash
MamaVillage v2.0> run 10 20        # 运行10个tick，最多20轮对话
MamaVillage v2.0> conversations 30 # 查看最近30条对话
MamaVillage v2.0> stats            # 显示统计信息
MamaVillage v2.0> agent 小李       # 查看特定Agent详情
MamaVillage v2.0> cleanup 7        # 清理7天前的数据
```

### 编程接口

```python
from core import (
    MamaVillageSimulation, AgentProfileManager,
    MemorySystemManager, MamaVillageWorkflow
)

# 创建模拟实例
simulation = MamaVillageSimulation()

# 运行模拟
simulation.run_simulation(
    max_ticks=20,
    tick_interval=2.0,
    max_conversations=30
)

# 查看结果
simulation.show_conversation_stats()
```

## 🔧 配置和自定义

### 环境变量

- `OPENAI_API_KEY`: OpenAI API密钥
- `OPENAI_MODEL`: 使用的模型（默认：gpt-4o-mini）
- `DATABASE_PATH`: 数据库文件路径
- `LOG_LEVEL`: 日志级别

### Agent配置自定义

可以通过修改 `agents/` 目录下的JSON文件来自定义Agent行为：

- **个性特征**: traits, interests, communication_style
- **数字习惯**: apps, video_preferences, screen_time
- **语言风格**: dialect, common_phrases, emoji_usage
- **行为参数**: response_probability, initiative_level

## 📈 监控和分析

### 实时统计

- 对话数量和类型分布
- Agent活跃度分析
- 知识传播路径追踪
- 社交网络结构分析

### 数据导出

```python
# 导出对话记录
simulation.memory_system.export_conversation_history("conversations.json")

# 获取统计数据
stats = simulation.memory_system.get_conversation_stats()
```

## 🔬 研究应用

### 研究方向

1. **知识传播机制**: 育儿知识在农村社群中的传播路径
2. **数字鸿沟**: 不同年龄段对数字工具的使用差异
3. **社会支持网络**: 互助行为的模式和效果
4. **传统vs现代**: 传统育儿智慧与现代科学的融合

### 数据收集

系统自动记录：
- 对话内容和模式
- 知识分享频率
- 求助和响应行为
- Agent间的影响关系

## 🛠️ 开发和扩展

### 添加新Agent

1. 在 `agents/` 目录创建JSON配置文件
2. 运行系统自动加载新Agent
3. 配置社交连接关系

### 扩展工作流

```python
# 在 workflow.py 中添加新节点
workflow.add_node("new_node", self._new_node_function)
workflow.add_edge("execute", "new_node")
```

### 自定义记忆处理

```python
class CustomMemoryManager(AgentMemoryManager):
    def process_memory(self, memory: Memory) -> Memory:
        # 自定义记忆处理逻辑
        return enhanced_memory
```

## 🐛 故障排除

### 常见问题

1. **API密钥错误**: 检查 `.env` 文件中的 `OPENAI_API_KEY`
2. **导入错误**: 确保所有依赖已正确安装
3. **数据库问题**: 删除 `memory/memory.sqlite` 重新初始化

### 调试模式

```bash
# 运行系统测试
python test_new_system.py

# 查看详细错误信息
python -c "
from core import MamaVillageSimulation
sim = MamaVillageSimulation()
"
```

## 📚 技术栈

- **LangGraph**: 状态图工作流引擎
- **LangChain**: Agent框架和记忆系统
- **OpenAI GPT-4o-mini**: 语言模型
- **Pydantic**: 数据验证和类型安全
- **SQLite**: 持久化存储
- **Python 3.8+**: 主要开发语言

## 🤝 贡献

欢迎贡献代码、报告问题或提出改进建议！

### 开发工作流

1. Fork 项目
2. 创建特性分支
3. 编写测试
4. 提交Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详见 `LICENSE` 文件。

## 🙏 致谢

- 感谢所有参与实地调研的农村妈妈们
- 感谢 LangChain 和 LangGraph 开源社区
- 感谢所有贡献者和支持者

---

*MamaVillage v2.0 - 用科技连接农村育儿智慧* 🏡❤️