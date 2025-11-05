from discord.ext import commands
import discord
import json
import os
import asyncio
import config  # <-- Import config

class CustomService(commands.Cog):
    """Cog for handling custom service orders and reviews."""

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
                with open(filename, "w") as f:
                    json.dump(default_data, f)
                return default_data

    # --- Helper Function for Refactored Close Logic ---

    async def _handle_close_and_review(self, interaction_or_ctx, ticket_id, ticket_data):
        """
        Handles all logic for closing a custom service ticket and starting the review.
        """
        guild = interaction_or_ctx.guild
        channel = interaction_or_ctx.channel
        
        ticket_creator_id = ticket_data['author']
        
        # 1. Delete ticket file
        ticket_file = f'jsons/customservices/{ticket_id}.json'
        if os.path.exists(ticket_file):
            os.remove(ticket_file)

        # 2. Send closing message
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
        review_category = discord.utils.get(guild.categories, name=config.TICKET_CATEGORY_NAME)
        if not review_category:
            review_category = await guild.create_category(name=config.TICKET_CATEGORY_NAME)

        numbers = await self._load_or_create_json('review_numbers.json')
        number = numbers[-1] + 1 if numbers else 1
        numbers.append(number)
        with open('review_numbers.json', 'w') as f:
            json.dump(numbers, f)

        try:
            creator = await guild.fetch_member(ticket_creator_id)
        except discord.NotFound:
            return # User left the server, abort review

        review_channel = await review_category.create_text_channel(name=f"⭐-review-{number}")
        await review_channel.set_permissions(guild.default_role, view_channel=False)
        await review_channel.set_permissions(creator, view_channel=True)

        def check(message):
            return message.channel == review_channel and message.author == creator

        reviewview = ReviewView(creator.id)
        await review_channel.send(f"{creator.mention}")
        reviewembed = discord.Embed(
            title="",
            description="```Thanks again for ordering and we highly appreciate your choice on choosing us! We invite you to share your experience and help us serve you better with your honest review. Your feedback fuels our growth!\nWould you like to leave a review?```",
            color=0x8B62FF)
        await review_channel.send(embed=reviewembed, view=reviewview)
        await reviewview.wait()

        if reviewview.response is not True:
            await review_channel.delete()
            return

        # Create RatingView
        view = RatingView(creator.id)
        ratingembed = discord.Embed(
            title="",
            description="```That’s Awesome! Would you like to rate your overall experience with us on a scale of 1 to 5?```",
            color=0x8B62FF)
        rating_msg = await review_channel.send(embed=ratingembed, view=view)

        await view.wait()

        if view.rating is None:
            await rating_msg.edit(content="Time's up! Please try again.", view=None)
            await review_channel.delete()
            return

        rating = view.rating
        
        comments = None
        try:
            message = await self.bot.wait_for("message", check=check, timeout=2880)
            comments = message.content
        except asyncio.TimeoutError:
            await review_channel.send("Time's up! Please try again.")
            await review_channel.delete()
            return

        stars = ":star: " * rating
        
        # Send review data to the specific channel
        subject = ticket_data.get('subject', 'Unknown Service')
        review_channel_to_send = None
        emoji = "⭐"
        sub = "Service"

        if subject == "Custom Artist Service":
            review_channel_to_send = self.bot.get_channel(config.ARTIST_REVIEW_LOG_CHANNEL_ID)
            emoji = "🎨"
            sub = "Artist"
        elif subject == "Custom Builder Service":
            review_channel_to_send = self.bot.get_channel(config.BUILDER_REVIEW_LOG_CHANNEL_ID)
            emoji = "🧱"
            sub = "Builder"
        elif "Developer Service" in subject: # Catches both Java and Bedrock
            review_channel_to_send = self.bot.get_channel(config.DEV_REVIEW_LOG_CHANNEL_ID)
            emoji = "🤖"
            sub = "Developer"

        if review_channel_to_send:
            pfp = creator.avatar.url if creator.avatar else creator.default_avatar.url
            embed = discord.Embed(title=f"{emoji} New {sub} Review⭐", color=0x8B62FF)
            embed.add_field(name="👤 Client", value=f"{creator.mention}", inline=False)
            embed.add_field(name="💭 Comments", value=f"```{comments}```", inline=False)
            embed.add_field(name="Rating", value=stars, inline=False)
            embed.set_thumbnail(url=pfp)
            await review_channel_to_send.send(embed=embed)

        await review_channel.delete()


    # --- Cog Listener ---

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(CloseCustomServiceView(self.bot))
        self.bot.add_view(DevMenuView(self.bot))

        users = await self._load_or_create_json("custom_service.json")
        if users:
            for user in users:
                self.bot.add_view(CustomServiceView(self.bot, user))

    # --- Cog Commands ---

    @commands.hybrid_command(name="customservice", description="Posts the custom service message.")
    @commands.has_permissions(administrator=True)
    async def customservice(self, ctx):

        specific_channel = ctx.guild.get_channel(config.CUSTOM_SERVICE_POST_CHANNEL_ID)
        if not specific_channel:
            await ctx.send(f"Error: Channel ID {config.CUSTOM_SERVICE_POST_CHANNEL_ID} not found.", ephemeral=True)
            return

        await ctx.send(
            f"New custom service message sent to {specific_channel.mention}", ephemeral=True)

        await specific_channel.send(file=discord.File('Ordering-1.png'),
                                    view=CustomServiceView(self.bot, ctx.author.id))
        
        users = await self._load_or_create_json("custom_service.json")
        if ctx.author.id not in users:
            users.append(ctx.author.id)
            with open("custom_service.json", "w") as f:
                json.dump(users, f, indent=4)

    @commands.hybrid_command(name="closecustomservice", description="Close the custom service ticket you are currently in.")
    @commands.has_permissions(administrator=True)
    async def closecustomservice(self, ctx):
        ticket_id = ctx.channel.id
        ticket_file = f'jsons/customservices/{ticket_id}.json'
        
        if not os.path.exists(ticket_file):
            return await ctx.send(f'Ticket #{ticket_id} does not exist.', ephemeral=True)

        try:
            with open(ticket_file) as f:
                ticket_data = json.load(f)
        except (IOError, json.JSONDecodeError):
            return await ctx.send(f'Error reading ticket data.', ephemeral=True)

        # Admin-only command, but we'll also allow the ticket author to be safe
        if ctx.author.id != ticket_data.get('author') and not ctx.author.guild_permissions.administrator:
            return await ctx.send(
                'Only the author of the ticket or an administrator can close it.', ephemeral=True)
        
        # Call the refactored function
        await self._handle_close_and_review(ctx, ticket_id, ticket_data)

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
            await interaction.response.send_message("⠀", ephemeral=True) # Send silent ack
        else:
            await interaction.response.send_message(
                "Only the ticket author can rate.", ephemeral=True)

    @discord.ui.button(label="No", custom_id="NO", style=discord.ButtonStyle.primary)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.author_id:
            self.response = False
            self.stop()
            await interaction.response.send_message(
                "Alright, the review channel will now close.")
        else:
            await interaction.response.send_message(
                "Only the ticket author can rate.", ephemeral=True)

