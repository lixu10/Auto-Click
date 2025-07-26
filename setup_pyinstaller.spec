"""
智能辅助点击器 - 使用PyInstaller打包
更推荐的打包方案，生成的exe文件更小更稳定
"""

# 这个文件用于PyInstaller打包
# 打包命令：pyinstaller --onefile --windowed --name="智能辅助点击器" main.py

# 或者使用这个配置文件：pyinstaller setup_pyinstaller.spec

# PyInstaller配置
block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['pynput.mouse', 'pynput.keyboard', 'PyQt5.sip'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='智能辅助点击器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 设置为False来隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标文件路径，如 'icon.ico'
)
