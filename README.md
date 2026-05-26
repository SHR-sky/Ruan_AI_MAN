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
| TTS Service | 语音合成（Kokoro） |
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
| 语音合成 | Kokoro |
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
├── finetune_dataset/     # 模型微调数据集（3 种风格 × 621 条对话记录）
│   ├── enthusiastic_local_guide.jsonl  # 热情本地通
│   ├── learned_history_scholar.jsonl   # 博学文史官
│   ├── cute_cartoon.jsonl              # 萌趣卡通
│   └── generate_dataset.py             # 数据生成脚本
├── docker-compose.yml    # 容器编排
└── 项目文档/                  # 开题报告、项目介绍等
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

---

## 更新日志

### 2026-05-27-V6

- **Live2D 响应式定位** — 添加 `ResizeObserver` 监听容器尺寸变化，同步更新 sprite 的 `x`（居中）、`y`（底部偏移）、`width`（宽度填充），确保切换设备和窗口缩放时模型位置比例不变
- **上半身构图** — `sprite.y = 容器高度 × 1.45`，配合 `anchor(0.5, 1)` 底部中心锚点 + `overflow:hidden`，裁剪下半身只露上半身，模型紧贴底部信息卡片形成连贯视觉
- **左侧面板 UI 优化** — 数字人区域去重阴影改淡渐变背景（`linear-gradient`），guide-card 缩小边距/圆角/字号（14px padding、18px 圆角），整体更轻盈紧凑

### 2026-05-27-V5

- **Live2D 数字人（Hiyori）成功接入并正常渲染** — 模型路径统一为 `/Resources/Hiyori/`（对齐 Knowledge_Agent 工程），Pixi.js + easy-live2d 初始化流程参照官方 Vue3 示例重写，去掉多余的 anchor/xy 手动定位
- **手动 Web Audio API 驱动口型同步** — 放弃 easy-live2d 内置 lip sync（v0.4.4 疑似有 bug），改为原生 `AudioContext.decodeAudioData()` → `AnalyserNode` 实时 RMS 振幅 → `RequestAnimationFrame` 每帧 `setParameterValueById('ParamMouthOpenY')`，口型随 TTS 音频平滑开合
- **Core SDK 来源修正** — `live2dcubismcore.min.js` 从 Knowledge_Agent 仓库拉取（SHA: `d225300e`，207KB），替换此前 npm 包 `live2dcubismcore` 第三方重打包版本
- **降级策略完善** — WebGL 不可用时回退 CSS 绿色圆形；Live2D 模型加载 10 秒超时自动降级；`stopVoice()` 可即时停止 Web Audio 源并复位口型
- **`start.bat` 端口统一** — 后端端口改为 8001，与 `vite.config.ts` 代理目标对齐

### 2026-05-27-V4

- **修复 text_utils 数字转中文越界 BUG** — `_small_number_to_cn()` 在处理超过 4 位数字段时索引越界导致 RAG 服务崩溃；新增长度守卫，超长数字直接逐位映射，避免 IndexError
- **前端代理端口修正** — `frontend/vite.config.ts` 和 `admin/vite.config.ts` 代理目标从 `127.0.0.1:8000` 改为 `127.0.0.1:8001`，与后端实际端口保持一致
- **清理后端 __pycache__ 缓存** — 删除残留 `.pyc` 文件，解决因缓存导致的旧路由注册与源码不匹配的问题（如 `/health` 返回内容与代码不一致）
- **回退 Live2D 数字人至 CSS 头像** — easy-live2d + Pixi.js 集成存在 WebGL / Core SDK 加载兼容性问题，暂时回退到纯 CSS 绿色圆形头像（保留数字人组件接口，待后续稳定后再接入 Live2D）

### 2026-05-26-V3

- **新增三种导游风格微调数据集** — 在 `finetune_dataset/` 下创建 3 个 JSONL 文件，每个包含 621 条 `messages` 格式对话记录（共 1,863 条），用于对 LLM 进行风格化指令微调
- **热情本地通**（`enthusiastic_local_guide.jsonl`）— 设定为"本地通小张"角色，语气活泼、充满感染力，常以"咱这儿啊……"开头，推荐小众玩法和私房路线，适合偏好地道体验的游客
- **博学文史官**（`learned_history_scholar.jsonl`）— 设定为"文史老学究"角色，语气稳重端庄、引经据典（《诗经》《中庸》《礼记》等），以"诸位请看…""且听我道来…"开篇，适合深度文化游群体
- **萌趣卡通**（`cute_cartoon.jsonl`）— 设定为"小云朵"卡通导游角色，大量使用 emoji 表情（✨🌈🎵🚀）、拟人化表达（大树伯伯、小河姐姐、太阳公公），适合亲子家庭游客
- **数据覆盖全面** — 每条数据包含 system / user / assistant 三端消息，覆盖项目知识库 23 个景区 × 27 种问法类型（位置、门票、交通、亲子、美食、历史、路线推荐、拍照打卡等），景区涵盖上海、江苏、浙江三地核心景点
- **可扩展生成脚本** — 保留 `generate_dataset.py`，支持随时扩展更多景区或问法模板重新生成

