# ISDN 2601 Final Project - 5轴机械臂控制系统

**使用 ESP8266 控制 5 个 SG90 舵机实现物品抓取和移动**

---

## 📋 项目目标

使用 5 个 SG90 舵机构建机械臂，成功抓取并移动指定物品：
- ✅ **立方体 (Cube)** - 10分
- ✅ **小圆柱 (Small Cylinder)** - 20分
- ✅ **小帽子 (Small Hat)** - 30分
- ✅ **小船 (Small Boat)** - 40分

**总分组成**: 视频演示 (60%) + 项目报告 (30%) + 代码 (10%)

---

## 🛠️ 硬件清单

| 组件 | 型号/规格 | 数量 |
|------|----------|------|
| 微控制器 | LOLIN (WEMOS) D1 R2 & mini (ESP8266) | 1 |
| 舵机 | SG90 (0-180°, 5V) | 5 |
| 扩展板 | 5路舵机扩展板 (提供5V和GND) | 1 |
| USB线 | Micro USB | 1 |
| 外部电源 | 5V 2A (可选，推荐) | 1 |
| 机械臂套件 | 5自由度机械臂框架 | 1 |

---

## 📦 项目结构

```
final project/
├── platformio.ini              # ESP8266 配置
├── src/
│   └── main.cpp               # 5舵机控制主程序
├── robot_arm_gui.py           # Python GUI 控制界面
├── PRESET_ACTIONS.cpp         # 预设动作序列示例
├── 25 Fall Final Project.pdf  # 项目要求文档 ⭐
├── sg90_datasheet.pdf         # SG90数据手册
├── sample video 8x.mp4        # 演示视频参考
└── README.md                  # 本文档 (综合指南)
```

---

## 🔌 接线说明

### ESP8266 扩展板引脚映射

| 扩展板标签 | ESP8266 GPIO | 舵机功能 | 代码定义 |
|-----------|--------------|---------|---------|
| D0 | GPIO16 | Servo1 - 腕部 | SERVO1_PIN |
| D1 | GPIO5  | Servo2 - 底座旋转 | SERVO2_PIN |
| D2 | GPIO4  | Servo3 - 肩部 | SERVO3_PIN |
| D3 | GPIO0  | Servo4 - 肘部 | SERVO4_PIN |
| D5 | GPIO14 | Servo5 - 夹爪 | SERVO5_PIN |

### 接线图

```
ESP8266 + 扩展板              5x SG90 舵机
┌─────────────────┐          ┌──────────────┐
│  5V (扩展板提供) ├──────────┤ VCC (红线x5) │
│ GND (扩展板提供) ├──────────┤ GND (棕线x5) │
│                 │          │              │
│  D0 (GPIO16)    ├──────────┤ Servo1 信号  │
│  D1 (GPIO5)     ├──────────┤ Servo2 信号  │
│  D2 (GPIO4)     ├──────────┤ Servo3 信号  │
│  D3 (GPIO0)     ├──────────┤ Servo4 信号  │
│  D5 (GPIO14)    ├──────────┤ Servo5 信号  │
└─────────────────┘          └──────────────┘
```

**⚠️ 重要提示**:
- 扩展板自动为每个舵机提供 5V 和 GND
- 如果舵机抖动，使用外部 5V 2A 电源
- 外部电源 GND 必须与 ESP8266 GND 共地

---

## 🚀 快速开始

### 1️⃣ 环境准备

#### 安装 PlatformIO (VS Code)
1. 打开 VS Code
2. 安装扩展: `PlatformIO IDE`
3. 重启 VS Code

#### 或使用 Arduino IDE
参考 `25 Fall Final Project.pdf` 第5页 "E) ESP8266 Set Up in Arduino"

### 2️⃣ 编译和上传

```powershell
# 进入项目目录
cd "c:\Users\hinpak\Documents\GitHub\isdn2601-final-2025fall\2601 final"

# 如果 pio 未配置到 PATH，用完整路径运行：
C:\Users\hinpak\.platformio\penv\Scripts\platformio.exe run

# 连接 LOLIN D1 R2 & mini 到 USB 端口

# 上传到开发板（先确认 COM 端口）
C:\Users\hinpak\.platformio\penv\Scripts\platformio.exe device list
C:\Users\hinpak\.platformio\penv\Scripts\platformio.exe run -t upload --upload-port COM6

# 打开串口监视器 (115200 波特率)
C:\Users\hinpak\.platformio\penv\Scripts\platformio.exe device monitor -b 115200 --port COM6
```

