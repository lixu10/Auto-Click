"""
智能辅助点击器打包配置文件
使用cx_Freeze进行打包
"""

import sys
from cx_Freeze import setup, Executable

# 构建选项
build_exe_options = {
    "packages": ["pynput", "PyQt5", "threading", "time", "random", "sys"],
    "excludes": ["tkinter"],  # 排除不需要的模块
    "include_files": [],  # 包含的额外文件
    "zip_include_packages": "*",
    "zip_exclude_packages": [],
    "optimize": 2,
}

# 基础设置
base = None
if sys.platform == "win32":
    base = "Win32GUI"  # 在Windows上隐藏控制台窗口

# 可执行文件配置
executables = [
    Executable(
        "main.py",
        base=base,
        target_name="智能辅助点击器.exe",
        icon=None,  # 可以添加图标文件路径
        copyright="Copyright (C) 2024 智能辅助点击器团队",
    )
]

# 主设置
setup(
    name="智能辅助点击器",
    version="2.0.0",
    description="智能辅助点击器 Professional Edition",
    author="智能辅助点击器团队",
    options={"build_exe": build_exe_options},
    executables=executables,
)
