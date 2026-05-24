# 景区导览服务 AI 数字人

> 第十五届中国软件杯大赛 · A组赛题 A5  
> 出题企业：锐捷网络（苏州）有限公司

基于多模态大模型的智能景区导览系统，覆盖 **游客交互端（Web）**、**管理后台** 和 **ESP32 硬件终端** 三端。

---

## 系统架构

```
┌─────────────┐  ┌──────────────┐  ┌──────────────────┐
│  游客交互端   │  │  管理后台     │  │  ESP32 随身终端   │
│  (Vue3 Web)  │  │  (Vue3 Web)  │  │  (GPS + OLED)    │
└──────┬───────┘  └──────┬───────┘  └────────┬─────────┘
       │                 │                   │
       └─────────────────┼───────────────────┘
                         │ API
               ┌─────────▼──────────┐
               │   FastAPI 后端      │
               │   RAG + LLM + ASR  │
               │   + TTS + 数字人    │
               └─────────┬──────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
     PostgreSQL      Qdrant/向量库     Redis
```

## 技术栈

| 层 | 选型 |
|------|------|
| 后端框架 | Python FastAPI |
| AI 模型 | Qwen2.5-VL / Qwen3（多模态大模型） |
| RAG 框架 | LangChain + Qdrant（向量数据库） |
| 语音识别 | Whisper / FunASR |
| 语音合成 | GPT-SoVITS / CosyVoice |
| 数字人 | MuseTalk / LivePortrait（2D 数字人驱动） |
| 游客前端 | Vue 3 + TypeScript + Vite |
| 管理后台 | Vue 3 + TypeScript + Vite |
| 硬件终端 | ESP32 + GPS(NEO-6M) + OLED(SSD1306) |
| 数据库 | PostgreSQL + Redis |
| 部署 | Docker Compose |

## 快速开始

### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 游客前端

```bash
cd frontend
npm install
npm run dev
```

### 管理后台

```bash
cd admin
npm install
npm run dev
```

### Docker 全量部署

```bash
docker-compose up -d
```

---

## 项目结构

```
├── backend/              # FastAPI 后端服务
│   ├── app/
│   │   ├── api/v1/       # API 路由（chat / knowledge / digital-human / admin / device）
│   │   ├── core/          # 配置与数据库
│   │   ├── models/        # SQLAlchemy 数据模型
│   │   └── services/      # 业务服务（RAG / LLM / ASR / TTS / GPS / DigitalHuman）
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/             # 游客交互端（Vue3）
│   ├── src/
│   │   ├── views/        # Chat.vue 主对话页面
│   │   ├── components/   # 数字人展示 / 消息气泡 / 语音输入
│   │   └── api/          # 后端 API 封装
│   └── Dockerfile
├── admin/                # 管理后台（Vue3）
│   ├── src/views/        # Dashboard / KnowledgeBase / DigitalHumanConfig
│   └── Dockerfile
├── esp32_sample/         # ESP32 硬件示例代码 + API 文档
│   ├── scenic_guide_esp32.ino  # 完整 Arduino 示例
│   └── API.md            # 设备 API 文档
├── docker-compose.yml    # 容器编排
└── 开题报告_景区导览服务AI数字人.md
```

## 设备 API

为 ESP32 硬件终端预留了 7 个专用接口，支持：

| 接口 | 用途 |
|------|------|
| `POST /gps` | 上报 GPS 位置，返回附近 POI 和主动提示 |
| `POST /query` | 文本问答（自动携带位置上下文） |
| `GET /pois` | 获取周边景点列表 |
| `GET /route` | 按兴趣推荐游览路线 |
| `POST /heartbeat` | 设备心跳监控 |

详见 `esp32_sample/API.md`。

## License

参赛团队自主开发部分软件著作权归参赛团队所有。
