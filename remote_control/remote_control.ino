// IF NO ACTIVITY, HOLD A BUTTON DOWN FOR 10+ SECONDS:
// v4 introduces a "light sleep" mode. Not actual "deep sleep," just a 10-second delay in the loop if no recent button activity.
// if it seems like there might be problems with sleep code, delete or comment out all lines tagged with "//sleep"

// Wifi- and OSC-related code is tagged with //wifi
//!!! Wifi differences from imu.ino: 
// - I included WiFi.h instead of WiFi101.h, but this at least declared WL_IDLE_STATUS for me and allowed me to connect to a router.

//OSC for Light Curve doc: https://docs.google.com/document/d/1OyvInZ4yD63il6pFvKUpxE_5A0A4D1BgE_5zifzlJRg/edit?usp=sharing

//Rough Outline:
// Create arrays of the button states and previous button states of a number of (probably 30) buttons.
// Map those arrays to 15 pins each on 2 I/O expander boards
// Listen for input on 30 pins
// Print out via serial which button # was pressed, and which pin number, on which MCP I/O expander, it's assigned to.
// (In that section, I can later add output to wifi/artnet/whatever external communication we're using)

// Example of typical button activity command:
/////// mcp[whichMCP[i]].digitalRead(buttonPin[i]);

//To Do:
//why send to both ports 6511 and 6512
//figure out if Serial output is slowing things down and if so, recommend disconnecting purple wire.  Then again, watch for stability issues caused by removal of this delay and consider adding something like delay(1)
//or maybe change baudrate of serial to 115200, 12 times 9600.
//Maybe add button/switch/knob for different modes?  Or board reset?  Or power on/off?  Or charge port?
//Maybe add LED or other indicator for which mode it's in?


//Decided not to do:
//See if debounce is necessary?  Or just implement it if you're bored? - edge detection moved downstream

//done or not needed
//include code from calib.ino (probalby not needed, left below commented out)
//check OSC message format, include link to formatting doc.
//test: short pin 6 to see debug

/*
MCP23x17 Pin #	Pin Name	Pin ID
21..............GPA0......0
22..............GPA1......1
23..............GPA2......2
24..............GPA3......3
25..............GPA4......4
26..............GPA5......5
27..............GPA6......6
28..............GPA7......7
1 ..............GPB0......8
2 ..............GPB1......9
3 ..............GPB2......10
4 ..............GPB3......11
5 ..............GPB4......12
6 ..............GPB5......13
7 ..............GPB6......14
8 ..............GPB7......15
*/

#include <Adafruit_MCP23X17.h>

//#include <WiFi101.h> //if I need this, maybe ask which version I need?
#include <WiFi.h>
#include <WiFiUdp.h> //wifi

// From "OSC" library in Arduino. You can find it by searching for "Open Sound Control" in library manager.
#include <OSCMessage.h> //wifi

const uint8_t debugJumperPin = 6;       //pin to short to ground if you want serial output for debug
bool serialOutput;                      //do you want serial output for debugging? (if so, ground debugJumperPin)
const unsigned long lightSleepTimeout = 120000; //number of milliseconds before "light sleep" mode begins if no button activity is detected. 120000 = 2 minutes
const unsigned long lightSleepCycle = 10000; //how long you might have to hold down a button to "wake" it from "light sleep" (number of milliseconds of delay to introduce into each iteration of the loop while in "light sleep" mode)
unsigned long lastButtonActivity = 1000000000; //timestamp at which last button activity was detected

//wifi
const uint8_t maxTimeBetweenUDP = 100; //maximum milliseconds before re-sending button status
int status = WL_IDLE_STATUS;

// //Shlomit's house
// IPAddress ip(192, 168, 1, 30);
// IPAddress gateway(192, 168, 1, 1);
// IPAddress subnet(255, 255, 255, 0);
// char SSID[] = "Verizon_VJ6D43";
// char PASS[] = "TheNet4me!";

// //Tinker's House
// IPAddress ip(192, 168, 1, 30);
// IPAddress gateway(192, 168, 1, 254);
// IPAddress subnet(255, 255, 255, 0);
// char SSID[] = "tinker and teatime";
// char PASS[] = "andtrextoo";

