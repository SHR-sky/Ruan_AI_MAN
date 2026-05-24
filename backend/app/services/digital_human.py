from fastapi import UploadFile


class DigitalHumanService:
    def __init__(self):
        self.config = {
            "name": "小导",
            "gender": "female",
            "voice_type": "default",
            "appearance_url": "",
        }

    def update_config(self, name: str, gender: str, voice_type: str, appearance_url: str) -> dict:
        self.config["name"] = name
        self.config["gender"] = gender
        self.config["voice_type"] = voice_type
        if appearance_url:
            self.config["appearance_url"] = appearance_url
        return self.config

    def get_config(self) -> dict:
        return self.config

    async def generate_expression(self, text: str) -> dict:
        return {"expression": "neutral", "phonemes": [], "duration": 0.0}

    async def upload_appearance(self, file: UploadFile) -> str:
        return f"/uploads/appearance/{file.filename}"
