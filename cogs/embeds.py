from discord.ext import commands
import discord



class Embeds(commands.Cog):
  """The description for Tickets goes here."""

  def __init__(self, bot):
    self.bot = bot

  #Rules Message
  @commands.hybrid_command(name="rules")
  @commands.has_permissions(administrator=True)
  async def rules(self, ctx, channel: discord.TextChannel):
      embed = discord.Embed(title="👮Discord Rules | Safasr Studios", description="\n1️⃣ **No spamming or scamming**: Repeating messages is like repeating history – it gets old fast. Please don't use excessive caps, emojis, or post too often. Also, any attempts to scam or beg for goods will not be tolerated and will result in immediate consequences. \n\n2️⃣ **No offensive language**: Our community is diverse, and we welcome everyone with open arms. Let's keep it that way and avoid using language that can hurt, harm, or offend others.\n\n3️⃣ **Respect others**: We all share a love for Minecraft. Please treat each other with kindness and respect, regardless of beliefs, backgrounds, or building styles. No bullying, no trolling, and no drama.\n\n4️⃣ **No NSFW content**: Minecraft can get wild, but let's keep our server PG. Please don't post anything inappropriate, lewd, or suggestive.\n\n5️⃣ **No doxing or sharing personal information**: Let's keep it real, but not too real. Sharing someone else's personal information is a big no-no. Let's protect each other's privacy and stay safe.\n\n6️⃣ **No advertising**: We love Minecraft and our community, but we don't want to turn into a commercial. Please don't promote other servers or websites without permission.\n\n7️⃣ **No impersonation**: It's like playing dress-up, but online. Impersonating other users, staff members, or any other individuals is not cool. However, if you want to be a jokester, keep it light and harmless. \n\n8️⃣ **Follow the rules**: The rules are like rails – they keep us on track. Please follow them and be cool. If you have any issues, our mods are always here to help. \n\n9️⃣ **Don't make us call the Discord police**: We love hanging out with you guys, but we have to follow the rules too. So, please don't make us bring out the Discord handcuffs by violating their Community Guidelines. We don't want to be buzzkills, but we also want to keep things cool and legal.", color=0x8B62FF)
      embed.set_image(url="https://cdn.discordapp.com/attachments/1092915397604421785/1104493066666127480/Line_Embed.png")
      await channel.send(embed = embed)
      await ctx.send(f"Message sent to {channel}!", ephemeral=True)

  #Terms of Service Message
  @commands.hybrid_command(name="tos")
  @commands.has_permissions(administrator=True)
  async def tos(self, ctx, channel: discord.TextChannel):
      embed = discord.Embed(title="✅ Terms Of Service | Safasr Studios", description = "\n**A. INTRODUCTION TO TOS** The \"Safasr Terms of Service\", possibly reffered as \"Safasr TOS\" are the terms and conditions listed below to ensure a secure trading between Safasr Studios and all the Clients. These TOS must be agreed on if ordering any of our services. It is our responsability to get you known to these TOS before ordering any of our comissions using Discord. If you do not agree on any of the terms, you may not have access to ask for services. The TOS apply on the entire time while using services from Safasr Studios.", color=0x8B62FF)

      embed1 = discord.Embed(description = "\n\n**B. SERVICES** The services of Safasr Studios are available only on our discord server and provided by the discord bot \"Safasr Services\". While ordering or interacting on our server, you commit to behave politely and remove any toxic behaviour that may result in a mental harm for other users. Safasr Studios staff have the rights to reject any commission for any reason.", color=0x8B62FF)

      embed2 = discord.Embed(title="", description = "\n\n**C. COMMISSION PROCESS** After opening a ticket, you will write a detailed description of the project that you’re looking for. First the conversation will be made between you and one of the Managers before he establish a contact with one of our specialists. After a series of questions/answers, you will be invited for a front payment. If you are a rank client, you must pay 25% of the total amount in advance, and the remaining amount after both parties agree on the final look of the build. If you are a client+ or higher, the payment will be made only at the end after confirming the end look. If during the work of the comission, the client request any modifications that weren’t mentioned in the questions/answers phase, we reserve the right to charge additional fee based on the changes asked. The additional fee will be announced to the client also. If over a certain period of time, the client won’t respond to our messages, the ticket will be closed. ", color=0x8B62FF)

      embed3 = discord.Embed(title="", description = '''\n\n**D. PAYMENT** Currently, our only payment method remains PayPal. The transactions will be made in a form of invoice sent only by ByGstEiseN#7665

 

All prices are unique and will vary depending on the project complexity.

Depending on what the price of the build can change:

-The presence of the interior or absence of it

-The amount of details

-Time of the delivery(deadline)

-General complexity

-Presence of terraforming or it's absence

-Integration of the build

''', color=0x8B62FF)

      embed4 = discord.Embed(title="", description = "\n\n**E. SHIPPING** The delivery of our services are taking place in an online environment, so you won't be asked to fill in any address. Constant updates on the order progression will be provided after the upfront payment for the rank Client, and after the questions/answers series for rank Client+ or higher.", color=0x8B62FF)

      embed5 = discord.Embed(title="", description = '''\n\n**F. CLIENT RANK PROGRESSION**

Client -> 1 to 3 orders Reward - 7% discount for your Third Order.

Client+ -> 4 to 8 orders Reward - 10% discount for your Eighth Order.

Client++ -> 9+ orders Reward - 15% discount for your 10th Order.

Safasr Studios and its Staff members are allowed to grant whatever rank for a client according to the trust that we built in our customers. Periodically (or after a long Client inactivity), Safasr Studios is allowed to lower the rank of the Client.

Seasonal discounts can be also made for clients with specific rank only''', color=0x8B62FF)

      embed6 = discord.Embed(title="", description='''**G. REFUND POLICY & CANCELLATION** If at the end the qualities of the services didn’t meet your expectations, you will be granted with a 100% refund (PayPal fees are non-refundable).

If the delay will be caused by you, a third party, or something beyond our control and restricts us from ending the order, you are not entitled to a refund. We reserve the right to suspend or cancel any commission in the event of a breach of our TOS or any other laws. In this case, you will be fully refunded and the service will belong to Safasr Studios.''')

      embed7 = discord.Embed(title="", description="**H. DISTRIBUTION & RESELLING** The use of our products in premade setups or commercial purposes (making money from the sale of or product), will be considered as distribution or reselling of our service. If you’d like to order a service with commercial rights fully transfered to you, an additional 25usd will be added to initial price of the commission.")
    
      embed7.set_image(url="https://cdn.discordapp.com/attachments/1092915397604421785/1104493066666127480/Line_Embed.png")
      await channel.send(embed = embed)
      await channel.send(embed = embed1)
      await channel.send(embed = embed2)
      await channel.send(embed = embed3)
      await channel.send(embed = embed4)
      await channel.send(embed = embed5)
      await channel.send(embed = embed6)
      await channel.send(embed = embed7)

      await ctx.send(f"Message sent to {channel}!", ephemeral=True)

async def setup(bot):
  await bot.add_cog(Embeds(bot))
    