//LightCurve
IPAddress ip(192, 168, 13, 30);
IPAddress gateway(192, 168, 13, 1);
IPAddress subnet(255, 255, 255, 0);
char SSID[] = "lightcurve";
char PASS[] = "curvelight";

WiFiUDP udp;
unsigned long lastUDPPacketSent = 0;  //timestamp at which last UDP packet was sent

#define BOTTOM 0 //which MCP I/O expansion board is a button plugged into
#define TOP 1 //which MCP I/O expansion board is a button plugged into

//declaring I/O expander objects 
Adafruit_MCP23X17 mcp[2];

const uint8_t numberOfButtons = 30;

const uint8_t whichMCP[] = {
/* MCP for button 0 */  BOTTOM,
/* MCP for button 1 */  BOTTOM,
/* MCP for button 2 */  BOTTOM,
/* MCP for button 3 */  BOTTOM,
/* MCP for button 4 */  BOTTOM,
/* MCP for button 5 */  BOTTOM,
/* MCP for button 6 */  BOTTOM,
/* MCP for button 7 */  BOTTOM,
/* MCP for button 8 */  BOTTOM,
/* MCP for button 9 */  BOTTOM,
/* MCP for button 10 */ BOTTOM,
/* MCP for button 11 */ BOTTOM,
/* MCP for button 12 */ BOTTOM,
/* MCP for button 13 */ BOTTOM,
/* MCP for button 14 */ TOP, // NOTE THAT BUTTON 14 IS ON THE TOP HALF, DESPITE BEING THE 15th BUTTON.  (button 19 is on the bottom half)
/* MCP for button 15 */ TOP,
/* MCP for button 16 */ TOP,
/* MCP for button 17 */ TOP,
/* MCP for button 18 */ TOP,
/* MCP for button 19 */ BOTTOM, // NOTE THAT BUTTON 19 IS ON THE BOTTOM HALF, DESPITE BEING IN THE SECOND HALF OF THE BUTTONS SEQUENTIALLY.  (button 14 is on the bottom half)
/* MCP for button 20 */ TOP,
/* MCP for button 21 */ TOP,
/* MCP for button 22 */ TOP,
/* MCP for button 23 */ TOP,
/* MCP for button 24 */ TOP,
/* MCP for button 25 */ TOP,
/* MCP for button 26 */ TOP,
/* MCP for button 27 */ TOP,
/* MCP for button 28 */ TOP,
/* MCP for button 29 */ TOP
};

const uint8_t buttonPin[] = {
  // The state of "button 0" will be stored in buttonState[0], the pin for "button 0" will be stored in buttonPin[0], etc.
0, // pin for button 0
1, // pin for button 1
2, // pin for button 2
3, // pin for button 3
4, // pin for button 4
5, // pin for button 5
6, // pin for button 6
7, // pin for button 7
8, // pin for button 8
9, // pin for button 9
10, // pin for button 10
11, // pin for button 11
12, // pin for button 12
13, // pin for button 13
4, // pin for button 14 // NOTE THAT BUTTON 14 USES THE PIN THAT, IF IT WERE LABELED SEQUENTIALLY, WOULD BELONG TO BUTTON 19.  (due to the semi-arbitrary way in which the halves were constructed and the subsequent development of the face-numbering layout, no arrangement of button numbers could keep a perfectly sequential half.  This layout keeps all buttons except 14 and 19 with their respective "halves" of the sequential list of buttons.  This is why they have swapped pin numbers)
0, // pin for button 15
1, // pin for button 16
2, // pin for button 17
3, // pin for button 18
14, // pin for button 19 //SEE NOTE ON BUTTON 14 ABOVE
5, // pin for button 20
6, // pin for button 21
7, // pin for button 22
8, // pin for button 23
9, // pin for button 24
10, // pin for button 25
11, // pin for button 26
12, // pin for button 27
13, // pin for button 28
14 // pin for button 29 //which is actually the 30th button
};


