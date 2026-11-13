from asyncio.log import logger
import logging
import discord
from discord.ext import commands
from config import settings
from database.database import Database
from services.elevenlabs import ElevenLabsService
from services.voice_manager import VoiceManager
from commands.tts import setup_tts
from commands.voice import setup_voice
from commands.settings import setup_settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("discord_tts")


class TTSBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.db = Database(settings.database_path)
        self.eleven = ElevenLabsService(settings.elevenlabs_api_key)
        self.voice_manager = VoiceManager(self, self.db, self.eleven)

    async def setup_hook(self):
        await self.db.initialize()
        await setup_tts(self)
        await setup_voice(self)
        await setup_settings(self)
        synced = await self.tree.sync()
        log.info("Synchronisation de %d commandes slash.", len(synced))

    async def close(self):
        await self.voice_manager.close_all()
        await self.db.close()
        await super().close()

bot = TTSBot()


@bot.event
async def on_ready():
    log.info("Connecté en tant que %s (%s)", bot.user, bot.user.id)


if __name__ == "__main__":
    if not settings.discord_token or not settings.elevenlabs_api_key:
        raise RuntimeError("DISCORD_TOKEN et ELEVENLABS_API_KEY doivent être définis dans .env")
    bot.run(settings.discord_token)
