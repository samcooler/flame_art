#include <Adafruit_PWMServoDriver.h>
// #include <Adafruit_GFX.h>
// #include <Adafruit_SSD1306.h>
#include <PCF8575.h>


// set up display
#define SCREEN_WIDTH 128 // OLED display width, in pixels
#define SCREEN_HEIGHT 64 // OLED display height, in pixels

#define OLED_RESET     -1
#define SCREEN_ADDRESS 0x3C 
// Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// PCF8575 GPIO module
PCF8575 pcf8575(0x20);

// SERVOS
const int NUM_VALVES = 10;
float valveStates[NUM_VALVES];      // Stores valve states (0.0 to 1.0)
// int calMin[NUM_VALVES] = {2420, 2420, 2420, 2420}; // min flow calibration (highest number)
int calMin[NUM_VALVES] = {2400,2400,2400,2400,2400,2400,2400,2400,2400,2400};
int calMax[NUM_VALVES];             // max calibration values, define below using range from min (microseconds)
const int calRange = 1000;          // msec also, low to high

const int INTERVAL_MAX = 1400;
const int INTERVAL_MIN = 300;

// SOLENOID
// const int SOLENOID_PINS[NUM_VALVES] = {22, 19, 17, 15};
int SOLENOID_PINS[NUM_VALVES];// = {0,1,2,3,4,5,6,7,8,9};
bool prevValveState = false;
bool prevSolenoidState = false;
bool currentSolenoidState = false;
bool currentValveState = false;

int solenoidDutyCycleInit = 30;
int solenoidDutyCycle[NUM_VALVES];

long startTime = 0;

struct ValveData {
  float currentValue;
  float nextValue;
  unsigned long previousTime;
  unsigned long nextTime;
  unsigned long solenoidToggleTime;
  bool solenoidState;
};

ValveData valveData[NUM_VALVES];
bool artMode = 1;

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

int valueToMsec(int valveNum, float state) {
  return (calMin[valveNum] + (calMax[valveNum] - calMin[valveNum]) * state);
}

void controlValve(int valveNum, int servoValue) {
  pwm.writeMicroseconds(valveNum, servoValue);
}

void setValveState(int valveNum, float state, bool print = 0) {
  valveStates[valveNum] = state;
  int servoValue = valueToMsec(valveNum, state);
  controlValve(valveNum, servoValue);
  if (print) {
    Serial.print("Set valve ");
    Serial.print(valveNum + 1);
    Serial.print(" to state ");
    Serial.println(state);
  }
}

void setSolenoidState(int valveNum, bool state) {
  pcf8575.write(valveNum, state); // valveNum is the pin number on PCF8575
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("START");
  
  pcf8575.begin(); // Initialize PCF8575

  // start display
  // while(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
  //   Serial.println(F("SSD1306 allocation failed"));
  //   delay(200);
  // }
  // display.clearDisplay();
  // display.setTextSize(1);      // Normal 1:1 pixel scale
  // display.setTextColor(SSD1306_WHITE); // Draw white text
  // display.display();
  // display.drawPixel(10, 10, SSD1306_WHITE);
  // display.display();
  // delay(1000);
  // display.drawPixel(20, 10, SSD1306_WHITE);
  // display.display();
  // drawDisplay();

  pwm.begin();
  Serial.println("servo pwm output begun");
  pwm.setOscillatorFrequency(25200000);
  pwm.setPWMFreq(50);  // Analog servos run at ~50 Hz updates

  for (int i = 0; i < NUM_VALVES; i++) {
    solenoidDutyCycle[i] = solenoidDutyCycleInit;
    valveStates[i] = 0.0;
    // calMin[i] = 2500;  // Default values
    calMax[i] = calMin[i] - calRange;  // Default values
  
    // enable and turn off solenoid outputs
    setSolenoidState(i, 0);  // Initially off
  }

  Serial.println("All zero");
  // Set each valve to zero
  for (int i = 0; i < NUM_VALVES; i++) {
    setValveState(i, 0.0);
  }
  delay(1000);  // Wait for 1 second

  // Pulse all valves to 0.2
  Serial.println("All 0.2");
  for (int i = 0; i < NUM_VALVES; i++) {
    setValveState(i, 0.2);
  }
  delay(200);  // Wait for 1 second

  // Set all valves back to zero
  Serial.println("All zero");
  for (int i = 0; i < NUM_VALVES; i++) {
    setValveState(i, 0.0);
  }
  delay(2000);  // Wait for 2 second

  Serial.println("Valve Controller Interface");
  Serial.println("Type commands and press enter to execute.");
  Serial.print("> ");  // Command line symbol
}

