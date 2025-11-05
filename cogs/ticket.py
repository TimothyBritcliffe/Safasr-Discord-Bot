from discord.ext import commands
import discord
import json
import os
import asyncio


class Ticket(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  #Listener to keep views (buttons) active
  @commands.Cog.listener()
  async def on_ready(self):
    # Load the list of items from the items.json file
    with open("items.json", "r") as f:
        items = json.load(f)

    # Create an Item1View instance for each item
    
    if items:
        for item in items:
            self.bot.add_view(Item1View(self.bot, item))
            self.bot.add_view(CloseTicketView(self.bot, item))
    



  #Code to create the message with buttons (comment this out once it is used in your desired channel)
  @commands.hybrid_command(name="catalogue",
                         description="Creates the catalogue message.")
  @commands.has_permissions(administrator=True)
  async def catalogue(self, ctx, name: str, description: str, version: str,
                 size: str, priceinusd: float):
      # Prompt the user to upload an image
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
  
      # Create the embed with the user-defined information
      embed = discord.Embed(title=f"**{name}**", description=f"*{description}*", color=0x8B62FF)
      embed.add_field(name=":wrench: Version", value=version)
      embed.add_field(name=":triangular_ruler: Size", value=size)
      embed.add_field(name=":dollar: Price", value=f"{priceinusd} USD")
      embed.set_image(url=image_url)
      subject = name
      specific_channel = ctx.guild.get_channel(1104564513581305928)
      await ctx.send(f"Item {name} created in {specific_channel.mention}")
      # Send the embed to the specific channel
      await specific_channel.send(embed=embed, view=Item1View(self.bot, subject))
  
      # Send a confirmation message to the channel where the command was used
  
      # Save the item name to items.json
      items = []
      with open("items.json", "r") as f:
          items = json.load(f)
      items.append(name)
      with open("items.json", "w") as f:
          json.dump(items, f)

  #Command to close the current 'Catalogue' ticket
  @commands.hybrid_command(name="closecatalogue", description="Close the catalogue ticket you are currently in.")
  async def closecatalogue(self, ctx):
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
    # Create review channel
    review_category = discord.utils.get(ctx.guild.categories, name="――――― 𝗠𝗬 𝗢𝗥𝗗𝗘𝗥𝗦 ――――")
    if not review_category:
      review_category = await ctx.guild.create_category(name="――――― 𝗠𝗬 𝗢𝗥𝗗𝗘𝗥𝗦 ――――")
    with open('review_numbers.json', 'r') as f:
        numbers = json.load(f)
    number = None
    if numbers:
        last_number = numbers[-1]
        number = last_number + 1
    else:
        number = 1

    # Create a new ticket channel
    review_channel = await review_category.create_text_channel(name=f"⭐-review-{number}")
    numbers.append(number)
    with open('review_numbers.json', 'w') as f:
        json.dump(numbers, f)
    await review_channel.set_permissions(ctx.guild.default_role,
                                         view_channel=False)
    await review_channel.set_permissions(
      await ctx.guild.fetch_member(ticket_creator), view_channel=True)

    creator = await ctx.guild.fetch_member(ticket_creator)

    def check(message):
      return message.channel == review_channel and message.author == creator
      
    reviewview = ReviewView(creator.id)
    await review_channel.send(f"<@{ticket_creator}>")
    reviewembed = discord.Embed(title="", description="```Thanks again for ordering and we highly appreciate your choice on choosing us! We invite you to share your experience and help us serve you better with your honest review. Your feedback fuels our growth!\nWould you like to leave a review?```", color=0x8B62FF)
    await review_channel.send(embed=reviewembed, view=reviewview)
    await reviewview.wait()

    if reviewview.response is None:
        await review_channel.delete()
        return
    if reviewview.response == False:
        await review_channel.delete()
        return
    if reviewview.response == True:

    
        # Create RatingView
        view = RatingView(creator.id)
        ratingembed = discord.Embed(title="", description="```That’s Awesome! Would you like to rate your overall experience with us on a scale of 1 to 5?```", color=0x8B62FF)
        # Send rating message with buttons
        rating_msg = await review_channel.send(embed=ratingembed, view=view)
    
        # Wait for the rating or timeout
        await view.wait()
    
        if view.rating is None:
            await rating_msg.edit(content="Time's up! Please try again.", view=None)
            await review_channel.delete()
            return
    
        rating = view.rating
    
        
        comments = None
        while comments is None:
          try:
            message = await self.bot.wait_for("message", check=check, timeout=300)
            comments = message.content
          except asyncio.TimeoutError:
            await review_channel.send("Time's up! Please try again.")
            return
        stars = ""
        for i in range(rating):
          stars += ":star: "
        # Send review data to the specific channel
        review_channel_to_send = self.bot.get_channel(1104564795564372069)
        pfp = creator.avatar.url
        embed = discord.Embed(title=f"📦New Catalog Review⭐",
                              color=0x8B62FF)
        embed.add_field(name="👤 Client", value=f"<@{ticket_creator}>", inline=False)
        embed.add_field(name="💭 Comments", value=f"```{comments}```", inline=False)
        embed.add_field(name="Rating", value=stars, inline=False)
        embed.add_field(name="Product Ordered", value=f"{self.subject}".title())
        embed.set_thumbnail(url=pfp)
        review_channel_to_send.send(embed=embed)
    
        # Delete the review channel
        await review_channel.delete()

#View that has two buttons allowing users to opt into leaving a review or opting out
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

#View with buttons that when pressed dictate the users rating of choice of their experience/product
class RatingView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=2880)
        self.author_id = author_id
        self.rating = None

    @discord.ui.button(label="1⭐", custom_id="rating_1", style=discord.ButtonStyle.primary)
    async def rate_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.author_id:
            self.rating = 1
            self.stop()
            embed = discord.Embed(title="", description="```Amazing! Would you like to leave a small comment regarding your experience and the results you’ve got?``` *Write a comment and send it as a message here*", color=0x8B62FF)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Only the ticket author can rate.", ephemeral=True)
          
    @discord.ui.button(label="2⭐", custom_id="rating_2", style=discord.ButtonStyle.primary)
    async def rate_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.author_id:
            self.rating = 2
            self.stop()
            embed = discord.Embed(title="", description="```Amazing! Would you like to leave a small comment regarding your experience and the results you’ve got?``` *Write a comment and send it as a message here*", color=0x8B62FF)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Only the ticket author can rate.", ephemeral=True)
          
    @discord.ui.button(label="3⭐", custom_id="rating_3", style=discord.ButtonStyle.primary)
    async def rate_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.author_id:
            self.rating = 3
            self.stop()
            embed = discord.Embed(title="", description="```Amazing! Would you like to leave a small comment regarding your experience and the results you’ve got?``` *Write a comment and send it as a message here*", color=0x8B62FF)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Only the ticket author can rate.", ephemeral=True)
          
    @discord.ui.button(label="4⭐", custom_id="rating_4", style=discord.ButtonStyle.primary)
    async def rate_4(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.author_id:
            self.rating = 4
            self.stop()
            embed = discord.Embed(title="", description="```Amazing! Would you like to leave a small comment regarding your experience and the results you’ve got?``` *Write a comment and send it as a message here*", color=0x8B62FF)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Only the ticket author can rate.", ephemeral=True)
          
    @discord.ui.button(label="5⭐", custom_id="rating_5", style=discord.ButtonStyle.primary)
    async def rate_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.author_id:
            self.rating = 5
            self.stop()
            embed = discord.Embed(title="", description="```Amazing! Would you like to leave a small comment regarding your experience and the results you’ve got?``` *Write a comment and send it as a message here*", color=0x8B62FF)
            await interaction.response.send_message(embed=embed)

        else:
            await interaction.response.send_message("Only the ticket author can rate.", ephemeral=True)
    
  

#View that creates a new ticket for a catalogue item purchase
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
    category = discord.utils.get(interaction.guild.categories, name="――――― 𝗠𝗬 𝗢𝗥𝗗𝗘𝗥𝗦 ――――")
    if not category:
      category = await interaction.guild.create_category(name="――――― 𝗠𝗬 𝗢𝗥𝗗𝗘𝗥𝗦 ――――")
    
    with open('catalogue_numbers.json', 'r') as f:
        numbers = json.load(f)
    number = None
    if numbers:
        last_number = numbers[-1]
        number = last_number + 1
    else:
        number = 1

    # Create a new ticket channel
    channel = await category.create_text_channel(name=f"📦-catalogue-{number}")
    numbers.append(number)
    with open('catalogue_numbers.json', 'w') as f:
        json.dump(numbers, f)
    # Set channel permissions to only allow access to users with the "Manage Channels" permission
    await channel.set_permissions(interaction.guild.default_role,
                                  reason="Private Ticket",
                                  view_channel=False)
    await channel.set_permissions(interaction.user,
                                  read_messages=True,
                                  send_messages=True,
                                  view_channel=True)
    await interaction.response.send_message(
      f"Ticket channel created in {channel.mention}", ephemeral=True)
    # Save the ticket data
    ticket_data = {
      'subject': self.subject,
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

#View containing a button that closes the ticket
class CloseTicketView(discord.ui.View):

  def __init__(self, bot, subject):
    super().__init__(timeout=None)
    self.bot = bot
    self.subject = subject

  @discord.ui.button(label="Close Ticket",
                     custom_id="close_ticket",
                     style=discord.ButtonStyle.danger)
  async def close(self, interaction: discord.Interaction,
                  button: discord.ui.Button):
    ticket_id = interaction.channel_id

    ticket_file = f'jsons/tickets/{ticket_id}.json'

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

      # Create review channel
    review_category = discord.utils.get(interaction.guild.categories,
                                        name="――――― 𝗠𝗬 𝗢𝗥𝗗𝗘𝗥𝗦 ――――")
    if not review_category:
      review_category = await interaction.guild.create_category(name="――――― 𝗠𝗬 𝗢𝗥𝗗𝗘𝗥𝗦 ――――")
    with open('review_numbers.json', 'r') as f:
        numbers = json.load(f)
    number = None
    if numbers:
        last_number = numbers[-1]
        number = last_number + 1
    else:
        number = 1

    # Create a new ticket channel
    review_channel = await review_category.create_text_channel(name=f"⭐-review-{number}")
    numbers.append(number)
    with open('review_numbers.json', 'w') as f:
        json.dump(numbers, f)
    await review_channel.set_permissions(interaction.guild.default_role,
                                         view_channel=False)
    await review_channel.set_permissions(
      await interaction.guild.fetch_member(ticket_creator), view_channel=True)

    creator = await interaction.guild.fetch_member(ticket_creator)

    def check(message):
      return message.channel == review_channel and message.author == creator

    reviewview = ReviewView(creator.id)
    await review_channel.send(f"<@{ticket_creator}>")
    reviewembed = discord.Embed(title="", description=f"```Thanks again for ordering and we highly appreciate your choice on choosing us! We invite you to share your experience and help us serve you better with your honest review. Your feedback fuels our growth!\nWould you like to leave a review?```", color=0x8B62FF)
    await review_channel.send(embed=reviewembed, view=reviewview)
    await reviewview.wait()

    if reviewview.response is None:
        await review_channel.delete()
        return
    if reviewview.response == False:
        await review_channel.delete()
        return
    if reviewview.response == True:

    
        # Create RatingView
        view = RatingView(creator.id)
        ratingembed = discord.Embed(title="", description="```That’s Awesome! Would you like to rate your overall experience with us on a scale of 1 to 5?```", color=0x8B62FF)
        # Send rating message with buttons
        rating_msg = await review_channel.send(embed=ratingembed, view=view)
    
        # Wait for the rating or timeout
        await view.wait()
    
        if view.rating is None:
            await rating_msg.edit(content="Time's up! Please try again.", view=None)
            await review_channel.delete()
            return
    
        rating = view.rating

                    
        comments = None
        while comments is None:
          try:
            message = await self.bot.wait_for("message", check=check, timeout=300)
            comments = message.content
          except asyncio.TimeoutError:
            await review_channel.send("Time's up! Please try again.")
            return
        stars = ""
        for i in range(rating):
          stars += ":star: "
        # Send review data to the specific channel
        review_channel_to_send = self.bot.get_channel(1104564795564372069)
        pfp = creator.avatar.url
        embed = discord.Embed(title=f"📦New Catalog Review⭐",
                              color=0x8B62FF)
        embed.add_field(name="👤 Client", value=f"<@{ticket_creator}>", inline=False)
        embed.add_field(name="💭 Comments", value=f"```{comments}```", inline=False)
        embed.add_field(name="Rating", value=stars, inline=False)
        embed.add_field(name="Product Ordered", value=f"{self.subject}".title())
        embed.set_thumbnail(url=pfp)
        await review_channel_to_send.send(embed=embed)
    
        # Delete the review channel
        await review_channel.delete()
    
async def setup(bot):
  await bot.add_cog(Ticket(bot))
