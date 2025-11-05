from discord.ext import commands
import discord
import json
import os
import asyncio


class CustomService(commands.Cog):
    """The description for Tickets goes here."""

    def __init__(self, bot):
        self.bot = bot

    #Load Views On Ready to allow previously made ones to stay active while keeping newly made ones active aswell
    @commands.Cog.listener()
    async def on_ready(self):

        self.bot.add_view(CloseCustomServiceView(self.bot))

        self.bot.add_view(DevMenuView(self.bot))

        with open("custom_service.json", "r") as f:
            users = json.load(f)
        if users:
            for user in users:
                self.bot.add_view(CustomServiceView(self.bot, user))

    #Allows administrators to create a product
    @commands.hybrid_command(name="customservice")
    @commands.has_permissions(administrator=True)
    async def customservice(self, ctx):

        specific_channel = ctx.guild.get_channel(1093577086066765864)
        await ctx.send(
            f"New custom service message sent to {specific_channel.mention}")

        await specific_channel.send(file=discord.File('Ordering-1.png'),
                                    view=CustomServiceView(
                                        self.bot, ctx.author.id))
        with open("custom_service.json", "r") as f:
            users = json.load(f)
        users.append(ctx.author.id)
        with open("custom_service.json", "w") as f:
            json.dump(users, f)

    #Allows administrators to close a product ticket made by a client
    @commands.hybrid_command(name="closecustomservice", description="Close the custom service ticket you are currently in.")
    @commands.has_permissions(administrator=True)
    async def closecustomservice(self, ctx):
        # Get the channel_id
        ticket_id = ctx.channel.id

        # Check if the ticket exists
        ticket_file = f'jsons/customservices/{ticket_id}.json'
        if not os.path.exists(ticket_file):
            return await ctx.send(f'Ticket #{ticket_id} does not exist.')

        # Load the ticket data
        with open(ticket_file) as f:
            ticket_data = json.load(f)

        # Check if the author or an admin is trying to close the ticket
        if ctx.author.id != ticket_data[
                'author'] and not ctx.author.guild_permissions.administrator:
            return await ctx.send(
                'Only the author of the ticket or an administrator can close it.'
            )
        ticket_creator = ticket_data['author']
        # Delete the ticket file
        os.remove(ticket_file)
        await ctx.send(f'This ticket has been closed by <@{ctx.author.id}>.')
        await asyncio.sleep(3)

        # Delete the ticket channel
        ticket_channel = ctx.guild.get_channel(ticket_id)
        if ticket_channel:
            await ticket_channel.delete()
        # Create review channel
        review_category = discord.utils.get(ctx.guild.categories,
                                            name="――――― 𝗠𝗬 𝗢𝗥𝗗𝗘𝗥𝗦 ――――")
        if not review_category:
            review_category = await ctx.guild.create_category(
                name="――――― 𝗠𝗬 𝗢𝗥𝗗𝗘𝗥𝗦 ――――")

        with open('review_numbers.json', 'r') as f:
            numbers = json.load(f)
        number = None
        if numbers:
            last_number = numbers[-1]
            number = last_number + 1
        else:
            number = 1

        # Create a new ticket channel
        review_channel = await review_category.create_text_channel(
            name=f"⭐-review-{number}")
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
        await review_channel.send(f"{creator.mention}")
        reviewembed = discord.Embed(
            title="",
            description=
            "```Thanks again for ordering and we highly appreciate your choice on choosing us! We invite you to share your experience and help us serve you better with your honest review. Your feedback fuels our growth!\nWould you like to leave a review?```",
            color=0x8B62FF)
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
            ratingembed = discord.Embed(
                title="",
                description=
                "```That’s Awesome! Would you like to rate your overall experience with us on a scale of 1 to 5?```",
                color=0x8B62FF)
            # Send rating message with buttons
            rating_msg = await review_channel.send(embed=ratingembed,
                                                   view=view)

            # Wait for the rating or timeout
            await view.wait()

            if view.rating is None:
                await rating_msg.edit(content="Time's up! Please try again.",
                                      view=None)
                await review_channel.delete()
                return

            rating = view.rating

            comments = None
            while comments is None:
                try:
                    message = await self.bot.wait_for("message",
                                                      check=check,
                                                      timeout=2880)
                    comments = message.content
                except asyncio.TimeoutError:
                    await review_channel.send("Time's up! Please try again.")
                    return
            stars = ""
            for i in range(rating):
                stars += ":star: "
            # Send review data to the specific channel
            if ticket_data['subject'] == "Custom Artist Service":
                review_channel_to_send = self.bot.get_channel(
                    1093577146607337533)
                emoji = "🎨"
                sub = "Artist"
            if ticket_data['subject'] == "Custom Builder Service":
                review_channel_to_send = self.bot.get_channel(
                    1093569044688404612)
                emoji = "🧱"
                sub = "Builder"
            if ticket_data['subject'] == "Custom Developer Service":
                review_channel_to_send = self.bot.get_channel(
                    1093572910754566204)
                emoji = "🤖"
                sub = "Developer"
            pfp = creator.avatar.url
            embed = discord.Embed(title=f"{emoji} New {sub} Review⭐",
                                  color=0x8B62FF)
            embed.add_field(name="👤 Client",
                            value=f"{creator.mention}",
                            inline=False)
            embed.add_field(name="💭 Comments",
                            value=f"```{comments}```",
                            inline=False)
            embed.add_field(name="Rating", value=stars, inline=False)
            embed.set_thumbnail(url=pfp)
            await review_channel_to_send.send(embed=embed)

            # Delete the review channel
            await review_channel.delete()

