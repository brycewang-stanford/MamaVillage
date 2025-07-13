# 📊 数据库检查工具使用指南

## 🎯 功能概述

`check_database.py` 是一个强大的SQLite数据库检查工具，专门为妈妈互助小区项目设计，用于：

- 📋 查看数据库表结构和统计信息
- 👥 检查所有Agent信息
- 🧠 分析记忆数据
- 💬 查看对话历史
- 📅 检查日常计划
- 🔍 搜索特定内容
- 💾 导出数据报告

## 🚀 基础使用

### 快速检查（推荐）
```bash
# 激活虚拟环境
source mama_village_env/bin/activate

# 检查整个数据库
python check_database.py

# 只显示概要统计
python check_database.py --summary
```

### 查看帮助信息
```bash
python check_database.py --help
```

## 📋 详细命令参数

### 基础参数
```bash
--db PATH              # 指定数据库文件路径（默认：memory/memory.sqlite）
--limit N              # 限制显示的记录数（默认：20）
--no-details           # 不显示详细信息，只显示概要
--summary              # 只显示概要统计
```

### 表格筛选
```bash
--table agents         # 只检查agents表
--table memories       # 只检查memories表  
--table conversations  # 只检查conversations表
--table daily_plans    # 只检查daily_plans表
```

### Agent筛选
```bash
--agent 小李           # 只显示小李相关的数据
--agent mama_xiaoli    # 使用agent ID筛选
```

### 搜索功能
```bash
--search "发烧"        # 搜索包含"发烧"的对话和记忆
--search "推拿"        # 搜索传统技能相关内容
```

### 导出功能
```bash
--export report.txt    # 导出数据到指定文件
--export              # 自动生成文件名导出
```

## 💡 使用示例

### 示例1：检查整个数据库
```bash
python check_database.py
```
输出包括：
- 数据库表结构
- 概要统计信息
- 所有agents详情
- 最近20条记忆
- 最近20条对话
- 最近20条计划

### 示例2：只查看对话记录
```bash
python check_database.py --table conversations --limit 50
```

### 示例3：查看特定Agent的数据
```bash
python check_database.py --agent 小李 --limit 30
```

### 示例4：搜索健康相关内容
```bash
python check_database.py --search "发烧"
python check_database.py --search "生病"
python check_database.py --search "医院"
```

### 示例5：导出完整报告
```bash
python check_database.py --export "analysis_report.txt"
```

### 示例6：快速概要检查
```bash
python check_database.py --summary
```

## 📊 输出格式说明

### 表结构信息
```
📋 表名: conversations
   列信息:
     • id: INTEGER (主键) NOT NULL
     • from_agent: TEXT NOT NULL
     • to_agent: TEXT
     • message: TEXT NOT NULL
     • conversation_type: TEXT DEFAULT 'chat'
     • timestamp: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
     • metadata: TEXT
   📈 记录数: 45
```

### Agent信息
```
👥 Agents表数据
================================================================================
📊 总共 4 个agent

1. Agent详细信息:
   ID: mama_xiaoli
   姓名: 小李
   年龄: 28
   教育: 高中
   角色: 年轻妈妈
   创建时间: 2024-01-15 10:30:00
   性格特点: ['细心', '好学', '爱刷手机', '容易焦虑']
   兴趣爱好: ['育儿视频', '健康知识', '购物直播']
```

### 对话记录
```
💬 Conversations表数据 (最近20条)
================================================================================
📊 总对话数: 45, 显示最近 20 条

📈 对话类型统计:
   chat: 35 条
   help_request: 8 条
   advice: 2 条

👥 发言统计:
   小李: 15 条
   王芳: 12 条
   张奶奶: 10 条
   小陈: 8 条

💬 对话详情:
 1. [2024-01-15 14:2] 💬 小李 → 群聊:
    "姐妹们，今天孩子特别乖😊"
 2. [2024-01-15 14:2] 🆘 小陈 → 群聊:
    "怎么办啊，宝宝不肯吃辅食😰"
```

### 记忆分析
```
🧠 Memories表数据 (最近20条)
================================================================================
📊 总记忆数: 120, 显示最近 20 条

📈 记忆类型统计:
   observation: 45 条
   action: 35 条
   learning: 20 条
   reflection: 15 条
   plan: 5 条

📝 记忆详情:
 1. [2024-01-15 14:2] 小李 (learning):
    从育儿知识视频中学到：宝宝sleep训练方法
    重要性: 5
    元数据: ['topic', 'content', 'platform']
```

### 搜索结果
```
🔍 搜索关键词: '发烧'
================================================================================

💬 对话中的搜索结果:
 1. [2024-01-15 14:2] 小陈 → 群聊: "我家宝宝昨晚发烧了，用了退热贴还是38度，该怎么办啊😰"
 2. [2024-01-15 13:5] 张奶奶 → 群聊: "孩子发烧的时候，我们老人家的经验是..."

🧠 记忆中的搜索结果:
 1. [2024-01-15 14:2] 小陈 (concern): 担心孩子：孩子有点不舒服...
```

## 🛠️ 高级功能

### 数据分析工作流
1. **概要检查**：`python check_database.py --summary`
2. **详细分析**：`python check_database.py --limit 50`
3. **搜索特定内容**：`python check_database.py --search "关键词"`
4. **导出报告**：`python check_database.py --export`

### 研究用途示例
```bash
# 分析育儿求助模式
python check_database.py --search "怎么办" --table conversations

# 检查知识传播
python check_database.py --search "经验" --table memories

# 分析agent活跃度
python check_database.py --table conversations --limit 100

# 导出完整数据进行外部分析
python check_database.py --export research_data.txt
```

### 故障排除
```bash
# 检查数据库完整性
python check_database.py --summary

# 查看特定agent的所有活动
python check_database.py --agent 小李

# 检查最近的错误或异常
python check_database.py --search "失败" --search "错误"
```

## 📈 数据解读建议

### 关注指标
1. **对话频率**：conversations表的记录数和时间分布
2. **参与度**：各agent的发言统计
3. **内容质量**：help_request vs advice的比例
4. **知识传播**：learning类型记忆的数量和内容
5. **系统健康**：error或异常记录

### 分析维度
- **时间维度**：查看对话和记忆的时间分布
- **角色维度**：比较不同年龄/角色的行为模式
- **内容维度**：分析讨论的主题和关键词
- **互动维度**：观察agent之间的互动模式

## 🚨 注意事项

1. **数据隐私**：导出的文件可能包含敏感信息，请妥善保管
2. **性能考虑**：大数据库查询可能需要较长时间
3. **文件位置**：确保数据库文件路径正确
4. **编码问题**：导出文件使用UTF-8编码，确保查看工具支持中文

## 🔧 故障排除

### 常见错误
```bash
# 数据库文件不存在
❌ 数据库文件不存在: memory/memory.sqlite
解决：运行一次模拟生成数据库，或检查路径

# 权限问题
❌ 连接数据库失败: Permission denied
解决：检查文件权限或使用sudo

# 内容显示乱码
解决：确保终端支持UTF-8编码
```

### 调试技巧
```bash
# 检查数据库是否存在
ls -la memory/

# 检查数据库文件大小
ls -lh memory/memory.sqlite

# 使用SQLite命令行工具验证
sqlite3 memory/memory.sqlite ".tables"
```

---

💡 **提示**：建议在模拟运行后立即使用该工具检查数据质量和系统行为。