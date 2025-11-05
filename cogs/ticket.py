from discord.ext import commands
import discord
import json
import os
import asyncio
import config  # <-- Import the new config file

class Ticket(commands.Cog):

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

  async def _handle_ticket_close_and_review(self, interaction_or_ctx, ticket_id, ticket_data):
    """
    Handles all logic for closing a ticket and starting the review process.
    Called by both the /closecatalogue command and the Close button.
    """
    # Get common attributes from interaction or context
    guild = interaction_or_ctx.guild
    
    ticket_creator_id = ticket_data['author']
    item_subject = ticket_data.get('subject', 'Unknown Item') # <-- BUG FIX: Get subject from data
    
    # 1. Delete ticket file
    ticket_file = f'jsons/tickets/{ticket_id}.json'
    if os.path.exists(ticket_file):
        os.remove(ticket_file)

    # 2. Send closing message (if it's a command)
    channel = interaction_or_ctx.channel
    if isinstance(interaction_or_ctx, commands.Context):
        await channel.send(f'This ticket has been closed by {interaction_or_ctx.author.mention}.')

    await asyncio.sleep(3)

    # 3. Delete the ticket channel
    if channel and channel.id == ticket_id:
        try:
            await channel.delete()
        except discord.NotFound:
            pass # Channel already deleted

    # 4. Create review channel
    review_category = discord.utils.get(guild.categories, name="――――― 𝗠𝗬 𝗢𝗥𝗗𝗘𝗥𝗦 ――――")
    if not review_category:
        review_category = await guild.create_category(name="――――― 𝗠𝗬 𝗢𝗥𝗗𝗘𝗥𝗦 ――――")
    
    numbers = await self._load_or_create_json('review_numbers.json')
    number = numbers[-1] + 1 if numbers else 1
    numbers.append(number)
    with open('review_numbers.json', 'w') as f:
        json.dump(numbers, f)

    try:
        creator_member = await guild.fetch_member(ticket_creator_id)
    except discord.NotFound:
        return # User left the server, abort review

    review_channel = await review_category.create_text_channel(name=f"⭐-review-{number}")
    await review_channel.set_permissions(guild.default_role, view_channel=False)
    await review_channel.set_permissions(creator_member, view_channel=True)

    def check(message):
        return message.channel == review_channel and message.author == creator_member
      
    reviewview = ReviewView(creator_member.id)
    await review_channel.send(f"{creator_member.mention}")
    reviewembed = discord.Embed(title="", description="```Thanks again for ordering and we highly appreciate your choice on choosing us! We invite you to share your experience and help us serve you better with your honest review. Your feedback fuels our growth!\nWould you like to leave a review?```", color=0x8B62FF)
    await review_channel.send(embed=reviewembed, view=reviewview)
    await reviewview.wait()

    if reviewview.response is not True:
        await review_channel.delete()
        return

    # Create RatingView
    view = RatingView(creator_member.id)
    ratingembed = discord.Embed(title="", description="```That’s Awesome! Would you like to rate your overall experience with us on a scale of 1 to 5?```", color=0x8B62FF)
    rating_msg = await review_channel.send(embed=ratingembed, view=view)

    await view.wait()

    if view.rating is None:
        await rating_msg.edit(content="Time's up! Please try again.", view=None)
        await review_channel.delete()
        return

    rating = view.rating
    
    comments = None
    try:
        message = await self.bot.wait_for("message", check=check, timeout=300)
        comments = message.content
    except asyncio.TimeoutError:
        await review_channel.send("Time's up! Please try again.")
        await review_channel.delete() # Also delete channel on comment timeout
        return
        
    stars = ":star: " * rating
    
    # Send review data to the specific channel from config
    review_channel_to_send = self.bot.get_channel(config.REVIEW_LOG_CHANNEL_ID) # <-- CONFIG VAR
    
    if review_channel_to_send:
        pfp = creator_member.avatar.url if creator_member.avatar else creator_member.default_avatar.url
        embed = discord.Embed(title=f"📦New Catalog Review⭐",
                              color=0x8B62FF)
        embed.add_field(name="👤 Client", value=f"{creator_member.mention}", inline=False)
        embed.add_field(name="💭 Comments", value=f"```{comments}```", inline=False)
        embed.add_field(name="Rating", value=stars, inline=False)
        embed.add_field(name="Product Ordered", value=f"{item_subject}".title()) # <-- BUG FIX
        embed.set_thumbnail(url=pfp)
        await review_channel_to_send.send(embed=embed)

    await review_channel.delete()

  # --- Cog Listener ---

  @commands.Cog.listener()
  async def on_ready(self):
    items = await self._load_or_create_json("items.json") # <-- Use helper
    
    if items:
        for item in items:
            self.bot.add_view(Item1View(self.bot, item))
            self.bot.add_view(CloseTicketView(self.bot, item))

  # --- Cog Commands ---

  @commands.hybrid_command(name="catalogue",
                         description="Creates the catalogue message.")
  @commands.has_permissions(administrator=True)
  async def catalogue(self, ctx, name: str, description: str, version: str,
                 size: str, priceinusd: float):
      await ctx.send("Please upload an image for the item.")
      try:
          message = await self.bot.wait_for(
              "message",
              check=lambda m: m.channel == ctx.channel and m.author == ctx.author and len(m.attachments) > 0,
              timeout=60.0
          )
          image_url = message.attachments[0].url
      except asyncio.TimeoutError:
          await ctx.send("Timed out waiting for image.")
          return
  
      embed = discord.Embed(title=f"**{name}**", description=f"*{description}*", color=0x8B62FF)
      embed.add_field(name=":wrench: Version", value=version)
      embed.add_field(name=":triangular_ruler: Size", value=size)
      embed.add_field(name=":dollar: Price", value=f"{priceinusd} USD")
      embed.set_image(url=image_url)
      subject = name
      
      # Use channel ID from config file
      specific_channel = ctx.guild.get_channel(config.CATALOGUE_CHANNEL_ID) # <-- CONFIG VAR
      if not specific_channel:
          await ctx.send(f"Error: Catalogue channel ID ({config.CATALOGUE_CHANNEL_ID}) not found.")
          return
          
      await ctx.send(f"Item {name} created in {specific_channel.mention}")
      await specific_channel.send(embed=embed, view=Item1View(self.bot, subject))
  
      # Save the item name to items.json
      items = await self._load_or_create_json("items.json") # <-- Use helper
      items.append(name)
      with open("items.json", "w") as f:
          json.dump(items, f, indent=4)

  @commands.hybrid_command(name="closecatalogue", description="Close the catalogue ticket you are currently in.")
  async def closecatalogue(self, ctx):
    ticket_id = ctx.channel.id
    ticket_file = f'jsons/tickets/{ticket_id}.json'
    
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
    await self._handle_ticket_close_and_review(ctx, ticket_id, ticket_data)


