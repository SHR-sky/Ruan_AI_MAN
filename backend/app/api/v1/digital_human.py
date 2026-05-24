from fastapi import APIRouter, UploadFile, File
from app.services.digital_human import DigitalHumanService

router = APIRouter()
dh_service = DigitalHumanService()


@router.post("/config")
async def update_config(
    name: str = "小导",
    gender: str = "female",
    voice_type: str = "default",
    appearance_url: str = "",
):
    config = dh_service.update_config(name, gender, voice_type, appearance_url)
    return {"status": "ok", "config": config}


@router.get("/config")
async def get_config():
    return dh_service.get_config()


@router.post("/appearance")
async def upload_appearance(file: UploadFile = File(...)):
    url = await dh_service.upload_appearance(file)
    return {"url": url, "status": "updated"}