提示：如果已将 PlatformIO 添加到系统 PATH，可直接使用 `pio run`、`pio run -t upload` 和 `pio device monitor`。

### 3️⃣ 测试舵机

上传成功后，串口会显示:
```
=== ISDN 2601 Mechanical Arm Control ===
Board: LOLIN D1 R2 & mini (ESP8266)
Servos: 5x SG90

Servos attached to pins:
  Servo1 (Wrist)    -> D0 (GPIO16)
  Servo2 (Base)     -> D1 (GPIO5)
  Servo3 (Shoulder) -> D2 (GPIO4)
  Servo4 (Elbow)    -> D3 (GPIO0)
  Servo5 (Gripper)  -> D5 (GPIO14)

System ready!
```

---

## 🎮 控制方式

### 方法1: 串口命令控制

通过串口监视器 (115200) 发送以下命令:

| 命令 | 功能 | 示例 |
|------|------|------|
| `help` 或 `h` | 显示帮助信息 | `help` |
| `status` 或 `s` | 显示当前所有舵机角度 | `status` |
| `reset` 或 `r` | 重置所有舵机到90° | `reset` |
| `set <舵机> <角度>` | 单独控制一个舵机 | `set 1 45` |
| `move <a1> <a2> <a3> <a4> <a5>` | 同时控制5个舵机 | `move 90 60 120 45 30` |
| `open` | 打开夹爪 (servo5 -> 90°) | `open` |
| `close` | 关闭夹爪 (servo5 -> 30°) | `close` |
| `save` | 保存当前位置（打印代码格式） | `save` |

### 方法2: WASD 键盘控制

| 按键 | 舵机 | 功能 | 说明 |
|------|------|------|------|
| **W** | Servo3 | 肩部 **上升** | 角度 -5° |
| **S** | Servo3 | 肩部 **下降** | 角度 +5° |
| **A** | Servo2 | 底座 **左转** | 角度 +5° |
| **D** | Servo2 | 底座 **右转** | 角度 -5° |
| **Q** | Servo4 | 肘部 **上升** | 角度 +5° |
| **E** | Servo4 | 肘部 **下降** | 角度 -5° |
| **Z** | Servo1 | 腕部 **上升** | 角度 -5° |
| **X** | Servo1 | 腕部 **下降** | 角度 +5° |
| **[** | Servo5 | 夹爪 **打开** | 30° |
| **]** | Servo5 | 夹爪 **关闭** | 90° |

### 方法3: Python GUI 控制界面

#### 安装依赖
```powershell
pip install pyserial pygame
```

#### 启动GUI
```powershell
python robot_arm_gui.py
```

#### GUI功能
- **串口连接**: 自动检测并连接ESP8266
- **滑块控制**: 5个舵机实时角度控制 (0-180°)
- **键盘面板**: 可视化WASD控制按钮
- **快捷操作**: 一键打开/关闭夹爪，保存位置等
- **实时日志**: 显示所有串口通信
- **调试模式**: 无需连接机械臂即可测试指令

### 方法4: 游戏手柄控制 🎮

#### 支持的手柄类型
- Xbox 360/One 手柄
- PlayStation 4/5 手柄
- 其他兼容SDL2的游戏手柄

#### 摇杆映射
| 摇杆 | 控制舵机 | 功能 | 说明 |
|------|----------|------|------|
| **左摇杆 X轴** | Servo2 | 底座旋转 | 左/右转向 |
| **左摇杆 Y轴** | Servo3 | 肩部升降 | 上/下移动 |
| **右摇杆 X轴** | Servo4 | 肘部弯曲 | 前/后伸展 |
| **右摇杆 Y轴** | Servo1 | 腕部旋转 | 手腕转动 |

#### 按键映射
| 按键 | 功能 | 说明 |
|------|------|------|
| **A键** | 打开夹爪 | Servo5 → 30° |
| **B键** | 关闭夹爪 | Servo5 → 90° |