#Class to create a review button option for users to either opt to leave a review or opt to not
class ReviewView(discord.ui.View):

    def __init__(self, author_id):
        super().__init__(timeout=2880)
        self.author_id = author_id
        self.response = None

    @discord.ui.button(label="Yes",
                       custom_id="YES",
                       style=discord.ButtonStyle.primary)
    async def yes(self, interaction: discord.Interaction,
                  button: discord.ui.Button):
        if interaction.user.id == self.author_id:
            self.response = True
            self.stop()
            await interaction.response.send_message("⠀")
        else:
            await interaction.response.send_message(
                "Only the ticket author can rate.", ephemeral=True)

    @discord.ui.button(label="No",
                       custom_id="NO",
                       style=discord.ButtonStyle.primary)
    async def no(self, interaction: discord.Interaction,
                 button: discord.ui.Button):
        if interaction.user.id == self.author_id:
            self.response = False
            self.stop()
            await interaction.response.send_message(
                "Alright, the review channel will now close.")

#Class to create rating buttons for users to rate their experience/product
class RatingView(discord.ui.View):

    def __init__(self, author_id):
        super().__init__(timeout=2880)
        self.author_id = author_id
        self.rating = None

    @discord.ui.button(label="1⭐",
                       custom_id="rating_1",
                       style=discord.ButtonStyle.primary)
    async def rate_1(self, interaction: discord.Interaction,
                     button: discord.ui.Button):
        if interaction.user.id == self.author_id:
            self.rating = 1
            self.stop()
            embed = discord.Embed(
                title="",
                description=
                "```Amazing! Would you like to leave a small comment regarding your experience and the results you’ve got?``` *Write a comment and send it as a message here*",
                color=0x8B62FF)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                "Only the ticket author can rate.", ephemeral=True)

    @discord.ui.button(label="2⭐",
                       custom_id="rating_2",
                       style=discord.ButtonStyle.primary)
    async def rate_2(self, interaction: discord.Interaction,
                     button: discord.ui.Button):
        if interaction.user.id == self.author_id:
            self.rating = 2
            self.stop()
            embed = discord.Embed(
                title="",
                description=
                "```Amazing! Would you like to leave a small comment regarding your experience and the results you’ve got?``` *Write a comment and send it as a message here*",
                color=0x8B62FF)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                "Only the ticket author can rate.", ephemeral=True)

    @discord.ui.button(label="3⭐",
                       custom_id="rating_3",
                       style=discord.ButtonStyle.primary)
    async def rate_3(self, interaction: discord.Interaction,
                     button: discord.ui.Button):
        if interaction.user.id == self.author_id:
            self.rating = 3
            self.stop()
            embed = discord.Embed(
                title="",
                description=
                "```Amazing! Would you like to leave a small comment regarding your experience and the results you’ve got?``` *Write a comment and send it as a message here*",
                color=0x8B62FF)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                "Only the ticket author can rate.", ephemeral=True)

    @discord.ui.button(label="4⭐",
                       custom_id="rating_4",
                       style=discord.ButtonStyle.primary)
    async def rate_4(self, interaction: discord.Interaction,
                     button: discord.ui.Button):
        if interaction.user.id == self.author_id:
            self.rating = 4
            self.stop()
            embed = discord.Embed(
                title="",
                description=
                "```Amazing! Would you like to leave a small comment regarding your experience and the results you’ve got?``` *Write a comment and send it as a message here*",
                color=0x8B62FF)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                "Only the ticket author can rate.", ephemeral=True)

    @discord.ui.button(label="5⭐",
                       custom_id="rating_5",
                       style=discord.ButtonStyle.primary)
    async def rate_5(self, interaction: discord.Interaction,
                     button: discord.ui.Button):
        if interaction.user.id == self.author_id:
            self.rating = 5
            self.stop()
            embed = discord.Embed(
                title="",
                description=
                "```Amazing! Would you like to leave a small comment regarding your experience and the results you’ve got?``` *Write a comment and send it as a message here*",
                color=0x8B62FF)
            await interaction.response.send_message(embed=embed)

        else:
            await interaction.response.send_message(
                "Only the ticket author can rate.", ephemeral=True)

