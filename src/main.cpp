#include <Arduino.h>
#include <Servo.h>
#include "PRESET_ACTIONS.h"

/* 
 * ISDN 2601 Final Project - 5-Servo Mechanical Arm
 * Control 5x SG90 servos to grab and move designated items:
 * - Cube (10%)
 * - Small cylinder (20%)
 * - Small hat (30%)
 * - Small boat (40%)
 */

// Define 5 Servo objects for mechanical arm
Servo servo1;  // Wrist
Servo servo2;  // Base rotation
Servo servo3;  // Shoulder
Servo servo4;  // Elbow
Servo servo5;  // Gripper

// Function declarations (forward declarations)
void printHelp();
void printStatus();
void resetPosition();
void openGripper();
void closeGripper();
void processCommand(String cmd);
void setServoAngle(int servoNum, int angle);
void moveAllServos(int angles[]);
int parseAngles(String str, int* angles, int maxCount);

// ESP8266 Pin assignments (Extension board labels -> GPIO)
// Refer to project document Table for pin mapping
#define SERVO1_PIN D0   // GPIO16
#define SERVO2_PIN D1   // GPIO5
#define SERVO3_PIN D2   // GPIO4
#define SERVO4_PIN D6   // GPIO12
#define SERVO5_PIN D5   // GPIO14

// Initial positions (degrees)
int pos1 = 90;
int pos2 = 45;
int pos3 = 100;
int pos4 = 0;
int pos5 = 90;

// Movement step size for WASD control
const int STEP_SIZE = 5;  // Degrees to move per key press

void setup() {
  Serial.begin(115200);
  delay(100);
  
  Serial.println("\n\n=== ISDN 2601 Mechanical Arm Control ===");
  Serial.println("Board: LOLIN D1 R2 & mini (ESP8266)");
  Serial.println("Servos: 5x SG90\n");
  
  // Attach servos to PWM pins
  servo1.attach(SERVO1_PIN);
  servo2.attach(SERVO2_PIN);
  servo3.attach(SERVO3_PIN);
  servo4.attach(SERVO4_PIN);
  servo5.attach(SERVO5_PIN);
  
  Serial.println("Servos attached to pins:");
  Serial.println("  Servo1 (Wrist)    -> D0 (GPIO16)");
  Serial.println("  Servo2 (Base)     -> D1 (GPIO5)");
  Serial.println("  Servo3 (Shoulder) -> D2 (GPIO4)");
  Serial.println("  Servo4 (Elbow)    -> D3 (GPIO0)");
  Serial.println("  Servo5 (Gripper)  -> D5 (GPIO14)");
  
  // Initialize to center position
  servo1.write(pos1);
  servo2.write(pos2);
  servo3.write(pos3);
  servo4.write(pos4);
  servo5.write(pos5);
  
  delay(1000);
  Serial.println("\nSystem ready!\n");
  printHelp();
}

void loop() {
  // Check for serial commands
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    processCommand(input);
  }
  
  delay(10);
}