// void displayValves(bool force = 0);

void loop() {

  if (artMode) {
    updateArtMode();
    delay(10);  // Add a delay to throttle the output rate
  }

  static String commandBuffer;  // Holds the incoming command
  while (Serial.available() > 0) {
    char inChar = Serial.read();      // Read a character
    if (inChar == '\n') {             // Check for the end of the command
      processCommand(commandBuffer);  // Process the complete command
      commandBuffer = "";             // Clear the command buffer
      Serial.print("> ");             // Display the command line symbol again
    } else {
      commandBuffer += inChar;  // Add the character to the command buffer
    }
  }
  delay(1);
}

int displayCounter = 0;  // Add this global variable at the top of your code

void displayValves(bool force = 0) {
  displayCounter++;
  if (!force && (displayCounter % 10 != 0)) {  // Change 10 to any other number to adjust the display frequency
    return;                                    // Skip displaying this frame
  }
  displayCounter = 0;  // Reset the counter after a display

  Serial.println();
  for (int i = 0; i < NUM_VALVES; i++) {
    Serial.print("Valve ");
    Serial.print(i + 1);
    Serial.print(": |");
    int position = (int)(valveStates[i] * 16);
    for (int j = 0; j <= 16; j++) {
      if (j == position) {
        Serial.print("X");
      }
       else {
        Serial.print(" ");
      }
    }
    Serial.print("| Cal: (");
    Serial.print(calMin[i]);
    Serial.print(", ");
    Serial.print(calMax[i]);
    Serial.print(") Val: ");
    Serial.print(valveStates[i], 2);
    Serial.print(" (");
    Serial.print(valueToMsec(i, valveStates[i]));
    Serial.println(")");
  }
  // drawDisplay();

}


void testValve(int valveNum) {
  float testPositions[3] = { 0.0, 0.5, 1.0 };
  for (int j = 0; j < 3; j++) {
    setValveState(valveNum, testPositions[j]);
    delay(1000);
  }
  setValveState(valveNum, 0.0);  // Reset to 0 after testing
}

void rangeTest() {
  for (int i = 0; i < NUM_VALVES; i++) {
    testValve(i);
  }
  Serial.println("Range test completed");
}

void setCalibration(int valveNum, int minVal, int maxVal) {
  calMin[valveNum] = minVal;
  calMax[valveNum] = maxVal;
  Serial.print("Calibrated valve ");
  Serial.print(valveNum + 1);
  Serial.print(" with min ");
  Serial.print(minVal);
  Serial.print(" and max ");
  Serial.println(maxVal);
  testValve(valveNum);  // Test the specified valve after calibration
}

void setupArtMode() {
  for (int i = 0; i < NUM_VALVES; i++) {
    valveData[i].currentValue = 0.0;
    valveData[i].nextValue = random(0, 100) / 100.0;
    valveData[i].previousTime = millis();
    valveData[i].nextTime = millis() + random(1000, 2000);  // Random time between 1 to 5 seconds
    valveData[i].solenoidToggleTime = valveData[i].previousTime + random(0, (valveData[i].nextTime - valveData[i].previousTime));
    valveData[i].solenoidState = random(2);  // Randomly set to true or false
  }
  artMode = true;
}


void updateArtMode() {
  unsigned long currentTime = millis();
  for (int i = 0; i < NUM_VALVES; i++) {
    if (currentTime >= valveData[i].nextTime) {
      // Update data for next interpolation cycle
      
      Serial.print(valveData[i].previousTime);
      valveData[i].previousTime = valveData[i].nextTime;
      valveData[i].nextTime = currentTime + random(INTERVAL_MIN, INTERVAL_MAX);
      valveData[i].currentValue = valveData[i].nextValue;
      valveData[i].nextValue = random(0, 100) / 100.0;
    }
    // Interpolate valve position
    float t = (float)(currentTime - valveData[i].previousTime) / (valveData[i].nextTime - valveData[i].previousTime);
    float interpolatedValue = lerp(valveData[i].currentValue, valveData[i].nextValue, t);
    setValveState(i, interpolatedValue);

    // Change solenoid value
    if (currentTime >= valveData[i].solenoidToggleTime && currentTime < valveData[i].nextTime) {
      // Determine if the solenoid should be turned on based on the duty cycle
      bool shouldTurnOn = random(100) < solenoidDutyCycle[i];
      setSolenoidState(i, shouldTurnOn);
      valveData[i].solenoidToggleTime = valveData[i].nextTime + random(0, (valveData[i].nextTime - currentTime));
      valveData[i].solenoidState = shouldTurnOn;

    }
  }
  displayValves();
}

