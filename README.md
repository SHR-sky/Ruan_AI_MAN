# 景区导览服务 AI 数字人

> 第十五届中国软件杯大赛 · A组赛题 A5  
> 出题企业：锐捷网络（苏州）有限公司

基于多模态大模型的智能景区导览系统，覆盖 **游客交互端（Web）**、**管理后台** 和 **ESP32 硬件终端** 三端。

---

## 系统架构

### 表现层（三端接入）

| 端 | 技术 | 交互方式 |
|----|------|----------|
| 游客交互端 | Vue 3 Web | 数字人对话 / 语音问答 / 路线推荐 |
| 管理后台 | Vue 3 Web | 知识库管理 / 数据大屏 / 数字人配置 |
| ESP32 终端 | Arduino + GPS + OLED | 按键问答 / 定位上报 / 附近提醒 |

### 服务层（FastAPI 后端）

| 服务 | 职责 |
|------|------|
| Chat Service | WebSocket 实时对话、流式响应 |
| RAG Service | 向量检索 + 关键词混合检索 + LLM 生成 |
| ASR Service | 语音识别（Whisper） |
| TTS Service | 语音合成（GPT-SoVITS） |
| Digital Human Service | 数字人口型/表情驱动（MuseTalk） |
| GPS Service | 位置计算、附近 POI 搜索、路线规划 |
| Device Service | ESP32 设备管理、心跳监控 |

### 数据层

| 存储 | 用途 |
|------|------|
| PostgreSQL | 业务数据（对话记录、用户、配置） |
| Qdrant（向量库） | 知识库向量索引，用于 RAG 语义检索 |
| Redis | 会话缓存、实时排行榜、消息队列 |

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
