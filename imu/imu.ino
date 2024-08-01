#include <Adafruit_BNO08x.h>

#include <SPI.h>
#include <WiFi101.h>
#include <WiFiUdp.h>

// From "OSC" library in Arduino. You can find it by searching for "Open Sound Control" in library manager.
#include <OSCBundle.h>
#include <OSCMessage.h>
#include <OSCTiming.h>

#define BNO08X_RESET -1

IPAddress ip(192, 168, 13, 211);
IPAddress gateway(192, 168, 13, 1);
IPAddress subnet(255, 255, 255, 0);

Adafruit_BNO08x bno08x(BNO08X_RESET);
sh2_SensorValue_t bnoSensorValue;

int status = WL_IDLE_STATUS;

// Create a secrets file with your network info that looks like:
// #define IMU_SSID "my ssid"
// #define IMU_PASS "password"
// #include "imu_secrets.h"
// char SSID[] = IMU_SSID;
// char PASS[] = IMU_PASS;
char SSID[] = "lightcurve";
char PASS[] = "curvelight";

WiFiUDP udp;

IPAddress targetIpAddress(192, 168, 13, 255);

void setup(void)
{
  Serial.begin(115200);
  // while (!Serial)
  delay(200);

  Serial.println("Light Curve IMU");

  WiFi.setPins(8, 7, 4, 2);
  if (WiFi.status() == WL_NO_SHIELD)
  {
    Serial.println("WiFi shield not detected. This means something is wrong with the code or you are running this on a different board. Goodbye.");
    while (true)
    {
      delay(10);
    }
  }

  Serial.println(" calling initial wificonnect in setup");
  wifiConnect();
  printWiFiStatus();

  Serial.println(" starting bno08x connection: begin_I2C");

  if (!bno08x.begin_I2C())
  {
    Serial.println("Failed to find BNO08x chip, resetting");
    delay(200);
    NVIC_SystemReset();
  }

  Serial.println("BNO08x Found!");

  for (int n = 0; n < bno08x.prodIds.numEntries; n++)
  {
    Serial.print("Part ");
    Serial.print(bno08x.prodIds.entry[n].swPartNumber);
    Serial.print(": Version :");
    Serial.print(bno08x.prodIds.entry[n].swVersionMajor);
    Serial.print(".");
    Serial.print(bno08x.prodIds.entry[n].swVersionMinor);
    Serial.print(".");
    Serial.print(bno08x.prodIds.entry[n].swVersionPatch);
    Serial.print(" Build ");
    Serial.println(bno08x.prodIds.entry[n].swBuildNumber);
  }

  tellBnoWhatReportsWeWant();

  udp.begin(6510);

  Serial.println("Reading events");
  delay(100);
}

