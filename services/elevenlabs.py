import aiohttp
from config import settings 

class ElevenLabsError(Exception):
    pass


class ElevenLabsService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.elevenlabs.io/v1"

    async def validate_voice(self, voice_id: str) -> dict:
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                f"{self.base_url}/voices/{voice_id}",
                headers={"xi-api-key": self.api_key},
            ) as response:
                if response.status == 404:
                    raise ElevenLabsError("Cette voix n'existe pas ou n'est pas accessible avec cette clé API.")
                if response.status == 401:
                    raise ElevenLabsError("Clé API ElevenLabs invalide.")
                if response.status >= 400:
                    detail = (await response.text())[:500]
                    raise ElevenLabsError(f"ElevenLabs a répondu {response.status}: {detail}")
                return await response.json()

    async def synthesize(self, voice_id: str, text: str) -> bytes:
        url = f"{self.base_url}/text-to-speech/{voice_id}/stream"

        params = {
            "output_format": settings.elevenlabs_output_format
        }

        payload = {
            "text": text,
            "model_id": settings.elevenlabs_model_id
        }

        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                params=params,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:

                if response.status >= 400:
                    raise ElevenLabsError(
                        f"ElevenLabs error: {await response.text()}"
                    )

                audio = await response.read()

                if not audio:
                    raise ElevenLabsError("Audio stream is empty")

                return audio
