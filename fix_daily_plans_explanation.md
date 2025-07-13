# 🔧 Daily Plans 记录缺失问题解决方案

## 🔍 问题原因

在您之前运行的20轮模拟中，daily_plans表中没有记录的原因是：

### 代码层面的问题
1. **数据库缺少方法**：`memory/database.py` 中没有实现 `add_daily_plan()` 方法
2. **临时解决方案**：在 `langgraph/planner.py` 中，计划被保存到了 `memories` 表而不是 `daily_plans` 表
3. **注释说明**：代码中有注释"由于database.py中还没有实现这个方法，先用memory记录"

### 数据实际保存位置
您的计划数据实际上保存在了 `memories` 表中，类型为 `memory_type = "plan"`

## ✅ 已修复的内容

### 1. 添加了数据库方法
```python
# 新增方法
add_daily_plan()      # 添加日常计划
get_daily_plans()     # 获取日常计划
update_plan_status()  # 更新计划状态
```

### 2. 更新了planner.py
- 现在会同时保存到 `daily_plans` 表和 `memories` 表
- 添加了保存成功的提示信息

## 🔍 如何查看您之前的计划数据

### 方法1：通过memories表查看
```bash
# 查看plan类型的记忆
python check_database.py --search "计划行动"

# 或者直接查看memories表中的plan类型数据
python check_database.py --table memories --limit 50
```

### 方法2：使用专门的脚本
```bash
source mama_village_env/bin/activate
python -c "
from memory.database import MemoryDatabase
db = MemoryDatabase()

# 查看所有plan类型的记忆
for agent_id in ['mama_xiaoli', 'mama_wangfang', 'grandma_zhang', 'mama_xiaochen']:
    memories = db.get_recent_memories(agent_id, limit=100, memory_type='plan')
    if memories:
        print(f'\n{agent_id} 的计划 ({len(memories)}条):')
        for mem in memories[:5]:  # 显示前5条
            print(f'  - {mem[\"content\"]}')
"
```

## 🚀 从现在开始

新的模拟运行将会正确保存到 `daily_plans` 表中。您可以通过以下方式验证：

### 1. 运行新的模拟
```bash
python run.py
# 选择模式4，设置5轮对话测试
```

### 2. 检查daily_plans表
```bash
python check_database.py --table daily_plans
```

### 3. 对比新旧数据
```bash
# 查看新的daily_plans
python check_database.py --table daily_plans --limit 20

# 查看旧的plan记忆
python check_database.py --search "计划行动"
```

## 📊 数据迁移建议

如果您想将之前的计划数据迁移到 `daily_plans` 表，可以运行这个脚本：

```python
from memory.database import MemoryDatabase
import json

db = MemoryDatabase()

# 获取所有plan类型的记忆
all_plan_memories = []
for agent_id in ['mama_xiaoli', 'mama_wangfang', 'grandma_zhang', 'mama_xiaochen']:
    memories = db.get_recent_memories(agent_id, limit=1000, memory_type='plan')
    all_plan_memories.extend(memories)

print(f"找到 {len(all_plan_memories)} 条计划记忆")

# 迁移到daily_plans表
migrated = 0
for memory in all_plan_memories:
    try:
        # 解析metadata获取更多信息
        metadata = json.loads(memory.get('metadata', '{}')) if memory.get('metadata') else {}
        
        success = db.add_daily_plan(
            agent_id=memory['agent_id'],
            planned_action=memory['content'].replace('计划行动：', ''),
            priority=memory.get('importance', 5),
            planned_time=metadata.get('planned_time', ''),
            status='completed'  # 因为是历史数据，标记为已完成
        )
        
        if success:
            migrated += 1
    except Exception as e:
        print(f"迁移失败: {e}")

print(f"成功迁移 {migrated} 条计划数据")
```

## 🎯 验证修复结果

### 运行测试
```bash
# 测试新功能
python -c "
from memory.database import MemoryDatabase
from langgraph.planner import PlannerNode

db = MemoryDatabase()
planner = PlannerNode(db)

# 模拟生成计划（需要API密钥）
test_profile = {
    'name': '测试妈妈',
    'age': 30,
    'role': '年轻妈妈',
    'concerns': ['孩子健康']
}

try:
    plan = planner._generate_fallback_plan('test_agent', test_profile)
    planner._save_plan_to_database('test_agent', plan)
    
    # 检查是否保存成功
    saved_plans = db.get_daily_plans('test_agent')
    print(f'✅ 新功能测试成功，保存了 {len(saved_plans)} 条计划')
except Exception as e:
    print(f'测试过程中遇到问题: {e}')
"
```

## 📝 总结

- **问题**：之前的计划数据保存在 `memories` 表中，而不是 `daily_plans` 表
- **原因**：代码实现不完整
- **解决方案**：已添加完整的数据库支持
- **数据恢复**：您的计划数据仍然存在，只是在不同的表中
- **未来**：新的模拟将正确保存到 `daily_plans` 表

现在您可以重新运行模拟，daily_plans表将会有正确的记录！