void wifiConnect(void) {
  int checkCount = 0;

  WiFi.config(ip, gateway, subnet);
  WiFi.begin(SSID, PASS);

  Serial.print(" CONNECTING TO WIFI ");
  Serial.println(SSID);

  while (WiFi.status() != WL_CONNECTED)
  {
    // Print connecting message once a second, is all
    if (checkCount <= 0)
    {
      Serial.println("still connecting to wifi ");
      checkCount = 100;
    }

    delay(10);
    checkCount--;
  }

  Serial.println("Connected to wifi");

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

void tellBnoWhatReportsWeWant(void)
{
  Serial.println("Setting desired reports");
  if (!bno08x.enableReport(SH2_GRAVITY))
  {
    Serial.println("Could not enable gravity report");
  }
  if (!bno08x.enableReport(SH2_GAME_ROTATION_VECTOR))
  {
    Serial.println("Could not enable game rotation report");
  }
  if (!bno08x.enableReport(SH2_GYROSCOPE_CALIBRATED))
  {
    Serial.println("Could not enable gyro report");
  }
}

void dumpSensorValue( sh2_SensorValue_t *sv) {
  Serial.print("sensorId: "); Serial.println(sv->sensorId);

  switch(sv->sensorId) {
    case SH2_GRAVITY:
      Serial.print("SensorEvent: Gravity - x: ");
      Serial.print(sv->un.gravity.x);
      Serial.print(" y: ");
      Serial.print(sv->un.gravity.y);
      Serial.print(" z: ");
      Serial.println(sv->un.gravity.z);
      break;

    case SH2_GAME_ROTATION_VECTOR:
      Serial.print("SensorEvent: Game Rotation Vector - r: ");
      Serial.print(sv->un.gameRotationVector.real);
      Serial.print(" i: ");
      Serial.print(sv->un.gameRotationVector.i);
      Serial.print(" j: ");
      Serial.print(sv->un.gameRotationVector.j);
      Serial.print(" k: ");
      Serial.println(bnoSensorValue.un.gameRotationVector.k);
      break;

    case SH2_GYROSCOPE_CALIBRATED:
      Serial.print("SensorEvent: Gyroscope Vector - x: ");
      Serial.print(bnoSensorValue.un.gyroscope.x);
      Serial.print(" y: ");
      Serial.print(bnoSensorValue.un.gyroscope.y);
      Serial.print(" z: ");
      Serial.println(bnoSensorValue.un.gyroscope.z);
      break;

    default:
      Serial.print(" unexpected sensor type");
  }
}

float gravity_x = 0.0;
float gravity_y = 0.0;
float gravity_z = 0.0;

float rotation_x = 0.0;
float rotation_y = 0.0;
float rotation_z = 0.0;

float gyro_x = 0.0;
float gyro_y = 0.0;
float gyro_z = 0.0;

unsigned long last_send = 0;

const unsigned long MAX_LONG = 0xFFFFFFFF;
const unsigned long MAX_LONG_MILLI = 4294967;
const int ms_between_packets = 50;
const int USE_BUNDLE = 1;

void loop()
{

  yield(); // needed?

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println(" WIFI DISCONNECTED RECONNECTING from loop ");
    wifiConnect();
    return;
  }

  if (bno08x.wasReset())  {
    Serial.print("Sensor was reset - ");
    tellBnoWhatReportsWeWant();
  }

  if (bno08x.getSensorEvent(&bnoSensorValue)) {

    // dumpSensorValue( &bnoSensorValue );

    switch (bnoSensorValue.sensorId) {
      case SH2_GRAVITY:
        gravity_x = bnoSensorValue.un.gravity.x;
        gravity_y = bnoSensorValue.un.gravity.y;
        gravity_z = bnoSensorValue.un.gravity.z;
        break;

      case SH2_GAME_ROTATION_VECTOR:
        rotation_x = bnoSensorValue.un.gameRotationVector.i;
        rotation_y = bnoSensorValue.un.gameRotationVector.j;
        rotation_z = bnoSensorValue.un.gameRotationVector.k;
        break;
      
      case SH2_GYROSCOPE_CALIBRATED:
        gyro_x = bnoSensorValue.un.gyroscope.x;
        gyro_y = bnoSensorValue.un.gyroscope.y;
        gyro_z = bnoSensorValue.un.gyroscope.z;
        break;

    }; // switch sensorId

  };

  // every so often send a packet
  unsigned long now = millis();
  if (last_send < now - ms_between_packets) {
    last_send = now;

#if 0
    // build the bundle? Bundles seem to work poorly

    OSCBundle bundle;

    // OSC time is definitionally in NTP time which is UTC, but that's impractical on a device like this
    osctime_t osc_time;
    osc_time.seconds = now / 1000;
    osc_time.fractionofseconds = ( now % 1000 ) * MAX_LONG_MILLI; 
    bundle.setTimetag(osc_time);

    OSCMessage grav_msg ("/LC/gravity");
    grav_msg.add(gravity_x);
    grav_msg.add(gravity_y);
    grav_msg.add(gravity_z);
    bundle.add(grav_msg);

    OSCMessage rot_msg ("/LC/rotation");
    rot_msg.add(rotation_x);
    rot_msg.add(rotation_y);
    rot_msg.add(rotation_z);
    bundle.add(rot_msg);

    OSCMessage gyro_msg ("/LC/gyro");
    gyro_msg.add(gyro_x);
    gyro_msg.add(gyro_y);
    gyro_msg.add(gyro_z);
    bundle.add(gyro_msg);

    // send the bundle
    udp.beginPacket(targetIpAddress, 6511);
    bundle.send(udp);
    udp.endPacket();
    //udp.beginPacket(targetIpAddress, 6512);
    //bundle.send(udp);
    //udp.endPacket();

#else

    OSCMessage imu_msg("/LC/imu");
    imu_msg.add((unsigned int) now); //unsigned long confuse the library
    imu_msg.add(rotation_x);
    imu_msg.add(rotation_y);
    imu_msg.add(rotation_z);
    imu_msg.add(gravity_x);
    imu_msg.add(gravity_y);
    imu_msg.add(gravity_z);
    imu_msg.add(gyro_x);
    imu_msg.add(gyro_y);
    imu_msg.add(gyro_z);

#if 0
    Serial.print("transmit: rotation: x: ");
    Serial.print(rotation_x);
    Serial.print(" y: ");
    Serial.print(rotation_y);
    Serial.print(" z: ");
    Serial.println(rotation_z);
#endif

    // send the packet
    udp.beginPacket(targetIpAddress, 6511);
    imu_msg.send(udp);
    udp.endPacket();

    // only if you need to send to a second port on the same machine
    //udp.beginPacket(targetIpAddress, 6512);
    //bundle.send(udp);
    //udp.endPacket();

#endif

  }

}
