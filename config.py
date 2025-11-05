# List of cogs to load at startup
cogs = [
    'cogs.ticket',
    'cogs.support',
    'cogs.customservice',
    'cogs.embeds',
    'cogs.verification'
]

# Bot command prefix
PREFIX = "!"

# --- Server Specific Channel IDs ---
# These IDs are moved from the cogs to make the bot more configurable.

# Channel ID where new catalogue items are posted (from cogs/ticket.py)
CATALOGUE_CHANNEL_ID = 1104564513581305928

# Channel ID where completed reviews are logged (from cogs/ticket.py)
REVIEW_LOG_CHANNEL_ID = 1104564795564372069

# Role ID to be given upon verification (from cogs/verification.py)
VERIFICATION_ROLE_ID = 993458372202475590

# --- Custom Service Cog IDs (from cogs/customservice.py) ---

# Channel where the main "Order a Custom Service" message is posted
CUSTOM_SERVICE_POST_CHANNEL_ID = 1093577086066765864

# Channel for "Artist" service reviews
ARTIST_REVIEW_LOG_CHANNEL_ID = 1093577146607337533
# Channel for "Builder" service reviews
BUILDER_REVIEW_LOG_CHANNEL_ID = 1093569044688404612
# Channel for "Developer" service reviews
DEV_REVIEW_LOG_CHANNEL_ID = 1093572910754566204

# Role ID for "Builder" staff
BUILDER_ROLE_ID = 993451622946570322
# Role ID for "Artist" staff
ARTIST_ROLE_ID = 1084062670812106762
# Role ID for "Developer" staff
DEV_ROLE_ID = 1085304441156149341

# Category name for all tickets (from cogs/support.py and others)
TICKET_CATEGORY_NAME = "――――― 𝗠𝗬 𝗢𝗥𝗗𝗘𝗥𝗦 ――――"