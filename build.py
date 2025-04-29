import os
import subprocess
import sys
import platform

def build_exe():
    """
    使用PyInstaller打包应用程序为EXE文件
    """
    print("开始打包程序...")
    
    # 构建PyInstaller命令，使用python -m方式执行
    cmd = [
        sys.executable,  # 当前Python解释器路径
        '-m',
        'PyInstaller',
        '--name=自动点击器',
        '--windowed',  # 不显示控制台窗口
        '--onefile',   # 打包为单个EXE文件
        '--noupx',     # 不使用UPX压缩
        '--clean',     # 清理临时文件
        'auto_clicker_gui.py'
    ]
    
    # 如果是Windows系统，添加图标
    if platform.system() == 'Windows':
        # 如果有图标文件，请取消下面这行的注释并提供正确的路径
        # cmd.append('--icon=icon.ico')
        pass
    
    # 执行PyInstaller命令
    try:
        print(f"执行命令: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        
        # 打包成功后的提示
        print("\n打包完成！")
        
        # 显示生成的EXE文件路径
        exe_path = os.path.join('dist', '自动点击器.exe')
        if os.path.exists(exe_path):
            print(f"可执行文件已生成：{os.path.abspath(exe_path)}")
        else:
            print("警告：未找到生成的EXE文件")
    
    except subprocess.CalledProcessError as e:
        print(f"打包失败，错误：{e}")
        return False
    except Exception as e:
        print(f"发生未知错误：{e}")
        return False
    
    return True

if __name__ == "__main__":
    # 执行打包
    build_exe() 