#Custom service buttons that open a ticket for a specific category
class CustomServiceView(discord.ui.View):

    def __init__(self, bot, author):
        super().__init__(timeout=None)
        self.bot = bot
        self.subject = ""
        self.seller = author

    @discord.ui.button(label="🧱 Build Service",
                       custom_id="GET1",
                       style=discord.ButtonStyle.primary)
    async def button(self, interaction: discord.Interaction,
                     button: discord.ui.Button):
        self.subject = "Custom Builder Service"
        category = discord.utils.get(interaction.guild.categories,
                                     name="――――― 𝗠𝗬 𝗢𝗥𝗗𝗘𝗥𝗦 ――――")
        if not category:
            category = await interaction.guild.create_category(
                name="――――― 𝗠𝗬 𝗢𝗥𝗗𝗘𝗥𝗦 ――――")

        with open('builder_numbers.json', 'r') as f:
            numbers = json.load(f)
        number = None
        if numbers:
            last_number = numbers[-1]
            number = last_number + 1
        else:
            number = 1

        # Create a new ticket channel
        channel = await category.create_text_channel(
            name=f"🧱-builder-service-{number}")
        numbers.append(number)
        with open('builder_numbers.json', 'w') as f:
            json.dump(numbers, f)

        # Set channel permissions to only allow access to users with the "Manage Channels" permission
        await channel.set_permissions(interaction.guild.default_role,
                                      reason="Private Ticket",
                                      view_channel=False)
        await channel.set_permissions(interaction.user,
                                      read_messages=True,
                                      send_messages=True,
                                      view_channel=True)
        await channel.set_permissions(
            interaction.guild.get_role(993451622946570322),
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
            'chatlogs': 'Ticket Opened',
            'seller': self.seller
        }
        with open(f'jsons/customservices/{channel.id}.json', 'w') as f:
            json.dump(ticket_data, f)
        embed = discord.Embed(
            title=f"🧱 **{self.subject}**",
            description=
            "The Staff will be with you shortly. :clock2:\n Please don't close the ticket or all the information for your order will be lost!\n\n```Meanwhile, we suggest for you to leave a detailed description of the product you're thinking on ordering.```",
            color=0x8B62FF)
        embed.add_field(name="👤 Creator",
                        value=f"<@{interaction.user.id}>",
                        inline=False)
        await channel.send(embed=embed, view=CloseCustomServiceView(self.bot))

    @discord.ui.button(label="🎨 Artist Service",
                       custom_id="GET2",
                       style=discord.ButtonStyle.primary)
    async def button1(self, interaction: discord.Interaction,
                      button: discord.ui.Button):
        self.subject = "Custom Artist Service"
        category = discord.utils.get(interaction.guild.categories,
                                     name="――――― 𝗠𝗬 𝗢𝗥𝗗𝗘𝗥𝗦 ――――")
        if not category:
            category = await interaction.guild.create_category(
                name="――――― 𝗠𝗬 𝗢𝗥𝗗𝗘𝗥𝗦 ――――")

        with open('art_numbers.json', 'r') as f:
            numbers = json.load(f)
        number = None
        if numbers:
            last_number = numbers[-1]
            number = last_number + 1
        else:
            number = 1

        # Create a new ticket channel
        channel = await category.create_text_channel(
            name=f"🎨-art-service-{number}")
        numbers.append(number)
        with open('art_numbers.json', 'w') as f:
            json.dump(numbers, f)

        # Set channel permissions to only allow access to users with the "Manage Channels" permission
        await channel.set_permissions(interaction.guild.default_role,
                                      reason="Private Ticket",
                                      view_channel=False)
        await channel.set_permissions(interaction.user,
                                      read_messages=True,
                                      send_messages=True,
                                      view_channel=True)
        await channel.set_permissions(
            interaction.guild.get_role(1084062670812106762),
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
            'chatlogs': 'Ticket Opened',
            'seller': self.seller
        }
        with open(f'jsons/customservices/{channel.id}.json', 'w') as f:
            json.dump(ticket_data, f)
        embed = discord.Embed(
            title=f"🎨 **{self.subject}**",
            description=
            "The Staff will be with you shortly. :clock2:\n Please don't close the ticket or all the information for your order will be lost!\n\n```Meanwhile, we suggest for you to leave a detailed description of the product you're thinking on ordering.```",
            color=0x8B62FF)
        embed.add_field(name="👤 Creator",
                        value=f"<@{interaction.user.id}>",
                        inline=False)
        await channel.send(embed=embed, view=CloseCustomServiceView(self.bot))

    @discord.ui.button(label="🤖 DEV Service",
                       custom_id="GET3",
                       style=discord.ButtonStyle.primary)
    async def button2(self, interaction: discord.Interaction,
                      button: discord.ui.Button):
        await interaction.response.send_message(view=DevMenuView(self.bot),
                                                ephemeral=True)

