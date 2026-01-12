/************ BLYNK CONFIG ************/
#define BLYNK_TEMPLATE_ID "TMPL3kj3_7cC4"
#define BLYNK_TEMPLATE_NAME "DustbinFIllDashboard"
#define BLYNK_AUTH_TOKEN "_X32fv9hG6EWSzfRKHbPwnX8vfu6EHok"

/************ LIBRARIES ************/
#include <WiFi.h>
#include <BlynkSimpleEsp32.h>
#include <HX711.h>

/************ WIFI CREDENTIALS ************/
char ssid[] = "wifi";          // 2.4 GHz WiFi ONLY
char pass[] = "1234567a";

/************ PIN DEFINITIONS ************/
#define TRIG_PIN 5
#define ECHO_PIN 18
#define HX711_DOUT 4a
#define HX711_SCK 16   // SAFE GPIO (not a boot pin)

/************ OBJECTS ************/
HX711 scale;
BlynkTimer timer;

/************ VARIABLES ************/
float distance = 0.0;
float fillLevel = 0.0;
float weight = 0.0;
bool alertSent = false;

/************ CONSTANTS ************/
const float BIN_HEIGHT = 20.0;        // cm (adjust to your bin height)
const float WEIGHT_THRESHOLD = 2000;  // grams
const float FILL_THRESHOLD = 80.0;    // %

/************ SETUP ************/
void setup() {
  Serial.begin(115200);
  delay(1000);

  /* ---------- GPIO INIT ---------- */
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  /* ---------- WIFI INIT ---------- */
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, pass);

  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  /* ---------- HX711 INIT ---------- */
  scale.begin(HX711_DOUT, HX711_SCK);
  Serial.print("Initializing HX711");
  while (!scale.is_ready()) {
    delay(300);
    Serial.print(".");
  }
  Serial.println(" Ready");

  scale.set_scale(435);   // 🔧 CALIBRATION FACTOR
  scale.tare();           // Reset scale to zero

  /* ---------- BLYNK INIT ---------- */
  Blynk.config(BLYNK_AUTH_TOKEN, "blynk.cloud", 80);

  Serial.print("Connecting to Blynk");
  if (Blynk.connect(10000)) {
    Serial.println("\nBlynk Connected (ONLINE)");
  } else {
    Serial.println("\nBlynk Connection FAILED");
  }

  /* ---------- TIMER ---------- */
  timer.setInterval(2000L, sendSensorData);
}

/************ LOOP ************/
void loop() {
  if (!Blynk.connected()) {
    Blynk.connect();
  }

  Blynk.run();
  timer.run();
}

/************ SENSOR TASK ************/
void sendSensorData() {

  /* ---------- ULTRASONIC ---------- */
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000); // 30 ms timeout
  if (duration == 0) {
    Serial.println("Ultrasonic timeout");
    return;
  }

  distance = (duration * 0.0343) / 2.0;

  fillLevel = ((BIN_HEIGHT - distance) / BIN_HEIGHT) * 100.0;
  fillLevel = constrain(fillLevel, 0, 100);

  /* ---------- WEIGHT ---------- */
  weight = scale.get_units(3);  // grams

  /* ---------- SEND TO BLYNK ---------- */
  Blynk.virtualWrite(V0, fillLevel);   // Gauge
  Blynk.virtualWrite(V1, weight);      // Weight
  Blynk.virtualWrite(V2, distance);    // Distance

  /* ---------- ALERT LOGIC ---------- */
  if ((fillLevel >= FILL_THRESHOLD || weight >= WEIGHT_THRESHOLD) && !alertSent) {
    Blynk.logEvent("dustbin_full", "Dustbin needs emptying!");
    alertSent = true;
  }

  if (fillLevel < FILL_THRESHOLD && weight < WEIGHT_THRESHOLD) {
    alertSent = false;
  }

  /* ---------- SERIAL OUTPUT ---------- */
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.print(" cm | Fill: ");
  Serial.print(fillLevel);
  Serial.print(" % | Weight: ");
  Serial.print(weight);
  Serial.println(" g");
}
