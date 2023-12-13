// Include WIFI Libraries
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

// Constant Setup
const int SLEEP = 40;
const int FREQUENCY = 50; // hertz
const int SECOND = 1000; // milisecond
const float IDLEVOLTAGE = 1.73; // volts
const int READINGINTERVAL = 1; // seconds
const char* ssid = "Kampung Bali";
const char* password = "(//////)";

// Setup current device state
int currentDeviceState = 0;

// Create WebServer on port 80
ESP8266WebServer server(80);

void setup() {
  Serial.begin(9600);

  // Connect to existing wi-fi network
  WiFi.begin(ssid, password);

  // Check wi-fi is connected to network
  while (WiFi.status() != WL_CONNECTED){
      delay(1000);
      Serial.print(".");
    }
  Serial.println("");
  Serial.println("WiFi connected...!");
  Serial.print("Got IP: "); Serial.println(WiFi.localIP());

  // Show data on server
  server.on("/pumpstate", handleDeviceState);

  server.begin();
  Serial.println("HTTP server started");
  
}

void loop() {
  server.handleClient();
  
  float minVal = IDLEVOLTAGE; 
  float maxVal = IDLEVOLTAGE; 
  float delta;
  
  for (int i=0; i<(FREQUENCY * READINGINTERVAL); i++){
      /*
       * Read amperemeter values
       */
       
      float amperemeterValue = readAmperemeterValue();

      // Check and assign minimum value
      if (amperemeterValue < minVal){
          minVal = amperemeterValue;
        }

      // Check and assign maximum value
      if (amperemeterValue > maxVal){
          maxVal = amperemeterValue;
        }

      // Convert sine wave readings to highest peak
      float normMax = maxVal - IDLEVOLTAGE;
      float normMin = IDLEVOLTAGE - minVal;
      if (normMax > normMin){
          delta = normMax;
        }
      else{
          delta = normMin;
        }

      
      delay(SECOND / FREQUENCY);
    }

    /*
     * Write ampere signal to RaspberryPi
     */
    //digitalWrite(NODEMCU_W, deviceState(delta))
    currentDeviceState = deviceState(delta);
    Serial.println(delta);
    //Serial.println(delta);

}

float readAmperemeterValue(){
  /*
  Returns amperemeter sensor value for particular time
  in time when this function called

  The analog port for this readings set to `A0`
  */
  int sensorValue = analogRead(A0);
  float voltage = sensorValue * (3.3 / 1023.0);
  return voltage;
  }

int deviceState(float deltaReadings){
    /*
     Convert readings to binary value
     to decide on / off value.
     */
     const float FLUCTUATION = 0.03;
     int state;
     if (deltaReadings > FLUCTUATION){
        state = 1;
      }
     else {
        state = 0;
      }

     return state;
  }

void handleDeviceState(){
    server.send(200, "text/html", String(currentDeviceState));
  }