void demo_pulses() {
  for (float fraction = 0.1; fraction <= 1.0; fraction += 0.1) {
    // Set all servo valves to the fraction and wait
    for (int i = 0; i < NUM_VALVES; i++) {
      setValveState(i, fraction);
    }
    displayValves(1);
    delay(500); // Adjust the delay as needed

    // Open all solenoids, wait, and then close them
    for (int i = 0; i < NUM_VALVES; i++) {
      setSolenoidState(i, 1);
    }
    displayValves(1);
    delay(500); // Adjust the delay as needed

    for (int i = 0; i < NUM_VALVES; i++) {
      setSolenoidState(i, 0);
    }
    displayValves(1);
    delay(500); // Adjust the delay as needed
  }
}

void demo_wave_solenoids() {
  int length = 3;
  // setSolenoidState((start + add) % NUM_VALVES, 1);

  for(int start = 0; start < NUM_VALVES; start ++) {
    for(int curr = 0; curr < NUM_VALVES; curr ++) {
      // for(int add = 0; add < length; add ++) {
      //   setSolenoidState((start + add) % NUM_VALVES, 1);
      // }
      if(curr == start) {
        setSolenoidState(curr, 1);
      } else {
        setSolenoidState(curr, 0);
      }
      
    }
    delay(2000);
  }
}


void demo_wave() {
  // Close all solenoids
  for (int i = 0; i < NUM_VALVES; i++) {
    setSolenoidState(i, 0);
  }

  for (int i = 0; i < NUM_VALVES; i++) {
    // Open servo to 100%
    setValveState(i, 1.0);
    delay(50);

    // Open solenoid
    setSolenoidState(i, 1);

    // Change servo valve from 100% to 10% and back
    float step = .05;
    int wait = 300;
    for (float fraction = 1.0; fraction >= 0.1; fraction -= step) {
      setValveState(i, fraction);
      delay(wait);
      displayValves(1);
    }
    for (float fraction = 0.1; fraction <= 1.0; fraction += step) {
      setValveState(i, fraction);
      delay(wait);
      displayValves(1);
    }

    // Close solenoid
    setSolenoidState(i, 0);
    displayValves(1);
  }
}


void demo_multiwave() {
  const int repeatCount = 3; // Number of times to repeat the wave

  const int waveSteps = 20; // Total steps in the wave (up and down)
  float wavePattern[waveSteps];

  // Initialize the wave pattern
  for (int i = 0; i < waveSteps / 2; i++) {
    // Increase from 10% to 100% in the first half of the wave
    wavePattern[i] = 0.1 + (i / (float)(waveSteps / 2 - 1)) * (1.0 - 0.1);
  }

  for (int i = waveSteps / 2; i < waveSteps; i++) {
    // Decrease from 100% back to 10% in the second half of the wave
    wavePattern[i] = 1.0 - ((i - waveSteps / 2) / (float)(waveSteps / 2 - 1)) * (1.0 - 0.1);
  }

  // Open solenoids
  for (int i = 0; i < NUM_VALVES; i++) {
    setSolenoidState(i, 1);
  }

  for (int repeat = 0; repeat < repeatCount; repeat++) {
    for (int step = 0; step < waveSteps; step++) {
      for (int valve = 0; valve < NUM_VALVES; valve++) {
        // Calculate the index for each valve with an offset that evenly splits the wave
        int index = (step + (valve * waveSteps / NUM_VALVES)) % waveSteps;
        setValveState(valve, wavePattern[index]);
      }
      displayValves(1);
      delay(100); // Adjust the delay as needed
    }
  }

  // Set all valves back to zero at the end
  for (int i = 0; i < NUM_VALVES; i++) {
    setValveState(i, 0.5);
  }
}


