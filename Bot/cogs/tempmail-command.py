import uuid

import discord
from discord import Localizations, SlashCommandOption, ApplicationCommandInteraction, AutocompleteInteraction, \
	SlashCommandOptionChoice
from discord.ext import commands
from Bot.TempMailAPI import TempMailAPI
from Bot.utils.LanguageTransformer import map_locale

tempmailAPI = TempMailAPI()


class TempMailCommand(commands.Cog):
	def __init__(self, bot):
		self.bot: commands.Bot = bot

	@commands.Cog.listener()
	async def on_ready(self):
		print(f'Bot is on {len(self.bot.guilds)} guilds')
		for guild in self.bot.guilds:
			print(f'Guild: {guild.name} ({guild.id})')

	@commands.Cog.slash_command(
		name='tempmail',
		description='generates a temporary email address',
		description_localizations=Localizations(german='Generiert eine temporäre E-Mail-Adresse'),
		options=[
			SlashCommandOption(
				name='prefix',
				description='the name of the email address (in front of the @)',
				description_localizations=Localizations(german='Der Name der E-Mail-Adresse (vor dem @)'),
				option_type=str,
				autocomplete=True,
				required=False
			),
			SlashCommandOption(
				name='domain',
				description='the domain of the email address',
				description_localizations=Localizations(german='Die Domain der E-Mail-Adresse'),
				option_type=str,
				autocomplete=True,
				required=False,
			)
		]
	)
	async def tempmail(self, ctx: ApplicationCommandInteraction, prefix: str = None, domain: str = None):
		locale = map_locale(ctx.author_locale.value)
		if prefix is None:
			prefix = uuid.uuid4().hex
		else:
			prefix = prefix.replace('@', '').replace(' ', '').replace('.', '')

		if domain is None:
			domain = 'tempmail.mx'
		else:
			#  Test if domain is valid
			domains = (await tempmailAPI.get_domains()).get('response')
			if domain not in domains:
				domain = 'tempmail.mx'

		await ctx.respond(f'Your email address is: {prefix}@{domain}', hidden=True)

	@tempmail.autocomplete_callback
	async def tempmail_autocomplete(self, ctx: AutocompleteInteraction,  prefix: str = None, domain: str = None) -> None:
		if ctx.focused_option_name == 'prefix':
			prefixes = [SlashCommandOptionChoice(name=uuid.uuid4().hex, value=uuid.uuid4().hex),
			            SlashCommandOptionChoice(name=ctx.author.name, value=ctx.author.name),
			            SlashCommandOptionChoice(name=str(ctx.author.id), value=str(ctx.author.id))]
			await ctx.send_choices(prefixes)
		elif ctx.focused_option_name == 'domain':
			domains_raw = (await tempmailAPI.get_domains()).get('response')
			domains = [SlashCommandOptionChoice(name=domain, value=domain) for domain in domains_raw]
			await ctx.send_choices(domains)


def setup(bot):
	bot.add_cog(TempMailCommand(bot))
