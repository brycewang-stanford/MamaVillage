#!/usr/bin/env python3
"""
数据库检查工具演示脚本
展示各种使用方式
"""

import os
import subprocess
import sys

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"📋 {description}")
    print(f"🔧 命令: {cmd}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"❌ 错误: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        return False

def main():
    """主演示函数"""
    print("🎬 数据库检查工具演示")
    print("这个演示将展示check_database.py的各种功能")
    
    # 激活虚拟环境的前缀
    venv_prefix = "source mama_village_env/bin/activate && "
    
    # 检查数据库是否存在
    if not os.path.exists("memory/memory.sqlite"):
        print("\n⚠️ 数据库文件不存在，请先运行模拟生成一些数据：")
        print("python run.py")
        print("选择模式4，设置5轮对话进行测试")
        return
    
    demos = [
        {
            "cmd": f"{venv_prefix}python check_database.py --help",
            "desc": "查看帮助信息"
        },
        {
            "cmd": f"{venv_prefix}python check_database.py --summary",
            "desc": "显示数据库概要统计"
        },
        {
            "cmd": f"{venv_prefix}python check_database.py --table agents --no-details",
            "desc": "查看所有agents（简化显示）"
        },
        {
            "cmd": f"{venv_prefix}python check_database.py --table conversations --limit 5",
            "desc": "查看最近5条对话记录"
        },
        {
            "cmd": f"{venv_prefix}python check_database.py --table memories --limit 10",
            "desc": "查看最近10条记忆"
        },
        {
            "cmd": f"{venv_prefix}python check_database.py --agent 小李 --limit 5",
            "desc": "查看小李相关的数据"
        },
        {
            "cmd": f"{venv_prefix}python check_database.py --search '孩子'",
            "desc": "搜索包含'孩子'的内容"
        },
        {
            "cmd": f"{venv_prefix}python check_database.py --search '辅食' --table conversations",
            "desc": "在对话中搜索'辅食'相关内容"
        }
    ]
    
    print(f"\n🚀 开始演示 {len(demos)} 个功能...")
    
    for i, demo in enumerate(demos, 1):
        input(f"\n按Enter键继续第{i}个演示...")
        success = run_command(demo["cmd"], demo["desc"])
        if not success:
            print(f"⚠️ 第{i}个演示失败，继续下一个...")
    
    print("\n" + "="*60)
    print("🎉 演示完成！")
    print("\n💡 更多用法示例:")
    print("• 导出数据：python check_database.py --export analysis.txt")
    print("• 查看特定表：python check_database.py --table memories --limit 50")  
    print("• 搜索关键词：python check_database.py --search '发烧'")
    print("• 查看agent详情：python check_database.py --agent 张奶奶")
    
    print("\n📖 详细文档请查看：DATABASE_CHECKER_GUIDE.md")

if __name__ == "__main__":
    main()