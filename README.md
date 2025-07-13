## 📘 中文版 README

# 妈妈互助小区（MamaVillage）

一个模拟中国农村育儿社群的社会模拟系统，基于 GPT-4o-mini + Python 构建。社区中包含年轻妈妈与年长奶奶，她们通过短视频、聊天 App 等工具互相学习、交流、带娃和支持。

> **技术说明**：当前版本(v1.0)主要使用 OpenAI API 直接实现，为快速原型验证。v2.0 计划使用 LangChain + LangGraph 进行系统性重构，实现更复杂的 Agent 工作流和状态管理。

### 🌟 项目亮点

* **真实贴近中国农村母婴现实：**

  * 大多数妈妈或奶奶学历不高（小学至大专或本科），但都能熟练使用智能手机。
  * 会刷抖音、看微信视频号、使用健康/育儿 App。
  * 社区语言多为口语化、地方化、非标准书面语。

* **技能与经验传承：**

  * 模拟“奶奶教年轻妈妈推拿”、“妈妈推荐育儿视频号”等现实互动。
  * 知识在亲友关系网中自然扩散。

* **低成本、强代入：**

  * 无需图形界面，使用 emoji + 对话文本即可呈现真实感。
  * 非常适合乡村公共卫生干预、数字素养提升等方向的原型研究。

* **可接入 NGO 与政府干预角色：**

  * 模拟健康讲座、营养包发放、心理支持热线等干预介入效果。

---

### 🧠 系统架构

```
MamaVillage/
├── agents/
│   ├── mama_xiaoli.json     ← 28岁年轻妈妈（小李）
│   ├── mama_wangfang.json   ← 32岁经验妈妈（王芳）
│   ├── mama_xiaochen.json   ← 25岁新手妈妈（小陈）
│   └── grandma_zhang.json   ← 58岁资深奶奶（张奶奶）
├── langgraph/              ← Agent核心模块
│   ├── planner.py          ← 每日行为计划生成
│   ├── observer.py         ← 环境感知和事件记录
│   ├── reflector.py        ← 反思和记忆抽象
│   └── executor.py         ← 行为执行和社交互动
├── memory/
│   ├── database.py         ← 数据库操作类
│   ├── memory.sqlite       ← SQLite记忆数据库
│   └── memory-check.ipynb  ← 数据分析notebook
├── prompts/
│   └── reflection_prompt.txt ← 反思生成提示词
├── run.py                  ← 模拟主程序
├── config.py              ← 配置管理
└── check_database.py      ← 数据库检查工具
```

---

### 🔧 核心模块说明