# --- Views ---

class ReviewView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=2880)
        self.author_id = author_id
        self.response = None

    @discord.ui.button(label="Yes", custom_id="YES", style=discord.ButtonStyle.primary)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.author_id:
            self.response = True
            self.stop()
            await interaction.response.send_message("⠀")
        else:
            await interaction.response.send_message("Only the ticket author can rate.", ephemeral=True)
            
    @discord.ui.button(label="No", custom_id="NO", style=discord.ButtonStyle.primary)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.author_id:
          self.response = False
          self.stop()
          await interaction.response.send_message("Alright, the review channel will now close.")

class RatingView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=2880)
        self.author_id = author_id
        self.rating = None

    async def send_rating_response(self, interaction: discord.Interaction, rating: int):
        if interaction.user.id == self.author_id:
            self.rating = rating
            self.stop()
            embed = discord.Embed(title="", description="```Amazing! Would you like to leave a small comment regarding your experience and the results you’ve got?``` *Write a comment and send it as a message here*", color=0x8B62FF)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Only the ticket author can rate.", ephemeral=True)

    @discord.ui.button(label="1⭐", custom_id="rating_1", style=discord.ButtonStyle.primary)
    async def rate_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_rating_response(interaction, 1)
          
    @discord.ui.button(label="2⭐", custom_id="rating_2", style=discord.ButtonStyle.primary)
    async def rate_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_rating_response(interaction, 2)
          
    @discord.ui.button(label="3⭐", custom_id="rating_3", style=discord.ButtonStyle.primary)
    async def rate_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_rating_response(interaction, 3)
          
    @discord.ui.button(label="4⭐", custom_id="rating_4", style=discord.ButtonStyle.primary)
    async def rate_4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_rating_response(interaction, 4)
          
    @discord.ui.button(label="5⭐", custom_id="rating_5", style=discord.ButtonStyle.primary)
    async def rate_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_rating_response(interaction, 5)