### 2026-05-26-V2

- **接入 Qwen3.5-0.8B GGUF 本地大模型** — 将 `Qwen3.5-0.8B-IQ4_NL.gguf` 移至 `models/`，安装 `llama-cpp-python`（CUDA 12.4 预编译 whl，兼容 12.6），GPU 全层加载，实现纯本地 LLM 推理
- **LLM 服务重写** — `LLMService` 从桩代码重写为基于 `llama_cpp.Llama` 的单例服务，提供 `chat()` / `chat_stream()`，模型路径通过 `LLM_MODEL_PATH` 配置（默认 `models/Qwen3.5-0.8B-IQ4_NL.gguf`）
- **RAG 管道升级：LLM 总结式回答** — `RAGService.generate()` 改为：关键词检索 → 构建上下文 → Qwen 阅读后以自然口吻总结输出（≤200 字、不直接复制原文），达到"导游用自己话介绍"的效果；LLM 故障时自动降级返回原始内容前 300 字
- **RAG 兜底策略** — 无匹配知识时，LLM 礼貌告知无相关信息并建议咨询游客中心，替代原有硬编码模板
- **依赖更新** — `requirements.txt` 新增 `llama-cpp-python>=0.3.0`，`config.py` 新增 `LLM_MODEL_PATH` 配置项
- **验证脚本** — `scripts/verify_tts/test_qwen_rag.py` 可直接运行验证 RAG+LLM 全链路

### 2026-05-26

- **TTS 引擎更换为 Kokoro-82M** — 统一使用 `KokoroTTSEngine`，基于 `kokoro` 包（KPipeline + KModel）驱动，模型文件存放于 `models/kokoro/`（config.json + kokoro-v1_0.pth + voices/*.pt）
- **多中文音色** — 内置 `zf_xiaoxiao`（默认/女声）、`zf_xiaoni`（温柔）、`zf_xiaobei`（活泼）、`zm_yunxi`（男声）四种音色，前端按 voice_type 映射
- **分句合成 + 间隙拼接** — 按标点切句（最长 180 字符），逐句异步合成后以 15ms 静音间隙拼接，平衡自然停顿与整段输出
- **依赖精简** — 新增 `kokoro>=0.9.4`、`misaki[zh]>=0.9.4`，采样率 24000 Hz，无需额外 BERT 模型下载
- **移除 DevContainer 引用** — `.devcontainer/`、`.vscode/` 不再纳入版本管理
- **验证脚本** — `scripts/verify_tts/test_kokoro.py` 可直接运行验证合成流程

### 2026-05-25

- **TTS 引擎更换为 Qwen-TTS** — 移除旧 TTS 语音合成残留，统一使用Qwen TTS
- **TTS 播放链路重构** — 前端回答语音改为一次请求完整 WAV，后端统一缓存输出，减少多段播放造成的漏句和断续
- **网页端初步完成** — 游客前端实现数字人展示、语音输入、对话气泡、自动播放导览等功能；管理后台实现知识库管理、数据看板、数字人配置
- **RAG 知识库检索** — 基于 Qwen 大模型 + Qdrant 向量数据库，支持景区知识的多模态检索与 LLM 生成回答
- **ASR 语音识别** — 集成 Whisper / FunASR，支持游客语音提问
- **Demo 导览页面** — 首次加载自动播放欢迎导览并展示景点介绍，接口分离文字与音频以优化加载速度
- **初始回复精简** — 缩短网页首屏欢迎文案，提升用户体验
- **修复播放/停止逻辑** — 点击停止播放时不再重新开始播放音频
- **女声 TTS 音色** — 默认使用 Vivian 明亮女声（映射自 voice_type=female）
- **对话区滚动条** — 修复长回复导致 UI 被撑变形的问题，添加纵向滚动条
- **每条回复播放按钮** — 每条 AI 回复气泡右下角添加 ▶ 按钮，支持单独重播语音
- **前端设备状态展示** — 页面 header 显示 GPU/CPU 运行设备和 TTS 引擎名称
- **一键启动脚本** — 创建 `start.bat`，同时启动后端（uvicorn）+ 两个前端（Vite）
