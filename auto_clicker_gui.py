import sys
import time
import threading
import random
from pynput import mouse as ms
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QSlider, QCheckBox, QGroupBox, QSpinBox,
                             QDoubleSpinBox, QStyleFactory, QTabWidget)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette

# 线程锁，确保线程安全
lock = threading.Lock()

class AutoClickerGUI(QMainWindow):
    # 自定义信号用于线程安全更新UI
    update_left_cps_signal = pyqtSignal(float, float)
    update_right_cps_signal = pyqtSignal(float, float)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("自动点击器")
        self.setMinimumSize(600, 500)
        
        # 状态变量
        self.left_clicking_active = False
        self.right_clicking_active = False
        self.left_button_held = False
        self.right_button_held = False
        
        # 模式状态
        self.mode = "normal"  # normal, mode1, mode2
        self.mode1_continuous = False  # 模式一中的连续点击状态
        
        # 点击计数
        self.left_click_count = 0
        self.right_click_count = 0
        self.side_button_count = 0
        self.last_left_click_time = 0
        self.last_right_click_time = 0
        self.last_side_button_time = 0
        self.last_side_button = None
        
        # 左键点击参数
        self.left_max_cps = 12
        self.left_min_cps = 10
        self.left_jitter_range = 1.0
        
        # 右键点击参数
        self.right_max_cps = 26
        self.right_min_cps = 23
        self.right_jitter_range = 1.2
        
        # 键盘快捷键配置
        self.use_mouse_side_buttons = True
        
        # 创建鼠标控制器
        self.mouse_controller = ms.Controller()
        
        # 设置UI样式
        self.set_style()
        
        # 初始化UI
        self.init_ui()
        
        # 启动线程
        self.start_threads()
        
        # 启动鼠标监听
        self.start_mouse_listener()
        
    def set_style(self):
        """设置应用的样式"""
        # 使用Fusion样式
        QApplication.setStyle(QStyleFactory.create('Fusion'))
        
        # 深色主题
        dark_palette = QPalette()
        dark_color = QColor(53, 53, 53)
        disabled_color = QColor(127, 127, 127)
        
        dark_palette.setColor(QPalette.Window, dark_color)
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(33, 33, 33))
        dark_palette.setColor(QPalette.AlternateBase, dark_color)
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Disabled, QPalette.Text, disabled_color)
        dark_palette.setColor(QPalette.Button, dark_color)
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_color)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        
        QApplication.setPalette(dark_palette)
    
    def init_ui(self):
        """初始化用户界面"""
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        tab_widget.setFont(QFont("微软雅黑", 10))
        
        # 第一个选项卡 - 主控制面板
        main_tab = QWidget()
        main_tab_layout = QVBoxLayout(main_tab)
        
        # 左键自动点击组
        left_click_group = QGroupBox("左键自动点击")
        left_click_group.setFont(QFont("微软雅黑", 10, QFont.Bold))
        left_click_layout = QVBoxLayout(left_click_group)
        
        # 左键开关和CPS显示
        left_switch_layout = QHBoxLayout()
        self.left_button = QPushButton("开启左键自动点击")
        self.left_button.setCheckable(True)
        self.left_button.clicked.connect(self.toggle_left_clicking)
        self.left_button.setFont(QFont("微软雅黑", 10))
        self.left_button.setMinimumHeight(40)
        
        self.left_cps_label = QLabel("实际CPS: 0.00 | 目标CPS: 0.00")
        self.left_cps_label.setFont(QFont("微软雅黑", 10))
        
        left_switch_layout.addWidget(self.left_button)
        left_switch_layout.addWidget(self.left_cps_label)
        left_click_layout.addLayout(left_switch_layout)
        
        # 右键自动点击组
        right_click_group = QGroupBox("右键自动点击")
        right_click_group.setFont(QFont("微软雅黑", 10, QFont.Bold))
        right_click_layout = QVBoxLayout(right_click_group)
        
        # 右键开关和CPS显示
        right_switch_layout = QHBoxLayout()
        self.right_button = QPushButton("开启右键自动点击")
        self.right_button.setCheckable(True)
        self.right_button.clicked.connect(self.toggle_right_clicking)
        self.right_button.setFont(QFont("微软雅黑", 10))
        self.right_button.setMinimumHeight(40)
        
        self.right_cps_label = QLabel("实际CPS: 0.00 | 目标CPS: 0.00")
        self.right_cps_label.setFont(QFont("微软雅黑", 10))
        
        right_switch_layout.addWidget(self.right_button)
        right_switch_layout.addWidget(self.right_cps_label)
        right_click_layout.addLayout(right_switch_layout)
        
        # 添加到主选项卡
        main_tab_layout.addWidget(left_click_group)
        main_tab_layout.addWidget(right_click_group)
        
        # 鼠标侧键控制选项
        mouse_control_group = QGroupBox("鼠标侧键控制")
        mouse_control_group.setFont(QFont("微软雅黑", 10, QFont.Bold))
        mouse_control_layout = QVBoxLayout(mouse_control_group)
        
        self.mouse_side_checkbox = QCheckBox("启用鼠标侧键控制 (侧键5切换左键, 侧键4切换右键)")
        self.mouse_side_checkbox.setChecked(self.use_mouse_side_buttons)
        self.mouse_side_checkbox.toggled.connect(self.toggle_mouse_side_buttons)
        self.mouse_side_checkbox.setFont(QFont("微软雅黑", 10))
        
        mouse_control_layout.addWidget(self.mouse_side_checkbox)
        main_tab_layout.addWidget(mouse_control_group)
        
        # 第二个选项卡 - 左键设置
        left_settings_tab = QWidget()
        left_settings_layout = QVBoxLayout(left_settings_tab)
        
        # 左键CPS范围控制
        left_cps_group = QGroupBox("左键CPS设置")
        left_cps_group.setFont(QFont("微软雅黑", 10, QFont.Bold))
        left_cps_layout = QVBoxLayout(left_cps_group)
        
        # 最大CPS
        left_max_cps_layout = QHBoxLayout()
        left_max_cps_label = QLabel("最大CPS:")
        left_max_cps_label.setFont(QFont("微软雅黑", 10))
        self.left_max_cps_spin = QSpinBox()
        self.left_max_cps_spin.setRange(1, 100)
        self.left_max_cps_spin.setValue(self.left_max_cps)
        self.left_max_cps_spin.setFont(QFont("微软雅黑", 10))
        self.left_max_cps_spin.valueChanged.connect(self.update_left_max_cps)
        
        left_max_cps_layout.addWidget(left_max_cps_label)
        left_max_cps_layout.addWidget(self.left_max_cps_spin)
        left_cps_layout.addLayout(left_max_cps_layout)
        
        # 最小CPS
        left_min_cps_layout = QHBoxLayout()
        left_min_cps_label = QLabel("最小CPS:")
        left_min_cps_label.setFont(QFont("微软雅黑", 10))
        self.left_min_cps_spin = QSpinBox()
        self.left_min_cps_spin.setRange(1, 100)
        self.left_min_cps_spin.setValue(self.left_min_cps)
        self.left_min_cps_spin.setFont(QFont("微软雅黑", 10))
        self.left_min_cps_spin.valueChanged.connect(self.update_left_min_cps)
        
        left_min_cps_layout.addWidget(left_min_cps_label)
        left_min_cps_layout.addWidget(self.left_min_cps_spin)
        left_cps_layout.addLayout(left_min_cps_layout)
        
        # 抖动范围
        left_jitter_layout = QHBoxLayout()
        left_jitter_label = QLabel("抖动范围(±):")
        left_jitter_label.setFont(QFont("微软雅黑", 10))
        self.left_jitter_spin = QDoubleSpinBox()
        self.left_jitter_spin.setRange(0.0, 5.0)
        self.left_jitter_spin.setValue(self.left_jitter_range)
        self.left_jitter_spin.setSingleStep(0.1)
        self.left_jitter_spin.setFont(QFont("微软雅黑", 10))
        self.left_jitter_spin.valueChanged.connect(self.update_left_jitter)
        
        left_jitter_layout.addWidget(left_jitter_label)
        left_jitter_layout.addWidget(self.left_jitter_spin)
        left_cps_layout.addLayout(left_jitter_layout)
        
        left_settings_layout.addWidget(left_cps_group)
        
        # 第三个选项卡 - 右键设置
        right_settings_tab = QWidget()
        right_settings_layout = QVBoxLayout(right_settings_tab)
        
        # 右键CPS范围控制
        right_cps_group = QGroupBox("右键CPS设置")
        right_cps_group.setFont(QFont("微软雅黑", 10, QFont.Bold))
        right_cps_layout = QVBoxLayout(right_cps_group)
        
        # 最大CPS
        right_max_cps_layout = QHBoxLayout()
        right_max_cps_label = QLabel("最大CPS:")
        right_max_cps_label.setFont(QFont("微软雅黑", 10))
        self.right_max_cps_spin = QSpinBox()
        self.right_max_cps_spin.setRange(1, 100)
        self.right_max_cps_spin.setValue(self.right_max_cps)
        self.right_max_cps_spin.setFont(QFont("微软雅黑", 10))
        self.right_max_cps_spin.valueChanged.connect(self.update_right_max_cps)
        
        right_max_cps_layout.addWidget(right_max_cps_label)
        right_max_cps_layout.addWidget(self.right_max_cps_spin)
        right_cps_layout.addLayout(right_max_cps_layout)
        
        # 最小CPS
        right_min_cps_layout = QHBoxLayout()
        right_min_cps_label = QLabel("最小CPS:")
        right_min_cps_label.setFont(QFont("微软雅黑", 10))
        self.right_min_cps_spin = QSpinBox()
        self.right_min_cps_spin.setRange(1, 100)
        self.right_min_cps_spin.setValue(self.right_min_cps)
        self.right_min_cps_spin.setFont(QFont("微软雅黑", 10))
        self.right_min_cps_spin.valueChanged.connect(self.update_right_min_cps)
        
        right_min_cps_layout.addWidget(right_min_cps_label)
        right_min_cps_layout.addWidget(self.right_min_cps_spin)
        right_cps_layout.addLayout(right_min_cps_layout)
        
        # 抖动范围
        right_jitter_layout = QHBoxLayout()
        right_jitter_label = QLabel("抖动范围(±):")
        right_jitter_label.setFont(QFont("微软雅黑", 10))
        self.right_jitter_spin = QDoubleSpinBox()
        self.right_jitter_spin.setRange(0.0, 5.0)
        self.right_jitter_spin.setValue(self.right_jitter_range)
        self.right_jitter_spin.setSingleStep(0.1)
        self.right_jitter_spin.setFont(QFont("微软雅黑", 10))
        self.right_jitter_spin.valueChanged.connect(self.update_right_jitter)
        
        right_jitter_layout.addWidget(right_jitter_label)
        right_jitter_layout.addWidget(self.right_jitter_spin)
        right_cps_layout.addLayout(right_jitter_layout)
        
        right_settings_layout.addWidget(right_cps_group)
        
        # 添加所有选项卡
        tab_widget.addTab(main_tab, "主控制面板")
        tab_widget.addTab(left_settings_tab, "左键设置")
        tab_widget.addTab(right_settings_tab, "右键设置")
        
        # 添加到主布局
        main_layout.addWidget(tab_widget)
        
        # 版权信息
        copyright_label = QLabel("© 2023 自动点击器 - 版本 1.0")
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setFont(QFont("微软雅黑", 8))
        main_layout.addWidget(copyright_label)
        
        # 连接信号
        self.update_left_cps_signal.connect(self.update_left_cps_display)
        self.update_right_cps_signal.connect(self.update_right_cps_display)
    
    def toggle_left_clicking(self):
        """切换左键自动点击状态"""
        with lock:
            self.left_clicking_active = not self.left_clicking_active
        
        if self.left_clicking_active:
            self.left_button.setText("关闭左键自动点击")
            self.left_button.setStyleSheet("background-color: #a83232;")
        else:
            self.left_button.setText("开启左键自动点击")
            self.left_button.setStyleSheet("")
    
    def toggle_right_clicking(self):
        """切换右键自动点击状态"""
        with lock:
            self.right_clicking_active = not self.right_clicking_active
        
        if self.right_clicking_active:
            self.right_button.setText("关闭右键自动点击")
            self.right_button.setStyleSheet("background-color: #a83232;")
        else:
            self.right_button.setText("开启右键自动点击")
            self.right_button.setStyleSheet("")
    
    def toggle_mouse_side_buttons(self, state):
        """切换是否使用鼠标侧键控制"""
        self.use_mouse_side_buttons = state
    
    def update_left_max_cps(self, value):
        """更新左键最大CPS值"""
        self.left_max_cps = value
        # 确保最小CPS不大于最大CPS
        if self.left_min_cps > value:
            self.left_min_cps = value
            self.left_min_cps_spin.setValue(value)
    
    def update_left_min_cps(self, value):
        """更新左键最小CPS值"""
        self.left_min_cps = value
        # 确保最大CPS不小于最小CPS
        if self.left_max_cps < value:
            self.left_max_cps = value
            self.left_max_cps_spin.setValue(value)
    
    def update_left_jitter(self, value):
        """更新左键抖动范围"""
        self.left_jitter_range = value
    
    def update_right_max_cps(self, value):
        """更新右键最大CPS值"""
        self.right_max_cps = value
        # 确保最小CPS不大于最大CPS
        if self.right_min_cps > value:
            self.right_min_cps = value
            self.right_min_cps_spin.setValue(value)
    
    def update_right_min_cps(self, value):
        """更新右键最小CPS值"""
        self.right_min_cps = value
        # 确保最大CPS不小于最小CPS
        if self.right_max_cps < value:
            self.right_max_cps = value
            self.right_max_cps_spin.setValue(value)
    
    def update_right_jitter(self, value):
        """更新右键抖动范围"""
        self.right_jitter_range = value
    
    def update_left_cps_display(self, actual_cps, target_cps):
        """更新左键CPS显示"""
        self.left_cps_label.setText(f"实际CPS: {actual_cps:.2f} | 目标CPS: {target_cps:.2f}")
    
    def update_right_cps_display(self, actual_cps, target_cps):
        """更新右键CPS显示"""
        self.right_cps_label.setText(f"实际CPS: {actual_cps:.2f} | 目标CPS: {target_cps:.2f}")
    
    def start_threads(self):
        """启动自动点击线程"""
        # 左键自动点击线程
        self.left_click_thread = threading.Thread(target=self.left_auto_clicker)
        self.left_click_thread.daemon = True
        self.left_click_thread.start()
        
        # 右键自动点击线程
        self.right_click_thread = threading.Thread(target=self.right_auto_clicker)
        self.right_click_thread.daemon = True
        self.right_click_thread.start()
    
    def start_mouse_listener(self):
        """启动鼠标监听器"""
        self.mouse_listener = ms.Listener(on_click=self.on_mouse_click)
        self.mouse_listener.daemon = True
        self.mouse_listener.start()
    
    def on_mouse_click(self, x, y, button, pressed):
        """处理鼠标点击事件"""
        if not self.use_mouse_side_buttons:
            return
            
        current_time = time.time()
        
        # 处理侧键点击
        if button == ms.Button.x1 or button == ms.Button.x2:  # 侧键4或5
            if pressed:
                if current_time - self.last_side_button_time < 0.3 and self.last_side_button == button:
                    self.side_button_count += 1
                else:
                    self.side_button_count = 1
                self.last_side_button_time = current_time
                self.last_side_button = button
            else:
                # 松开侧键时处理模式切换
                if self.side_button_count == 1:  # 单次点击
                    if self.mode == "normal":  # 从普通模式进入模式一
                        self.mode = "mode1"
                        self.left_clicking_active = False
                        self.right_clicking_active = False
                        self.mode1_continuous = False
                        if button == ms.Button.x1:
                            self.left_button.setChecked(True)
                        else:
                            self.right_button.setChecked(True)
                    elif self.mode == "mode1":  # 从模式一返回普通模式
                        self.mode = "normal"
                        self.left_clicking_active = False
                        self.right_clicking_active = False
                        self.mode1_continuous = False
                        if button == ms.Button.x1:
                            self.left_button.setChecked(False)
                        else:
                            self.right_button.setChecked(False)
                elif self.side_button_count >= 3:  # 三次点击
                    if self.mode == "normal":  # 从普通模式进入模式二
                        self.mode = "mode2"
                        self.left_clicking_active = True
                        self.right_clicking_active = True
                        self.mode1_continuous = False
                        if button == ms.Button.x1:
                            self.left_button.setChecked(True)
                        else:
                            self.right_button.setChecked(True)
                    elif self.mode == "mode2":  # 从模式二返回普通模式
                        self.mode = "normal"
                        self.left_clicking_active = False
                        self.right_clicking_active = False
                        self.mode1_continuous = False
                        if button == ms.Button.x1:
                            self.left_button.setChecked(False)
                        else:
                            self.right_button.setChecked(False)
                    
        # 处理左键点击
        elif button == ms.Button.left:
            if pressed:
                self.left_button_held = True
                if self.mode == "mode1":  # 只在模式一下处理连续点击
                    self.left_click_count += 1
                    if current_time - self.last_left_click_time < 0.3:  # 300ms内连续点击
                        if self.left_click_count >= 3:  # 连续点击3次进入自动模式
                            self.mode1_continuous = True
                            self.left_clicking_active = True
                    else:
                        self.left_click_count = 1
                    self.last_left_click_time = current_time
            else:
                self.left_button_held = False
                if self.mode == "mode1" and self.mode1_continuous:
                    # 在模式一的连续点击状态下，停止点击则退出连续模式
                    self.mode1_continuous = False
                    self.left_clicking_active = False
                    
        # 处理右键点击
        elif button == ms.Button.right:
            if pressed:
                self.right_button_held = True
                if self.mode == "mode1":  # 只在模式一下处理连续点击
                    self.right_click_count += 1
                    if current_time - self.last_right_click_time < 0.3:  # 300ms内连续点击
                        if self.right_click_count >= 3:  # 连续点击3次进入自动模式
                            self.mode1_continuous = True
                            self.right_clicking_active = True
                    else:
                        self.right_click_count = 1
                    self.last_right_click_time = current_time
            else:
                self.right_button_held = False
                if self.mode == "mode1" and self.mode1_continuous:
                    # 在模式一的连续点击状态下，停止点击则退出连续模式
                    self.mode1_continuous = False
                    self.right_clicking_active = False
    
    def left_auto_clicker(self):
        """左键自动点击线程"""
        last_click_time = 0
        while True:
            if self.left_clicking_active and (
                self.mode == "mode2" or  # 模式二直接点击
                (self.mode == "mode1" and self.mode1_continuous)  # 模式一需要连续点击状态
            ):
                current_time = time.time()
                if current_time - last_click_time >= 1.0 / random.uniform(self.left_min_cps, self.left_max_cps):
                    with lock:
                        self.mouse_controller.click(ms.Button.left)
                        # 添加随机抖动
                        if self.left_jitter_range > 0:
                            x, y = self.mouse_controller.position
                            self.mouse_controller.position = (
                                x + random.uniform(-self.left_jitter_range, self.left_jitter_range),
                                y + random.uniform(-self.left_jitter_range, self.left_jitter_range)
                            )
                            self.mouse_controller.position = (x, y)
                    last_click_time = current_time
            time.sleep(0.001)
    
    def right_auto_clicker(self):
        """右键自动点击线程"""
        last_click_time = 0
        while True:
            if self.right_clicking_active and (
                self.mode == "mode2" or  # 模式二直接点击
                (self.mode == "mode1" and self.mode1_continuous)  # 模式一需要连续点击状态
            ):
                current_time = time.time()
                if current_time - last_click_time >= 1.0 / random.uniform(self.right_min_cps, self.right_max_cps):
                    with lock:
                        self.mouse_controller.click(ms.Button.right)
                        # 添加随机抖动
                        if self.right_jitter_range > 0:
                            x, y = self.mouse_controller.position
                            self.mouse_controller.position = (
                                x + random.uniform(-self.right_jitter_range, self.right_jitter_range),
                                y + random.uniform(-self.right_jitter_range, self.right_jitter_range)
                            )
                            self.mouse_controller.position = (x, y)
                    last_click_time = current_time
            time.sleep(0.001)
    
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        # 停止所有活动
        with lock:
            self.left_clicking_active = False
            self.right_clicking_active = False
        
        # 接受关闭事件
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AutoClickerGUI()
    window.show()
    sys.exit(app.exec_()) 