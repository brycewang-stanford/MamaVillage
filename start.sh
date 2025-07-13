#!/bin/bash

echo "🏡 妈妈互助小区启动脚本"
echo "=========================="

# 检查Python 3.11版本
python_version=$(python3.11 --version 2>&1)
if [[ $? -eq 0 ]]; then
    echo "✅ Python版本: $python_version"
else
    echo "❌ 未找到Python 3.11，请先安装Python 3.11"
    exit 1
fi

# 检查虚拟环境是否存在
if [[ ! -d "mama_village_env" ]]; then
    echo "📦 创建Python 3.11虚拟环境..."
    python3.11 -m venv mama_village_env
    if [[ $? -eq 0 ]]; then
        echo "✅ 虚拟环境创建成功"
    else
        echo "❌ 虚拟环境创建失败"
        exit 1
    fi
fi

# 检查依赖文件
if [[ ! -f "requirements.txt" ]]; then
    echo "❌ 未找到requirements.txt文件"
    exit 1
fi

# 检查环境配置
if [[ ! -f ".env" ]]; then
    echo "⚠️ 未找到.env文件，正在从模板复制..."
    if [[ -f ".env.example" ]]; then
        cp .env.example .env
        echo "✅ 已创建.env文件，请编辑并添加您的OpenAI API密钥"
        echo "📝 编辑命令: nano .env"
        echo ""
        read -p "按Enter继续，或Ctrl+C退出去配置API密钥..."
    else
        echo "❌ 未找到.env.example模板文件"
        exit 1
    fi
fi

# 检查API密钥
if ! grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
    echo "⚠️ 检测到API密钥可能未配置"
    echo "请确保在.env文件中设置了有效的OPENAI_API_KEY"
    echo ""
    read -p "继续运行？(y/N): " confirm
    if [[ $confirm != "y" && $confirm != "Y" ]]; then
        echo "已取消运行"
        exit 0
    fi
fi

# 激活虚拟环境并安装依赖
echo "📦 检查Python依赖..."
source mama_village_env/bin/activate

pip install -r requirements.txt -q

if [[ $? -eq 0 ]]; then
    echo "✅ 依赖安装完成"
else
    echo "❌ 依赖安装失败"
    exit 1
fi

# 创建必要目录
mkdir -p memory

echo ""
echo "🚀 启动妈妈互助小区模拟系统..."
echo ""

# 运行主程序
python run.py