#### 使用步骤
1. **连接手柄**: 先连接游戏手柄到电脑
2. **启动GUI**: `python robot_arm_gui.py`
3. **检测手柄**: 点击"检测手柄"按钮
4. **启用调试模式**: 勾选"调试模式"复选框（可选）
5. **启动控制**: 点击"启动手柄控制"按钮
6. **开始控制**: 使用摇杆和按键控制机械臂

#### 控制特性
- **死区处理**: 小幅摇杆移动会被忽略，避免抖动
- **平滑控制**: 角度变化平滑，避免突兀移动
- **按键防抖**: 按键有0.5秒防抖延迟
- **实时反馈**: GUI显示当前角度和发送指令

---

## 📐 抓取物品步骤

### 基本流程

1. **打开夹爪** → `open` 或 `[`
2. **移动到物品上方** → `move <angles>` 或 GUI滑块
3. **下降到物品位置** → 调整肩部/肘部 (W/S/Q/E)
4. **夹紧物品** → `close` 或 `]`
5. **抬起物品** → 调整肩部/肘部 (W/S/Q/E)
6. **旋转底座** → `set 2 <angle>` 或 A/D键
7. **移动到目标位置** → `move <angles>` 或 GUI滑块
8. **放下物品** → 调整高度
9. **松开夹爪** → `open` 或 `[`
10. **返回初始位置** → `reset`

### 建议角度范围 (需根据实际调整)

| 舵机 | 功能 | 建议范围 | 说明 |
|------|------|---------|------|
| Servo1 | 腕部 | 45-135° | 调整夹爪角度 |
| Servo2 | 底座旋转 | 0-180° | 控制左右转向 |
| Servo3 | 肩部 | 30-150° | 控制高度 |
| Servo4 | 肘部 | 30-150° | 配合肩部调整位置 |
| Servo5 | 夹爪 | 30(闭)-90(开)° | 30=夹紧, 90=松开 |

---

## 📹 视频演示要求

### 录制内容
- 分别演示抓取和移动 4 个物品:
  1. 立方体 (Cube) - 10%
  2. 小圆柱 (Small Cylinder) - 20%
  3. 小帽子 (Small Hat) - 30%
  4. 小船 (Small Boat) - 40%

### 提交要求
- **截止时间**: 2025年12月20日 23:59
- **提交位置**: Canvas/Assignments/Final Project Video
- **格式**: 可以是 4 个单独视频或 1 个合并视频
- **参考**: `sample video 8x.mp4` (Canvas 提供)

---

## 📄 项目报告要求 (30%)

### 报告结构

| 章节 | 分值 | 要求 |
|------|------|------|
| Title Page | 1% | 项目标题、姓名学号、大学名、提交日期 |
| Abstract | 10% | ≤300词，概述工作内容、目标、结果、结论 |
| Table of Contents | 1% | 章节目录 |
| Introduction and Theory | 20% | 目标、理论背景 (不要复制项目文档!) |
| Equipment/Material List | 7% | 所有使用的设备清单+实验装置图 |
| Procedures | 10% | 设计过程和解决方案 (过去时) |
| Results | 20% | 展示你的结果 |
| Discussion | 20% | 解释结果、评论完成情况、分析误差 |
| Conclusion | 10% | 总结、未来改进建议 |
| References and Appendices | 1% | 参考文献和附录 |

### 提交要求
- **截止时间**: 2025年12月20日 23:59
- **提交位置**: Canvas/Assignments/Final Project Report

---

## 💻 代码提交 (10%)

### GitHub Classroom
- **提交链接**: https://classroom.github.com/a/M9aW25uf
- **命名规则**: 使用 Canvas 中的小组名 (例如: Final Project 25)

### 提交步骤

1. **接受作业**: 点击链接，使用小组名创建仓库
2. **克隆仓库**: `git clone <你的仓库地址>`
3. **复制文件**: 复制 `platformio.ini`、`src/`、`README.md`、`.gitignore`
4. **提交代码**:
   ```powershell
   git add .
   git commit -m "Final project submission"
   git push origin main
   ```

---

## 🔧 代码结构说明

### 主要函数

