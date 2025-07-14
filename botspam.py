import asyncio
import discord
from discord import app_commands
from discord.ui import View
import nest_asyncio

nest_asyncio.apply()

TOKEN = ""

intents = discord.Intents.default()
intents.guilds = True

async def safe_followup_send(interaction, content=None, **kwargs):
    try:
        await interaction.followup.send(content, **kwargs)
    except discord.HTTPException as e:
        if e.status == 429:
            # silently ignore rate limit error
            pass
        else:
            raise

class ContinueView(View):
    def __init__(self, message: str, remaining: int, user_id: int):
        super().__init__(timeout=120)
        self.message = message
        self.remaining = remaining
        self.user_id = user_id

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.primary)
    async def continue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This button isn't for you!", ephemeral=True)
            return

        try:
            await interaction.response.defer(ephemeral=True)

            count = min(self.remaining, 5)

            for _ in range(count):
                await safe_followup_send(interaction, self.message)
                await asyncio.sleep(0.1)

            remaining_after = self.remaining - count

            button.disabled = True
            await interaction.message.edit(view=self)

            if remaining_after > 0:
                new_view = ContinueView(self.message, remaining_after, self.user_id)
                await safe_followup_send(
                    interaction,
                    f"Click Continue to send {remaining_after} more message(s)...",
                    ephemeral=True,
                    view=new_view
                )
            else:
                await safe_followup_send(interaction, "All messages sent!", ephemeral=True)

        except Exception as e:
            print(f"Error in button callback: {e}")
            try:
                await safe_followup_send(interaction, f"Error: {e}", ephemeral=True)
            except:
                pass

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

client = MyClient()

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user} (ID: {client.user.id})")

@client.tree.command(name="spam", description="Spam messages in batches of 5 (max 30)")
@app_commands.describe(message="The message to spam", count="Number of times to send (max 30)")
async def spam(interaction: discord.Interaction, message: str, count: app_commands.Range[int, 1, 30]):
    await interaction.response.defer(ephemeral=True)

    first_batch = min(count, 5)

    for _ in range(first_batch):
        await safe_followup_send(interaction, message)
        await asyncio.sleep(0.1)

    remaining = count - first_batch

    if remaining > 0:
        view = ContinueView(message, remaining, interaction.user.id)
        await safe_followup_send(
            interaction,
            f"Click Continue to send {remaining} more message(s)...",
            ephemeral=True,
            view=view
        )
    else:
        await safe_followup_send(interaction, "All messages sent!", ephemeral=True)

@client.tree.command(name="sentjoke", description="Send the Roblox official joke message")
async def sentjoke(interaction: discord.Interaction):
    # Ephemeral first message
    await interaction.response.send_message("Sending joke link...", ephemeral=True)
    await asyncio.sleep(0.5)
    # Public followup message with the Roblox joke
    await interaction.followup.send(
        "official roblox message, we have been partnered with discord, Claim your nitro now by playing roblox!!! https://discord.gift/eC969wN9wHfnfSSxDAShM3U4"
    )


if __name__ == "__main__":
    asyncio.run(client.start(TOKEN))
