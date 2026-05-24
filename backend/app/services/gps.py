import math
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class POI:
    id: str
    name: str
    lat: float
    lng: float
    description: str
    category: str
    audio_guide_id: Optional[str] = None
    image_url: Optional[str] = None


SAMPLE_POI_DB: List[POI] = [
    POI(id="poi_001", name="山门", lat=31.2304, lng=121.4737,
        description="景区入口，建于清代乾隆年间", category="古迹"),
    POI(id="poi_002", name="大雄宝殿", lat=31.2310, lng=121.4742,
        description="始建于唐代，内有金身佛像", category="古迹"),
    POI(id="poi_003", name="观景台", lat=31.2325, lng=121.4755,
        description="俯瞰全景区的最佳位置", category="观景点"),
    POI(id="poi_004", name="竹林小径", lat=31.2298, lng=121.4725,
        description="全长500米的幽静竹林步道", category="自然"),
    POI(id="poi_005", name="古桥", lat=31.2318, lng=121.4730,
        description="明代石拱桥，距今600年历史", category="古迹"),
    POI(id="poi_006", name="茶室", lat=31.2308, lng=121.4748,
        description="提供本地特色茶饮和小食", category="服务"),
    POI(id="poi_007", name="博物馆", lat=31.2330, lng=121.4760,
        description="展示景区历史文化与文物", category="文化"),
    POI(id="poi_008", name="儿童乐园", lat=31.2290, lng=121.4735,
        description="亲子互动游乐区", category="设施"),
]


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class GPSService:
    def __init__(self, poi_db: Optional[List[POI]] = None):
        self.poi_db = poi_db or SAMPLE_POI_DB

    def get_nearby_pois(self, lat: float, lng: float, radius: int = 500) -> List[dict]:
        results = []
        for poi in self.poi_db:
            dist = haversine(lat, lng, poi.lat, poi.lng)
            if dist <= radius:
                results.append({
                    "id": poi.id,
                    "name": poi.name,
                    "lat": poi.lat,
                    "lng": poi.lng,
                    "description": poi.description,
                    "category": poi.category,
                    "distance_m": round(dist, 1),
                })
        results.sort(key=lambda x: x["distance_m"])
        return results

    def get_nearest_poi(self, lat: float, lng: float) -> Optional[dict]:
        nearest = None
        min_dist = float("inf")
        for poi in self.poi_db:
            dist = haversine(lat, lng, poi.lat, poi.lng)
            if dist < min_dist:
                min_dist = dist
                nearest = {
                    "id": poi.id,
                    "name": poi.name,
                    "lat": poi.lat,
                    "lng": poi.lng,
                    "description": poi.description,
                    "category": poi.category,
                    "distance_m": round(min_dist, 1),
                }
        return nearest

    def get_route(self, lat: float, lng: float, interest: str = "all") -> List[dict]:
        filtered = self.poi_db
        interest_map = {
            "古迹": ["古迹", "文化"],
            "自然": ["自然", "观景点"],
            "亲子": ["设施", "自然"],
            "文化": ["文化", "古迹"],
            "休闲": ["服务", "观景点"],
        }
        if interest in interest_map:
            cats = interest_map[interest]
            filtered = [p for p in filtered if p.category in cats]

        user_pos = (lat, lng)
        sorted_pois = sorted(filtered, key=lambda p: haversine(lat, lng, p.lat, p.lng))
        route = []
        for i, poi in enumerate(sorted_pois):
            dist = haversine(lat, lng, poi.lat, poi.lng) if i == 0 else haversine(
                sorted_pois[i - 1].lat, sorted_pois[i - 1].lng, poi.lat, poi.lng
            )
            route.append({
                "order": i + 1,
                "id": poi.id,
                "name": poi.name,
                "lat": poi.lat,
                "lng": poi.lng,
                "description": poi.description,
                "category": poi.category,
                "distance_from_prev_m": round(dist, 1),
            })
        return route
