// 预设动作序列示例
// 可以将这些函数添加到 main.cpp 中，实现一键抓取

#include <Arduino.h>
#include <Servo.h>

// 外部声明 (如果在 main.cpp 中使用)
extern Servo servo1, servo2, servo3, servo4, servo5;

// ======================
// 抓取立方体 (Cube)
// ======================
void grabCube() {
  Serial.println("=== Grabbing Cube ===");
  
  // 1. 打开夹爪
  servo5.write(30);
  delay(500);
  
  servo2.write(0);
  servo3.write(150);
  servo4.write(100);
  servo1.write(90);
  delay(1000);
  // move 90 0 150 90 30
  
  // 小心下降
  servo1.write(50);
  delay(1000);
  // move 50 0 150 90 30

  // 夹取
  servo5.write(90);
  delay(500);
  
  // 抬起
  servo3.write(170);
  delay(800);
  
  // 旋转
  servo2.write(170);
  delay(1000);
  
  // 放置
  servo3.write(60);
  servo1.write(60);
  servo4.write(55);
  delay(800);
  
  // 8. 松开立方体
  servo5.write(30);
  delay(500);
  
  // 返回
  servo4.write(0);
  servo3.write(100);
  servo1.write(90);
  servo2.write(45);
  delay(500);
  // move 90 45 100 0 30

  Serial.println("=== Cube grabbed successfully! ===\n");
}

// ======================
// 抓取小圆柱 (Small Cylinder)
// ======================
void grabCylinder() {
  Serial.println("=== Grabbing Small Cylinder ===");
  
  // 打开夹爪
  servo5.write(30);
  delay(500);
  
  // 移动到圆柱上方 (根据实际位置调整)
  servo2.write(45); // base
  servo3.write(25); // shoulder
  servo4.write(0); // elbow
  servo1.write(90); // wrist
  delay(1000);
  // move 90 45 25 0 30
  
  // 下降
  servo3.write(10);
  delay(800);
  servo1.write(100);
  delay(800);
  // move 100 45 10 0 30
  
  // 夹紧 (圆柱较细，可能需要不同的夹爪角度)
  servo5.write(75);
  delay(500);
  // move 100 45 10 0 75
  
  // 抬起
  servo3.write(45);
  servo1.write(50);
  delay(800);
  // move 90 75 180 85 75
  
  // 旋转到目标
  servo2.write(130);
  delay(1000);
  
  // 放下
  servo3.write(25);
  servo1.write(60);
  delay(800);
  
  // 松开
  servo5.write(30);
  delay(500);
  
  // 返回
  servo3.write(100);
  servo1.write(90);
  servo2.write(45);
  delay(500);
  
  Serial.println("=== Cylinder grabbed successfully! ===\n");
}

// ======================
// 抓取小帽子 (Small Hat)
// ======================
void grabHat() {
  Serial.println("=== Grabbing Small Hat ===");
  
  servo5.write(30);
  delay(500);
  
  // 移动到帽子位置
  servo2.write(0);
  servo3.write(150);
  servo4.write(90);
  servo1.write(90);
  delay(1000);
  // move 90 0 150 90 30
  
  // 小心下降
  servo3.write(140);
  servo1.write(70);
  delay(1000);
  // move 70 0 140 90 30

  // 夹取
  servo5.write(90);
  delay(500);
  
  // 抬起
  servo3.write(160);
  delay(800);
  
  // 旋转
  servo2.write(50);
  delay(1000);
  
  // 放置
  servo3.write(120);
  servo1.write(60);
  delay(800);
  
  // 松开
  servo2.write(170); 
  delay(180);
  servo5.write(30);
  delay(500);
  
  // 返回
  servo4.write(0);
  servo3.write(100);
  servo1.write(90);
  servo2.write(45);
  delay(500);
  
  Serial.println("=== Hat grabbed successfully! ===\n");
}

// ======================
// 抓取小船 (Small Boat)
// ======================
void grabBoat() {
  Serial.println("=== Grabbing Small Boat ===");
  
  // 船可能是最难的物品
  servo5.write(30);
  delay(500);
  
  // 移动到船的位置
  servo2.write(0);
  servo3.write(35);
  servo4.write(10);
  servo1.write(120);
  delay(1000);
  
  // 调整角度接近船
  servo3.write(30);
  servo1.write(105);
  delay(1000);
  
  // 夹取
  servo5.write(70);  // 可能需要更紧的夹持
  delay(600);
  
  // 小心抬起
  servo3.write(45);
  servo1.write(65);
  delay(1000);
  
  // 旋转
  servo2.write(170);
  delay(1200);
  
  // 放置
  servo3.write(45);
  servo1.write(20);
  delay(1000);
  
  // 松开
  servo5.write(30);
  delay(500);
  
  // 返回初始位置
  servo3.write(100);
  servo1.write(90);
  servo2.write(45);
  delay(500);
  
  Serial.println("=== Boat grabbed successfully! ===\n");
}

// ======================
// 演示所有抓取动作
// ======================
void demonstrateAll() {
  Serial.println("\n========================================");
  Serial.println("  Full Demonstration - All Items");
  Serial.println("========================================\n");
  
  delay(2000);
  
  grabCube();
  delay(2000);
  
  grabCylinder();
  delay(2000);
  
  grabHat();
  delay(2000);
  
  grabBoat();
  delay(2000);
  
  Serial.println("========================================");
  Serial.println("  Demonstration Complete!");
  Serial.println("========================================\n");
}

// ======================
// 使用方法
// ======================
/*
在 main.cpp 的 processCommand 函数中添加:

} else if (cmd == "cube") {
  grabCube();
} else if (cmd == "cylinder") {
  grabCylinder();
} else if (cmd == "hat") {
  grabHat();
} else if (cmd == "boat") {
  grabBoat();
}

然后通过串口发送命令:
- cube      : 抓取立方体
- cylinder  : 抓取圆柱
- hat       : 抓取帽子
- boat      : 抓取船
- demo      : 演示全部

⚠️ 重要提示:
上述角度值是示例，必须根据你的实际硬件调整！
建议步骤:
1. 先用 "set" 命令手动测试每个关键位置
2. 记录成功的角度组合
3. 更新这些函数中的角度值
4. 反复测试和微调
*/