```cpp
// 初始化5个舵机并连接到引脚
void setup()

// 主循环，接收串口命令
void loop()

// 处理用户命令
void processCommand(String cmd)

// 设置单个舵机角度
void setServoAngle(int servoNum, int angle)

// 同时移动所有舵机
void moveAllServos(int angles[])

// 打开/关闭夹爪
void openGripper()
void closeGripper()

// 重置到初始位置
void resetPosition()

// 显示当前状态
void printStatus()
```

### 自定义动作序列

你可以在 `src/main.cpp` 中添加预设动作序列:

```cpp
void grabCube() {
  // 抓取立方体的动作序列
  openGripper();
  delay(500);

  int pickupPos[] = {45, 60, 120, 80, 90};
  moveAllServos(pickupPos);
  delay(1000);

  closeGripper();
  delay(500);

  // ... 移动到目标位置
}
```

---

## 🐛 故障排查

### 舵机不响应
- ✅ 检查扩展板是否正确连接到 ESP8266
- ✅ 确认 5V 电源是否稳定
- ✅ 查看串口是否输出 "Servos attached to pins"
- ✅ 尝试 `reset` 命令

### 舵机抖动
- ✅ 使用外部 5V 2A 电源 (不要只依赖 USB)
- ✅ 确保 GND 共地
- ✅ 减慢移动速度，增加 `delay()`

### 上传失败
```powershell
# 1. 查看可用端口（未设置 PATH 时使用完整路径）
C:\Users\hinpak\.platformio\penv\Scripts\platformio.exe device list

# 2. 手动指定端口上传
C:\Users\hinpak\.platformio\penv\Scripts\platformio.exe run -t upload --upload-port COM6

# 3. 检查驱动是否安装 (CH340/CP2102)
```

### 串口无输出
- 检查波特率是否设为 **115200**
- 按下开发板上的 RESET 按钮
- 重新上传代码

### GUI无法连接
- 确认ESP8266已上电并运行
- 检查串口是否被其他程序占用
- 尝试刷新端口列表

---

## 📚 参考资源

### 项目文档
- **25 Fall Final Project.pdf** - 完整项目要求 ⭐
- **sg90_datasheet.pdf** - SG90 舵机技术参数
- **sample video 8x.mp4** - 演示视频参考

### PWM 原理
- 脉冲宽度: 0.5ms ~ 2.5ms
- 脉冲周期: 20ms (50Hz)
- 1.5ms = 90° (中心位置)
- 1.0ms = 0°
- 2.0ms = 180°

### ESP8266 资源
- PlatformIO 文档: https://docs.platformio.org/
- ESP8266 Arduino Core: https://arduino-esp8266.readthedocs.io/
- Servo 库文档: https://www.arduino.cc/reference/en/libraries/servo/

---

## ✅ 提交清单

在截止日期前确保:

- [ ] **视频** (60%): 上传到 Canvas/Assignments/Final Project Video
  - [ ] 立方体演示 (10%)
  - [ ] 小圆柱演示 (20%)
  - [ ] 小帽子演示 (30%)
  - [ ] 小船演示 (40%)

- [ ] **报告** (30%): 上传到 Canvas/Assignments/Final Project Report
  - [ ] Title Page (1%)
  - [ ] Abstract (10%)
  - [ ] Table of Contents (1%)
  - [ ] Introduction and Theory (20%)
  - [ ] Equipment/Material List (7%)
  - [ ] Procedures (10%)
  - [ ] Results (20%)
  - [ ] Discussion (20%)
  - [ ] Conclusion (10%)
  - [ ] References and Appendices (1%)

- [ ] **代码** (10%): 提交到 GitHub Classroom
  - [ ] https://classroom.github.com/a/M9aW25uf
  - [ ] 使用正确的小组名

---

## 🎯 成功建议

1. **提前测试**: 尽早测试硬件连接和舵机响应
2. **记录角度**: 为每个物品记录成功的角度组合
3. **平滑移动**: 使用延时避免舵机急动
4. **外部电源**: 强烈推荐使用 5V 2A 外部电源
5. **多次练习**: 在录制视频前多次练习抓取动作
6. **备份代码**: 定期提交到 GitHub
7. **详细记录**: 报告中记录设计过程和遇到的问题

---

**祝你项目成功！🎉**

如有问题，请参考 `25 Fall Final Project.pdf` 或联系助教。