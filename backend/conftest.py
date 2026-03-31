"""
conftest.py - pytest 公共固件配置
"""
import sys
import os

# 将 backend 目录添加到 Python 路径，使 'app' 包可以被导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
