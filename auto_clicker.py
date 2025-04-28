import time
import threading
import random
from pynput import mouse as ms

# 左键自动点击模式开关
left_clicking_active = False
# 右键自动点击模式开关
right_clicking_active = False
# 线程锁，确保线程安全
lock = threading.Lock()

# 左键点击参数
LEFT_MAX_CPS = 12  # 最大CPS值
LEFT_MIN_CPS = LEFT_MAX_CPS - 2  # 最小CPS值（抖动下限）
LEFT_JITTER_RANGE = 1.0  # 抖动范围 ±1

# 右键点击参数 (单独配置)
RIGHT_MAX_CPS = 26  # 右键最大CPS值
RIGHT_MIN_CPS = RIGHT_MAX_CPS - 3  # 右键最小CPS值（抖动下限）
RIGHT_JITTER_RANGE = 1.2  # 右键抖动范围 ±1.2

# 创建鼠标控制器
mouse_controller = ms.Controller()

# 鼠标按键处理
def on_mouse_click(x, y, button, pressed):
    global left_clicking_active, right_clicking_active
    
    # 检测鼠标侧键5（通常对应按钮5）- 控制左键点击
    if button == ms.Button.x1 and pressed:  # x1对应侧键5
        with lock:
            left_clicking_active = not left_clicking_active
            print(f"左键自动点击模式: {'开启' if left_clicking_active else '关闭'}")
            if left_clicking_active:
                print(f"左键目标CPS范围: {LEFT_MIN_CPS}-{LEFT_MAX_CPS} (带±{LEFT_JITTER_RANGE}随机抖动)")

    # 检测鼠标侧键4（通常对应按钮4）- 控制右键点击
    if button == ms.Button.x2 and pressed:  # x2对应侧键4
        with lock:
            right_clicking_active = not right_clicking_active
            print(f"右键自动点击模式: {'开启' if right_clicking_active else '关闭'}")
            if right_clicking_active:
                print(f"右键目标CPS范围: {RIGHT_MIN_CPS}-{RIGHT_MAX_CPS} (带±{RIGHT_JITTER_RANGE}随机抖动)")

# 左键自动点击线程
def left_auto_clicker():
    global left_clicking_active
    click_count = 0
    start_count_time = time.time()
    
    while True:
        with lock:
            is_active = left_clicking_active
        
        if is_active:
            # 添加随机抖动到点击速率
            current_cps = random.uniform(LEFT_MIN_CPS, LEFT_MAX_CPS)
            # 再添加更小的随机抖动在±JITTER_RANGE范围内
            current_cps += random.uniform(-LEFT_JITTER_RANGE, LEFT_JITTER_RANGE)
            # 确保CPS不会为负或过小
            current_cps = max(1.0, current_cps)
            
            # 计算此次点击的延迟
            current_delay = 1.0 / current_cps
            
            # 直接执行左键点击
            mouse_controller.click(ms.Button.left)
            click_count += 1
            
            # 每秒计算一次实际CPS
            current_time = time.time()
            elapsed = current_time - start_count_time
            if elapsed >= 1.0:
                actual_cps = click_count / elapsed
                print(f"左键实际CPS: {actual_cps:.2f}, 当前目标CPS: {current_cps:.2f}")
                start_count_time = current_time
                click_count = 0
            
            # 应用随机化的延迟
            time.sleep(current_delay)
        else:
            # 重置计数器
            click_count = 0
            start_count_time = time.time()
            # 短暂休眠，减少CPU使用
            time.sleep(0.1)

# 右键自动点击线程 - 独立的逻辑
def right_auto_clicker():
    global right_clicking_active
    click_count = 0
    start_count_time = time.time()
    
    while True:
        with lock:
            is_active = right_clicking_active
        
        if is_active:
            # 添加随机抖动到点击速率 - 使用右键专用参数
            current_cps = random.uniform(RIGHT_MIN_CPS, RIGHT_MAX_CPS)
            # 再添加更小的随机抖动在±RIGHT_JITTER_RANGE范围内
            current_cps += random.uniform(-RIGHT_JITTER_RANGE, RIGHT_JITTER_RANGE)
            # 确保CPS不会为负或过小
            current_cps = max(1.0, current_cps)
            
            # 计算此次点击的延迟
            current_delay = 1.0 / current_cps
            
            # 直接执行右键点击
            mouse_controller.click(ms.Button.right)
            click_count += 1
            
            # 每秒计算一次实际CPS
            current_time = time.time()
            elapsed = current_time - start_count_time
            if elapsed >= 1.0:
                actual_cps = click_count / elapsed
                print(f"右键实际CPS: {actual_cps:.2f}, 当前目标CPS: {current_cps:.2f}")
                start_count_time = current_time
                click_count = 0
            
            # 应用随机化的延迟
            time.sleep(current_delay)
        else:
            # 重置计数器
            click_count = 0
            start_count_time = time.time()
            # 短暂休眠，减少CPU使用
            time.sleep(0.1)

# 创建并启动左键自动点击线程
left_click_thread = threading.Thread(target=left_auto_clicker)
left_click_thread.daemon = True
left_click_thread.start()

# 创建并启动右键自动点击线程
right_click_thread = threading.Thread(target=right_auto_clicker)
right_click_thread.daemon = True
right_click_thread.start()

# 设置鼠标监听
mouse_listener = ms.Listener(on_click=on_mouse_click)
mouse_listener.start()

print("自动点击脚本已启动 - 带随机抖动")
print("左键配置:")
print(f"  目标CPS范围: {LEFT_MIN_CPS}-{LEFT_MAX_CPS} (带±{LEFT_JITTER_RANGE}随机抖动)")
print("右键配置:")
print(f"  目标CPS范围: {RIGHT_MIN_CPS}-{RIGHT_MAX_CPS} (带±{RIGHT_JITTER_RANGE}随机抖动)")
print("按鼠标侧键5(x1)切换左键自动点击模式")
print("按鼠标侧键4(x2)切换右键自动点击模式")
print("程序将持续运行，请使用任务管理器或关闭终端窗口退出")

# 主线程保持活动状态
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    # 如果用户按下Ctrl+C，程序也会退出
    pass 