class RatingView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=2880)
        self.author_id = author_id
        self.rating = None

    async def send_rating_response(self, interaction: discord.Interaction, rating: int):
        if interaction.user.id == self.author_id:
            self.rating = rating
            self.stop()
            embed = discord.Embed(
                title="",
                description="```Amazing! Would you like to leave a small comment regarding your experience and the results you’ve got?``` *Write a comment and send it as a message here*",
                color=0x8B62FF)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                "Only the ticket author can rate.", ephemeral=True)

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

class CustomServiceView(discord.ui.View):
    def __init__(self, bot, author):
        super().__init__(timeout=None)
        self.bot = bot
        self.subject = ""
        self.seller = author

    async def create_ticket_channel(self, interaction: discord.Interaction, service_name: str, number_file: str, role_id: int):
        self.subject = service_name
        
        category = discord.utils.get(interaction.guild.categories, name=config.TICKET_CATEGORY_NAME)
        if not category:
            category = await interaction.guild.create_category(name=config.TICKET_CATEGORY_NAME)

        # Use safe JSON loader
        service_cog = self.bot.get_cog("CustomService")
        numbers = await service_cog._load_or_create_json(number_file)
        number = numbers[-1] + 1 if numbers else 1
        numbers.append(number)
        
        with open(number_file, 'w') as f:
            json.dump(numbers, f)

        # Determine emoji for channel name
        emoji = "❓"
        if "Builder" in service_name: emoji = "🧱"
        if "Artist" in service_name: emoji = "🎨"
        if "Developer" in service_name: emoji = "🤖"

        channel = await category.create_text_channel(
            name=f"{emoji}-{service_name.split(' ')[1].lower()}-{number}")

        # Permissions
        staff_role = interaction.guild.get_role(role_id)
        await channel.set_permissions(interaction.guild.default_role, reason="Private Ticket", view_channel=False)
        await channel.set_permissions(interaction.user, read_messages=True, send_messages=True, view_channel=True)
        if staff_role:
            await channel.set_permissions(staff_role, read_messages=True, send_messages=True, view_channel=True)
        
        await interaction.response.send_message(
            f"Ticket channel created in {channel.mention}", ephemeral=True)
        
        # Ensure directory exists
        os.makedirs('jsons/customservices', exist_ok=True)
        
        ticket_data = {
            'subject': self.subject,
            'status': 'Open',
            'author': interaction.user.id,
            'channelid': channel.id,
            'chatlogs': 'Ticket Opened',
            'seller': self.seller
        }
        with open(f'jsons/customservices/{channel.id}.json', 'w') as f:
            json.dump(ticket_data, f, indent=4)
            
        embed = discord.Embed(
            title=f"{emoji} **{self.subject}**",
            description="The Staff will be with you shortly. :clock2:\n Please don't close the ticket or all the information for your order will be lost!\n\n```Meanwhile, we suggest for you to leave a detailed description of the product you're thinking on ordering.```",
            color=0x8B62FF)
        embed.add_field(name="👤 Creator", value=f"<@{interaction.user.id}>", inline=False)
        await channel.send(embed=embed, view=CloseCustomServiceView(self.bot))


    @discord.ui.button(label="🧱 Build Service", custom_id="GET1", style=discord.ButtonStyle.primary)
    async def button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket_channel(interaction, "Custom Builder Service", 'builder_numbers.json', config.BUILDER_ROLE_ID)

    @discord.ui.button(label="🎨 Artist Service", custom_id="GET2", style=discord.ButtonStyle.primary)
    async def button1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket_channel(interaction, "Custom Artist Service", 'art_numbers.json', config.ARTIST_ROLE_ID)

    @discord.ui.button(label="🤖 DEV Service", custom_id="GET3", style=discord.ButtonStyle.primary)
    async def button2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(view=DevMenuView(self.bot), ephemeral=True)