void processCommand(String cmd) {
  cmd.toLowerCase();
  
  // WASD keyboard control
  if (cmd == "w") {
    // W - Shoulder up (servo3 increase angle)
    int newAngle = constrain(pos3 + STEP_SIZE, 0, 180);
    servo3.write(newAngle);
    pos3 = newAngle;
    Serial.print("W: Shoulder UP -> ");
    Serial.print(pos3);
    Serial.println("°");
    
  } else if (cmd == "s") {
    // S - Shoulder down (servo3 decrease angle)
    int newAngle = constrain(pos3 - STEP_SIZE, 0, 180);
    servo3.write(newAngle);
    pos3 = newAngle;
    Serial.print("S: Shoulder DOWN -> ");
    Serial.print(pos3);
    Serial.println("°");
    
  } else if (cmd == "a") {
    // A - Base rotate left (servo2 increase angle)
    int newAngle = constrain(pos2 + STEP_SIZE, 0, 180);
    servo2.write(newAngle);
    pos2 = newAngle;
    Serial.print("A: Base LEFT -> ");
    Serial.print(pos2);
    Serial.println("°");
    
  } else if (cmd == "d") {
    // D - Base rotate right (servo2 decrease angle)
    int newAngle = constrain(pos2 - STEP_SIZE, 0, 180);
    servo2.write(newAngle);
    pos2 = newAngle;
    Serial.print("D: Base RIGHT -> ");
    Serial.print(pos2);
    Serial.println("°");
    
  } else if (cmd == "q") {
    // Q - Elbow up (servo4 decrease angle)
    int newAngle = constrain(pos4 - STEP_SIZE, 0, 180);
    servo4.write(newAngle);
    pos4 = newAngle;
    Serial.print("Q: Elbow UP -> ");
    Serial.print(pos4);
    Serial.println("°");
    
  } else if (cmd == "e") {
    // E - Elbow down (servo4 increase angle)
    int newAngle = constrain(pos4 + STEP_SIZE, 0, 180);
    servo4.write(newAngle);
    pos4 = newAngle;
    Serial.print("E: Elbow DOWN -> ");
    Serial.print(pos4);
    Serial.println("°");
    
  } else if (cmd == "z") {
    // Z - Wrist up (servo1 increase angle)
    int newAngle = constrain(pos1 + STEP_SIZE, 0, 180);
    servo1.write(newAngle);
    pos1 = newAngle;
    Serial.print("Z: Wrist UP -> ");
    Serial.print(pos1);
    Serial.println("°");
    
  } else if (cmd == "x") {
    // X - Wrist down (servo1 decrease angle)
    int newAngle = constrain(pos1 - STEP_SIZE, 0, 180);
    servo1.write(newAngle);
    pos1 = newAngle;
    Serial.print("X: Wrist DOWN -> ");
    Serial.print(pos1);
    Serial.println("°");
    
  } else if (cmd == "help" || cmd == "h") {
    printHelp();
    
  } else if (cmd == "status" || cmd == "s") {
    printStatus();
    
  } else if (cmd == "reset" || cmd == "r") {
    resetPosition();
    
  } else if (cmd == "open") {
    openGripper();
    
  } else if (cmd == "close") {
    closeGripper();
    
  } else if (cmd == "[") {
    // [ - Open gripper quickly
    openGripper();
    
  } else if (cmd == "]") {
    // ] - Close gripper quickly
    closeGripper();
    
  } else if (cmd == "save") {
    // Save current position (print for recording)
    Serial.println("\n=== Current Position (Copy for PRESET_ACTIONS.cpp) ===");
    Serial.print("servo1.write("); Serial.print(pos1); Serial.println(");  // Wrist");
    Serial.print("servo2.write("); Serial.print(pos2); Serial.println(");  // Base");
    Serial.print("servo3.write("); Serial.print(pos3); Serial.println(");  // Shoulder");
    Serial.print("servo4.write("); Serial.print(pos4); Serial.println(");  // Elbow");
    Serial.print("servo5.write("); Serial.print(pos5); Serial.println(");  // Gripper");
    Serial.print("\n// Or use: move ");
    Serial.print(pos1); Serial.print(" ");
    Serial.print(pos2); Serial.print(" ");
    Serial.print(pos3); Serial.print(" ");
    Serial.print(pos4); Serial.print(" ");
    Serial.println(pos5);
    Serial.println("======================================================\n");
    
  } else if (cmd.startsWith("set ")) {
    // Format: set 1 90 (servo number, angle)
    int space1 = cmd.indexOf(' ');
    int space2 = cmd.indexOf(' ', space1 + 1);
    
    if (space2 > 0) {
      int servoNum = cmd.substring(space1 + 1, space2).toInt();
      int angle = cmd.substring(space2 + 1).toInt();
      
      setServoAngle(servoNum, angle);
    } else {
      Serial.println("Error: Use format 'set <servo> <angle>'");
    }
    
  } else if (cmd.startsWith("move ")) {
    // Format: move 90 45 120 60 30 (5 angles for all servos)
    int angles[5];
    int count = parseAngles(cmd.substring(5), angles, 5);
    
    if (count == 5) {
      moveAllServos(angles);
    } else {
      Serial.println("Error: Need 5 angles. Use 'move <a1> <a2> <a3> <a4> <a5>'");
    }
    
  } else if (cmd == "cube") {
    grabCube();
  } else if (cmd == "cylinder") {
    grabCylinder();
  } else if (cmd == "hat") {
    grabHat();
  } else if (cmd == "boat") {
    grabBoat();
  } else {
    Serial.println("Unknown command. Type 'help' for command list.");
  }
}

