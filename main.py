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
        self.setWindowTitle("智能模拟点击器 - Half Auto Clicker")
        self.setMinimumSize(800, 650)
        self.resize(900, 700)
        
        # 字体缩放基准
        self.base_width = 900  # 基准宽度
        self.base_height = 700  # 基准高度
        self.current_scale_factor = 1.0  # 当前缩放因子
        
        # 状态变量
        self.assist_mode_active = True  # 辅助模式默认开启
        self.left_button_held = False
        self.right_button_held = False
        
        # 点击计数和时间跟踪
        self.left_click_count = 0
        self.right_click_count = 0
        self.last_left_click_time = 0
        self.last_right_click_time = 0
        self.left_click_times = []  # 记录左键点击时间（包含用户+辅助）
        self.right_click_times = []  # 记录右键点击时间（包含用户+辅助）
        self.user_left_click_times = []  # 仅记录用户左键点击时间
        self.user_right_click_times = []  # 仅记录用户右键点击时间
        
        # 左键点击参数
        self.left_max_cps = 23
        self.left_min_cps = 22
        self.left_jitter_range = 1.0
        self.left_interval = 50  # 左键点击间隔（毫秒）
        
        # 右键点击参数
        self.right_max_cps = 24
        self.right_min_cps = 23
        self.right_jitter_range = 1.2
        self.right_interval = 50  # 右键点击间隔（毫秒）
        
        # 键盘快捷键配置
        self.assist_threshold = 3  # CPS阈值，超过此值启动辅助
        
        # 用户活动检测参数
        self.idle_timeout = 0.20  # 用户停止点击多长时间后停止辅助（秒）
        self.last_user_left_click = 0  # 最后一次用户左键点击时间
        self.last_user_right_click = 0  # 最后一次用户右键点击时间
        
        # 防止辅助点击被监听器捕获的标志
        self.is_assist_clicking = False
        
        # 创建鼠标控制器
        self.mouse_controller = ms.Controller()
        
        # 设置UI样式
        self.set_style()
        
        # 初始化UI
        self.init_ui()
        
        # 启动线程
        self.start_threads()
        
        # 启动鼠标监听（仅用于检测点击频率）
        self.start_mouse_listener()
        
        # 连接窗口大小改变事件
        self.resizeEvent = self.on_resize
        
    def calculate_scale_factor(self):
        """根据当前窗口大小计算字体缩放因子"""
        current_width = self.width()
        current_height = self.height()
        
        # 计算宽度和高度的缩放比例
        width_scale = current_width / self.base_width
        height_scale = current_height / self.base_height
        
        # 使用较小的缩放比例，确保内容不会太大
        scale_factor = min(width_scale, height_scale)
        
        # 限制缩放范围，避免过小或过大
        scale_factor = max(0.8, min(scale_factor, 2.0))
        
        return scale_factor
    
    def get_scaled_font_size(self, base_size):
        """获取缩放后的字体大小"""
        return int(base_size * self.current_scale_factor)
    
    def on_resize(self, event):
        """窗口大小改变事件处理"""
        super().resizeEvent(event)
        
        # 计算新的缩放因子
        new_scale_factor = self.calculate_scale_factor()
        
        # 如果缩放因子变化较大，更新字体
        if abs(new_scale_factor - self.current_scale_factor) > 0.1:
            self.current_scale_factor = new_scale_factor
            self.update_all_fonts()
    
    def update_all_fonts(self):
        """更新所有组件的字体大小"""
        try:
            # 更新标题字体
            if hasattr(self, 'title_label'):
                self.title_label.setStyleSheet(f"""
                    QLabel {{
                        font-size: {self.get_scaled_font_size(32)}px;
                        font-weight: bold;
                        color: #6495ed;
                        margin: 0px;
                    }}
                """)
            
            # 更新所有选项卡字体
            for i in range(self.findChild(QTabWidget).count()):
                tab_widget = self.findChild(QTabWidget)
                if tab_widget:
                    tab_widget.setFont(QFont("微软雅黑", self.get_scaled_font_size(14)))
        except:
            pass  # 忽略更新过程中的错误
        
    def set_style(self):
        """设置现代化的应用样式"""
        # 使用Fusion样式
        QApplication.setStyle(QStyleFactory.create('Fusion'))
        
        # 现代深色主题
        dark_palette = QPalette()
        
        # 主色调 - 深蓝灰色系
        primary_dark = QColor(45, 50, 65)  # 主背景色
        secondary_dark = QColor(55, 62, 78)  # 次要背景色
        accent_color = QColor(100, 149, 237)  # 强调色
        text_color = QColor(255, 255, 255)  # 主文本色
        text_secondary = QColor(200, 200, 200)  # 次要文本色
        disabled_color = QColor(120, 120, 120)  # 禁用色
        
        dark_palette.setColor(QPalette.Window, primary_dark)
        dark_palette.setColor(QPalette.WindowText, text_color)
        dark_palette.setColor(QPalette.Base, QColor(40, 44, 58))
        dark_palette.setColor(QPalette.AlternateBase, secondary_dark)
        dark_palette.setColor(QPalette.ToolTipBase, secondary_dark)
        dark_palette.setColor(QPalette.ToolTipText, text_color)
        dark_palette.setColor(QPalette.Text, text_color)
        dark_palette.setColor(QPalette.Disabled, QPalette.Text, disabled_color)
        dark_palette.setColor(QPalette.Button, secondary_dark)
        dark_palette.setColor(QPalette.ButtonText, text_color)
        dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_color)
        dark_palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Link, accent_color)
        dark_palette.setColor(QPalette.Highlight, accent_color)
        dark_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        QApplication.setPalette(dark_palette)
        
        # 设置全局样式表
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: #2d3241;
            }}
            QTabWidget::pane {{
                border: 2px solid #373e4e;
                border-radius: 8px;
                background-color: #373e4e;
                margin-top: -2px;
            }}
            QTabWidget::tab-bar {{
                alignment: center;
            }}
            QTabBar::tab {{
                background-color: #2d3241;
                color: #c8c8c8;
                padding: 14px 24px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 500;
                min-width: 90px;
                max-width: 140px;
                font-size: {self.get_scaled_font_size(18)}px;
            }}
            QTabBar::tab:selected {{
                background-color: #6495ed;
                color: white;
                font-weight: 600;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: #4a5268;
                color: white;
            }}
            QGroupBox {{
                font-weight: 600;
                border: 2px solid #5a6178;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 10px;
                background-color: rgba(90, 97, 120, 0.3);
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                color: #6495ed;
                font-size: {self.get_scaled_font_size(19)}px;
            }}
            QSpinBox, QDoubleSpinBox {{
                background-color: #40465a;
                border: 2px solid #5a6178;
                border-radius: 6px;
                padding: 12px;
                color: white;
                font-size: {self.get_scaled_font_size(18)}px;
                min-width: {int(100 * self.current_scale_factor)}px;
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border-color: #6495ed;
            }}
            QLabel {{
                color: #e0e0e0;
                font-size: {self.get_scaled_font_size(18)}px;
            }}
            QCheckBox {{
                color: #e0e0e0;
                font-size: {self.get_scaled_font_size(18)}px;
            }}
        """)
    
    
    def init_ui(self):
        """初始化现代化用户界面"""
        # 计算初始缩放因子
        self.current_scale_factor = self.calculate_scale_factor()
        
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局 - 使用更大的边距
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(15)
        
        # 创建标题栏
        self.create_header(main_layout)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        tab_widget.setFont(QFont("微软雅黑", self.get_scaled_font_size(18)))
        tab_widget.setMinimumHeight(500)
        # 禁用选项卡滚动，确保所有选项卡都可见
        tab_widget.setUsesScrollButtons(False)
        tab_widget.setElideMode(Qt.ElideNone)
        
        # 创建各个选项卡
        self.create_main_control_tab(tab_widget)
        self.create_left_settings_tab(tab_widget)
        self.create_right_settings_tab(tab_widget)
        self.create_about_tab(tab_widget)
        
        # 添加到主布局
        main_layout.addWidget(tab_widget)
        
        # 创建状态栏
        self.create_status_bar(main_layout)
        
        # 连接信号
        self.update_left_cps_signal.connect(self.update_left_cps_display)
        self.update_right_cps_signal.connect(self.update_right_cps_display)
        
        # 启动CPS计算定时器
        self.cps_timer = QTimer()
        self.cps_timer.timeout.connect(self.calculate_cps)
        self.cps_timer.start(100)  # 每100ms计算一次CPS
        
        # 初始检查配置合理性
        self.check_config_validity()
    
    def create_header(self, layout):
        """创建应用标题栏"""
        header_widget = QWidget()
        header_widget.setMaximumHeight(80)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # 左侧：应用图标和标题
        left_header = QWidget()
        left_layout = QHBoxLayout(left_header)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 应用标题
        title_label = QLabel("智能模拟点击器")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: {self.get_scaled_font_size(32)}px;
                font-weight: bold;
                color: #6495ed;
                margin: 0px;
            }}
        """)
        
        subtitle_label = QLabel("Professional Edition v2.0")
        subtitle_label.setStyleSheet(f"""
            QLabel {{
                font-size: {self.get_scaled_font_size(16)}px;
                color: #a0a0a0;
                margin: 0px;
            }}
        """)
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        left_layout.addLayout(title_layout)
        left_layout.addStretch()
        
        # 右侧：状态指示器
        self.status_indicator = QLabel("● 运行中")
        self.status_indicator.setStyleSheet(f"""
            QLabel {{
                font-size: {self.get_scaled_font_size(18)}px;
                font-weight: bold;
                color: #4CAF50;
                background-color: rgba(76, 175, 80, 0.1);
                border: 1px solid #4CAF50;
                border-radius: 15px;
                padding: 10px 18px;
            }}
        """)
        
        header_layout.addWidget(left_header)
        header_layout.addStretch()
        header_layout.addWidget(self.status_indicator)
        
        layout.addWidget(header_widget)
    
    def create_main_control_tab(self, tab_widget):
        """创建主控制面板选项卡"""
        main_tab = QWidget()
        main_layout = QVBoxLayout(main_tab)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 上半部分：控制面板
        control_row = QHBoxLayout()
        control_row.setSpacing(20)
        
        # 左列：辅助控制
        assist_control_group = self.create_assist_control_group()
        control_row.addWidget(assist_control_group, 1)
        
        # 右列：参数设置
        settings_group = self.create_settings_group()
        control_row.addWidget(settings_group, 1)
        
        main_layout.addLayout(control_row)
        
        # 下半部分：实时监控
        monitor_group = self.create_monitor_group()
        main_layout.addWidget(monitor_group)
        
        # 配置警告（使用滚动区域避免挤压）
        self.create_warning_section(main_layout)
        
        main_layout.addStretch()
        tab_widget.addTab(main_tab, "🏠 主控制面板")
    
    def create_assist_control_group(self):
        """创建辅助控制组"""
        group = QGroupBox("辅助模式控制")
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        
        # 状态显示
        self.assist_status_label = QLabel(f"状态：已启用 • 阈值：{self.assist_threshold} CPS • 延迟：{self.idle_timeout:.1f}s")
        self.assist_status_label.setStyleSheet(f"""
            QLabel {{
                font-size: {self.get_scaled_font_size(19)}px;
                color: #c8c8c8;
                background-color: #40465a;
                border-radius: 6px;
                padding: 12px 16px;
            }}
        """)
        layout.addWidget(self.assist_status_label)
        
        # 辅助模式开关按钮 - 更现代的设计
        self.assist_toggle_btn = QPushButton("🔴 关闭辅助模式")
        self.assist_toggle_btn.setMinimumHeight(int(55 * self.current_scale_factor))
        self.assist_toggle_btn.setFont(QFont("微软雅黑", self.get_scaled_font_size(17), QFont.Bold))
        self.set_button_style(self.assist_toggle_btn, enabled=True)
        self.assist_toggle_btn.clicked.connect(self.toggle_assist_mode)
        layout.addWidget(self.assist_toggle_btn)
        
        return group
    
    def create_settings_group(self):
        """创建设置组"""
        group = QGroupBox("参数配置")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # 阈值设置
        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("启动阈值:")
        threshold_label.setMinimumWidth(int(100 * self.current_scale_factor))
        threshold_label.setFont(QFont("微软雅黑", self.get_scaled_font_size(18)))
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(1, 20)
        self.threshold_spin.setValue(self.assist_threshold)
        self.threshold_spin.setSuffix(" CPS")
        self.threshold_spin.setFont(QFont("微软雅黑", self.get_scaled_font_size(18)))
        self.threshold_spin.valueChanged.connect(self.update_threshold)
        
        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self.threshold_spin)
        threshold_layout.addStretch()
        layout.addLayout(threshold_layout)
        
        # 停止延迟设置
        timeout_layout = QHBoxLayout()
        timeout_label = QLabel("停止延迟:")
        timeout_label.setMinimumWidth(int(100 * self.current_scale_factor))
        timeout_label.setFont(QFont("微软雅黑", self.get_scaled_font_size(18)))
        self.idle_timeout_spin = QDoubleSpinBox()
        self.idle_timeout_spin.setRange(0.1, 5.0)
        self.idle_timeout_spin.setValue(self.idle_timeout)
        self.idle_timeout_spin.setSingleStep(0.1)
        self.idle_timeout_spin.setSuffix(" 秒")
        self.idle_timeout_spin.setFont(QFont("微软雅黑", self.get_scaled_font_size(18)))
        self.idle_timeout_spin.valueChanged.connect(self.update_idle_timeout)
        
        timeout_layout.addWidget(timeout_label)
        timeout_layout.addWidget(self.idle_timeout_spin)
        timeout_layout.addStretch()
        layout.addLayout(timeout_layout)
        
        return group
    
    def create_monitor_group(self):
        """创建监控组"""
        group = QGroupBox("实时监控")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # CPS显示卡片
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        
        # 左键CPS卡片
        left_card = self.create_cps_card("左键", "#FF6B6B")
        self.left_cps_value = left_card.findChild(QLabel, "cps_value")
        self.left_cps_detail = left_card.findChild(QLabel, "cps_detail")
        self.left_cps_status = left_card.findChild(QLabel, "cps_status")
        cards_layout.addWidget(left_card)
        
        # 右键CPS卡片
        right_card = self.create_cps_card("右键", "#4ECDC4")
        self.right_cps_value = right_card.findChild(QLabel, "cps_value")
        self.right_cps_detail = right_card.findChild(QLabel, "cps_detail")
        self.right_cps_status = right_card.findChild(QLabel, "cps_status")
        cards_layout.addWidget(right_card)
        
        layout.addLayout(cards_layout)
        return group
    
    def create_cps_card(self, title, color):
        """创建CPS显示卡片"""
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(64, 70, 90, 0.8);
                border: 2px solid {color};
                border-radius: 10px;
                margin: 5px;
            }}
        """)
        card.setMinimumHeight(140)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(6)
        
        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: {self.get_scaled_font_size(20)}px;
                font-weight: bold;
                color: {color};
                margin: 0px;
            }}
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 总CPS数值
        cps_value = QLabel("0.0")
        cps_value.setObjectName("cps_value")
        cps_value.setStyleSheet(f"""
            QLabel {{
                font-size: {self.get_scaled_font_size(32)}px;
                font-weight: bold;
                color: white;
                margin: 0px;
            }}
        """)
        cps_value.setAlignment(Qt.AlignCenter)
        layout.addWidget(cps_value)
        
        # 详细CPS分解显示
        cps_detail = QLabel("(0.0)CPS + (0.0)CPS")
        cps_detail.setObjectName("cps_detail")
        cps_detail.setStyleSheet(f"""
            QLabel {{
                font-size: {self.get_scaled_font_size(15)}px;
                color: #b0b0b0;
                margin: 0px;
            }}
        """)
        cps_detail.setAlignment(Qt.AlignCenter)
        layout.addWidget(cps_detail)
        
        # 状态
        cps_status = QLabel("待机")
        cps_status.setObjectName("cps_status")
        cps_status.setStyleSheet(f"""
            QLabel {{
                font-size: {self.get_scaled_font_size(16)}px;
                color: #c8c8c8;
                margin: 0px;
            }}
        """)
        cps_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(cps_status)
        
        return card
    
    def create_warning_section(self, layout):
        """创建警告提示区域"""
        # 配置警告 - 使用可折叠的设计
        self.config_warning_label = QLabel("")
        self.config_warning_label.setFont(QFont("微软雅黑", self.get_scaled_font_size(16)))
        self.config_warning_label.setStyleSheet(f"""
            QLabel {{
                color: #FF9800;
                background-color: rgba(255, 152, 0, 0.1);
                border: 2px solid #FF9800;
                border-radius: 8px;
                padding: 16px 20px;
                margin: 5px 0px;
                font-size: {self.get_scaled_font_size(16)}px;
            }}
        """)
        self.config_warning_label.setWordWrap(True)
        self.config_warning_label.hide()
        layout.addWidget(self.config_warning_label)
    
    def set_button_style(self, button, enabled=True):
        """设置按钮样式"""
        if enabled:
            button.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #4CAF50, stop:1 #45a049);
                    border: none;
                    border-radius: 8px;
                    color: white;
                    font-weight: bold;
                    padding: 8px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #5CBF60, stop:1 #4CAF50);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #3d8b40, stop:1 #2e7d32);
                }
            """)
        else:
            button.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #f44336, stop:1 #da190b);
                    border: none;
                    border-radius: 8px;
                    color: white;
                    font-weight: bold;
                    padding: 8px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #f66356, stop:1 #f44336);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #b71c0c, stop:1 #8b0000);
                }
            """)
    

    
    def create_left_settings_tab(self, tab_widget):
        """创建左键设置选项卡"""
        left_tab = QWidget()
        layout = QVBoxLayout(left_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 左键设置组
        left_group = QGroupBox("左键辅助设置")
        left_group.setFont(QFont("微软雅黑", self.get_scaled_font_size(17), QFont.Bold))
        left_layout = QVBoxLayout(left_group)
        left_layout.setSpacing(15)
        
        # 启用状态
        self.left_enabled_cb = QCheckBox("启用左键辅助")
        self.left_enabled_cb.setChecked(True)
        self.left_enabled_cb.setFont(QFont("微软雅黑", self.get_scaled_font_size(16)))
        left_layout.addWidget(self.left_enabled_cb)
        
        # CPS范围设置
        cps_group = QGroupBox("目标CPS范围（手动+模拟总和）")
        cps_group.setFont(QFont("微软雅黑", self.get_scaled_font_size(16)))
        cps_layout = QVBoxLayout(cps_group)
        cps_layout.setSpacing(12)
        
        # 最大CPS设置
        max_cps_layout = QHBoxLayout()
        max_cps_label = QLabel("最大CPS:")
        max_cps_label.setMinimumWidth(int(90 * self.current_scale_factor))
        max_cps_label.setFont(QFont("微软雅黑", self.get_scaled_font_size(16)))
        
        self.left_max_cps_spin = QSpinBox()
        self.left_max_cps_spin.setRange(1, 50)
        self.left_max_cps_spin.setValue(self.left_max_cps)
        self.left_max_cps_spin.setSuffix(" CPS")
        self.left_max_cps_spin.setFont(QFont("微软雅黑", self.get_scaled_font_size(16)))
        self.left_max_cps_spin.valueChanged.connect(self.update_left_max_cps)
        
        max_cps_layout.addWidget(max_cps_label)
        max_cps_layout.addWidget(self.left_max_cps_spin)
        max_cps_layout.addStretch()
        cps_layout.addLayout(max_cps_layout)
        
        # 最小CPS设置
        min_cps_layout = QHBoxLayout()
        min_cps_label = QLabel("最小CPS:")
        min_cps_label.setMinimumWidth(int(90 * self.current_scale_factor))
        min_cps_label.setFont(QFont("微软雅黑", self.get_scaled_font_size(16)))
        
        self.left_min_cps_spin = QSpinBox()
        self.left_min_cps_spin.setRange(1, 50)
        self.left_min_cps_spin.setValue(self.left_min_cps)
        self.left_min_cps_spin.setSuffix(" CPS")
        self.left_min_cps_spin.setFont(QFont("微软雅黑", self.get_scaled_font_size(16)))
        self.left_min_cps_spin.valueChanged.connect(self.update_left_min_cps)
        
        min_cps_layout.addWidget(min_cps_label)
        min_cps_layout.addWidget(self.left_min_cps_spin)
        min_cps_layout.addStretch()
        cps_layout.addLayout(min_cps_layout)
        
        left_layout.addWidget(cps_group)
        
        # 添加说明
        desc_label = QLabel("左键辅助说明：\n• 当检测到用户左键点击频率超过设定阈值时自动启动\n• 总CPS（手动+模拟）将在设定的最大最小范围内随机浮动\n• 当用户停止点击超过设定延迟时间会自动停止")
        desc_label.setFont(QFont("微软雅黑", self.get_scaled_font_size(17)))
        desc_label.setStyleSheet(f"""
            QLabel {{
                color: #a0a0a0;
                background-color: #40465a;
                border-radius: 6px;
                padding: 16px;
                margin: 10px 0px;
                font-size: {self.get_scaled_font_size(17)}px;
            }}
        """)
        desc_label.setWordWrap(True)
        left_layout.addWidget(desc_label)
        
        layout.addWidget(left_group)
        layout.addStretch()
        
        tab_widget.addTab(left_tab, "⚙️ 左键设置")
    
    def create_right_settings_tab(self, tab_widget):
        """创建右键设置选项卡"""
        right_tab = QWidget()
        layout = QVBoxLayout(right_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 右键设置组
        right_group = QGroupBox("右键辅助设置")
        right_group.setFont(QFont("微软雅黑", self.get_scaled_font_size(17), QFont.Bold))
        right_layout = QVBoxLayout(right_group)
        right_layout.setSpacing(15)
        
        # 启用状态
        self.right_enabled_cb = QCheckBox("启用右键辅助")
        self.right_enabled_cb.setChecked(True)
        self.right_enabled_cb.setFont(QFont("微软雅黑", self.get_scaled_font_size(16)))
        right_layout.addWidget(self.right_enabled_cb)
        
        # CPS范围设置
        cps_group = QGroupBox("目标CPS范围（手动+模拟总和）")
        cps_group.setFont(QFont("微软雅黑", self.get_scaled_font_size(16)))
        cps_layout = QVBoxLayout(cps_group)
        cps_layout.setSpacing(12)
        
        # 最大CPS设置
        max_cps_layout = QHBoxLayout()
        max_cps_label = QLabel("最大CPS:")
        max_cps_label.setMinimumWidth(int(90 * self.current_scale_factor))
        max_cps_label.setFont(QFont("微软雅黑", self.get_scaled_font_size(16)))
        
        self.right_max_cps_spin = QSpinBox()
        self.right_max_cps_spin.setRange(1, 50)
        self.right_max_cps_spin.setValue(self.right_max_cps)
        self.right_max_cps_spin.setSuffix(" CPS")
        self.right_max_cps_spin.setFont(QFont("微软雅黑", self.get_scaled_font_size(16)))
        self.right_max_cps_spin.valueChanged.connect(self.update_right_max_cps)
        
        max_cps_layout.addWidget(max_cps_label)
        max_cps_layout.addWidget(self.right_max_cps_spin)
        max_cps_layout.addStretch()
        cps_layout.addLayout(max_cps_layout)
        
        # 最小CPS设置
        min_cps_layout = QHBoxLayout()
        min_cps_label = QLabel("最小CPS:")
        min_cps_label.setMinimumWidth(int(90 * self.current_scale_factor))
        min_cps_label.setFont(QFont("微软雅黑", self.get_scaled_font_size(16)))
        
        self.right_min_cps_spin = QSpinBox()
        self.right_min_cps_spin.setRange(1, 50)
        self.right_min_cps_spin.setValue(self.right_min_cps)
        self.right_min_cps_spin.setSuffix(" CPS")
        self.right_min_cps_spin.setFont(QFont("微软雅黑", self.get_scaled_font_size(16)))
        self.right_min_cps_spin.valueChanged.connect(self.update_right_min_cps)
        
        min_cps_layout.addWidget(min_cps_label)
        min_cps_layout.addWidget(self.right_min_cps_spin)
        min_cps_layout.addStretch()
        cps_layout.addLayout(min_cps_layout)
        
        right_layout.addWidget(cps_group)
        
        # 添加说明
        desc_label = QLabel("右键辅助说明：\n• 当检测到用户右键点击频率超过设定阈值时自动启动\n• 总CPS（手动+模拟）将在设定的最大最小范围内随机浮动\n• 当用户停止点击超过设定延迟时间会自动停止")
        desc_label.setFont(QFont("微软雅黑", self.get_scaled_font_size(17)))
        desc_label.setStyleSheet(f"""
            QLabel {{
                color: #a0a0a0;
                background-color: #40465a;
                border-radius: 6px;
                padding: 16px;
                margin: 10px 0px;
                font-size: {self.get_scaled_font_size(17)}px;
            }}
        """)
        desc_label.setWordWrap(True)
        right_layout.addWidget(desc_label)
        
        layout.addWidget(right_group)
        layout.addStretch()
        
        tab_widget.addTab(right_tab, "⚙️ 右键设置")
    
    def create_about_tab(self, tab_widget):
        """创建关于选项卡"""
        about_tab = QWidget()
        layout = QVBoxLayout(about_tab)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 应用信息
        app_info_group = QGroupBox("应用信息")
        app_info_layout = QVBoxLayout(app_info_group)
        app_info_layout.setSpacing(10)
        
        # 应用名称和版本
        app_title = QLabel("智能模拟点击器 Half Auto Clicker")
        app_title.setFont(QFont("微软雅黑", self.get_scaled_font_size(22), QFont.Bold))
        app_title.setAlignment(Qt.AlignCenter)
        app_title.setStyleSheet("color: #6495ed; margin: 10px;")
        app_info_layout.addWidget(app_title)
        
        version_label = QLabel("版本：v2.0.0")
        version_label.setFont(QFont("微软雅黑", self.get_scaled_font_size(16)))
        version_label.setAlignment(Qt.AlignCenter)
        app_info_layout.addWidget(version_label)
        
        # GitHub地址
        github_label = QLabel("GitHub: https://github.com/lixu10/Auto-Click")
        github_label.setFont(QFont("微软雅黑", self.get_scaled_font_size(16)))
        github_label.setAlignment(Qt.AlignCenter)
        github_label.setStyleSheet("color: #6495ed; margin: 8px;")
        github_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        app_info_layout.addWidget(github_label)
        
        # 功能特性
        features_text = """
        🎯 智能检测：自动识别用户点击模式
        ⚡ 实时辅助：根据CPS阈值智能启动
        🔧 参数可调：支持自定义阈值和延迟
        📊 实时监控：显示左右键CPS数据
        🎨 现代界面：采用专业级UI设计
        🛡️ 稳定可靠：优化算法确保准确性
        """
        
        features_label = QLabel(features_text)
        features_label.setFont(QFont("微软雅黑", self.get_scaled_font_size(16)))
        features_label.setStyleSheet(f"""
            QLabel {{
                background-color: #40465a;
                border-radius: 8px;
                padding: 18px;
                color: #e0e0e0;
                line-height: 1.5;
                font-size: {self.get_scaled_font_size(16)}px;
            }}
        """)
        features_label.setWordWrap(True)
        app_info_layout.addWidget(features_label)
        
        layout.addWidget(app_info_group)
        layout.addStretch()
        
        # 版权信息
        copyright_label = QLabel("版权所有 © 2024-2025 智能模拟点击器团队")
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setFont(QFont("微软雅黑", self.get_scaled_font_size(15)))
        copyright_label.setStyleSheet("color: #a0a0a0; margin: 10px;")
        layout.addWidget(copyright_label)
        
        tab_widget.addTab(about_tab, "ℹ️ 关于")
    
    def create_status_bar(self, layout):
        """创建状态栏"""
        status_widget = QWidget()
        status_widget.setMaximumHeight(50)
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(10, 8, 10, 8)
        
        # 版本信息
        version_label = QLabel("v2.0.0")
        version_label.setFont(QFont("微软雅黑", self.get_scaled_font_size(18)))
        version_label.setStyleSheet("color: #6495ed; font-weight: bold;")
        
        status_layout.addStretch()
        status_layout.addWidget(version_label)
        
        layout.addWidget(status_widget)
    
    def calculate_cps(self):
        """计算并更新CPS显示"""
        current_time = time.time()
        
        # 清理超过1秒的点击记录
        self.left_click_times = [t for t in self.left_click_times if current_time - t <= 1.0]
        self.right_click_times = [t for t in self.right_click_times if current_time - t <= 1.0]
        self.user_left_click_times = [t for t in self.user_left_click_times if current_time - t <= 1.0]
        self.user_right_click_times = [t for t in self.user_right_click_times if current_time - t <= 1.0]
        
        # 计算真实的CPS（基于时间间隔）
        left_cps = self.calculate_real_cps(self.left_click_times)
        right_cps = self.calculate_real_cps(self.right_click_times)
        
        # 更新显示
        self.update_left_cps_signal.emit(left_cps, 0)
        self.update_right_cps_signal.emit(right_cps, 0)
    
    def calculate_real_cps(self, click_times):
        """计算真实的CPS - 使用更稳定的计算方法"""
        if len(click_times) == 0:
            return 0.0
        
        current_time = time.time()
        # 只考虑最近1.5秒内的点击，增加统计窗口
        recent_clicks = [t for t in click_times if current_time - t <= 1.5]
        
        if len(recent_clicks) <= 1:
            return len(recent_clicks)
        
        # 使用最近1秒内的点击数量进行计算，更稳定
        recent_1s_clicks = [t for t in recent_clicks if current_time - t <= 1.0]
        if len(recent_1s_clicks) >= 2:
            return len(recent_1s_clicks)
        else:
            # 如果1秒内点击数少于2，使用时间跨度计算
            time_span = recent_clicks[-1] - recent_clicks[0]
            if time_span > 0:
                return (len(recent_clicks) - 1) / time_span
            else:
                return len(recent_clicks)
    
    def toggle_left_clicking(self):
        """已移除 - 不再使用"""
        pass
    
    def toggle_right_clicking(self):
        """已移除 - 不再使用"""
        pass
    
    def toggle_mouse_side_buttons(self, state):
        """已移除 - 不再使用"""
        pass
    
    def update_left_max_cps(self, value):
        """更新左键最大CPS值"""
        self.left_max_cps = value
        # 确保最小CPS不大于最大CPS
        if self.left_min_cps > value:
            self.left_min_cps = value
            self.left_min_cps_spin.setValue(value)
        # 触发配置合理性检查
        self.check_config_validity()
    
    def update_left_min_cps(self, value):
        """更新左键最小CPS值"""
        self.left_min_cps = value
        # 确保最大CPS不小于最小CPS
        if self.left_max_cps < value:
            self.left_max_cps = value
            self.left_max_cps_spin.setValue(value)
        # 触发配置合理性检查
        self.check_config_validity()
    
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
        # 触发配置合理性检查
        self.check_config_validity()
    
    def update_right_min_cps(self, value):
        """更新右键最小CPS值"""
        self.right_min_cps = value
        # 确保最大CPS不小于最小CPS
        if self.right_max_cps < value:
            self.right_max_cps = value
            self.right_max_cps_spin.setValue(value)
        # 触发配置合理性检查
        self.check_config_validity()
    
    def update_right_jitter(self, value):
        """更新右键抖动范围"""
        self.right_jitter_range = value
    
    def update_idle_timeout(self, value):
        """更新空闲超时时间"""
        self.idle_timeout = value
        self.update_status_label()
        self.check_config_validity()
    
    def update_threshold(self, value):
        """更新辅助启动阈值"""
        self.assist_threshold = value
        self.update_status_label()
        self.check_config_validity()
    
    def check_config_validity(self):
        """检查配置参数的合理性并显示警告"""
        # 计算阈值CPS对应的最小点击间隔
        min_click_interval = 1.0 / self.assist_threshold if self.assist_threshold > 0 else 0
        
        # 检查停止延迟是否合适
        if self.idle_timeout < min_click_interval:
            # 建议的停止延迟应该是点击间隔的1.5-2倍，确保不会误判
            suggested_timeout = min_click_interval * 1.8
            warning_text = (f"⚠️ 配置警告：当前停止延迟({self.idle_timeout:.1f}秒) 小于阈值CPS的点击间隔"
                          f"({min_click_interval:.2f}秒)，可能导致辅助频繁启停。\n"
                          f"建议停止延迟设置为 {suggested_timeout:.1f}秒 或更大。")
            self.config_warning_label.setText(warning_text)
            self.config_warning_label.show()
        else:
            # 配置合理，隐藏警告
            self.config_warning_label.hide()
    
    def toggle_assist_mode(self):
        """切换辅助模式开关"""
        with lock:
            self.assist_mode_active = not self.assist_mode_active
        
        if self.assist_mode_active:
            self.assist_toggle_btn.setText("关闭辅助模式")
            self.assist_toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    border: 2px solid #45a049;
                    border-radius: 5px;
                    padding: 8px;
                    color: white;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """)
        else:
            self.assist_toggle_btn.setText("开启辅助模式")
            self.assist_toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    border: 2px solid #da190b;
                    border-radius: 5px;
                    padding: 8px;
                    color: white;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #da190b;
                }
                QPushButton:pressed {
                    background-color: #b71c0c;
                }
            """)
        
        self.update_status_label()
    
    def is_user_actively_clicking(self, button_type='left'):
        """更智能的用户活动检测"""
        current_time = time.time()
        
        if button_type == 'left':
            last_click_time = self.last_user_left_click
            user_clicks = self.user_left_click_times
        else:
            last_click_time = self.last_user_right_click
            user_clicks = self.user_right_click_times
        
        # 基本超时检查
        basic_timeout_check = (current_time - last_click_time) <= self.idle_timeout
        
        # 如果基本检查失败，进行更智能的检查
        if not basic_timeout_check:
            # 检查最近是否有持续的点击活动
            recent_clicks = [t for t in user_clicks if current_time - t <= (self.idle_timeout * 3)]
            if len(recent_clicks) >= 2:
                # 如果最近有多次点击，适当放宽超时限制
                extended_timeout = self.idle_timeout * 1.5
                return (current_time - last_click_time) <= extended_timeout
        
        return basic_timeout_check
    
    def update_status_label(self):
        """更新状态标签显示"""
        mode_text = "已启用" if self.assist_mode_active else "已关闭"
        if hasattr(self, 'assist_status_label'):
            self.assist_status_label.setText(f"状态：{mode_text} • 阈值：{self.assist_threshold} CPS • 延迟：{self.idle_timeout:.1f}s")
    
    def toggle_assist_mode(self):
        """切换辅助模式"""
        self.assist_mode_active = not self.assist_mode_active
        
        if self.assist_mode_active:
            self.assist_toggle_btn.setText("🔴 关闭辅助模式")
            self.set_button_style(self.assist_toggle_btn, enabled=True)
            if hasattr(self, 'status_indicator'):
                self.status_indicator.setText("● 运行中")
                self.status_indicator.setStyleSheet("""
                    QLabel {
                        font-size: 14px;
                        font-weight: bold;
                        color: #4CAF50;
                        background-color: rgba(76, 175, 80, 0.1);
                        border: 1px solid #4CAF50;
                        border-radius: 15px;
                        padding: 8px 16px;
                    }
                """)
        else:
            self.assist_toggle_btn.setText("🟢 启用辅助模式")
            self.set_button_style(self.assist_toggle_btn, enabled=False)
            if hasattr(self, 'status_indicator'):
                self.status_indicator.setText("● 已暂停")
                self.status_indicator.setStyleSheet("""
                    QLabel {
                        font-size: 14px;
                        font-weight: bold;
                        color: #f44336;
                        background-color: rgba(244, 67, 54, 0.1);
                        border: 1px solid #f44336;
                        border-radius: 15px;
                        padding: 8px 16px;
                    }
                """)
        
        # 更新状态标签
        self.update_status_label()
    
    def update_threshold(self, value):
        """更新阈值"""
        self.assist_threshold = value
        self.update_status_label()
        self.check_config_validity()
    
    def update_idle_timeout(self, value):
        """更新空闲超时"""
        self.idle_timeout = value
        self.update_status_label()
        self.check_config_validity()
    
    def update_left_cps_display(self, current_cps, target_cps):
        """更新左键CPS显示"""
        # 计算用户CPS和辅助CPS
        user_cps = self.calculate_real_cps(self.user_left_click_times)
        total_cps = self.calculate_real_cps(self.left_click_times)
        assist_cps = max(0, total_cps - user_cps)
        
        # 更新总CPS数值
        if hasattr(self, 'left_cps_value') and self.left_cps_value:
            self.left_cps_value.setText(f"{total_cps:.1f}")
        
        # 更新详细CPS分解显示
        if hasattr(self, 'left_cps_detail') and self.left_cps_detail:
            self.left_cps_detail.setText(f"真实({user_cps:.1f}) + 模拟({assist_cps:.1f})")
        
        # 更新状态
        if hasattr(self, 'left_cps_status') and self.left_cps_status:
            if not self.assist_mode_active:
                status = "辅助模式已关闭"
            elif user_cps > self.assist_threshold and self.is_user_actively_clicking('left'):
                status = "辅助中"
            elif user_cps > self.assist_threshold and not self.is_user_actively_clicking('left'):
                status = "用户停止点击"
            else:
                status = "待机"
            self.left_cps_status.setText(status)
    
    def update_right_cps_display(self, current_cps, target_cps):
        """更新右键CPS显示"""
        # 计算用户CPS和辅助CPS
        user_cps = self.calculate_real_cps(self.user_right_click_times)
        total_cps = self.calculate_real_cps(self.right_click_times)
        assist_cps = max(0, total_cps - user_cps)
        
        # 更新总CPS数值  
        if hasattr(self, 'right_cps_value') and self.right_cps_value:
            self.right_cps_value.setText(f"{total_cps:.1f}")
        
        # 更新详细CPS分解显示
        if hasattr(self, 'right_cps_detail') and self.right_cps_detail:
            self.right_cps_detail.setText(f"真实({user_cps:.1f}) + 模拟({assist_cps:.1f})")
            
        # 更新状态
        if hasattr(self, 'right_cps_status') and self.right_cps_status:
            if not self.assist_mode_active:
                status = "辅助模式已关闭"
            elif user_cps > self.assist_threshold and self.is_user_actively_clicking('right'):
                status = "辅助中"
            elif user_cps > self.assist_threshold and not self.is_user_actively_clicking('right'):
                status = "用户停止点击"
            else:
                status = "待机"
            self.right_cps_status.setText(status)
    
    def start_threads(self):
        """启动辅助点击线程"""
        # 左键辅助点击线程
        self.left_assist_thread = threading.Thread(target=self.left_assist_clicker)
        self.left_assist_thread.daemon = True
        self.left_assist_thread.start()
        
        # 右键辅助点击线程
        self.right_assist_thread = threading.Thread(target=self.right_assist_clicker)
        self.right_assist_thread.daemon = True
        self.right_assist_thread.start()
    
    def start_mouse_listener(self):
        """启动鼠标监听器（仅用于检测点击频率）"""
        self.mouse_listener = ms.Listener(on_click=self.on_mouse_click)
        self.mouse_listener.daemon = True
        self.mouse_listener.start()
    
    def on_mouse_click(self, x, y, button, pressed):
        """处理鼠标点击事件 - 仅记录点击时间用于CPS计算"""
        if not pressed:  # 跳过释放事件，只处理按下事件
            return
        
        # 如果是辅助点击，忽略此事件
        if self.is_assist_clicking:
            return
            
        current_time = time.time()
        
        # 记录左键点击时间
        if button == ms.Button.left:
            self.left_click_times.append(current_time)
            self.user_left_click_times.append(current_time)  # 单独记录用户点击
            self.left_button_held = True
            self.last_user_left_click = current_time  # 记录用户最后一次左键点击时间
                    
        # 记录右键点击时间
        elif button == ms.Button.right:
            self.right_click_times.append(current_time)
            self.user_right_click_times.append(current_time)  # 单独记录用户点击
            self.right_button_held = True
            self.last_user_right_click = current_time  # 记录用户最后一次右键点击时间
    
    def left_assist_clicker(self):
        """左键辅助点击线程 - 当CPS超过阈值且用户在持续点击时提供辅助"""
        last_assist_time = 0
        assist_interval = 0.05  # 辅助点击的基本间隔
        target_cps = self.left_min_cps  # 初始目标CPS
        cps_change_time = time.time()  # CPS变化时间
        cps_change_interval = random.uniform(0.5, 2.0)  # CPS变化间隔
        
        while True:
            if self.assist_mode_active and self.left_enabled_cb.isChecked():
                current_time = time.time()
                
                # 定期更新目标CPS，在设定范围内随机浮动
                if current_time - cps_change_time >= cps_change_interval:
                    target_cps = random.uniform(self.left_min_cps, self.left_max_cps)
                    cps_change_time = current_time
                    cps_change_interval = random.uniform(0.5, 2.0)  # 下次变化间隔
                
                # 计算当前用户左键CPS（不包含辅助点击）
                user_cps = self.calculate_real_cps(self.user_left_click_times)
                
                # 更智能的用户活动检测
                user_still_clicking = self.is_user_actively_clicking('left')
                
                # 如果用户CPS超过阈值且用户仍在点击，提供辅助点击
                if user_cps > self.assist_threshold and user_still_clicking:
                    # 计算需要的辅助CPS，确保总CPS达到目标
                    assist_cps = target_cps - user_cps
                    
                    # 确保辅助CPS为正数且不超过合理范围
                    if assist_cps > 0 and assist_cps <= 40:
                        # 计算辅助点击间隔
                        assist_interval = 1.0 / assist_cps
                        
                        # 检查是否到了下次辅助点击的时间
                        if current_time - last_assist_time >= assist_interval:
                            with lock:
                                # 设置辅助点击标志，防止被监听器捕获
                                self.is_assist_clicking = True
                                
                                # 执行辅助点击（不移动鼠标位置）
                                self.mouse_controller.click(ms.Button.left)
                                
                                # 记录辅助点击到总点击列表（但不记录到用户点击列表）
                                self.left_click_times.append(current_time)
                                
                                # 清除辅助点击标志
                                self.is_assist_clicking = False
                            last_assist_time = current_time
            time.sleep(0.005)  # 更高精度的睡眠时间
    
    def right_assist_clicker(self):
        """右键辅助点击线程 - 当CPS超过阈值且用户在持续点击时提供辅助"""
        last_assist_time = 0
        assist_interval = 0.05  # 辅助点击的基本间隔
        target_cps = self.right_min_cps  # 初始目标CPS
        cps_change_time = time.time()  # CPS变化时间
        cps_change_interval = random.uniform(0.5, 2.0)  # CPS变化间隔
        
        while True:
            if self.assist_mode_active and self.right_enabled_cb.isChecked():
                current_time = time.time()
                
                # 定期更新目标CPS，在设定范围内随机浮动
                if current_time - cps_change_time >= cps_change_interval:
                    target_cps = random.uniform(self.right_min_cps, self.right_max_cps)
                    cps_change_time = current_time
                    cps_change_interval = random.uniform(0.5, 2.0)  # 下次变化间隔
                
                # 计算当前用户右键CPS（不包含辅助点击）
                user_cps = self.calculate_real_cps(self.user_right_click_times)
                
                # 更智能的用户活动检测
                user_still_clicking = self.is_user_actively_clicking('right')
                
                # 如果用户CPS超过阈值且用户仍在点击，提供辅助点击
                if user_cps > self.assist_threshold and user_still_clicking:
                    # 计算需要的辅助CPS，确保总CPS达到目标
                    assist_cps = target_cps - user_cps
                    
                    # 确保辅助CPS为正数且不超过合理范围
                    if assist_cps > 0 and assist_cps <= 40:
                        # 计算辅助点击间隔
                        assist_interval = 1.0 / assist_cps
                        
                        # 检查是否到了下次辅助点击的时间
                        if current_time - last_assist_time >= assist_interval:
                            with lock:
                                # 设置辅助点击标志，防止被监听器捕获
                                self.is_assist_clicking = True
                                
                                # 执行辅助点击（不移动鼠标位置）
                                self.mouse_controller.click(ms.Button.right)
                                
                                # 记录辅助点击到总点击列表（但不记录到用户点击列表）
                                self.right_click_times.append(current_time)
                                
                                # 清除辅助点击标志
                                self.is_assist_clicking = False
                            last_assist_time = current_time
            time.sleep(0.005)  # 更高精度的睡眠时间
    
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        # 停止辅助模式
        with lock:
            self.assist_mode_active = False
        
        # 接受关闭事件
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AutoClickerGUI()
    window.show()
    sys.exit(app.exec_())