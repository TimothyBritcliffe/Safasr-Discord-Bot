from discord.ext import commands
import discord
import config  # <-- 1. Import config

class Verification(commands.Cog):
  """Handles the member verification system."""

  def __init__(self, bot):
    self.bot = bot

  #Listener to keep the verification view (button) active if the bot restarts
  @commands.Cog.listener()
  async def on_ready(self):
    self.bot.add_view(VerificationView())


  #Verify message containing a view (button)
  @commands.hybrid_command(name="verify", description="Posts the verification message.")
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
      
      # 2. Use the Role ID from config
      role = interaction.guild.get_role(config.VERIFICATION_ROLE_ID) 

      if role is None:
          # Safety check in case the ID in config is wrong or deleted
          await interaction.response.send_message("An error occurred. Please contact an administrator.", ephemeral=True)
          return
          
      if role in user.roles:
          try:
              await user.remove_roles(role)
              await interaction.response.send_message("'Member' role has been removed.", ephemeral=True)
          except discord.Forbidden:
              await interaction.response.send_message("I don't have permissions to remove your role. Please contact an admin.", ephemeral=True)
      else:
          try:
              await user.add_roles(role)
              await interaction.response.send_message("You have been successfully verified!", ephemeral=True)
          except discord.Forbidden:
              await interaction.response.send_message("I don't have permissions to give you the role. Please contact an admin.", ephemeral=True)

async def setup(bot):
  await bot.add_cog(Verification(bot))