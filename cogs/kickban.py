import datetime
import discord
import re
import time
import typing

from cogs import converters, utils
from cogs.checks import is_staff, check_bot_or_staff
from cogs.database import DatabaseCog
from discord.ext import commands


class KickBan(DatabaseCog):
    """
    Kicking and banning users.
    """

    async def cog_check(self, ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    def parse_time(self, length):
        # thanks Luc#5653
        units = {
            "d": 86400,
            "h": 3600,
            "m": 60,
            "s": 1
        }
        seconds = 0
        match = re.findall("([0-9]+[smhd])", length)  # Thanks to 3dshax server's former bot
        if not match:
            return None, None
        for item in match:
            seconds += int(item[:-1]) * units[item[-1]]
        timestamp = datetime.datetime.now()
        delta = datetime.timedelta(seconds=seconds)
        unban_time = timestamp + delta
        unban_time_string = unban_time.strftime("%Y-%m-%d %H:%M:%S")
        return unban_time, unban_time_string

    async def meme(self, beaner: discord.Member, beaned: discord.Member, action: str, channel: discord.TextChannel, reason: str):
        await channel.send(f"Seriously? What makes you think it's okay to try and {action} another staff or helper like that?")
        msg = f"{beaner.mention} attempted to {action} {beaned.mention}|{beaned} in {channel.mention} "
        if reason != "":
            msg += "for the reason " + reason
        await self.bot.channels['meta'].send(msg + (" without a reason" if reason == "" else ""))

    @is_staff("HalfOP")
    @commands.bot_has_permissions(kick_members=True)
    @commands.command(name="kick")
    async def kick_member(self, ctx, member: converters.SafeMember, *, reason=""):
        """Kicks a user from the server. Staff only."""
        if await check_bot_or_staff(ctx, member, "kick"):
            return
        msg = f"You were kicked from {ctx.guild.name}."
        if reason != "":
            msg += " The given reason is: " + reason
        msg += "\n\nYou are able to rejoin the server, but please read the rules in #welcome-and-rules before participating again."
        await utils.send_dm_message(member, msg)
        try:
            self.bot.actions.append("uk:" + str(member.id))
            await member.kick(reason=reason)
        except discord.errors.Forbidden:
            await ctx.send("💢 I don't have permission to do this.")
            return
        await ctx.safe_send(f"{member} is now gone. 👌")
        msg = f"👢 **Kick**: {ctx.author.mention} kicked {member.mention} | {self.bot.escape_text(member)}\n🏷 __User ID__: {member.id}"
        if reason != "":
            msg += "\n✏️ __Reason__: " + self.bot.escape_text(reason)
        await self.bot.channels['server-logs'].send(msg)
        signature = utils.command_signature(ctx.command)
        await self.bot.channels['mod-logs'].send(msg + (f"\nPlease add an explanation below. In the future, it is recommended to use `{signature}` as the reason is automatically sent to the user." if reason == "" else ""))

    @is_staff("OP")
    @commands.bot_has_permissions(ban_members=True)
    @commands.command(name="ban", aliases=["yeet"])
    async def ban_member(self, ctx, member: converters.SafeMember, days: typing.Optional[int] = 0, *, reason=""):
        """Bans a user from the server. OP+ only. Optional: [days] Specify up to 7 days of messages to delete."""
        if await check_bot_or_staff(ctx, member, "ban"):
            return
        if days > 7:
            days = 7
        elif days < 0:
            days = 0
        msg = f"You were banned from {ctx.guild.name}."
        if reason != "":
            msg += " The given reason is: " + reason
        msg += "\n\nThis ban does not expire."
        await utils.send_dm_message(member, msg)
        try:
            self.bot.actions.append("ub:" + str(member.id))
            await member.ban(reason=reason, delete_message_days=days)
        except discord.errors.Forbidden:
            await ctx.send("💢 I don't have permission to do this.")
            return
        await ctx.safe_send(f"{member} is now b&. 👍")
        msg = f"⛔ **Ban**: {ctx.author.mention} banned {member.mention} | {self.bot.escape_text(member)}\n🏷 __User ID__: {member.id}"
        if reason != "":
            msg += "\n✏️ __Reason__: " + self.bot.escape_text(reason)
        await self.bot.channels['server-logs'].send(msg)
        signature = utils.command_signature(ctx.command)
        await self.bot.channels['mod-logs'].send(msg + (f"\nPlease add an explanation below. In the future, it is recommended to use `{signature}` as the reason is automatically sent to the user." if reason == "" else ""))

    @is_staff("OP")
    @commands.bot_has_permissions(ban_members=True)
    @commands.command(name="banid", aliases=["yeetid"])
    async def banid_member(self, ctx, userid: int, *, reason=""):
        """Bans a user id from the server. OP+ only."""
        try:
            user = await self.bot.fetch_user(userid)
        except discord.errors.NotFound:
            await ctx.send(f"No user associated with ID {userid}.")
            return
        if await check_bot_or_staff(ctx, user, "ban"):
            return
        try:
            self.bot.actions.append("ub:" + str(user.id))
            await ctx.guild.ban(user, reason=reason, delete_message_days=0)
        except discord.errors.Forbidden:
            await ctx.send("💢 I don't have permission to do this.")
            return
        await ctx.safe_send(f"User {user.id} | {user.name} is now b&. 👍")
        msg = f"⛔ **Ban**: {ctx.author.mention} banned ID {user.id}"
        if reason != "":
            msg += "\n✏️ __Reason__: " + self.bot.escape_text(reason)
        await self.bot.channels['server-logs'].send(msg)
        signature = utils.command_signature(ctx.command)
        await self.bot.channels['mod-logs'].send(msg + (f"\nPlease add an explanation below. In the future, it is recommended to use `{signature}` as the reason is automatically sent to the user." if reason == "" else ""))

    @is_staff("OP")
    @commands.bot_has_permissions(ban_members=True)
    @commands.command(name="silentban", aliases=["quietyeet"])
    async def silentban_member(self, ctx, member: converters.SafeMember, days: typing.Optional[int] = 0, *, reason=""):
        """Bans a user from the server, without a notification. OP+ only.  Optional: [days] Specify up to 7 days of messages to delete."""
        if await check_bot_or_staff(ctx, member, "ban"):
            return
        if days > 7:
            days = 7
        elif days < 0:
            days = 0
        try:
            self.bot.actions.append("ub:" + str(member.id))
            await member.ban(reason=reason, delete_message_days=days)
        except discord.errors.Forbidden:
            await ctx.send("💢 I don't have permission to do this.")
            return
        await ctx.safe_send(f"{member} is now b&. 👍")
        reason = self.bot.escape_text(reason)
        msg = f"⛔ **Silent ban**: {ctx.author.mention} banned {member.mention} | {self.bot.escape_text(member)}\n"\
              f"🏷 __User ID__: {member.id}"
        if reason != "":
            msg += "\n✏️ __Reason__: " + self.bot.escape_text(reason)
        await self.bot.channels['server-logs'].send(msg)
        signature = utils.command_signature(ctx.command)
        await self.bot.channels['mod-logs'].send(msg + (f"\nPlease add an explanation below. In the future, it is recommended to use `{signature}`." if reason == "" else ""))

    @is_staff("OP")
    @commands.bot_has_permissions(ban_members=True)
    @commands.command(name="timeban", aliases=["timeyeet"])
    async def timeban_member(self, ctx, member: converters.SafeMember, length, *, reason=""):
        """Bans a user for a limited period of time. OP+ only.\n\nLength format: #d#h#m#s"""
        if await check_bot_or_staff(ctx, member, "timeban"):
            return
        unban_time, unban_time_string = self.parse_time(length)
        if unban_time_string is None:
            await ctx.send("Invalid length for ban!")
            return
        msg = f"You were banned from {ctx.guild.name}."
        if reason != "":
            msg += " The given reason is: " + reason
        msg += f"\n\nThis ban expires {unban_time_string} {time.tzname[0]}."
        await utils.send_dm_message(member, msg)
        try:
            self.bot.actions.append("ub:" + str(member.id))
            await member.ban(reason=reason, delete_message_days=0)
        except discord.errors.Forbidden:
            await ctx.send("💢 I don't have permission to do this.")
            return
        await self.add_timed_restriction(member.id, unban_time_string, 'timeban')
        await ctx.safe_send(f"{member} is now b& until {unban_time_string} {time.tzname[0]}. 👍")
        msg = f"⛔ **Time ban**: {ctx.author.mention} banned {member.mention} until {unban_time_string} | {member}\n🏷 __User ID__: {member.id}"
        if reason != "":
            msg += "\n✏️ __Reason__: " + self.bot.escape_text(reason)
        await self.bot.channels['server-logs'].send(msg)
        signature = utils.command_signature(ctx.command)
        await self.bot.channels['mod-logs'].send(msg + (f"\nPlease add an explanation below. In the future, it is recommended to use `{signature}` as the reason is automatically sent to the user." if reason == "" else ""))

    @is_staff("OP")
    @commands.bot_has_permissions(kick_members=True)
    @commands.command(name="softban", aliases=["gentleyeet"])
    async def softban_member(self, ctx, member: converters.SafeMember, *, reason):
        """Soft-ban a user. OP+ only.

        This "bans" the user without actually doing a ban on Discord. The bot will instead kick the user every time they join. Discord bans are account- and IP-based."""
        if await check_bot_or_staff(ctx, member, "softban"):
            return
        msg = f"This account is no longer permitted to participate in {ctx.guild.name}. The reason is: {reason}"
        await utils.send_dm_message(member, msg)
        try:
            await member.kick(reason=reason)
        except discord.errors.Forbidden:
            await ctx.send("💢 I don't have permission to do this.")
            return
        await ctx.safe_send(f"{member} is now b&. 👍")
        msg = f"⛔ **Soft-ban**: {ctx.author.mention} soft-banned {member.mention} | {self.bot.escape_text(member)}\n🏷 __User ID__: {member.id}\n✏️ __Reason__: {reason}"
        await self.bot.channels['mod-logs'].send(msg)
        await self.bot.channels['server-logs'].send(msg)

    @is_staff("OP")
    @commands.command(name="softbanid", aliases=["gentleyeetid"])
    async def softbanid_member(self, ctx, user_id: int, *, reason):
        """Soft-ban a user based on ID. OP+ only.

        This "bans" the user without actually doing a ban on Discord. The bot will instead kick the user every time they join. Discord bans are account- and IP-based."""
        user = await self.bot.fetch_user(user_id)
        if await check_bot_or_staff(ctx, user, "softban"):
            return
        softban = await self.get_softban(user_id)
        if softban:
            await ctx.send('User is already softbanned!')
            return
        await self.add_softban(user_id, ctx.author.id, reason)
        await ctx.send(f"ID {user_id} is now b&. 👍")
        msg = f"⛔ **Soft-ban**: {ctx.author.mention} soft-banned ID {self.bot.escape_text(user)}\n✏️ __Reason__: {reason}"
        await self.bot.channels['mod-logs'].send(msg)
        await self.bot.channels['server-logs'].send(msg)

    @is_staff("OP")
    @commands.command(name="unsoftban")
    async def unsoftban_member(self, ctx, user_id: int):
        """Un-soft-ban a user based on ID. OP+ only."""
        await self.remove_softban(user_id)
        user = await self.bot.fetch_user(user_id)
        await ctx.safe_send(f"{user} has been unbanned!")
        msg = f"⚠️ **Un-soft-ban**: {ctx.author.mention} un-soft-banned {self.bot.escape_text(user)}"
        await self.bot.channels['mod-logs'].send(msg)

    @is_staff("SuperOP")
    @commands.bot_has_permissions(ban_members=True)
    @commands.command(name="ban2time")
    async def convert_ban(self, ctx, user_id: int, length="", *, reason):
        """Converts a ban to timeban"""
        user = await self.bot.fetch_user(user_id)
        try:
            await self.bot.guild.fetch_ban(user)
        except discord.errors.NotFound:
            await ctx.send(f"No ban found for ID {user_id}.")
            return
        if await self.get_time_restrictions_by_user_type(user_id, 'timeban') is not None:
            await ctx.send("User is already timebanned.")
            return
        unban_time, unban_time_string = self.parse_time(length)
        if not unban_time_string:
            await ctx.send("Invalid length for ban!")
            return
        await self.add_timed_restriction(user_id, unban_time_string, "timeban")
        reason = self.bot.escape_text(reason)
        safe_user = self.bot.escape_text(user)
        await ctx.send(f"{user.mention}|{safe_user} is now b& until {unban_time_string} {time.tzname[0]}. 👍")
        msg = f"⛔ **Ban Change**: {ctx.author.mention} changed {safe_user} ban to a timeban until {unban_time_string}\n🏷 __User ID__: {user.id} \n✏️ __Reason__: {reason}"
        await self.bot.channels['server-logs'].send(msg)
        await self.bot.channels['mod-logs'].send(msg)

    @is_staff("SuperOP")
    @commands.bot_has_permissions(ban_members=True)
    @commands.command(name="time2ban")
    async def convert_timeban(self, ctx, user_id: int, *, reason):
        """Converts a timeban to ban"""
        user = await self.bot.fetch_user(user_id)
        try:
            await self.bot.guild.fetch_ban(user)
        except discord.errors.NotFound:
            await ctx.send(f"No ban found for ID {user_id}.")
            return
        await self.remove_timed_restriction(user_id, 'timeban')
        await ctx.send(f"{user.mention}|{self.bot.escape_text(user)} is now b& forever. 👍")
        reason = self.bot.escape_text(reason)
        msg = f"⛔ **Ban Change**: {ctx.author.mention} changed {self.bot.escape_text(user)} timeban to an indefinite ban.\n🏷 __User ID__: {user.id} \n✏️ __Reason__: {reason}"
        await self.bot.channels['server-logs'].send(msg)
        await self.bot.channels['mod-logs'].send(msg)


def setup(bot):
    bot.add_cog(KickBan(bot))
