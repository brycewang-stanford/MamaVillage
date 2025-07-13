#!/bin/bash

echo "🏡 激活妈妈互助小区虚拟环境"
echo "=============================="

# 检查虚拟环境是否存在
if [[ ! -d "mama_village_env" ]]; then
    echo "❌ 虚拟环境不存在，请先运行 ./start.sh 创建环境"
    exit 1
fi

# 激活虚拟环境
source mama_village_env/bin/activate

# 检查激活是否成功
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ 虚拟环境已激活: $(basename $VIRTUAL_ENV)"
    echo "📝 Python版本: $(python --version)"
    echo ""
    echo "现在可以运行以下命令："
    echo "  python run.py          - 运行主程序"
    echo "  python test_system.py  - 运行系统测试"
    echo "  deactivate             - 退出虚拟环境"
    echo ""
    
    # 启动一个新的shell来保持虚拟环境激活
    exec $SHELL
else
    echo "❌ 虚拟环境激活失败"
    exit 1
fi