uint8_t buttonState[numberOfButtons];
uint8_t lastButtonState [numberOfButtons];

void setup() {
  pinMode(debugJumperPin, INPUT_PULLUP);
  Serial.begin(9600);
  //while (!Serial);

  if (!mcp[0].begin_I2C(0x20)) {
    Serial.println("Error initializing expander 0x20.");
    //while (1);
    }

  if (!mcp[1].begin_I2C(0x21)) {
    Serial.println("Error initializing expander 0x21.");
    //while (1);
    }

  for (uint8_t i = 0; i < numberOfButtons; i++) {
    // configure button pins for input with pull up
    mcp[whichMCP[i]].pinMode(buttonPin[i], INPUT_PULLUP);
    //Set button state values to "OFF"
    buttonState[i]=1;
    lastButtonState[i]=1;
  }
 
  //wifi
  int checkCount = 0;
  while (WiFi.status() != WL_CONNECTED)
  {
    if (checkCount <= 0)
    {
      Serial.print("Trying to connect to SSID: ");
      Serial.println(SSID);

      WiFi.begin(SSID, PASS);
      WiFi.config(ip, gateway, subnet);
      checkCount = 25;
    }

    delay(400);
    checkCount--;
  }
  Serial.println("Connected to wifi");
  printWiFiStatus();

  //wifi
  udp.begin(6510);
  Serial.println("Reading events");
  delay(100);

  lastButtonActivity = millis(); //by pretending a button was just pressed, the timer begins now for when "light sleep" mode should begin  //sleep 
  Serial.println("Looping...");
}

void loop() {
  //delay(1000); //uncomment for ease of reading debug information
  serialOutput = !digitalRead(debugJumperPin); //input pullup, read the relevant IO pin to decide whether to send Serial messages for debugging
  bool buttonChanged = false; // buttons have not yet been pressed or released this time through the loop
  if(serialOutput) {printWiFiStatus();}
  //wifi
  IPAddress targetIpAddress(192, 168, 13, 255); //lightcurve
  //IPAddress targetIpAddress(192, 168, 1, 136); //Tink's laptop for debug
  OSCMessage msg("/LC/nozzles");

  for (uint8_t i = 0; i < numberOfButtons; i++) {
    buttonState[i] = mcp[whichMCP[i]].digitalRead(buttonPin[i]);
    if (buttonState[i] == LOW) {
      // if the current state is LOW then the button went from unpressed to pressed (off to on) (remember input pullup):
      //wifi - add button state to OSC message.
      msg.add('T');
      if(serialOutput){Serial.print("T");}
    } else {
      // if the current state is HIGH then the button went from pressed to unpressed (on to off):
      //wifi - add button state to OSC message.
      msg.add('F'); 
      if(serialOutput){Serial.print("F");} 
    }

    if (buttonState[i] != lastButtonState[i]) {
      // if the state of this button has changed, set a flag to send a UDP message this time through the loop, and maybe print out previous button state and current button state for debugging
      //   also mark the time of this button activity for purposes of deciding whether to go into "sleep mode"
      //wifi
      buttonChanged = true;
      lastButtonActivity = millis();

        //if(serialOutput){Serial.print(lastButtonState[i]);}
        //if(serialOutput){Serial.print(" ");}
        //if(serialOutput){Serial.print(buttonState[i]);}
        //if(serialOutput){Serial.print(" ");}

      // if the state has changed, print out button number
      if(serialOutput){Serial.print("Button number ");}
      if(serialOutput){Serial.print(i);}
      
      if (buttonState[i] == LOW) {
        // if the current state is LOW then the button went from unpressed to pressed (off to on) (remember input pullup):

        //Print out button activity
        if(serialOutput){Serial.print(" is ON");}
      } else {
        // if the current state is HIGH then the button went from pressed to unpressed (on to off):
        if(serialOutput){Serial.print(" is OFF");}
      }
      
      //and whether on or off, print out the pressed/released button's assigned MCP and pin number
      if (whichMCP[i]==TOP) {
        if(serialOutput){Serial.print(", assigned to the _Top_ half MCP I/O expander, Pin # ");}}
      if (whichMCP[i]==BOTTOM) {
        if(serialOutput){Serial.print(", assigned to the _Bottom_ half MCP I/O expander, Pin #");}}
      if(serialOutput){Serial.println(buttonPin[i]);}
       
      // Delay a little bit to avoid bouncing
      //delay(50); //BUT DO THIS WITH MILLIS SEE LINK IN NOTES DOC
    }
    // save the current state as the last state, for next time through the loop
    lastButtonState[i] = buttonState[i];
  }

  if (buttonChanged || millis()>lastUDPPacketSent+maxTimeBetweenUDP) { //note this doesn't send a UDP packet every x amount of time, but rather waits the maxTimeBetweenUDP after any UDP send including ones triggered by button presses, so if someone is button-mashing, we don't need more packets sent.
    udp.beginPacket(targetIpAddress, 6511);
    msg.send(udp);
    udp.endPacket();
    // "only if you need to send to a second port on the same machine"
    //udp.beginPacket(targetIpAddress, 6512);
    //udp.beginPacket(targetIpAddress, 10000); //simulator on Tinker's laptop was listening on this port
    //msg.send(udp);
    //udp.endPacket();
    //lastUDPPacketSent = millis();  //reset timer on when the last UDP packet was sent
  }
  if(serialOutput){Serial.println("");}
  if(millis() > lastButtonActivity + lightSleepTimeout){  //sleep
    delay (lightSleepCycle);                              //sleep
  }                                                       //sleep
}