float lerp(float a, float b, float t) {
  return a + t * (b - a);
}

void processCommand(String command) {
  char cmdType = command.charAt(0);
  artMode = false;  // Exit art mode if active

  if (cmdType == 'd') {
    displayValves(1);
    return;
  } else if (cmdType == 'r') {
    rangeTest();
    return;
  } else if (cmdType == 'a') {
    setupArtMode();
    return;
  }

  int spaceIndex = command.indexOf(' ');
  if (cmdType == 'v') {
    int valveNum = command.charAt(1) - '0';
    if (valveNum < 1 || valveNum > NUM_VALVES) {
      Serial.println("Invalid valve number");
      return;
    }
    valveNum -= 1;  // Adjust to 0-indexed
    if (spaceIndex == -1) {
      Serial.println("Unrecognized command");
      return;
    }    
    float valveState = command.substring(spaceIndex + 1).toFloat();
    setValveState(valveNum, valveState);
    displayValves(1);
  }
  
  if (cmdType == 'c') {
    int valveNum = command.charAt(1) - '0';
    int secondSpaceIndex = command.indexOf(' ', spaceIndex + 1);
    if (secondSpaceIndex == -1) {
      Serial.println("Unrecognized command");
      return;
    }
    int minVal = command.substring(spaceIndex + 1, secondSpaceIndex).toInt();
    int maxVal = command.substring(secondSpaceIndex + 1).toInt();
    setCalibration(valveNum, minVal, maxVal);
  }

  if (cmdType == 'n') {
    int number = command.charAt(1) - '0';
    int solenoidState = command.charAt(2) - '0';
    if (solenoidState == 0 || solenoidState == 1) {
      // for (int i = 0; i < NUM_VALVES; i++) {
      setSolenoidState(number, solenoidState);
      Serial.print("Solenoid ");
      Serial.print(number);
      Serial.print(" set: ");
      Serial.println(solenoidState ? "OPEN" : "CLOSED");
      // }
    } else {
      Serial.println("Invalid solenoid state. Use 0 for CLOSED, 1 for OPEN.");
    }
  }

  // demo mode makes some nice patterns
  if (cmdType == 'm') {
    int demoNum = command.charAt(2) - '0';
    switch (demoNum) {
      case 1: demo_pulses(); break;
      case 2: demo_wave(); break;
      case 3: demo_multiwave(); break;
      case 4: demo_wave_solenoids(); break;
      default: Serial.println("Invalid demo mode number"); break;
    }
    return;
  }

  if (cmdType == 's') {
    int firstSpaceIndex = command.indexOf(' ');
    if (firstSpaceIndex == -1) {
      Serial.println("Unrecognized command");
      return;
    }
    int secondSpaceIndex = command.indexOf(' ', firstSpaceIndex + 1);
    if (secondSpaceIndex == -1) {
      Serial.println("Unrecognized command");
      return;
    }
    int thirdSpaceIndex = command.indexOf(' ', secondSpaceIndex + 1);
    if (thirdSpaceIndex == -1) {
      Serial.println("Unrecognized command");
      return;
    }

  }
}

// void drawDisplay() { // Add a default max height parameter
//   return;
//   int maxRectHeight = SCREEN_HEIGHT / 2;
//   display.clearDisplay(); // Clear the display buffer
//   int rectWidth = SCREEN_WIDTH / 10; // Divide screen width by number of valves

//   for (int i = 0; i < NUM_VALVES; i++) {
//     // Calculate the rectangle's height based on the valve state and the maximum height
//     int rectHeight = valveStates[i] * maxRectHeight; 

//     // Calculate the Y position so the rectangle is at the bottom
//     int rectY = SCREEN_HEIGHT - rectHeight;

//     // If the solenoid is ON, fill the rectangle. Otherwise, just draw the outline.
//     if (digitalRead(SOLENOID_PINS[i]) == HIGH) {
//       display.fillRect(i * rectWidth, rectY, rectWidth, rectHeight, SSD1306_WHITE);
//     } else {
//       display.drawRect(i * rectWidth, rectY, rectWidth, rectHeight, SSD1306_WHITE);
//     }
//   }

//   display.display();
// }
