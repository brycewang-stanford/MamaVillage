# 🏡 妈妈互助小区 - 快速开始

## 🚀 一键启动

您的Python 3.11虚拟环境已经配置完成！现在可以快速启动系统：

### 方法1：一键启动（推荐）
```bash
./start.sh
```

### 方法2：手动激活虚拟环境
```bash
# 激活虚拟环境
./activate_env.sh

# 然后运行程序
python run.py
```

### 方法3：直接使用虚拟环境
```bash
source mama_village_env/bin/activate
python run.py
```

## ⚙️ 配置OpenAI API密钥

**重要**：运行前请确保配置了OpenAI API密钥：

1. 编辑 `.env` 文件：
```bash
nano .env
```

2. 添加您的API密钥：
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

3. 保存文件（Ctrl+X，然后Y，然后Enter）

## 🧪 测试系统

在运行主程序前，建议先测试系统：
```bash
# 激活虚拟环境
source mama_village_env/bin/activate

# 运行测试
python test_system.py
```

## 🎮 运行模式

启动后会看到四种运行模式：

1. **自动模拟** - 运行20个tick的完整模拟
2. **交互模式** - 手动控制，推荐用于调试
3. **快速演示** - 运行5个tick，适合第一次体验
4. **限制对话轮数模拟** - 🆕 精确控制对话数量，推荐用于研究分析

## 📱 Agent角色

系统包含4个农村妈妈角色：

- **小李** (28岁) - 年轻妈妈，爱学习但容易焦虑 😰
- **王芳** (32岁) - 经验妈妈，实用主义，乐于分享 👍  
- **张奶奶** (58岁) - 资深奶奶，传统智慧，亲切温和 👵
- **小陈** (25岁) - 新手妈妈，谨慎小心，依赖性强 🤔

## 💬 期待的效果

运行后您会看到：
- 真实的中文对话交流
- 育儿经验分享
- 求助和互助行为
- 学习和反思过程

例如：
```
👤 小李: 刷抖音看育儿视频
   └─ 📱 在抖音看育儿知识视频 ✨学到新知识
   
👤 张奶奶: 在群里聊天交流  
   └─ 💬 对群聊说: "孩子啊，我跟你说，这个推拿方法真的好用👵"
```

## 🛠️ 交互模式命令

进入交互模式后可以使用：

- `run 5` - 运行5个tick的模拟
- `status` - 查看当前状态
- `agent 小李` - 查看小李的详细信息
- `clear` - 清空数据库（谨慎使用）
- `quit` - 退出程序

## 📊 环境信息

- **Python版本**: 3.11.13
- **虚拟环境**: mama_village_env
- **主要依赖**: OpenAI, LangGraph, LangChain
- **数据库**: SQLite (memory/memory.sqlite)

## 🆕 对话轮数限制功能

选择模式4可以精确控制对话数量：
- 设置最大对话轮数（推荐20轮）
- 实时监控对话进度
- 自动停止并显示对话记录
- 导出对话数据进行分析

### 交互模式新命令
- `run 10 20` - 运行10个tick，最多20轮对话
- `conversations 20` - 查看最近20条对话
- `export_conversations` - 导出对话到文件
- `stats` - 显示对话统计信息

📖 详细使用说明请查看：`CONVERSATION_LIMIT_GUIDE.md`

## 🎯 首次运行建议

1. 先运行 `python test_system.py` 确保系统正常
2. 选择"限制对话轮数模拟"，设置10轮对话体验新功能
3. 观察对话效果后再尝试更多轮数的模拟
4. 使用交互模式深入了解各个agent的状态

祝您使用愉快！🎉