void printWiFiStatus()
{
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());

  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);

  long rssi = WiFi.RSSI();
  Serial.print("signal strength (RSSI):");
  Serial.print(rssi);
  Serial.println(" dBm");
}





// Eric said: "If you have issues with the WiFi, you can try copying the code from calib.ino beginWifi function, since that is running on an ESP32S3 and has some special settings"
// So far (August 10, 2024), wifi has been connecting to three different residential routers. Tests with Light Curve hardware forthcoming...
/*

// This should be called repeatedly, with a delay of at least 1ms between calls, until `isWifiConnected` returns true.
void beginWifi()
{
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  WiFi.useStaticBuffers(true);
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.setTxPower(WIFI_POWER_8_5dBm);
  WiFi.setMinSecurity(WIFI_AUTH_WEP);
  WiFi.config(ip, gateway, subnet);
  WiFi.begin(ssid, password);
}

// Returns true when wifi is connected
bool isWifiConnected()
{
  return WiFi.status() == WL_CONNECTED;
}

//Code to include in "setup()"
// Start trying to connect to wifi
beginWifi();

//Code to include in "loop()"
if (!isWifiConnected())
{
  updateArtMode();
  delay(10);
  msSinceLastWifiBegin += 10;
  if (msSinceLastWifiBegin > 800)
  {
    msSinceLastWifiBegin = 0;

    Serial.print("Status: ");
    switch (WiFi.status())
    {
    case WL_NO_SHIELD:
      Serial.println("WL_NO_SHIELD");
      break;
    case WL_IDLE_STATUS:
      Serial.println("WL_IDLE_STATUS");
      break;
    case WL_NO_SSID_AVAIL:
      Serial.println("WL_NO_SSID_AVAIL");
      break;
    case WL_SCAN_COMPLETED:
      Serial.println("WL_SCAN_COMPLETED");
      break;
    case WL_CONNECTED:
      Serial.println("WL_CONNECTED");
      break;
    case WL_CONNECT_FAILED:
      Serial.println("WL_CONNECT_FAILED");
      break;
    case WL_CONNECTION_LOST:
      Serial.println("WL_CONNECTION_LOST");
      break;
    case WL_DISCONNECTED:
      Serial.println("WL_DISCONNECTED");
      break;
    }

    Serial.println("Attempting to connect to wifi");
    beginWifi();
  }
}
else
{
  Serial.println("Wifi connected");
  if(serialOutput){printWiFiStatus();}
  artMode = false;
  artnetMode = true;
  beginArtnet();
}
*/
