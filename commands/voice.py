import discord
from discord import app_commands
from discord.ext import commands
from services.elevenlabs import ElevenLabsError


async def setup_voice(bot: commands.Bot):
    @bot.tree.command(
        name="set-personal-voice",
        description="Définit ta voix ElevenLabs, ou celle d'un membre si tu es administrateur.",
    )
    @app_commands.describe(
        voice_id="Identifiant de la voix dans ta bibliothèque ElevenLabs",
        user="Membre ciblé (laisser vide pour configurer ta propre voix)",
    )
    @app_commands.guild_only()
    async def set_personal_voice(
        interaction: discord.Interaction,
        voice_id: app_commands.Range[str, 1, 100],
        user: discord.Member | None = None,
    ):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Commande réservée aux serveurs.", ephemeral=True)

        target = user or interaction.user
        is_admin = interaction.user.guild_permissions.administrator
        if target.id != interaction.user.id and not is_admin:
            return await interaction.response.send_message(
                "Tu peux uniquement configurer ta propre voix. Un administrateur peut configurer celle des autres.",
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            await bot.eleven.validate_voice(voice_id)
            await bot.db.set_voice(interaction.guild.id, target.id, voice_id)
            await interaction.followup.send(
                f"Voix enregistrée pour **{target.display_name}** sur ce serveur.",
                ephemeral=True,
            )
        except ElevenLabsError as exc:
            await interaction.followup.send(f"Impossible de valider cette voix : {exc}", ephemeral=True)