* **agents/**: 四个角色的详细人设，包括教育背景、性格特点、关注重点和手机使用习惯
* **langgraph/**: 实现"感知 → 计划 → 执行 → 反思"的Agent认知循环（当前版本直接调用OpenAI API）
* **memory/**: SQLite数据库存储对话、记忆、计划等数据，支持自然语言检索
* **prompts/**: 针对中国农村语境的提示词工程，生成符合角色特点的口语化表达
* **run.py**: 控制模拟时间步长，支持交互模式和批量模拟

---

### 🧪 实验结果展示

#### 📊 20轮模拟数据概览
- **时间跨度**: 2025-07-13 20:57:24 至 20:59:42（约2分18秒）
- **总计划数**: 40条（全部保存在记忆系统中）
- **对话记录**: 6条（包括群聊和私聊）
- **记忆总数**: 96条（行动、反思、学习等）

#### 👥 各角色活动统计
| 角色 | 年龄 | 计划数 | 主要关注点 |
|------|------|--------|-----------|
| 小李 | 28岁 | 10条 | 营养午餐、公园散步、育儿视频 |
| 王芳 | 32岁 | 15条 | 回复朋友、分享经验、照顾孩子 |
| 小陈 | 25岁 | 10条 | 辅食准备、育儿学习、寻求建议 |
| 张奶奶 | 58岁 | 5条 | 关心孙辈、分享经验、学习新知识 |

#### 💬 真实对话样例
```
👩 小陈（新手妈妈）: 
"哎呀，大家好，我是小陈，最近打算给妞妞做辅食，感觉有点紧张，
不知道该怎么开始？🤔 还有，想带她去公园散步，正常吗？😰"

👩 小李（年轻妈妈）:
"哎呀，亲爱的们，我最近看了一个育儿视频，教了不少预防感冒的小技巧，
真的是很有用哦！😘💕大家可以一起看看，孩子的健康最重要嘛！🤱👶"

👵 张奶奶（资深奶奶）:
"孩子啊，我跟你说，辅食真是个头疼事，网上的乱七八糟的我都看不懂😅。
不过跟村里其他妈妈聊聊，学到不少好点子❤️。"
```

#### 🧠 认知行为模式
- **学习行为**: 看育儿视频、查找健康信息、学习新技能
- **社交行为**: 群聊求助、私信交流、分享经验
- **照护行为**: 准备辅食、陪伴散步、关注健康
- **反思行为**: 总结经验、调整计划、记录感受

---

### 🌍 政策与社会意义

#### 📈 对发展中国家儿童早期发展的启示

**1. 数字化健康教育潜力**
- 智能手机在农村地区的普及为健康信息传播提供了新渠道
- 短视频等形式更适合低学历人群的学习偏好
- 同伴网络比专业机构更容易建立信任关系

**2. 代际知识传承机制**
- 传统育儿智慧与现代健康知识的融合路径
- 年长者的经验与年轻父母的学习需求形成互补
- 非正式学习网络的重要性不容忽视

**3. 政策干预的精准化**
- 基于真实行为模式设计干预措施
- 利用社交网络的自然传播力量
- 关注不同教育背景群体的信息接受方式

**4. 资源配置优化建议**
- 优先发展移动健康服务而非线下设施
- 培养社区健康促进员而非依赖专业医护
- 设计适合口语传播的健康信息内容

#### 🎯 实际应用场景
- **公共卫生部门**: 测试健康信息传播策略
- **NGO组织**: 设计社区干预项目
- **学术研究**: 研究数字鸿沟与健康公平
- **政策制定**: 评估移动健康政策效果

---

## 📗 English README

# MamaVillage: A Rural Mother-Grandmother Support Simulation in China

MamaVillage simulates a multigenerational caregiving community in rural China, where both younger mothers and older grandmothers interact, learn, and support each other using smartphones, WeChat, and Douyin (TikTok China).

> **Technical Note**: Current version (v1.0) primarily uses OpenAI API directly for rapid prototyping. Version 2.0 plans systematic refactoring with LangChain + LangGraph for more sophisticated Agent workflows and state management.

### 🌟 Highlights

* **Localized Social Reality:**

  * Most agents have low-to-medium education (primary school to associate degree or bachelor degree).
  * All agents are digitally literate: they watch Douyin, use health/parenting apps, and chat on WeChat.
  * Their conversation style reflects oral and dialect-influenced Chinese.

* **Knowledge & Skill Diffusion:**

  * Simulates how grandmothers pass on massage techniques, or how moms share parenting video accounts.
  * Knowledge spreads through family/friend networks naturally.

* **Cost-efficient & Emotionally Engaging:**

  * No visual rendering needed — emoji + natural language simulate life vividly.
  * Supports public health prototyping, digital literacy interventions, and sociolinguistic simulations.

* **Supports NGO/Gov Interventions:**

  * Add social workers, health promoters, or nutrition consultants as agents.
  * Observe how communities react to interventions like mental health hotlines or parenting training.

---

### 🧠 System Architecture

```
MamaVillage/
├── agents/
│   ├── mama_xiaoli.json     ← 28-year-old young mother (Xiao Li)
│   ├── mama_wangfang.json   ← 32-year-old experienced mother (Wang Fang)
│   ├── mama_xiaochen.json   ← 25-year-old new mother (Xiao Chen)
│   └── grandma_zhang.json   ← 58-year-old seasoned grandmother
├── langgraph/              ← Agent core modules
│   ├── planner.py          ← Daily behavior planning
│   ├── observer.py         ← Environmental perception & logging
│   ├── reflector.py        ← Reflection & memory abstraction
│   └── executor.py         ← Behavior execution & social interaction
├── memory/
│   ├── database.py         ← Database operations
│   ├── memory.sqlite       ← SQLite memory database
│   └── memory-check.ipynb  ← Data analysis notebook
├── prompts/
│   └── reflection_prompt.txt ← Reflection generation prompts
├── run.py                  ← Main simulation program
├── config.py              ← Configuration management
└── check_database.py      ← Database inspection tool
```

---

### 🧪 Experimental Results & Sample Interactions

#### 📊 20-Round Simulation Overview
- **Time Span**: 2025-07-13 20:57:24 to 20:59:42 (approximately 2 minutes 18 seconds)
- **Total Plans**: 40 plans (all stored in memory system)
- **Conversations**: 6 conversations (group and private chats)
- **Total Memories**: 96 memories (actions, reflections, learning, etc.)

#### 💬 Authentic Dialogue Samples
```
👩 Xiao Chen (New Mother): 
"Hey everyone, I'm Xiao Chen. I'm planning to make complementary food for Niu Niu, 
but I'm a bit nervous. How should I start? 🤔 Also, is it normal to take her for 
walks in the park? 😰"

👩 Xiao Li (Young Mother):
"Oh dear, I recently watched a parenting video with lots of tips for preventing 
colds—it's really useful! 😘💕 Everyone should check it out, children's health 
is most important! 🤱👶"

👵 Grandma Zhang (Seasoned Grandmother):
"Child, let me tell you, complementary food is such a headache. I can't understand 
all that online stuff 😅. But chatting with other moms in the village, I learned 
quite a few good ideas ❤️."
```

---

### 🌍 Policy & Social Implications for Child Development in Developing Countries

#### 📈 Digital Health Education Potential
- **Mobile Access**: Smartphones provide new channels for health information dissemination in rural areas
- **Learning Preferences**: Short videos suit learning patterns of low-literacy populations
- **Trust Networks**: Peer networks establish trust more easily than professional institutions

#### 🔄 Intergenerational Knowledge Transfer
- **Knowledge Fusion**: Pathways for integrating traditional childcare wisdom with modern health knowledge
- **Complementary Roles**: Elder experience complements young parents' learning needs
- **Informal Networks**: The crucial importance of non-formal learning networks

#### 🎯 Policy Intervention Applications
- **Public Health Departments**: Test health information dissemination strategies
- **NGO Organizations**: Design community intervention projects  
- **Academic Research**: Study digital divide and health equity
- **Policy Making**: Evaluate mobile health policy effectiveness

---

### 🚀 安装与运行

#### 环境要求
- Python 3.11+
- OpenAI API Key

#### 安装步骤
```bash
# 1. 克隆项目
git clone https://github.com/yourusername/MamaVillage.git
cd MamaVillage

# 2. 创建虚拟环境
python3.11 -m venv mama_village_env
source mama_village_env/bin/activate  # Windows: mama_village_env\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置API密钥
cp config.py.example config.py
# 编辑 config.py，添加您的 OpenAI API Key

# 5. 运行模拟
python run.py
```

#### 当前技术栈 (v1.0)
- **核心**: Python 3.11 + OpenAI API (GPT-4o-mini)
- **数据库**: SQLite3
- **数据分析**: Pandas + Jupyter Notebook
- **未来计划**: LangChain + LangGraph (v2.0)

---

### 🔄 版本规划

#### v1.0 (当前版本)
- ✅ 基础Agent框架和角色设定
- ✅ 直接OpenAI API调用
- ✅ SQLite记忆存储
- ✅ 对话和行为模拟

#### v2.0 (计划中)
- 🔄 LangGraph工作流重构
- 🔄 LangChain工具链集成
- 🔄 复杂状态管理
- 🔄 插件化干预模块

---

## 🧾 License

MIT License



