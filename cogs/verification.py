from discord.ext import commands
import discord

class Verification(commands.Cog):
  """The description for Tickets goes here."""

  def __init__(self, bot):
    self.bot = bot

  #Listener to keep the verification view (button) active if the bot restarts and so that it doesn't change to a state of inactivity
  @commands.Cog.listener()
  async def on_ready(self):
    self.bot.add_view(VerificationView())


  #Verify message containing a view (button)
  @commands.hybrid_command(name="verify")
  @commands.has_permissions(administrator=True)
  async def verify(self, ctx):
    
    embed = discord.Embed(title="✅ Welcome to Safasr Studios! 👋 ", description="To start Your journey gain full access to the server, please click the button bellow! ↙️", color=0x8B62FF)
    await ctx.send(embed=embed, view=VerificationView())

#View (button) that gives/removes a specified role from the user in the server
class VerificationView(discord.ui.View):

  def __init__(self):
    super().__init__(timeout=None)

  @discord.ui.button(label="✅ Verify", custom_id="VERIFY", style=discord.ButtonStyle.success)
  async def button(self, interaction: discord.Interaction, button: discord.ui.Button):
      user = interaction.user
      role_id = 993458372202475590
      role = interaction.guild.get_role(role_id)

      if role in user.roles:
          await user.remove_roles(role)
          await interaction.response.send_message("'Member' role has been removed", ephemeral=True)
      else:
          await user.add_roles(role)
          await interaction.response.send_message("You have been successfully verified!", ephemeral=True)

async def setup(bot):
  await bot.add_cog(Verification(bot))