#A dropdown to select a specific type of service
class DevMenuView(discord.ui.View):

    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.subject = ""
        self.selectitem = None

    @discord.ui.select(placeholder="What type of service are you looking for?",
                       options=[
                           discord.SelectOption(label="Java", value="1"),
                           discord.SelectOption(label="Bedrock", value="2")
                       ],
                       custom_id="DEVSELECT")
    async def service_type(self, interaction: discord.Interaction,
                           select_item: discord.ui.Select):
        self.selectitem = select_item.values[0]
        if int(self.selectitem) == 1:
            self.subject = "Custom Developer Service | Java"
        if int(self.selectitem) == 2:
            self.subject = "Custom Developer Service | Bedrock"

        category = discord.utils.get(interaction.guild.categories,
                                     name="――――― 𝗠𝗬 𝗢𝗥𝗗𝗘𝗥𝗦 ――――")
        if not category:
            category = await interaction.guild.create_category(
                name="――――― 𝗠𝗬 𝗢𝗥𝗗𝗘𝗥𝗦 ――――")

        with open('dev_numbers.json', 'r') as f:
            numbers = json.load(f)
        number = None
        if numbers:
            last_number = numbers[-1]
            number = last_number + 1
        else:
            number = 1

        # Create a new ticket channel
        channel = await category.create_text_channel(
            name=f"🤖-dev-service-{number}")
        numbers.append(number)
        with open('dev_numbers.json', 'w') as f:
            json.dump(numbers, f)

        # Set channel permissions to only allow access to users with the "Manage Channels" permission
        await channel.set_permissions(interaction.guild.default_role,
                                      reason="Private Ticket",
                                      view_channel=False)
        await channel.set_permissions(interaction.user,
                                      read_messages=True,
                                      send_messages=True,
                                      view_channel=True)
        await channel.set_permissions(
            interaction.guild.get_role(1085304441156149341),
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
            'chatlogs': 'Ticket Opened',
        }
        with open(f'jsons/customservices/{channel.id}.json', 'w') as f:
            json.dump(ticket_data, f)
        embed = discord.Embed(
            title=f"🤖 **{self.subject}**",
            description=
            "The Staff will be with you shortly. :clock2:\n Please don't close the ticket or all the information for your order will be lost!\n\n```Meanwhile, we suggest for you to leave a detailed description of the product you're thinking on ordering.```",
            color=0x8B62FF)
        embed.add_field(name="👤 Creator",
                        value=f"<@{interaction.user.id}>",
                        inline=False)
        await channel.send(embed=embed, view=CloseCustomServiceView(self.bot))

