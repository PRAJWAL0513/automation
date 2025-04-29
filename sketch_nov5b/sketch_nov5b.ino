#include <WiFi.h>
#include <PubSubClient.h>

// WiFi credentials
const char* ssid = "SSID";
const char* password = "Password";

// MQTT Broker address
const char* mqtt_server = "192.168.107.6";

// Pin configurations
const int buttonPin = 15;
const int buttonPinr = 18;
const int ledPin = 2; // Use the same pin for the LED

WiFiClient espClient;
PubSubClient client(espClient);

long lastMsg = 0;

// Function to blink the LED
void blink_led(unsigned int times, unsigned int duration) {
  for (int i = 0; i < times; i++) {
    digitalWrite(ledPin, HIGH);
    delay(duration);
    digitalWrite(ledPin, LOW);
    delay(200);
  }
}

// Connect to WiFi
void setup_wifi() {
  delay(50);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  int c = 0;
  while (WiFi.status() != WL_CONNECTED) {
    blink_led(2, 200); // Blink LED twice (for 200ms ON time) to indicate that WiFi is not connected
    delay(1000);
    Serial.print(".");
    c = c + 1;
    if (c > 10) {
      ESP.restart(); // Restart ESP after 10 seconds if WiFi is not connected
    }
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

// Connect to the MQTT broker
void connect_mqttServer() {
  while (!client.connected()) {
    // First, check if connected to WiFi
    if (WiFi.status() != WL_CONNECTED) {
      setup_wifi();
    }

    Serial.print("Attempting MQTT connection...");
    if (client.connect("ESP32_client1")) {
      Serial.println("connected");
      client.subscribe("rpi/broadcast"); // Subscribe to topic
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" trying again in 2 seconds");
      blink_led(3, 200); // Blink LED three times (200ms on duration) to indicate MQTT failure
      delay(2000);
    }
  }
}

// Callback function for handling incoming MQTT messages
void callback(char* topic, byte* message, unsigned int length) {
  Serial.print("Message arrived on topic: ");
  Serial.print(topic);
  Serial.print(". Message: ");
  String messageTemp;
  
  for (int i = 0; i < length; i++) {
    messageTemp += (char)message[i];
  }
  Serial.println();

  if (String(topic) == "rpi/broadcast" && messageTemp == "10") {
    Serial.println("Action: blink LED");
    blink_led(1, 1250); // Blink LED once (for 1250ms ON time)
  }
}

void setup() {
  Serial.begin(115200);

  pinMode(buttonPin, INPUT);
  pinMode(buttonPinr, INPUT);
  pinMode(ledPin, OUTPUT);

  setup_wifi();
  client.setServer(mqtt_server, 1883); // 1883 is the default port for MQTT
  client.setCallback(callback);
}

void loop() {
  // Ensure MQTT client is connected
  if (!client.connected()) {
    connect_mqttServer();
  }

  client.loop();

  int buttonState = digitalRead(buttonPin); // Read the button state
  int buttonStater = digitalRead(buttonPinr); // Read the button state

  if (buttonState == HIGH) {
    // When button is pressed (HIGH), publish "one" to the MQTT broker
    
    digitalWrite(ledPin, HIGH);  // Turn on the LED when button is pressed
    client.publish("esp32/sensor1", "1"); // Publish a dummy message
    long now = millis();
    if (now - lastMsg > 500) {
    lastMsg = now;}
    //client.publish("esp32/sensor1", "1"); // Publish a dummy message
//    client.publish("esp32/sensor1", "one");  // Topic: esp32/button, Message: "one"
  
    delay(500); // Delay to prevent multiple publishes
    digitalWrite(ledPin, LOW);
  }
  
  if (buttonStater == HIGH) {
    // When button is pressed (HIGH), publish "one" to the MQTT broker
    
    digitalWrite(ledPin, HIGH);  // Turn on the LED when button is pressed
    client.publish("esp32/sensor1", "-1"); // Publish a dummy message
    long now = millis();
    if (now - lastMsg > 500) {
    lastMsg = now;}
  
    delay(500); // Delay to prevent multiple publishes
    digitalWrite(ledPin, LOW);
  } else {

    // When button is not pressed (LOW), turn off the LED
    digitalWrite(ledPin, LOW);
  }


}
