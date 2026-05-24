/**
 * 景区导览AI数字人 - ESP32 随身终端示例代码
 * 硬件: ESP32 + GPS模块(NEO-6M) + OLED显示屏(SSD1306) + 按键
 *
 * API 基础地址: 请修改为你的服务器地址
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <TinyGPSPlus.h>
#include <Wire.h>
#include <Adafruit_SSD1306.h>

// ===== 配置区 =====
const char* WIFI_SSID = "your_wifi_ssid";
const char* WIFI_PASS = "your_wifi_password";
const char* API_BASE = "http://your-server-ip:8000/api/v1/device";
const char* DEVICE_ID = "esp32_001";

// ===== 硬件引脚 =====
#define GPS_BAUD 9600
#define BTN_PIN 0
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1

// ===== 全局对象 =====
TinyGPSPlus gps;
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
HTTPClient http;
String currentPoiName = "";
float currentLat = 0, currentLng = 0;

void setup() {
  Serial.begin(115200);
  Serial2.begin(GPS_BAUD, SERIAL_8N1, 16, 17);  // RX=16, TX=17

  pinMode(BTN_PIN, INPUT_PULLUP);

  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("OLED 初始化失败");
  }
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.println("Connecting...");
  display.display();

  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  showMessage("WiFi OK", "");
}

void loop() {
  // 读取GPS
  while (Serial2.available() > 0) {
    gps.encode(Serial2.read());
  }

  if (gps.location.isUpdated()) {
    currentLat = gps.location.lat();
    currentLng = gps.location.lng();
    reportGPS();
  }

  // 按键触发查询
  if (digitalRead(BTN_PIN) == LOW) {
    delay(200);  // 防抖
    queryNearbyPOI();
  }
}

// ===== API调用 =====

/** 上报GPS位置，获取附近景点 */
void reportGPS() {
  String url = String(API_BASE) + "/gps";

  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  StaticJsonDocument<256> body;
  body["device_id"] = DEVICE_ID;
  body["lat"] = currentLat;
  body["lng"] = currentLng;
  body["battery"] = 85;  // 如有电量检测可替换为真实值

  String jsonStr;
  serializeJson(body, jsonStr);

  int code = http.POST(jsonStr);
  if (code == 200) {
    String resp = http.getString();
    parseGPSResponse(resp);
  }
  http.end();
}

/** 文本查询（支持当前位置上下文） */
void sendQuery(String question) {
  String url = String(API_BASE) + "/query";

  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  StaticJsonDocument<512> body;
  body["device_id"] = DEVICE_ID;
  body["query"] = question;
  body["lat"] = currentLat;
  body["lng"] = currentLng;

  String jsonStr;
  serializeJson(body, jsonStr);

  int code = http.POST(jsonStr);
  if (code == 200) {
    String resp = http.getString();
    StaticJsonDocument<1024> doc;
    deserializeJson(doc, resp);
    const char* answer = doc["answer"];
    showMessage("小导", answer);
  }
  http.end();
}

/** 获取附近POI列表 */
void queryNearbyPOI() {
  String url = String(API_BASE) + "/pois?lat=" + String(currentLat, 6)
               + "&lng=" + String(currentLng, 6) + "&radius=500";

  http.begin(url);
  int code = http.GET();
  if (code == 200) {
    String resp = http.getString();
    StaticJsonDocument<2048> doc;
    deserializeJson(doc, resp);
    JsonArray pois = doc["pois"];

    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("附近景点:");
    int count = min((int)pois.size(), 4);
    for (int i = 0; i < count; i++) {
      display.print(i + 1);
      display.print(". ");
      display.print(pois[i]["name"].as<String>());
      display.print(" ");
      display.print(pois[i]["distance_m"].as<int>());
      display.println("m");
    }
    display.display();
  }
  http.end();
}

// ===== 辅助函数 =====

void parseGPSResponse(String json) {
  StaticJsonDocument<2048> doc;
  deserializeJson(doc, json);

  if (doc.containsKey("suggestion")) {
    const char* msg = doc["suggestion"]["message"];
    const char* action = doc["suggestion"]["action"] | "";
    showMessage("提示", msg);
    if (strlen(action) > 0) {
      delay(2000);
      showMessage("操作", action);
    }
  }

  if (doc.containsKey("alert")) {
    showMessage("⚠ 警告", doc["alert"].as<String>());
  }
}

void showMessage(String title, String content) {
  display.clearDisplay();
  display.setCursor(0, 0);
  display.setTextSize(1);
  display.println(title);
  display.drawLine(0, 10, SCREEN_WIDTH, 10, SSD1306_WHITE);

  display.setCursor(0, 14);
  // 自动换行显示
  int maxChars = SCREEN_WIDTH / 6;
  int lineHeight = 10;
  int line = 0;
  for (int i = 0; i < content.length(); i += maxChars) {
    display.println(content.substring(i, min(i + maxChars, content.length())));
    line++;
    if (line >= 4) break;  // 最多显示4行
  }
  display.display();
}
