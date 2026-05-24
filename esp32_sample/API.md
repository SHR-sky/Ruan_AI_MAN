# ESP32 设备API文档

> 基础地址: `http://<server>:8000/api/v1/device`

---

## 1. 上报GPS位置

```
POST /gps
Content-Type: application/json

{
  "device_id": "esp32_001",
  "lat": 31.2304,
  "lng": 121.4737,
  "altitude": 15.0,      // 可选 海拔(米)
  "speed": 1.2,           // 可选 速度(km/h)
  "heading": 180,         // 可选 朝向角度
  "battery": 85           // 可选 电量(%)
}
```

**响应示例**:
```json
{
  "device_id": "esp32_001",
  "position": { "lat": 31.2304, "lng": 121.4737 },
  "nearby_count": 3,
  "nearby_pois": [
    { "id": "poi_001", "name": "山门", "distance_m": 15.2, "category": "古迹" },
    { "id": "poi_002", "name": "大雄宝殿", "distance_m": 85.0, "category": "古迹" }
  ],
  "nearest_poi_name": "山门",
  "suggestion": {
    "type": "arrived",
    "message": "您已到达山门",
    "poi_id": "poi_001",
    "action": "输入 '介绍山门' 开始导览"
  },
  "alert": null
}
```

---

## 2. 文本问答

```
POST /query
Content-Type: application/json

{
  "device_id": "esp32_001",
  "query": "介绍大雄宝殿的历史",
  "lat": 31.2304,      // 可选 用于位置上下文
  "lng": 121.4737
}
```

**响应**:
```json
{
  "device_id": "esp32_001",
  "answer": "大雄宝殿始建于唐代...",
  "nearby_pois": "游客附近有: 山门、大雄宝殿、古桥。"
}
```

---

## 3. 获取附近POI

```
GET /pois?lat=31.2304&lng=121.4737&radius=500
```

**响应**:
```json
{
  "count": 3,
  "pois": [
    { "id": "poi_001", "name": "山门", "lat": 31.2304, "lng": 121.4737,
      "description": "景区入口", "category": "古迹", "distance_m": 15.2 },
    ...
  ]
}
```

---

## 4. 获取最近POI

```
GET /pois/nearest?lat=31.2304&lng=121.4737
```

**响应**:
```json
{
  "found": true,
  "poi": {
    "id": "poi_001",
    "name": "山门",
    "distance_m": 15.2,
    "category": "古迹"
  }
}
```

---

## 5. 游览路线推荐

```
GET /route?lat=31.2304&lng=121.4737&interest=古迹
```

**interest 可选值**: `all`(默认) / `古迹` / `自然` / `亲子` / `文化` / `休闲`

---

## 6. 设备心跳

```
POST /heartbeat
Content-Type: application/json

{
  "device_id": "esp32_001",
  "battery": 85,
  "rssi": -65,
  "uptime": 3600,
  "free_heap": 120000
}
```

---

## 7. 获取API信息

```
GET /info
```

返回所有可用端点列表，ESP32初始化时可调用此接口自检连接。

---

## ESP32 接线参考

| 组件 | 引脚 |
|------|------|
| GPS TX | GPIO 16 |
| GPS RX | GPIO 17 |
| OLED SDA | GPIO 21 |
| OLED SCL | GPIO 22 |
| 按键 | GPIO 0 (GND触发) |

> 完整示例代码见 `scenic_guide_esp32.ino`