#Close custom service button
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

        # Load the ticket data
        with open(ticket_file) as f:
            ticket_data = json.load(f)
        self.subject = ticket_data['subject']
        # Check if the author or an admin is trying to close the ticket
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                'Only an administrator can close the ticket.')
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
            review_category = await interaction.guild.create_category(
                name="――――― 𝗠𝗬 𝗢𝗥𝗗𝗘𝗥𝗦 ――――")

        with open('review_numbers.json', 'r') as f:
            numbers = json.load(f)
        number = None
        if numbers:
            last_number = numbers[-1]
            number = last_number + 1
        else:
            number = 1

        # Create a new ticket channel
        review_channel = await review_category.create_text_channel(
            name=f"⭐-review-{number}")
        numbers.append(number)
        with open('review_numbers.json', 'w') as f:
            json.dump(numbers, f)
        await review_channel.set_permissions(interaction.guild.default_role,
                                             view_channel=False)
        await review_channel.set_permissions(
            await interaction.guild.fetch_member(ticket_creator),
            view_channel=True)

        creator = await interaction.guild.fetch_member(ticket_creator)

        def check(message):
            return message.channel == review_channel and message.author == creator

        reviewview = ReviewView(creator.id)
        await review_channel.send(f"{creator.mention}")
        reviewembed = discord.Embed(
            title="",
            description=
            "```Thanks again for ordering and we highly appreciate your choice on choosing us! We invite you to share your experience and help us serve you better with your honest review. Your feedback fuels our growth!\nWould you like to leave a review?```",
            color=0x8B62FF)
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
            ratingembed = discord.Embed(
                title="",
                description=
                "```That’s Awesome! Would you like to rate your overall experience with us on a scale of 1 to 5?```",
                color=0x8B62FF)
            # Send rating message with buttons
            rating_msg = await review_channel.send(embed=ratingembed,
                                                   view=view)

            # Wait for the rating or timeout
            await view.wait()

            if view.rating is None:
                await rating_msg.edit(content="Time's up! Please try again.",
                                      view=None)
                await review_channel.delete()
                return

            rating = view.rating

            comments = None
            while comments is None:
                try:
                    message = await self.bot.wait_for("message",
                                                      check=check,
                                                      timeout=2880)
                    comments = message.content
                except asyncio.TimeoutError:
                    await review_channel.send("Time's up! Please try again.")
                    return
            stars = ""
            for i in range(rating):
                stars += ":star: "
            # Send review data to the specific channel
            if ticket_data['subject'] == "Custom Artist Service":
                review_channel_to_send = self.bot.get_channel(
                    1093577146607337533)
                emoji = "🎨"
                sub = "Artist"
            if ticket_data['subject'] == "Custom Builder Service":
                review_channel_to_send = self.bot.get_channel(
                    1093569044688404612)
                emoji = "🧱"
                sub = "Builder"
            if ticket_data['subject'] == "Custom Developer Service | Java" or ticket_data['subject'] == "Custom Developer Service | Bedrock":
                review_channel_to_send = self.bot.get_channel(
                    1093572910754566204)
                emoji = "🤖"
                sub = "Developer"
            pfp = creator.avatar.url
            embed = discord.Embed(title=f"{emoji} New {sub} Review⭐",
                                  color=0x8B62FF)
            embed.add_field(name="👤 Client",
                            value=f"{creator.mention}",
                            inline=False)
            embed.add_field(name="💭 Comments",
                            value=f"```{comments}```",
                            inline=False)
            embed.add_field(name="Rating", value=stars, inline=False)
            embed.set_thumbnail(url=pfp)
            await review_channel_to_send.send(embed=embed)

            # Delete the review channel
            await review_channel.delete()

async def setup(bot):
    await bot.add_cog(CustomService(bot))