class Item1View(discord.ui.View):

  def __init__(self, bot, subject):
    super().__init__(timeout=None)
    self.bot = bot
    self.subject = subject

  @discord.ui.button(label="🤲Get",
                     custom_id="GET4",
                     style=discord.ButtonStyle.success)
  async def button(self, interaction: discord.Interaction,
                   button: discord.ui.Button):
    category = discord.utils.get(interaction.guild.categories, name="――――― M𝗬 𝗢𝗥𝗗𝗘𝗥𝗦 ――――")
    if not category:
      category = await interaction.guild.create_category(name="――――― 𝗠𝗬 𝗢𝗥𝗗𝗘𝗥𝗦 ――――")
    
    # Use helper to load numbers
    numbers = await self.bot.get_cog("Ticket")._load_or_create_json('catalogue_numbers.json')
    number = numbers[-1] + 1 if numbers else 1
    numbers.append(number)
    with open('catalogue_numbers.json', 'w') as f:
        json.dump(numbers, f)

    channel = await category.create_text_channel(name=f"📦-catalogue-{number}")
    await channel.set_permissions(interaction.guild.default_role,
                                  reason="Private Ticket",
                                  view_channel=False)
    await channel.set_permissions(interaction.user,
                                  read_messages=True,
                                  send_messages=True,
                                  view_channel=True)
    await interaction.response.send_message(
      f"Ticket channel created in {channel.mention}", ephemeral=True)
    
    # Ensure jsons/tickets directory exists
    os.makedirs('jsons/tickets', exist_ok=True)
    
    ticket_data = {
      'subject': self.subject, # This is the item name, good!
      'status': 'Open',
      'author': interaction.user.id,
      'channelid': channel.id,
      'chatlogs': 'Ticket Opened'
    }
    with open(f'jsons/tickets/{channel.id}.json', 'w') as f:
      json.dump(ticket_data, f)
      
    embed = discord.Embed(title="👀I'm interested in this item📦", description="The Staff will be with you shortly. 🕐Please don't close the ticket or all the information for your order will be lost!", color=0x8B62FF)
    embed.add_field(name="👤 Creator",
                    value=f"<@{interaction.user.id}>",
                    inline=False)
    embed.add_field(name="Item", value=self.subject)
    await channel.send(embed=embed, view=CloseTicketView(self.bot, self.subject))

class CloseTicketView(discord.ui.View):

  def __init__(self, bot, subject):
    super().__init__(timeout=None)
    self.bot = bot
    self.subject = subject # Note: this subject is from the *original* item, not the ticket
                          # This is why reading from ticket_data.json is crucial

  @discord.ui.button(label="Close Ticket",
                     custom_id="close_ticket",
                     style=discord.ButtonStyle.danger)
  async def close(self, interaction: discord.Interaction,
                  button: discord.ui.Button):
    ticket_id = interaction.channel_id
    ticket_file = f'jsons/tickets/{ticket_id}.json'

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
    await self.bot.get_cog("Ticket")._handle_ticket_close_and_review(interaction, ticket_id, ticket_data)
    
async def setup(bot):
  await bot.add_cog(Ticket(bot))