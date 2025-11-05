from discord.ext import commands
import discord
import json
import os
import asyncio
import config  # <-- Import config

class Support(commands.Cog):
  """Cog for handling support tickets."""

  def __init__(self, bot):
    self.bot = bot

  # --- Helper Function for JSON I/O ---
  
  async def _load_or_create_json(self, filename, default_data=[]):
    """
    Safely loads a JSON file. If it doesn't exist or is corrupt,
    it creates/resets it with default_data.
    """
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            json.dump(default_data, f)
        return default_data
    else:
        try:
            with open(filename, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # If file is corrupt or empty, reset it
            with open(filename, "w") as f:
                json.dump(default_data, f)
            return default_data

  # --- Helper Function for Refactored Close Logic ---

  async def _handle_close_support_ticket(self, interaction_or_ctx, ticket_id, ticket_data):
    """
    Handles all logic for closing a support ticket.
    Called by both the /closesupport command and the Close button.
    """
    # Get common attributes from interaction or context
    channel = interaction_or_ctx.channel
    user = interaction_or_ctx.author if isinstance(interaction_or_ctx, commands.Context) else interaction_or_ctx.user
    
    # 1. Delete ticket file
    ticket_file = f'jsons/support/{ticket_id}.json'
    if os.path.exists(ticket_file):
        os.remove(ticket_file)

    # 2. Send closing message
    if isinstance(interaction_or_ctx, commands.Context):
        await channel.send(f'This ticket has been closed by {user.mention}.')
    else:
        # Button interaction was already responded to
        pass

    await asyncio.sleep(3)

    # 3. Delete the ticket channel
    if channel and channel.id == ticket_id:
        try:
            await channel.delete()
        except discord.NotFound:
            pass # Channel already deleted


  # --- Cog Listener ---

  @commands.Cog.listener()
  async def on_ready(self):
    self.bot.add_view(SupportView())
    self.bot.add_view(CloseSupportView())

  # --- Cog Commands ---

  @commands.hybrid_command(name = "support", description="Sends the support embed and button")
  @commands.has_permissions(administrator=True)
  async def support(self, ctx):
    embed = discord.Embed(title="❓ Support | Safasr Studios", description="Need help? Don't panic! Click the button below to open a support ticket and our team will come to your rescue faster than you can say \"Safasr Studios!\"\n\n```To open a ticket, click on the button below!```", color=0x8B62FF)
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1094284026908520569/1104682940144828447/support.png")
    await ctx.send(embed = embed, view = SupportView())


  @commands.hybrid_command(name="closesupport", description="Close the support ticket you are currently in.")
  async def closesupport(self, ctx):
    ticket_id = ctx.channel.id
    
    # <-- BUG FIX: Was 'jsons/tickets/', now 'jsons/support/'
    ticket_file = f'jsons/support/{ticket_id}.json' 
    
    if not os.path.exists(ticket_file):
      return await ctx.send(f'Ticket #{ticket_id} does not exist.', ephemeral=True)
      
    try:
        with open(ticket_file) as f:
            ticket_data = json.load(f)
    except (IOError, json.JSONDecodeError):
        return await ctx.send(f'Error reading ticket data.', ephemeral=True)

    if ctx.author.id != ticket_data.get('author') and not ctx.author.guild_permissions.administrator:
      return await ctx.send(
        'Only the author of the ticket or an administrator can close it.', ephemeral=True)
    
    # Call the refactored function
    await self._handle_close_support_ticket(ctx, ticket_id, ticket_data)


# --- Views ---

class SupportView(discord.ui.View):

  def __init__(self):
    super().__init__(timeout=None)

  @discord.ui.button(label="❔Support", custom_id="OPEN_TICKET", style=discord.ButtonStyle.success)
  async def button(self, interaction: discord.Interaction,
                   button: discord.ui.Button):
    
    # Use category name from config
    category = discord.utils.get(interaction.guild.categories, name=config.TICKET_CATEGORY_NAME)
    if not category:
      category = await interaction.guild.create_category(name=config.TICKET_CATEGORY_NAME)
    
    # Use safe JSON loader
    support_cog = self.bot.get_cog("Support")
    numbers = await support_cog._load_or_create_json('support_numbers.json')
    
    number = numbers[-1] + 1 if numbers else 1
    numbers.append(number)
    
    with open('support_numbers.json', 'w') as f:
        json.dump(numbers, f)

    channel = await category.create_text_channel(name=f"❔-support-{number}")
    await channel.set_permissions(interaction.guild.default_role, reason="Private Ticket", view_channel=False)
    await channel.set_permissions(interaction.user, read_messages=True, send_messages=True, view_channel=True)
    
    await interaction.response.send_message(
      f"Ticket channel created in {channel.mention}", ephemeral=True)
    
    # Ensure jsons/support directory exists
    os.makedirs('jsons/support', exist_ok=True)
    
    ticket_data = {
      'subject': "Support Ticket",
      'status': 'Open',
      'author': interaction.user.id,
      'channelid': channel.id,
      'chatlogs': 'Ticket Opened'
    }
    with open(f'jsons/support/{channel.id}.json', 'w') as f:
      json.dump(ticket_data, f)
      
    embed = discord.Embed(title="New Support Ticket", description="The Staff will be with you shortly. 🕐\nPlease state why you opened this ticktet", color=0x8B62FF)
    embed.add_field(name="👤 Creator",
                    value=f"<@{interaction.user.id}>",
                    inline=False)
    await channel.send(embed=embed, view=CloseSupportView())

class CloseSupportView(discord.ui.View):

  def __init__(self):
    super().__init__(timeout=None)

  @discord.ui.button(label="Close Ticket",
                     custom_id="CLOSE_TICKET",
                     style=discord.ButtonStyle.danger)
  async def close(self, interaction: discord.Interaction,
                  button: discord.ui.Button):
    ticket_id = interaction.channel_id
    ticket_file = f'jsons/support/{ticket_id}.json'

    if not os.path.exists(ticket_file):
      return await interaction.response.send_message(f'Ticket #{ticket_id} does not exist.', ephemeral=True)
      
    try:
        with open(ticket_file) as f:
          ticket_data = json.load(f)
    except (IOError, json.JSONDecodeError):
        return await interaction.response.send_message(f'Error reading ticket data.', ephemeral=True)

    if interaction.user.id != ticket_data.get('author') and not interaction.user.guild_permissions.administrator:
      return await interaction.response.send_message(
        'Only the author of the ticket or an administrator can close it.', ephemeral=True)

    # Defer response so helper function can work
    await interaction.response.send_message(f'This ticket has been closed by {interaction.user.mention}.')
    
    # Call the refactored function
    await self.bot.get_cog("Support")._handle_close_support_ticket(interaction, ticket_id, ticket_data)

async def setup(bot):
  await bot.add_cog(Support(bot))