class DevMenuView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.select(placeholder="What type of service are you looking for?",
                       options=[
                           discord.SelectOption(label="Java", value="1"),
                           discord.SelectOption(label="Bedrock", value="2")
                       ],
                       custom_id="DEVSELECT")
    async def service_type(self, interaction: discord.Interaction,
                           select_item: discord.ui.Select):
        
        service_cog = self.bot.get_cog("CustomService")
        service_subject = ""
        
        if select_item.values[0] == "1":
            service_subject = "Custom Developer Service | Java"
        elif select_item.values[0] == "2":
            service_subject = "Custom Developer Service | Bedrock"
        else:
            return # Should not happen

        # Find the CustomServiceView that triggered this
        # This is a bit complex, but we need the 'seller' info
        # A simpler way is to just omit seller for dev tickets if not needed
        # For now, let's just pass `author=None`
        
        # Re-using the create_ticket_channel logic from CustomServiceView
        # We need an instance of it, but we don't have one.
        # This suggests the create_ticket_channel logic should be on the COG, not the VIEW
        # ... but let's do a quick fix:
        
        temp_view = CustomServiceView(self.bot, author=None) # Author/Seller will be None
        await temp_view.create_ticket_channel(interaction, service_subject, 'dev_numbers.json', config.DEV_ROLE_ID)
        
        # We need to edit the original ephemeral message
        await interaction.edit_original_response(content="Ticket created!", view=None)


class CloseCustomServiceView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.subject = "None"

    @discord.ui.button(label="Close Ticket",
                       custom_id="close_service",
                       style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction,
                    button: discord.ui.Button):
        ticket_id = interaction.channel_id
        ticket_file = f'jsons/customservices/{ticket_id}.json'

        if not os.path.exists(ticket_file):
            return await interaction.response.send_message(f'Ticket #{ticket_id} does not exist.', ephemeral=True)
            
        try:
            with open(ticket_file) as f:
                ticket_data = json.load(f)
        except (IOError, json.JSONDecodeError):
            return await interaction.response.send_message(f'Error reading ticket data.', ephemeral=True)

        # This button is Admin-only close
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                'Only an administrator can close this ticket.', ephemeral=True)
        
        await interaction.response.send_message(
            f'This ticket has been closed by {interaction.user.mention}.')

        await self.bot.get_cog("CustomService")._handle_close_and_review(interaction, ticket_id, ticket_data)

async def setup(bot):
    await bot.add_cog(CustomService(bot))