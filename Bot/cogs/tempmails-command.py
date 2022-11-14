import discord
import i18n
from discord import Localizations, ApplicationCommandInteraction, Button, ButtonStyle, ComponentInteraction
from discord.ext import commands

from Bot.TempMailAPI import TempMailAPI
from Bot.utils.LanguageTransformer import map_locale
from Database.database_access import get_mails

tempmailAPI = TempMailAPI()


def apply_prefix(mail) -> str:
	return f'<a:punktanimiert:968899820414705704> {mail}'


class TempMailsCommand(commands.Cog):
	def __init__(self, bot):
		self.bot: commands.Bot = bot

	@commands.Cog.slash_command(
		name='tempmails',
		description='lists your claimed temporary email addresses',
		description_localizations=Localizations(german='Listet deine beanspruchten temporären E-Mail-Adressen auf'),
	)
	async def tempmail(self, ctx: ApplicationCommandInteraction):
		locale = map_locale(ctx.author_locale)
		mails = await get_mails(ctx.author.id)
		if len(mails) == 0:
			await ctx.respond(i18n.t('tempmails.no_mails', locale=locale), hidden=True)
			return
		message = await ctx.respond(i18n.t('tempmails.loading', locale=locale), hidden=True)
		await self.send_mails_paginated(message, mails, locale=locale)

	async def send_mails_paginated(self, message: discord.Message, mails: list, page: int = 1, locale: str = 'en'):
		#  get 10 mails from the current page
		current_mails = mails[(page - 1) * 10:page * 10]
		#  create string list of current_mails
		current_mails_str = '\n'.join(map(apply_prefix, current_mails))

		embed = discord.Embed(
			title=i18n.t('tempmails.title', locale=locale),
			description=i18n.t('tempmails.description', locale=locale, mails=current_mails_str),
			color=0x2f3136
		)
		embed.set_footer(text=i18n.t('tempmails.footer', locale=locale, count=len(mails)))
		#  create buttons
		buttons = []
		#  previous page button
		if page > 1:
			buttons.append(Button(label=i18n.t('tempmails.previous_page', locale=locale, page=(page - 1)), style=ButtonStyle.grey,
			                      custom_id=f'mx-switch_page:{page - 1}'))
		else:
			buttons.append(Button(label=i18n.t('tempmails.first_page', locale=locale), style=ButtonStyle.grey,
			                      disabled=True, custom_id='mx-first_page'))
		#  next page button
		if len(mails) > page * 10:
			buttons.append(Button(label=i18n.t('tempmails.next_page', locale=locale, page=(page + 1)), style=ButtonStyle.grey,
			                      custom_id=f'mx-switch_page:{page + 1}'))
		else:
			buttons.append(Button(label=i18n.t('tempmails.last_page', locale=locale), style=ButtonStyle.grey,
			                      disabled=True, custom_id='mx-last_page'))
		await message.edit(content='', embed=embed, components=[buttons])

	@commands.Cog.on_click('^mx-switch_page:[0-9]+$')
	async def switch_page(self, interaction: ComponentInteraction, _):
		await interaction.defer(hidden=True)
		#  get page from button id
		page = int(interaction.data.custom_id.split(':')[1])
		#  get mails from database
		mails = await get_mails(interaction.author.id)
		#  send mails paginated
		await self.send_mails_paginated(interaction.message, mails, page=page, locale=map_locale(interaction.author_locale))


def setup(bot):
	bot.add_cog(TempMailsCommand(bot))