void printHelp() {
  Serial.println("===== Available Commands =====");
  Serial.println("=== WASD Keyboard Control ===");
  Serial.println("  a / d    - Base LEFT / RIGHT (Servo2)");
  Serial.println("  w / s    - Shoulder UP / DOWN (Servo3)");
  Serial.println("  q / e    - Elbow UP / DOWN (Servo4)");
  Serial.println("  z / x    - Wrist UP / DOWN (Servo1)");
  Serial.println("  [ / ]    - Gripper OPEN / CLOSE (Servo5)");
  Serial.println("");
  Serial.println("=== Quick Commands ===");
  Serial.println("  help                  - Show this help");
  Serial.println("  status                - Show current servo positions");
  Serial.println("  reset                 - Reset all servos to init position");
  Serial.println("  set <servo> <angle>   - Set servo N to angle (e.g., set 1 45)");
  Serial.println("  move <a1> .. <a5>     - Move all servos (e.g., move 90 60 120 45 30)");
  Serial.println("  open                  - Open gripper (servo5 -> 30°)");
  Serial.println("  close                 - Close gripper (servo5 -> 90°)");
  Serial.println("  save                  - Print current angles (for recording)");
  Serial.println("==============================\n");
}

void printStatus() {
  Serial.println("\n=== Current Positions ===");
  Serial.print("  Servo1 (Wrist):    "); Serial.print(pos1); Serial.println("°");
  Serial.print("  Servo2 (Base):     "); Serial.print(pos2); Serial.println("°");
  Serial.print("  Servo3 (Shoulder): "); Serial.print(pos3); Serial.println("°");
  Serial.print("  Servo4 (Elbow):    "); Serial.print(pos4); Serial.println("°");
  Serial.print("  Servo5 (Gripper):  "); Serial.print(pos5); Serial.println("°");
  Serial.println("========================\n");
}

void resetPosition() {
  Serial.println("Resetting to init position...");
  
  pos1 = 90;
  pos2 = 45;
  pos3 = 100;
  pos4 = 0;
  pos5 = 90;
  
  servo1.write(pos1);
  servo2.write(pos2);
  servo3.write(pos3);
  servo4.write(pos4);
  servo5.write(pos5);
  
  delay(500);
  Serial.println("Reset complete!\n");
}

void setServoAngle(int servoNum, int angle) {
  if (servoNum < 1 || servoNum > 5) {
    Serial.println("Error: Servo number must be 1-5");
    return;
  }
  
  if (angle < 0 || angle > 180) {
    Serial.println("Error: Angle must be 0-180");
    return;
  }
  
  switch (servoNum) {
    case 1:
      servo1.write(angle);
      pos1 = angle;
      Serial.print("Servo1 -> ");
      break;
    case 2:
      servo2.write(angle);
      pos2 = angle;
      Serial.print("Servo2 -> ");
      break;
    case 3:
      servo3.write(angle);
      pos3 = angle;
      Serial.print("Servo3 -> ");
      break;
    case 4:
      servo4.write(angle);
      pos4 = angle;
      Serial.print("Servo4 -> ");
      break;
    case 5:
      servo5.write(angle);
      pos5 = angle;
      Serial.print("Servo5 -> ");
      break;
  }
  
  Serial.print(angle);
  Serial.println("°");
}

void moveAllServos(int angles[]) {
  Serial.println("Moving all servos...");
  
  servo1.write(angles[0]);
  servo2.write(angles[1]);
  servo3.write(angles[2]);
  servo4.write(angles[3]);
  servo5.write(angles[4]);
  
  pos1 = angles[0];
  pos2 = angles[1];
  pos3 = angles[2];
  pos4 = angles[3];
  pos5 = angles[4];
  
  delay(500);
  Serial.print("Positions: ");
  for (int i = 0; i < 5; i++) {
    Serial.print(angles[i]);
    if (i < 4) Serial.print(", ");
  }
  Serial.println("\n");
}

void openGripper() {
  Serial.println("Opening gripper...");
  servo5.write(30);
  pos5 = 30;
  delay(500);
  Serial.println("Gripper opened!\n");
}

void closeGripper() {
  Serial.println("Closing gripper...");
  servo5.write(90);
  pos5 = 90;
  delay(500);
  Serial.println("Gripper closed!\n");
}

int parseAngles(String str, int* angles, int maxCount) {
  int count = 0;
  int startIdx = 0;
  
  str.trim();
  
  while (count < maxCount && startIdx < str.length()) {
    int spaceIdx = str.indexOf(' ', startIdx);
    String numStr;
    
    if (spaceIdx == -1) {
      numStr = str.substring(startIdx);
      startIdx = str.length();
    } else {
      numStr = str.substring(startIdx, spaceIdx);
      startIdx = spaceIdx + 1;
    }
    
    numStr.trim();
    if (numStr.length() > 0) {
      angles[count] = numStr.toInt();
      count++;
    }
  }
  
  return count;
}
