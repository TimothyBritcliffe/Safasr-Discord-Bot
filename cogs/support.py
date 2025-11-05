from discord.ext import commands
import discord
import json
import os
import asyncio


class Support(commands.Cog):
  """The description for Tickets goes here."""

  def __init__(self, bot):
    self.bot = bot

  #Listener to keep all buttons that have previously been made and will be made active
  @commands.Cog.listener()
  async def on_ready(self):
    self.bot.add_view(SupportView())
    self.bot.add_view(CloseSupportView())

  #Support ticket message with buttons (views)
  @commands.hybrid_command(name = "support", description="Sends the support embed and button")
  @commands.has_permissions(administrator=True)
  async def support(self, ctx):

    embed = discord.Embed(title="❓ Support | Safasr Studios", description="Need help? Don't panic! Click the button below to open a support ticket and our team will come to your rescue faster than you can say \"Safasr Studios!\n\n```To open a ticket, click on the button below!```", color=0x8B62FF)

    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1094284026908520569/1104682940144828447/support.png")
    await ctx.send(embed = embed, view = SupportView())


  #Command to close a support ticket
  @commands.hybrid_command(name="closesupport", description="Close the support ticket you are currently in.")
  async def closesupport(self, ctx):
    # Get the channel_id
    ticket_id = ctx.channel.id

    # Check if the ticket exists
    ticket_file = f'jsons/tickets/{ticket_id}.json'
    if not os.path.exists(ticket_file):
      return await ctx.send(f'Ticket #{ticket_id} does not exist.')

    # Load the ticket data
    with open(ticket_file) as f:
      ticket_data = json.load(f)

    # Check if the author or an admin is trying to close the ticket
    if ctx.author.id != ticket_data[
        'author'] and not ctx.author.guild_permissions.administrator:
      return await ctx.send(
        'Only the author of the ticket or an administrator can close it.')
    ticket_creator = ticket_data['author']
    # Delete the ticket file
    os.remove(ticket_file)

    await ctx.send(
      f'This ticket has been closed by <@{ctx.author.id}>.')

    await asyncio.sleep(3)

    # Delete the ticket channel
    ticket_channel = ctx.guild.get_channel(ticket_id)
    if ticket_channel:
      await ticket_channel.delete()


#View to create a button that opens a support ticket
class SupportView(discord.ui.View):

  def __init__(self):
    super().__init__(timeout=None)

  @discord.ui.button(label="❔Support", custom_id="OPEN_TICKET", style=discord.ButtonStyle.success)
  async def button(self, interaction: discord.Interaction,
                   button: discord.ui.Button):
    category = discord.utils.get(interaction.guild.categories, name="――――― 𝗠𝗬 𝗢𝗥𝗗𝗘𝗥𝗦 ――――")
    if not category:
      category = await interaction.guild.create_category(name="――――― 𝗠𝗬 𝗢𝗥𝗗𝗘𝗥𝗦 ――――")
    
    with open('support_numbers.json', 'r') as f:
        numbers = json.load(f)
    number = None
    if numbers:
        last_number = numbers[-1]
        number = last_number + 1
    else:
        number = 1

    # Create a new ticket channel
    channel = await category.create_text_channel(name=f"❔-support-{number}")
    numbers.append(number)
    with open('support_numbers.json', 'w') as f:
        json.dump(numbers, f)
    # Set channel permissions to only allow access to users with the "Manage Channels" permission
    await channel.set_permissions(interaction.guild.default_role, reason="Private Ticket", view_channel=False)
    await channel.set_permissions(interaction.user, read_messages=True, send_messages=True, view_channel=True)
    
    await interaction.response.send_message(
      f"Ticket channel created in {channel.mention}", ephemeral=True)
    # Save the ticket data
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

#View that creates a button that will close the ticket that it is in when pressed
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

    # Load the ticket data
    with open(ticket_file) as f:
      ticket_data = json.load(f)

    # Check if the author or an admin is trying to close the ticket
    if interaction.user.id != ticket_data[
        'author'] and not interaction.user.guild_permissions.administrator:
      return await interaction.response.send_message(
        'Only the author of the ticket or an administrator can close it.')
    ticket_creator = ticket_data['author']
    # Delete the ticket file
    os.remove(ticket_file)

    await interaction.response.send_message(
      f'This ticket has been closed by <@{interaction.user.id}>.')

    await asyncio.sleep(3)

    # Delete the ticket channel
    ticket_channel = interaction.guild.get_channel(ticket_id)
    if ticket_channel:
      await ticket_channel.delete()

async def setup(bot):
  await bot.add_cog(Support(bot))