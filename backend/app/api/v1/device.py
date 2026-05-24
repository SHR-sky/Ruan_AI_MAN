from fastapi import APIRouter, Query, Body
from app.services.gps import GPSService
from app.services.rag import RAGService

router = APIRouter()
gps_service = GPSService()
rag_service = RAGService()


@router.get("/pois")
async def get_nearby_pois(
    lat: float = Query(..., description="纬度"),
    lng: float = Query(..., description="经度"),
    radius: int = Query(500, description="搜索半径(米)"),
):
    """获取附近景点 POI（适配ESP32小屏显示）"""
    pois = gps_service.get_nearby_pois(lat, lng, radius)
    return {
        "count": len(pois),
        "pois": pois,
    }


@router.get("/pois/nearest")
async def get_nearest_poi(
    lat: float = Query(...),
    lng: float = Query(...),
):
    """获取最近的景点"""
    poi = gps_service.get_nearest_poi(lat, lng)
    if poi:
        return {"found": True, "poi": poi}
    return {"found": False, "poi": None}


@router.post("/query")
async def device_query(
    device_id: str = Body(..., description="设备ID"),
    query: str = Body(..., description="游客提问文本"),
    lat: float = Body(None, description="当前纬度(可选)"),
    lng: float = Body(None, description="当前经度(可选)"),
):
    """ESP32文本查询接口 — 返回精简JSON，不含数字人/语音数据"""
    nearby_context = ""
    if lat is not None and lng is not None:
        nearby = gps_service.get_nearby_pois(lat, lng, radius=300)
        if nearby:
            names = [p["name"] for p in nearby[:3]]
            nearby_context = f"游客附近有: {'、'.join(names)}。"

    full_query = f"{nearby_context}游客问: {query}" if nearby_context else query
    answer = await rag_service.generate(full_query, session_id=device_id)

    return {
        "device_id": device_id,
        "answer": answer,
        "nearby_pois": nearby_context,
    }


@router.post("/gps")
async def report_gps(
    device_id: str = Body(..., description="设备ID"),
    lat: float = Body(..., description="纬度"),
    lng: float = Body(..., description="经度"),
    altitude: float = Body(None, description="海拔(米)"),
    speed: float = Body(None, description="速度(km/h)"),
    heading: float = Body(None, description="朝向角度"),
    battery: int = Body(None, description="设备电量百分比"),
):
    """ESP32上报GPS位置，返回附近POI和推荐"""
    nearby = gps_service.get_nearby_pois(lat, lng, radius=500)
    nearest = gps_service.get_nearest_poi(lat, lng)

    response = {
        "device_id": device_id,
        "position": {"lat": lat, "lng": lng},
        "nearby_count": len(nearby),
        "nearby_pois": nearby[:5],
        "nearest_poi_name": nearest["name"] if nearest else None,
        "suggestion": None,
    }

    if battery is not None and battery < 20:
        response["alert"] = f"电量不足({battery}%)，建议返回入口或前往充电站"

    if nearest and nearest["distance_m"] < 50:
        response["suggestion"] = {
            "type": "arrived",
            "message": f"您已到达{nearest['name']}",
            "poi_id": nearest["id"],
            "action": f"输入 '介绍{nearest['name']}' 开始导览",
        }
    elif nearest and nearest["distance_m"] < 200:
        nearest_poi = nearest
        response["suggestion"] = {
            "type": "nearby",
            "message": f"{nearest_poi['name']}距您{nearest_poi['distance_m']}米",
            "poi_id": nearest_poi["id"],
        }

    return response


@router.post("/heartbeat")
async def device_heartbeat(
    device_id: str = Body(...),
    battery: int = Body(None),
    rssi: int = Body(None, description="WiFi信号强度dBm"),
    uptime: int = Body(None, description="运行时长(秒)"),
    free_heap: int = Body(None, description="ESP32空闲内存(字节)"),
):
    """ESP32心跳 — 设备状态监控"""
    return {
        "status": "ok",
        "device_id": device_id,
        "timestamp": None,
        "server_time": None,
        "actions": [],
    }


@router.get("/route")
async def get_route(
    lat: float = Query(...),
    lng: float = Query(...),
    interest: str = Query("all", description="兴趣: 古迹/自然/亲子/文化/休闲"),
):
    """获取游览路线推荐（按兴趣排序）"""
    route = gps_service.get_route(lat, lng, interest)
    return {
        "interest": interest,
        "stop_count": len(route),
        "route": route,
    }


@router.get("/info")
async def device_info():
    """获取ESP32客户端需要的API信息"""
    return {
        "api_version": "1.0",
        "protocol": "REST/JSON",
        "encoding": "UTF-8",
        "endpoints": {
            "gps_report": "POST /api/v1/device/gps",
            "query": "POST /api/v1/device/query",
            "nearby_pois": "GET /api/v1/device/pois",
            "nearest_poi": "GET /api/v1/device/pois/nearest",
            "route": "GET /api/v1/device/route",
            "heartbeat": "POST /api/v1/device/heartbeat",
        },
        "max_query_length": 500,
        "response_format": "json",
    }
