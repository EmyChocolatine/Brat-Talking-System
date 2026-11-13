import discord
from discord import app_commands
from discord.ext import commands


async def setup_settings(bot: commands.Bot):
    @bot.tree.command(
        name="set-timeout",
        description="Configure le délai d'inactivité avant déconnexion."
    )
    @app_commands.describe(minutes="Délai en minutes (1 à 240).")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def set_timeout(
        interaction: discord.Interaction,
        minutes: app_commands.Range[int, 1, 240] = 30,
    ):
        await bot.db.set_timeout(interaction.guild_id, minutes)
        await interaction.response.send_message(
            f"Le bot se déconnectera après **{minutes} minute(s)** sans nouvelle demande.",
            ephemeral=True,
        )

    @set_timeout.error
    async def set_timeout_error(
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ):
        if isinstance(error, app_commands.MissingPermissions):
            message = "Seuls les administrateurs peuvent modifier le timeout."
        else:
            message = "Impossible de modifier le timeout."

        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)

    @bot.tree.command(
        name="toggle-confirmation-messages",
        description="Active ou désactive les messages de confirmation du bot."
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def toggle_confirmation_messages(interaction: discord.Interaction):
        guild_id = interaction.guild_id
        if guild_id is None:
            return await interaction.response.send_message(
                "Cette commande doit être utilisée sur un serveur.",
                ephemeral=True,
            )

        current = await bot.db.get_confirmation_messages(guild_id)
        new_value = not current
        await bot.db.set_confirmation_messages(guild_id, new_value)

        if new_value:
            message = "Les messages de confirmation sont maintenant **activés**."
        else:
            message = "Les messages de confirmation sont maintenant **désactivés**."

        await interaction.response.send_message(message, ephemeral=True)

    @toggle_confirmation_messages.error
    async def toggle_confirmation_messages_error(
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ):
        if isinstance(error, app_commands.MissingPermissions):
            message = "Seuls les administrateurs peuvent modifier les messages de confirmation."
        else:
            message = "Impossible de modifier les messages de confirmation."

        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
