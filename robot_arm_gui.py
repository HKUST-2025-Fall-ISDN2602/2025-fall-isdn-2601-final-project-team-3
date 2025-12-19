"""
ISDN 2601 机械臂 GUI 控制界面
通过串口实时控制 ESP8266 + 5舵机机械臂
支持游戏手柄控制和调试模式
"""

import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import threading
import time
import pygame
import math
import csv
import os
from datetime import datetime

class RobotArmGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ISDN 2601 机械臂控制台 - 支持游戏手柄")
        self.root.geometry("1200x900")
        self.root.resizable(False, False)
        
        # 串口连接
        self.serial_port = None
        self.is_connected = False
        self.reading_thread = None
        self.running = False
        
        # 调试模式
        self.debug_mode = True
        
        # 当前舵机位置
        self.positions = {
            'servo1': 90,  # Wrist
            'servo2': 90,  # Base
            'servo3': 90,  # Shoulder
            'servo4': 90,  # Elbow
            'servo5': 90   # Gripper
        }
        
        # 游戏手柄
        self.joystick = None
        self.joystick_thread = None
        self.joystick_running = False
        self.last_commands = []  # 存储最近的指令
        
        # 路径管理
        self.paths = {}  # {path_name: [(s1, s2, s3, s4, s5), ...]}
        self.current_path_name = None
        self.recording = False
        self.paths_dir = "robot_arm_paths"
        
        # 确保路径目录存在
        if not os.path.exists(self.paths_dir):
            os.makedirs(self.paths_dir)
        
        # 初始化pygame
        pygame.init()
        pygame.joystick.init()
        
        self.setup_ui()
        self.refresh_ports()
        self.detect_joystick()
        # 移到setup_ui之后调用，避免UI组件未初始化的问题
        self.load_existing_paths()
        
    def setup_ui(self):
        # ===== 串口连接区域 =====
        connection_frame = ttk.LabelFrame(self.root, text="串口连接", padding=10)
        connection_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        
        ttk.Label(connection_frame, text="端口:").grid(row=0, column=0, padx=5)
        self.port_combo = ttk.Combobox(connection_frame, width=15, state="readonly")
        self.port_combo.grid(row=0, column=1, padx=5)
        
        ttk.Button(connection_frame, text="刷新", command=self.refresh_ports).grid(row=0, column=2, padx=5)
        
        self.connect_btn = ttk.Button(connection_frame, text="连接", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=3, padx=5)
        
        self.status_label = ttk.Label(connection_frame, text="未连接", foreground="red")
        self.status_label.grid(row=0, column=4, padx=10)
        
        # 调试模式复选框
        self.debug_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(connection_frame, text="调试模式", variable=self.debug_var, 
                       command=self.toggle_debug_mode).grid(row=0, column=5, padx=10)
        
        # ===== 游戏手柄状态区域 =====
        joystick_frame = ttk.LabelFrame(self.root, text="游戏手柄状态", padding=10)
        joystick_frame.grid(row=0, column=3, padx=10, pady=10, sticky="ew")
        
        self.joystick_status_label = ttk.Label(joystick_frame, text="未检测到手柄", foreground="red")
        self.joystick_status_label.pack(pady=5)
        
        ttk.Button(joystick_frame, text="检测手柄", command=self.detect_joystick).pack(pady=5)
        
        # ===== 舵机控制区域 =====
        control_frame = ttk.LabelFrame(self.root, text="舵机控制", padding=10)
        control_frame.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky="ew")
        
        servos = [
            ("Servo2 - 底座 (Base)", "servo2", 0),
            ("Servo3 - 肩部 (Shoulder)", "servo3", 1),
            ("Servo4 - 肘部 (Elbow)", "servo4", 2),
            ("Servo1 - 腕部 (Wrist)", "servo1", 3),
            ("Servo5 - 夹爪 (Gripper)", "servo5", 4)
        ]
        
        self.sliders = {}
        self.angle_labels = {}
        
        for label, key, row in servos:
            ttk.Label(control_frame, text=label, width=25).grid(row=row, column=0, padx=5, pady=5, sticky="w")
            
            slider = ttk.Scale(control_frame, from_=0, to=180, orient="horizontal", length=300,
                             command=lambda val, k=key: self.on_slider_change(k, val))
            slider.set(90)
            slider.grid(row=row, column=1, padx=5, pady=5)
            self.sliders[key] = slider
            
            angle_label = ttk.Label(control_frame, text="90°", width=8, font=("Arial", 12, "bold"))
            angle_label.grid(row=row, column=2, padx=5, pady=5)
            self.angle_labels[key] = angle_label
            
            # -5° 和 +5° 按钮
            ttk.Button(control_frame, text="-5°", width=5,
                      command=lambda k=key: self.adjust_angle(k, -5)).grid(row=row, column=3, padx=2)
            ttk.Button(control_frame, text="+5°", width=5,
                      command=lambda k=key: self.adjust_angle(k, 5)).grid(row=row, column=4, padx=2)
        
        # ===== 快捷按钮区域 =====
        quick_frame = ttk.LabelFrame(self.root, text="快捷操作", padding=10)
        quick_frame.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky="ew")
        
        btn_config = [
            ("重置 (90°)", self.reset_all, 0, 0),
            ("打开夹爪", self.open_gripper, 0, 1),
            ("关闭夹爪", self.close_gripper, 0, 2),
            ("保存位置", self.save_position, 0, 3),
            ("发送全部", self.send_all_positions, 1, 0),
            ("停止", self.emergency_stop, 1, 1),
        ]
        
        for text, command, row, col in btn_config:
            ttk.Button(quick_frame, text=text, command=command, width=15).grid(
                row=row, column=col, padx=5, pady=5)
        
        # 游戏手柄控制区域
        gamepad_frame = ttk.LabelFrame(self.root, text="游戏手柄控制", padding=10)
        gamepad_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        
        # 摇杆映射说明
        ttk.Label(gamepad_frame, text="左摇杆: 前后控制腕部", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=2, pady=5)
        ttk.Label(gamepad_frame, text="右摇杆: 前后控制肘部", font=("Arial", 10, "bold")).grid(row=1, column=0, columnspan=2, pady=5)
        ttk.Label(gamepad_frame, text="十字键: 上下控制肩部，左右控制底座", font=("Arial", 10, "bold")).grid(row=2, column=0, columnspan=2, pady=5)
        ttk.Label(gamepad_frame, text="A键: 连续增加夹爪角度 (张开)", font=("Arial", 10)).grid(row=3, column=0, pady=2)
        ttk.Label(gamepad_frame, text="B键: 连续减少夹爪角度 (闭合)", font=("Arial", 10)).grid(row=3, column=1, pady=2)
        
        # 游戏手柄控制按钮
        ttk.Button(gamepad_frame, text="启动手柄控制", command=self.start_joystick_control).grid(row=4, column=0, pady=10)
        ttk.Button(gamepad_frame, text="停止手柄控制", command=self.stop_joystick_control).grid(row=4, column=1, pady=10)
        
        # ===== WASD 键盘控制区域 =====
        keyboard_frame = ttk.LabelFrame(self.root, text="键盘控制 (点击按钮或按键盘)", padding=10)
        keyboard_frame.grid(row=3, column=2, columnspan=2, padx=10, pady=10, sticky="ew")
        
        # 创建键盘布局
        keyboard_layout = [
            [None, "Q\n肘部↑", "W\n肩部↑", "E\n肘部↓", None, None, "[\n打开夹爪"],
            [None, "A\n底座←", "S\n肩部↓", "D\n底座→", None, None, "]\n关闭夹爪"],
            [None, "Z\n腕部↑", "X\n腕部↓", None, None, None, None]
        ]
        
        key_commands = {
            'Q': 'q', 'W': 'w', 'E': 'e', 'A': 'a', 'S': 's', 'D': 'd',
            'Z': 'z', 'X': 'x', '[': '[', ']': ']'
        }
        
        for row_idx, row in enumerate(keyboard_layout):
            for col_idx, key in enumerate(row):
                if key:
                    key_char = key.split('\n')[0]
                    btn = tk.Button(keyboard_frame, text=key, width=10, height=3,
                                  command=lambda k=key_char: self.send_keyboard_command(key_commands[k]))
                    btn.grid(row=row_idx, column=col_idx, padx=3, pady=3)
        
        # 绑定键盘事件
        self.root.bind('<Key>', self.on_key_press)
        
        # ===== 路径管理器区域 =====
        path_frame = ttk.LabelFrame(self.root, text="路径管理器 (Path Manager)", padding=10)
        path_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        # 路径列表
        path_list_frame = tk.Frame(path_frame)
        path_list_frame.pack(fill="both", expand=True, pady=5)
        
        ttk.Label(path_list_frame, text="已保存的路径:").pack(anchor="w")
        
        self.path_listbox = tk.Listbox(path_list_frame, height=8, width=30)
        self.path_listbox.pack(side="left", fill="both", expand=True)
        self.path_listbox.bind('<<ListboxSelect>>', self.on_path_select)
        
        path_scrollbar = ttk.Scrollbar(path_list_frame, command=self.path_listbox.yview)
        path_scrollbar.pack(side="right", fill="y")
        self.path_listbox.config(yscrollcommand=path_scrollbar.set)
        
        # 路径操作按钮
        path_btn_frame = tk.Frame(path_frame)
        path_btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(path_btn_frame, text="新建路径", command=self.create_new_path).pack(side="left", padx=2)
        ttk.Button(path_btn_frame, text="删除路径", command=self.delete_path).pack(side="left", padx=2)
        ttk.Button(path_btn_frame, text="重命名", command=self.rename_path).pack(side="left", padx=2)
        
        # 路径状态
        self.path_status_label = ttk.Label(path_frame, text="未选择路径", foreground="gray")
        self.path_status_label.pack(pady=5)
        
        # 手柄控制说明
        control_info = tk.Frame(path_frame, bg="#e8f4f8", relief="ridge", bd=2)
        control_info.pack(fill="x", pady=5)
        
        ttk.Label(control_info, text="🎮 手柄路径控制:", font=("Arial", 9, "bold"), background="#e8f4f8").pack(anchor="w", padx=5, pady=2)
        ttk.Label(control_info, text="LB键: 记录当前位置到路径", background="#e8f4f8").pack(anchor="w", padx=15)
        ttk.Label(control_info, text="RB键: 停止记录", background="#e8f4f8").pack(anchor="w", padx=15)
        ttk.Label(control_info, text="Y键: 执行路径 (Reset→Path→Reset)", background="#e8f4f8").pack(anchor="w", padx=15)
        ttk.Label(control_info, text="X键: Reset所有舵机到90°", background="#e8f4f8").pack(anchor="w", padx=15)
        
        # ===== 指令显示区域 =====
        command_frame = ttk.LabelFrame(self.root, text="发送指令历史", padding=10)
        command_frame.grid(row=4, column=2, padx=10, pady=10, sticky="nsew")
        
        self.command_text = tk.Text(command_frame, height=8, width=40, state="disabled", bg="#f0f0f0")
        self.command_text.pack(side="left", fill="both", expand=True)
        
        command_scrollbar = ttk.Scrollbar(command_frame, command=self.command_text.yview)
        command_scrollbar.pack(side="right", fill="y")
        self.command_text.config(yscrollcommand=command_scrollbar.set)
        
        # ===== 串口日志区域 =====
        log_frame = ttk.LabelFrame(self.root, text="串口日志", padding=10)
        log_frame.grid(row=4, column=3, padx=10, pady=10, sticky="nsew")
        
        self.log_text = tk.Text(log_frame, height=8, width=40, state="disabled")
        self.log_text.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 配置网格权重
        self.root.grid_rowconfigure(4, weight=1)
        
    def refresh_ports(self):
        """刷新可用串口列表"""
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        self.port_combo['values'] = port_list
        if port_list:
            self.port_combo.current(0)
            
    def toggle_connection(self):
        """切换串口连接状态"""
        if not self.is_connected:
            self.connect()
        else:
            self.disconnect()
            
    def connect(self):
        """连接串口"""
        port = self.port_combo.get()
        if not port:
            messagebox.showerror("错误", "请选择串口")
            return
            
        try:
            self.serial_port = serial.Serial(port, 115200, timeout=1)
            time.sleep(2)  # 等待ESP8266重启
            self.is_connected = True
            self.connect_btn.config(text="断开")
            self.status_label.config(text=f"已连接 {port}", foreground="green")
            self.log(f"成功连接到 {port}")
            
            # 启动读取线程
            self.running = True
            self.reading_thread = threading.Thread(target=self.read_serial, daemon=True)
            self.reading_thread.start()
            
            # 发送 status 命令获取当前位置
            time.sleep(0.5)
            self.send_command("status")
            
        except Exception as e:
            messagebox.showerror("连接失败", f"无法连接到 {port}\n错误: {str(e)}")
            
    def disconnect(self):
        """断开串口"""
        self.running = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.is_connected = False
        self.connect_btn.config(text="连接")
        self.status_label.config(text="未连接", foreground="red")
        self.log("已断开连接")
        
    def read_serial(self):
        """读取串口数据线程"""
        while self.running and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting:
                    line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self.log(f"← {line}")
                        # 解析位置信息
                        self.parse_position(line)
            except Exception as e:
                self.log(f"读取错误: {str(e)}")
            time.sleep(0.05)
            
    def parse_position(self, line):
        """解析舵机位置信息"""
        # 示例: "Servo1 (Base):     90°"
        if "Servo" in line and ":" in line:
            try:
                parts = line.split(":")
                servo_part = parts[0].strip()
                angle_part = parts[1].strip().replace("°", "")
                angle = int(angle_part)
                
                if "Servo1" in servo_part:
                    self.update_slider("servo1", angle)
                elif "Servo2" in servo_part:
                    self.update_slider("servo2", angle)
                elif "Servo3" in servo_part:
                    self.update_slider("servo3", angle)
                elif "Servo4" in servo_part:
                    self.update_slider("servo4", angle)
                elif "Servo5" in servo_part:
                    self.update_slider("servo5", angle)
            except:
                pass
                
    def update_slider(self, servo_key, angle):
        """更新滑块位置"""
        self.positions[servo_key] = angle
        self.sliders[servo_key].set(angle)
        self.angle_labels[servo_key].config(text=f"{angle}°")
        
    def toggle_debug_mode(self):
        """切换调试模式"""
        self.debug_mode = self.debug_var.get()
        if self.debug_mode:
            self.log("调试模式已启用 - 可以发送指令而无需连接机械臂")
        else:
            self.log("调试模式已禁用")
            
    def detect_joystick(self):
        """检测游戏手柄"""
        try:
            pygame.joystick.quit()
            pygame.joystick.init()
            
            joystick_count = pygame.joystick.get_count()
            if joystick_count > 0:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
                joystick_name = self.joystick.get_name()
                num_axes = self.joystick.get_numaxes()
                num_buttons = self.joystick.get_numbuttons()
                self.joystick_status_label.config(text=f"已连接: {joystick_name}", foreground="green")
                self.log(f"游戏手柄已连接: {joystick_name}")
                self.log(f"手柄信息: {num_axes}个轴, {num_buttons}个按键")
                return True
            else:
                self.joystick = None
                self.joystick_status_label.config(text="未检测到手柄", foreground="red")
                self.log("未检测到游戏手柄")
                return False
        except Exception as e:
            self.joystick = None
            self.joystick_status_label.config(text="手柄检测失败", foreground="red")
            self.log(f"游戏手柄检测失败: {str(e)}")
            return False
            
    def start_joystick_control(self):
        """启动游戏手柄控制"""
        if not self.joystick and not self.detect_joystick():
            messagebox.showwarning("未检测到手柄", "请先连接游戏手柄")
            return
            
        if self.joystick_running:
            self.log("游戏手柄控制已在运行")
            return
            
        self.joystick_running = True
        self.joystick_thread = threading.Thread(target=self.joystick_control_loop, daemon=True)
        self.joystick_thread.start()
        self.log("游戏手柄控制已启动")
        
    def stop_joystick_control(self):
        """停止游戏手柄控制"""
        self.joystick_running = False
        if self.joystick_thread:
            self.joystick_thread.join(timeout=1.0)
        self.log("游戏手柄控制已停止")
        
    def joystick_control_loop(self):
        """游戏手柄控制循环"""
        clock = pygame.time.Clock()
        deadzone = 0.15  # 死区阈值
        
        while self.joystick_running and self.joystick:
            try:
                pygame.event.pump()
                
                # 读取摇杆值 (-1 到 1)
                # 注意：不同手柄的轴映射可能不同，这里使用标准Xbox手柄映射
                left_x = self.joystick.get_axis(0)   # 左摇杆 X (不使用)
                left_y = self.joystick.get_axis(1)   # 左摇杆 Y (腕部)
                right_x = self.joystick.get_axis(3)  # 右摇杆 X (肘部) - 修正为axis 3
                right_y = self.joystick.get_axis(4)  # 右摇杆 Y (不使用) - 修正为axis 4
                
                # 读取D-pad (十字键)
                hat = self.joystick.get_hat(0)  # (x, y) -1, 0, 1
                dpad_x, dpad_y = hat
                
                # 应用死区
                left_y = 0 if abs(left_y) < deadzone else left_y
                right_x = 0 if abs(right_x) < deadzone else right_x
                
                # 转换到角度变化 (-5 到 5 度)
                wrist_delta = int(left_y * 5)      # 左摇杆前后控制腕部
                elbow_delta = int(right_x * 5)     # 右摇杆左右控制肘部
                shoulder_delta = int(dpad_y * 5)   # D-pad前后控制肩部
                base_delta = int(dpad_x * 5)       # D-pad左右控制底座
                
                # 应用角度变化
                if base_delta != 0:
                    self.adjust_angle_smooth("servo2", base_delta)
                if shoulder_delta != 0:
                    self.adjust_angle_smooth("servo3", shoulder_delta)
                if elbow_delta != 0:
                    self.adjust_angle_smooth("servo4", elbow_delta)
                if wrist_delta != 0:
                    self.adjust_angle_smooth("servo1", wrist_delta)
                
                # 检查按键 - 连续调节夹爪角度
                gripper_delta = 0
                if self.joystick.get_button(0):  # A键 - 减少夹爪角度 (闭合)
                    gripper_delta = -2
                if self.joystick.get_button(1):  # B键 - 增加夹爪角度 (张开)
                    gripper_delta = 2
                
                if gripper_delta != 0:
                    self.adjust_angle_smooth("servo5", gripper_delta)
                
                # X键 - Reset
                if self.joystick.get_button(2):  # X键
                    if not hasattr(self, 'last_x_press') or time.time() - self.last_x_press > 0.5:
                        self.reset_all()
                        self.last_x_press = time.time()
                
                # Y键 - 执行路径
                if self.joystick.get_button(3):  # Y键
                    if not hasattr(self, 'last_y_press') or time.time() - self.last_y_press > 1.0:
                        self.execute_path()
                        self.last_y_press = time.time()
                
                # LB键 - 记录位置
                if self.joystick.get_button(4):  # LB键
                    if not hasattr(self, 'last_lb_press') or time.time() - self.last_lb_press > 0.5:
                        self.record_current_position()
                        self.last_lb_press = time.time()
                
                # RB键 - 停止记录
                if self.joystick.get_button(5):  # RB键
                    if not hasattr(self, 'last_rb_press') or time.time() - self.last_rb_press > 0.5:
                        self.stop_recording()
                        self.last_rb_press = time.time()
                
                clock.tick(30)  # 30 FPS
                
            except Exception as e:
                self.log(f"游戏手柄控制错误: {str(e)}")
                break
                
        self.joystick_running = False
        
    def adjust_angle_smooth(self, servo_key, delta):
        """平滑调整角度"""
        current = self.positions[servo_key]
        new_angle = max(0, min(180, current + delta))
        
        if new_angle != current:
            self.positions[servo_key] = new_angle
            
            # 安全更新UI控件
            if servo_key in self.sliders:
                self.sliders[servo_key].set(new_angle)
            if servo_key in self.angle_labels:
                self.angle_labels[servo_key].config(text=f"{new_angle}°")
            
            # 发送命令
            servo_num = int(servo_key[-1])
            self.send_command(f"set {servo_num} {new_angle}")
            
    def send_command(self, command):
        """发送命令到串口"""
        if not self.debug_mode and (not self.is_connected or not self.serial_port):
            messagebox.showwarning("未连接", "请先连接串口或启用调试模式")
            return
            
        # 记录指令
        self.log_command(command)
            
        if self.debug_mode:
            self.log(f"调试 → {command}")
            return
            
        try:
            self.serial_port.write(f"{command}\n".encode())
            self.log(f"→ {command}")
        except Exception as e:
            self.log(f"发送失败: {str(e)}")
            
    def log_command(self, command):
        """记录发送的指令"""
        timestamp = time.strftime('%H:%M:%S')
        self.last_commands.append(f"{timestamp}: {command}")
        
        # 只保留最近50条指令
        if len(self.last_commands) > 50:
            self.last_commands.pop(0)
            
        # 更新显示
        self.command_text.config(state="normal")
        self.command_text.delete(1.0, "end")
        for cmd in self.last_commands[-20:]:  # 显示最近20条
            self.command_text.insert("end", cmd + "\n")
        self.command_text.see("end")
        self.command_text.config(state="disabled")
            
    def send_keyboard_command(self, key):
        """发送键盘命令"""
        self.send_command(key)
        
    def on_key_press(self, event):
        """处理键盘按键"""
        key = event.char.lower()
        valid_keys = ['w', 'a', 's', 'd', 'q', 'e', 'z', 'x', '[', ']']
        if key in valid_keys:
            self.send_command(key)
            
    def on_slider_change(self, servo_key, value):
        """滑块值改变时"""
        angle = int(float(value))
        self.positions[servo_key] = angle
        
        # 检查angle_labels是否已初始化
        if servo_key in self.angle_labels:
            self.angle_labels[servo_key].config(text=f"{angle}°")
        
        # 发送命令
        servo_num = int(servo_key[-1])  # servo1 -> 1
        self.send_command(f"set {servo_num} {angle}")
        
    def adjust_angle(self, servo_key, delta):
        """调整舵机角度"""
        current = self.positions[servo_key]
        new_angle = max(0, min(180, current + delta))
        self.sliders[servo_key].set(new_angle)
        
    def reset_all(self):
        """重置所有舵机到90度"""
        self.send_command("reset")
        for key in self.sliders:
            self.sliders[key].set(90)
            
    def open_gripper(self):
        """打开夹爪"""
        self.send_command("open")
        
    def close_gripper(self):
        """关闭夹爪"""
        self.send_command("close")
        
    def save_position(self):
        """保存当前位置"""
        self.send_command("save")
        
    def send_all_positions(self):
        """发送所有舵机位置"""
        positions = [self.positions[f'servo{i}'] for i in range(1, 6)]
        command = f"move {' '.join(map(str, positions))}"
        self.send_command(command)
        
    def emergency_stop(self):
        """紧急停止"""
        if messagebox.askyesno("确认", "确定要重置所有舵机吗？"):
            self.reset_all()
            
    def log(self, message):
        """添加日志"""
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")
        
    # ===== 路径管理功能 =====
    
    def load_existing_paths(self):
        """加载已保存的路径文件"""
        try:
            for filename in os.listdir(self.paths_dir):
                if filename.endswith('.csv'):
                    path_name = filename[:-4]
                    self.load_path_from_csv(path_name)
                    self.path_listbox.insert(tk.END, path_name)
        except Exception as e:
            self.log(f"加载路径失败: {str(e)}")
    
    def create_new_path(self):
        """创建新路径"""
        dialog = tk.Toplevel(self.root)
        dialog.title("创建新路径")
        dialog.geometry("300x100")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="路径名称:").pack(pady=10)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.pack(pady=5)
        name_entry.focus()
        
        def create():
            path_name = name_entry.get().strip()
            if not path_name:
                messagebox.showwarning("警告", "请输入路径名称")
                return
            if path_name in self.paths:
                messagebox.showwarning("警告", "路径名称已存在")
                return
            
            self.paths[path_name] = []
            self.path_listbox.insert(tk.END, path_name)
            self.current_path_name = path_name
            self.path_status_label.config(text=f"当前路径: {path_name} (0个点)", foreground="blue")
            self.save_path_to_csv(path_name)
            self.log(f"创建新路径: {path_name}")
            dialog.destroy()
        
        ttk.Button(dialog, text="创建", command=create).pack(pady=10)
        name_entry.bind('<Return>', lambda e: create())
    
    def delete_path(self):
        """删除选中的路径"""
        selection = self.path_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的路径")
            return
        
        path_name = self.path_listbox.get(selection[0])
        
        if messagebox.askyesno("确认删除", f"确定要删除路径 '{path_name}' 吗？"):
            # 删除CSV文件
            csv_path = os.path.join(self.paths_dir, f"{path_name}.csv")
            if os.path.exists(csv_path):
                os.remove(csv_path)
            
            # 从内存删除
            if path_name in self.paths:
                del self.paths[path_name]
            
            # 从列表框删除
            self.path_listbox.delete(selection[0])
            
            if self.current_path_name == path_name:
                self.current_path_name = None
                self.path_status_label.config(text="未选择路径", foreground="gray")
            
            self.log(f"已删除路径: {path_name}")
    
    def rename_path(self):
        """重命名路径"""
        selection = self.path_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要重命名的路径")
            return
        
        old_name = self.path_listbox.get(selection[0])
        
        dialog = tk.Toplevel(self.root)
        dialog.title("重命名路径")
        dialog.geometry("300x100")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="新名称:").pack(pady=10)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.insert(0, old_name)
        name_entry.pack(pady=5)
        name_entry.focus()
        name_entry.select_range(0, tk.END)
        
        def rename():
            new_name = name_entry.get().strip()
            if not new_name:
                messagebox.showwarning("警告", "请输入新名称")
                return
            if new_name in self.paths and new_name != old_name:
                messagebox.showwarning("警告", "路径名称已存在")
                return
            
            # 重命名CSV文件
            old_csv = os.path.join(self.paths_dir, f"{old_name}.csv")
            new_csv = os.path.join(self.paths_dir, f"{new_name}.csv")
            if os.path.exists(old_csv):
                os.rename(old_csv, new_csv)
            
            # 更新内存
            self.paths[new_name] = self.paths.pop(old_name)
            
            # 更新列表框
            self.path_listbox.delete(selection[0])
            self.path_listbox.insert(selection[0], new_name)
            self.path_listbox.selection_set(selection[0])
            
            if self.current_path_name == old_name:
                self.current_path_name = new_name
                point_count = len(self.paths[new_name])
                self.path_status_label.config(text=f"当前路径: {new_name} ({point_count}个点)", foreground="blue")
            
            self.log(f"路径已重命名: {old_name} → {new_name}")
            dialog.destroy()
        
        ttk.Button(dialog, text="重命名", command=rename).pack(pady=10)
        name_entry.bind('<Return>', lambda e: rename())
    
    def on_path_select(self, event):
        """路径选择事件"""
        selection = self.path_listbox.curselection()
        if selection:
            path_name = self.path_listbox.get(selection[0])
            self.current_path_name = path_name
            point_count = len(self.paths.get(path_name, []))
            self.path_status_label.config(text=f"当前路径: {path_name} ({point_count}个点)", foreground="blue")
            self.recording = False
    
    def record_current_position(self):
        """记录当前位置到路径"""
        if not self.current_path_name:
            messagebox.showwarning("警告", "请先选择一个路径")
            return
        
        # 获取当前所有舵机位置
        current_pos = (
            self.positions['servo1'],
            self.positions['servo2'],
            self.positions['servo3'],
            self.positions['servo4'],
            self.positions['servo5']
        )
        
        # 添加到路径
        self.paths[self.current_path_name].append(current_pos)
        
        # 保存到CSV
        self.save_path_to_csv(self.current_path_name)
        
        # 更新状态
        point_count = len(self.paths[self.current_path_name])
        self.path_status_label.config(
            text=f"当前路径: {self.current_path_name} ({point_count}个点) - 已记录", 
            foreground="green"
        )
        
        self.log(f"记录位置到 '{self.current_path_name}': {current_pos}")
    
    def stop_recording(self):
        """停止记录"""
        self.recording = False
        if self.current_path_name:
            point_count = len(self.paths[self.current_path_name])
            self.path_status_label.config(
                text=f"当前路径: {self.current_path_name} ({point_count}个点) - 已停止", 
                foreground="orange"
            )
            self.log(f"停止记录路径: {self.current_path_name}")
    
    def execute_path(self):
        """执行路径"""
        if not self.current_path_name:
            messagebox.showwarning("警告", "请先选择一个路径")
            return
        
        if not self.paths[self.current_path_name]:
            messagebox.showwarning("警告", "路径为空，请先记录位置")
            return
        
        # 在新线程中执行以避免阻塞GUI
        threading.Thread(target=self._execute_path_thread, daemon=True).start()
    
    def _execute_path_thread(self):
        """执行路径的线程函数"""
        try:
            self.log(f"开始执行路径: {self.current_path_name}")
            
            # 1. Reset
            self.reset_all()
            time.sleep(2)
            
            # 2. 执行路径中的每个位置
            for i, pos in enumerate(self.paths[self.current_path_name]):
                self.log(f"执行第{i+1}个位置: {pos}")
                
                # 发送move命令
                command = f"move {pos[0]} {pos[1]} {pos[2]} {pos[3]} {pos[4]}"
                self.send_command(command)
                
                # 更新GUI显示
                self.update_slider("servo1", pos[0])
                self.update_slider("servo2", pos[1])
                self.update_slider("servo3", pos[2])
                self.update_slider("servo4", pos[3])
                self.update_slider("servo5", pos[4])
                
                time.sleep(1.5)  # 等待机械臂移动到位
            
            # 3. Reset
            time.sleep(1)
            self.reset_all()
            
            self.log(f"路径执行完成: {self.current_path_name}")
            
        except Exception as e:
            self.log(f"执行路径错误: {str(e)}")
    
    def save_path_to_csv(self, path_name):
        """保存路径到CSV文件"""
        try:
            csv_path = os.path.join(self.paths_dir, f"{path_name}.csv")
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Servo1_Wrist', 'Servo2_Base', 'Servo3_Shoulder', 'Servo4_Elbow', 'Servo5_Gripper'])
                
                for pos in self.paths.get(path_name, []):
                    writer.writerow(pos)
            
            self.log(f"路径已保存: {csv_path}")
        except Exception as e:
            self.log(f"保存路径失败: {str(e)}")
    
    def load_path_from_csv(self, path_name):
        """从CSV文件加载路径"""
        try:
            csv_path = os.path.join(self.paths_dir, f"{path_name}.csv")
            positions = []
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # 跳过标题行
                
                for row in reader:
                    if len(row) == 5:
                        pos = tuple(int(x) for x in row)
                        positions.append(pos)
            
            self.paths[path_name] = positions
            self.log(f"加载路径: {path_name} ({len(positions)}个点)")
            
        except Exception as e:
            self.log(f"加载路径失败: {str(e)}")
        
    def on_closing(self):
        """关闭窗口时"""
        # 停止游戏手柄控制
        if self.joystick_running:
            self.stop_joystick_control()
            
        # 清理pygame
        pygame.quit()
        
        if self.is_connected:
            self.disconnect()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = RobotArmGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
