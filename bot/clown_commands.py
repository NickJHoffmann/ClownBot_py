import discord
from discord.ext import commands
import helper_functions
import global_
import re


class ClownInfo(commands.Cog):
    """
    Commands pertaining to clowns
    """

    def __init__(self, bot):
        self.bot = bot

    # https://discordpy.readthedocs.io/en/latest/api.html#discord.RawReactionActionEvent
    # https://discordpy.readthedocs.io/en/latest/api.html#discord.on_reaction_add
    # https://discordpy.readthedocs.io/en/latest/api.html#discord.abc.Messageable
    # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context.fetch_message
    # method to watch reactions
    # payload has properties:
    # channel_id: The channel ID where the reaction got added or removed.
    # emoji: The custom or unicode emoji being used.
    # event_type: The event type that triggered this action. Can be REACTION_ADD for reaction addition or REACTION_REMOVE for reaction removal.
    # guild_id: The guild ID where the reaction got added or removed, if applicable.
    # member: The member who added the reaction. Only available if event_type is REACTION_ADD and the reaction is inside a guild.
    # message_id: The message ID that got or lost a reaction.
    # user_id: The user ID who added the reaction or whose reaction was removed.
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # check to see if an emoji is added and that emoji is 🤡
        if str(payload.emoji) == '🤡':
            # get the channel to send a message to
            channel = self.bot.get_channel(payload.channel_id)

            # get the id of the message reacted to
            m_id = payload.message_id

            # get the id of the guild the message is in
            g_id = str(payload.guild_id)

            # fetch the message with the id
            message = await channel.fetch_message(m_id)
            sender = str(message.author)
            sender = sender.split('#')[0]
            # if the sender is ClownBot do nothing
            if sender == 'ClownBot_py':
                return
            if g_id not in global_.leaderboard.keys():
                global_.leaderboard[g_id] = {}
            # check for that user in the leaderboard obj
            # if the user is already in the leaderboard
            author_id = str(message.author.id)
            if author_id in global_.leaderboard[g_id].keys():
                global_.leaderboard[g_id][author_id] += 1
            # the user is not already in the leaderboard
            else:
                global_.leaderboard[g_id][author_id] = 1
            helper_functions.sort_leaderboard(g_id)
            helper_functions.save_leaderboard()
            print(global_.leaderboard)

    @commands.command()
    async def clowns(self, ctx):
        """
        Send a discord embed containing the clown leaderboard information for the server the command was called from
        :param ctx: Discord Context object
        """
        # https://discordpy.readthedocs.io/en/latest/api.html?highlight=embed#discord.Embed
        # create an embed from the leaderboard obj
        guild_id = str(ctx.guild.id)
        try:
            embed = discord.Embed()
            embed.title = 'Biggest Clowns'
            for clown_id in global_.leaderboard[guild_id]:
                clown_name = await helper_functions.get_display_name(ctx, clown_id)
                embed.add_field(
                    name=f'**{clown_name}**', value=f'> Clowns: {global_.leaderboard[guild_id][clown_id]}\n',
                    inline=False)
            await ctx.channel.send(embed=embed)
        except KeyError:
            await ctx.channel.send("No clowns yet!")

    @commands.command(hidden=True)
    @commands.check(helper_functions.is_clown_admin)
    async def clownset(self, ctx, clown_id: str, clown_num: int):
        """
        Forcibly set a given user's clown count for the server that command is called from. Can only be called from specific
        discord accounts.
        :param ctx: Discord Context object
        :param clown_id: Discord account ID of user to modify
        :param clown_num: Number to set clown count to
        """

        guild_id = str(ctx.guild.id)
        if str(ctx.guild.id) not in global_.leaderboard.keys():
            global_.leaderboard[guild_id] = {}
        global_.leaderboard[guild_id][clown_id] = clown_num
        helper_functions.sort_leaderboard(guild_id)
        helper_functions.save_leaderboard()

    @clownset.error
    async def clownset_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Hey, that's illegal")


class General(commands.Cog):
    """
    Misc. commands
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def test(self, ctx):
        """
      Test command
      :param ctx: Discord Context object
      """
        print(global_.leaderboard)
        await ctx.send("test")

    @commands.command()
    async def gamer(self, ctx):
        """
        Call the command sender a Gamer
        :param ctx: Discord Context object
        """
        await ctx.send(f"{ctx.author} is a Gamer")


class Wordle(commands.Cog):
    """
    Commands and listeners pertaining to Wordle
    """

    wordle_regex = re.compile(r"Wordle \d+ X/\d", re.IGNORECASE)

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Check if user posted a failed wordle attempt in a wordle channel, and clown them if so
        :param message:
        """
        if message.author == self.bot:
            return
        if helper_functions.is_wordle_channel(message.channel.name):
            if re.match(self.wordle_regex, message.content):
                await message.add_reaction('🤡')
