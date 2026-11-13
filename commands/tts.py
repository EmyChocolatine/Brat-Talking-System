import discord
from discord import app_commands
from discord.ext import commands


async def setup_tts(bot: commands.Bot):
    @bot.tree.command(name="t", description="Fait lire un texte dans votre canal vocal.")
    @app_commands.describe(texte="Texte à prononcer (jusqu'à 2000 caractères).")
    @app_commands.guild_only()
    async def t(interaction: discord.Interaction, texte: app_commands.Range[str, 1, 2000]):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message(
                "Cette commande doit être utilisée sur un serveur.", ephemeral=True
            )

        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message(
                "Tu dois d'abord rejoindre un canal vocal.", ephemeral=True
            )

        if not texte.strip():
            return await interaction.response.send_message(
                "Le texte est vide.", ephemeral=True
            )

        voice_id = await bot.db.get_voice(interaction.guild.id, interaction.user.id)
        if not voice_id:
            voice_id = await bot.db.get_voice(interaction.guild.id, 0)

        if not voice_id:
            return await interaction.response.send_message(
                "Aucune voix n'est configurée pour toi et aucune voix par défaut n'est définie sur ce serveur.",
                ephemeral=True,
            )

        confirmations_enabled = await bot.db.get_confirmation_messages(
            interaction.guild.id
        )

        # Discord exige un accusé de réception rapide pour les commandes slash.
        # Si les confirmations sont désactivées, on supprime immédiatement
        # le message éphémère de chargement après le defer.
        await interaction.response.defer(ephemeral=True, thinking=True)

        if not confirmations_enabled:
            try:
                await interaction.delete_original_response()
            except discord.HTTPException:
                pass

        session = bot.voice_manager.get_session(interaction.guild.id)

        try:
            await session.enqueue(interaction, texte, voice_id)

            if confirmations_enabled:
                await interaction.followup.send(
                    "Ajouté à la file d'attente vocale.",
                    ephemeral=True,
                )

        except discord.Forbidden:
            await interaction.followup.send(
                "Je n'ai pas la permission de rejoindre ou parler dans ce canal vocal.",
                ephemeral=True,
            )
        except Exception as exc:
            await interaction.followup.send(
                f"Impossible de rejoindre le vocal : {exc}",
                ephemeral=True,
            )
