import asyncio
import io
import logging

import discord

from config import settings
from services.elevenlabs import ElevenLabsError


log = logging.getLogger(__name__)


class GuildVoiceSession:
    def __init__(self, bot, guild_id: int, db, eleven):
        self.bot = bot
        self.guild_id = guild_id
        self.db = db
        self.eleven = eleven
        self.queue: asyncio.Queue = asyncio.Queue()
        self.worker: asyncio.Task | None = None
        self.lock = asyncio.Lock()
        self.voice_client: discord.VoiceClient | None = None

    async def enqueue(
        self,
        interaction: discord.Interaction,
        text: str,
        voice_id: str,
    ):
        async with self.lock:
            channel = interaction.user.voice.channel

            if self.voice_client and self.voice_client.is_connected():
                if self.voice_client.channel != channel:
                    await self.voice_client.move_to(channel)
            else:
                self.voice_client = await channel.connect()

            if self.worker is None or self.worker.done():
                self.worker = asyncio.create_task(self._worker())

            await self.queue.put((interaction, text, voice_id))

    async def _worker(self):
        while True:
            timeout_minutes = await self.db.get_timeout(
                self.guild_id,
                settings.default_timeout_minutes,
            )

            try:
                interaction, text, voice_id = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=timeout_minutes * 60,
                )
            except asyncio.TimeoutError:
                # Synchronise avec enqueue() pour éviter une tâche perdue
                # à la frontière du timeout.
                async with self.lock:
                    if not self.queue.empty():
                        continue

                    if self.voice_client and self.voice_client.is_connected():
                        await self.voice_client.disconnect()

                    self.voice_client = None
                    self.worker = None
                return

            try:
                confirmations_enabled = await self.db.get_confirmation_messages(
                    self.guild_id
                )

                if confirmations_enabled:
                    try:
                        await interaction.followup.send(
                            "🔊 Génération et lecture en cours…",
                            ephemeral=True,
                        )
                    except discord.HTTPException:
                        # Une confirmation qui échoue ne doit pas empêcher
                        # la génération et la lecture audio.
                        log.warning(
                            "Impossible d'envoyer le message de progression.",
                            exc_info=True,
                        )

                audio = await self.eleven.synthesize(voice_id, text)

                if not audio:
                    raise RuntimeError("ElevenLabs a retourné un audio vide.")

                log.info(
                    "Audio reçu : %s octets | Signature : %s",
                    len(audio),
                    audio[:16].hex(),
                )

                if not self.voice_client or not self.voice_client.is_connected():
                    member = interaction.user

                    if not member.voice or not member.voice.channel:
                        log.warning(
                            "Lecture annulée : l'utilisateur a quitté le canal vocal."
                        )
                        continue

                    self.voice_client = await member.voice.channel.connect()

                # Audio conservé en mémoire : aucun fichier temporaire.
                audio_buffer = io.BytesIO(audio)
                source = discord.FFmpegOpusAudio(
                    audio_buffer,
                    pipe=True,
                )

                loop = asyncio.get_running_loop()
                finished = loop.create_future()

                def after_play(error):
                    def complete():
                        if finished.done():
                            return
                        if error:
                            finished.set_exception(error)
                        else:
                            finished.set_result(None)

                    loop.call_soon_threadsafe(complete)

                self.voice_client.play(source, after=after_play)

                log.info(
                    "Lecture démarrée : connected=%s | playing=%s",
                    self.voice_client.is_connected(),
                    self.voice_client.is_playing(),
                )

                await finished

            except ElevenLabsError as exc:
                try:
                    await interaction.followup.send(
                        f"❌ {exc}",
                        ephemeral=True,
                    )
                except discord.HTTPException:
                    log.exception("Impossible d'envoyer l'erreur ElevenLabs à Discord")

            except Exception:
                log.exception("Erreur pendant la lecture TTS")
                try:
                    await interaction.followup.send(
                        "❌ Une erreur est survenue pendant la génération ou la lecture audio.",
                        ephemeral=True,
                    )
                except discord.HTTPException:
                    log.exception("Impossible d'envoyer le message d'erreur à Discord")

            finally:
                self.queue.task_done()

    async def close(self):
        if self.worker and not self.worker.done():
            self.worker.cancel()

        if self.voice_client and self.voice_client.is_connected():
            await self.voice_client.disconnect()


class VoiceManager:
    def __init__(self, bot, db, eleven):
        self.bot = bot
        self.db = db
        self.eleven = eleven
        self.sessions: dict[int, GuildVoiceSession] = {}

    def get_session(self, guild_id: int) -> GuildVoiceSession:
        if guild_id not in self.sessions:
            self.sessions[guild_id] = GuildVoiceSession(
                self.bot,
                guild_id,
                self.db,
                self.eleven,
            )
        return self.sessions[guild_id]

    async def close_all(self):
        await asyncio.gather(
            *(session.close() for session in self.sessions.values()),
            return_exceptions=True,
        )
