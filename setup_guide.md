# 妈妈互助小区 - 安装和运行指南

## 🚀 快速开始

### 1. 环境准备

确保你的系统已安装：
- Python 3.8 或更高版本
- pip 包管理器

### 2. 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt
```

### 3. 配置API密钥

1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，添加你的OpenAI API密钥：
```
OPENAI_API_KEY=你的OpenAI_API密钥
OPENAI_MODEL=gpt-4o-mini
DATABASE_PATH=memory/memory.sqlite
LOG_LEVEL=INFO
```

### 4. 运行系统

```bash
python run.py
```

## 📖 使用说明

### 运行模式

程序启动后会提供三种模式选择：

1. **自动模拟** - 运行20个tick的完整模拟
2. **交互模式** - 手动控制模拟进程
3. **快速演示** - 运行5个tick的快速演示

### 交互模式命令

在交互模式下可以使用以下命令：

- `run [ticks]` - 运行指定数量的tick（默认5个）
- `status` - 显示当前状态和统计信息
- `agent [name]` - 查看特定agent的详细信息
- `clear` - 清空数据库（需要确认）
- `quit` / `exit` - 退出程序

### Agent角色

系统包含4个预设的农村妈妈角色：

1. **小李** (mama_xiaoli) - 28岁年轻妈妈，爱学习但容易焦虑
2. **张奶奶** (grandma_zhang) - 58岁资深奶奶，经验丰富
3. **王芳** (mama_wangfang) - 32岁经验妈妈，实用主义者
4. **小陈** (mama_xiaochen) - 25岁新手妈妈，谨慎小心

## 🎯 系统特色

### 真实的对话风格
- 使用中文口语化表达
- 体现农村妈妈的语言特点
- 适当使用表情符号和网络用语

### 智能行为模拟
- **观察** - 感知环境和社区动态
- **计划** - 制定符合角色的日常计划
- **执行** - 进行社交、学习、育儿等活动
- **反思** - 总结经验和生成智慧

### 多样化互动
- 群聊交流
- 私信关怀
- 经验分享
- 求助互助
- 内容推荐

## 🔧 自定义配置

### 添加新的Agent

1. 在 `agents/` 目录下创建新的JSON文件
2. 参考现有agent的结构配置角色信息
3. 重启程序即可加载新agent

### 调整模拟参数

在 `run.py` 中可以调整：
- tick间隔时间
- agent活跃概率
- 行为类型分布
- 反思频率等

### 修改对话风格

在 `prompts/conversation_templates.py` 中可以：
- 调整角色对话特点
- 添加新的对话场景
- 修改常用语和表情符号

## 📊 数据存储

系统使用SQLite数据库存储：
- Agent基础信息
- 记忆和经验
- 对话历史
- 行为计划

数据库文件位置：`memory/memory.sqlite`

## ⚠️ 注意事项

1. **API费用**：系统使用OpenAI API，会产生费用。建议设置合理的使用限制。

2. **网络连接**：需要稳定的网络连接访问OpenAI API。

3. **存储空间**：长时间运行会积累大量对话和记忆数据。

4. **性能优化**：大量agent同时活跃时可能影响响应速度。

## 🐛 故障排除

### 常见问题

**Q: 提示"Import 'openai' could not be resolved"**
A: 运行 `pip install openai` 安装OpenAI包

**Q: 提示API密钥错误**
A: 检查 `.env` 文件中的API密钥是否正确设置

**Q: 数据库相关错误**
A: 确保 `memory/` 目录存在，或删除现有数据库文件重新创建

**Q: 对话生成失败**
A: 检查网络连接和API配额，系统会自动降级到简单回复

### 调试模式

设置环境变量开启详细日志：
```bash
export LOG_LEVEL=DEBUG
python run.py
```

## 📞 技术支持

如遇到问题，请检查：
1. Python版本兼容性
2. 依赖包安装完整性
3. API密钥配置正确性
4. 网络连接稳定性

---

💡 **提示**：首次运行建议选择"快速演示"模式，观察系统行为后再进行长时间模拟。