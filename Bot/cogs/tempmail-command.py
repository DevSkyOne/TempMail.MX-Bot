import datetime
import uuid

import discord
import i18n
from discord import Localizations, SlashCommandOption, ApplicationCommandInteraction, AutocompleteInteraction, \
	SlashCommandOptionChoice, Button, ButtonStyle, SelectMenu, SelectOption, ComponentInteraction, Modal, TextInput, \
	ModalSubmitInteraction, TextInputStyle
from discord.ext import commands
from Bot.TempMailAPI import TempMailAPI
from Bot.utils.LanguageTransformer import map_locale, repair_email_prefix
from Database.database_access import insert_or_update_mail

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
		locale = map_locale(ctx.author_locale)
		if prefix is None:
			prefix = uuid.uuid4().hex.lower()
		else:
			prefix = repair_email_prefix(prefix.lower())

		if domain is None:
			domain = 'tempmail.mx'
		else:
			#  Test if domain is valid
			domains = (await tempmailAPI.get_domains()).get('response')
			if domain not in domains:
				domain = 'tempmail.mx'

		message = await ctx.respond(i18n.t('tempmail.loading', locale=locale), hidden=True)
		await self.refresh_mail(message, prefix, domain, locale)

	async def refresh_mail(self, message: discord.Message, prefix: str,
	                       domain: str, locale: str = 'en', password: str = None):
		if password == 'None':
			password = None
		mails = await tempmailAPI.get_email(mail=f'{prefix}@{domain}', password=password)
		password_required = False

		if mails.get('response').__contains__('msg'):
			msg = mails.get('response').get('msg')
			password_required = (msg == 'Password required') or (msg == 'Wrong password')

		mail_options = []
		mail_row = []
		pass_button = Button(label=i18n.t('tempmail.button.unlock-pass', locale=locale), style=ButtonStyle.red,
		                     custom_id=f'mx-unlock-pass:{domain}@{prefix}')

		description = i18n.t('tempmail.embed.description-locked', locale=locale, prefix=prefix, domain=domain)
		if not password_required:
			description = i18n.t('tempmail.embed.description', locale=locale, prefix=prefix, domain=domain)
			pass_button = Button(label=i18n.t('tempmail.button.set-pass', locale=locale), style=ButtonStyle.gray,
			                     custom_id=f'mx-set-pass:{domain}@{prefix}:{password}')
			for mail in mails.get('response'):
				mail_options.append(SelectOption(label=f'{mail.get("message").get("subject")}',
				                                 description=i18n.t('tempmail.mails.from', locale=locale,
				                                                    sender=mail.get('message').get('from')),
				                                 value=mail.get('id')))

			if len(mail_options) > 0:
				mail_row = [
					SelectMenu(
						custom_id=f'mx-mails:{domain}@{prefix}:{password}',
						placeholder=i18n.t('tempmail.mails.select', locale=locale),
						options=mail_options
					)
				]

		embed = discord.Embed(
			title='TempMail.MX',
			description=description,
			color=0x2f3136
		)
		embed.set_footer(
			text=f'© 2022 TempMail.MX Bot ⬤ {i18n.t("tempmail.embed.footer", locale=locale, time=datetime.datetime.now().strftime("%H:%M:%S"))}')
		await message.edit(content='', embed=embed, components=[[
			Button(label=i18n.t('tempmail.button.refresh', locale=locale), style=ButtonStyle.green,
			       custom_id=f'mx-refresh:{domain}@{prefix}:{password}'),
			pass_button,
			Button(label=i18n.t('tempmail.button.send', locale=locale), style=ButtonStyle.gray,
			       custom_id=f'mx-send:{domain}@{prefix}:{password}', disabled=(password is None)),
			Button(label=i18n.t('tempmail.button.web', locale=locale), style=ButtonStyle.gray,
			       url=f'https://tempmail.mx/?mail={prefix}@{domain}')
		], mail_row])

	@commands.Cog.on_click('^mx-refresh:[a-z0-9._-]+@[0-9,a-z,.]+:[\S]+$')
	async def refresh_click(self, ctx: ComponentInteraction, _):
		await ctx.defer(hidden=True)
		locale = map_locale(ctx.author_locale)
		domain, prefix = ctx.data.custom_id.split(':')[1].split('@')
		password = ctx.data.custom_id.split(':')[2]
		await self.refresh_mail(ctx.message, prefix, domain, locale, password)

	@tempmail.autocomplete_callback
	async def tempmail_autocomplete(self, ctx: AutocompleteInteraction, prefix: str = None, domain: str = None) -> None:
		if ctx.focused_option_name == 'prefix':
			prefixes_raw = [uuid.uuid4().hex.lower(),
			                repair_email_prefix(ctx.author.name.lower()),
			                str(ctx.author.id)]
			prefixes = [SlashCommandOptionChoice(name=prefix_val, value=prefix_val) for prefix_val in prefixes_raw if
			            prefix_val.startswith(prefix)]
			await ctx.send_choices(prefixes)
		elif ctx.focused_option_name == 'domain':
			domains_raw = (await tempmailAPI.get_domains()).get('response')
			domains = [SlashCommandOptionChoice(name=domain_val, value=domain_val) for domain_val in domains_raw if
			           domain_val.startswith(domain) or domain is None]
			#  Sort domains by length ascending and then alphabetically
			domains.sort(key=lambda x: (len(x.name), x.name))
			#  Get the first 25 domains
			await ctx.send_choices(domains[:25])

	@commands.Cog.on_select('^mx-mails:[a-z0-9._-]+@[0-9,a-z,.]+:[\S]+$')
	async def mail_click(self, ctx: ComponentInteraction, _):
		mail_id = ctx.data.values[0]
		locale = map_locale(ctx.author_locale)
		domain, prefix = ctx.data.custom_id.split(':')[1].split('@')
		password = ctx.data.custom_id.split(':')[2]
		if password == 'None':
			password = None
		message = await ctx.respond(i18n.t('tempmail.loading', locale=locale), hidden=True)
		mails = await tempmailAPI.get_email(mail=f'{prefix}@{domain}', password=password)
		mail = None
		for mail_raw in mails.get('response'):
			if mail_raw.get('id') == mail_id:
				mail = mail_raw
				break
		if mail is None:
			await message.edit(content=i18n.t('tempmail.mails.not_found', locale=locale))
			return
		embed = discord.Embed(
			title=i18n.t('tempmail.mails.embed.title', locale=locale, subject=mail.get('message').get('subject'),
			             sender=mail.get('message').get('from')),
			description=i18n.t('tempmail.mails.embed.description', locale=locale, text=mail.get('message').get('text')),
			color=0x2f3136
		)
		embed.set_footer(
			text=f'© 2022 TempMail.MX Bot ⬤ {i18n.t("tempmail.embed.footer", locale=locale, time=datetime.datetime.now().strftime("%H:%M:%S"))}')
		await message.edit(content='', embed=embed, components=[])

	@commands.Cog.on_click('^mx-unlock-pass:[a-z0-9._-]+@[0-9,a-z,.]+$')
	async def unlock_pass_click(self, ctx: ComponentInteraction, _):
		domain, prefix = ctx.data.custom_id.split(':')[1].split('@')
		locale = map_locale(ctx.author_locale)
		await ctx.respond_with_modal(modal=Modal(
			custom_id=f'mx-unlock-pass-modal:{domain}@{prefix}',
			title=i18n.t('tempmail.unlock_pass.modal.title', locale=locale),
			components=[[
				TextInput(
					label=i18n.t('tempmail.unlock_pass.modal.input', locale=locale),
					custom_id=f'mx-unlock-pass-input',
					placeholder=i18n.t('tempmail.unlock_pass.modal.placeholder', locale=locale),
					min_length=1,
					max_length=100,
					required=True
				)
			]]
		))

	@commands.Cog.on_click('^mx-set-pass:[a-z0-9._-]+@[0-9,a-z,.]+:[\S]+$')
	async def set_pass_click(self, ctx: ComponentInteraction, _):
		domain, prefix = ctx.data.custom_id.split(':')[1].split('@')
		password = ctx.data.custom_id.split(':')[2]
		locale = map_locale(ctx.author_locale)
		await ctx.respond_with_modal(modal=Modal(
			custom_id=f'mx-set-pass-modal:{domain}@{prefix}:{password}',
			title=i18n.t('tempmail.set_pass.modal.title', locale=locale),
			components=[[
				TextInput(
					label=i18n.t('tempmail.set_pass.modal.input', locale=locale),
					custom_id=f'mx-set-pass-input',
					placeholder=i18n.t('tempmail.set_pass.modal.placeholder', locale=locale),
					min_length=1,
					max_length=100,
					required=True
				)
			]]
		))

	@commands.Cog.on_submit('^mx-unlock-pass-modal:[a-z0-9._-]+@[0-9,a-z,.]+$')
	async def unlock_pass_submit(self, ctx: ModalSubmitInteraction):
		await ctx.defer(hidden=True)
		domain, prefix = ctx.data.custom_id.split(':')[1].split('@')
		locale = map_locale(ctx.author_locale)
		password = ctx.get_field('mx-unlock-pass-input').value
		await self.refresh_mail(ctx.message, prefix, domain, locale, password)
		if await self.test_if_locked(mail=f'{prefix}@{domain}', password=password):
			return await ctx.edit(content=i18n.t('tempmail.unlock_pass.failed', locale=locale))
		await ctx.respond(i18n.t('tempmail.unlock_pass.success', locale=locale), hidden=True)
		await insert_or_update_mail(clientid=ctx.author.id, mail=f'{prefix}@{domain}')

	@commands.Cog.on_submit('^mx-set-pass-modal:[a-z0-9._-]+@[0-9,a-z,.]+:[\S]+$')
	async def set_pass_submit(self, ctx: ModalSubmitInteraction):
		await ctx.defer(hidden=True)
		domain, prefix = ctx.data.custom_id.split(':')[1].split('@')
		old_password = ctx.data.custom_id.split(':')[2]
		if old_password == 'None':
			old_password = None
		locale = map_locale(ctx.author_locale)
		password = ctx.get_field('mx-set-pass-input').value
		await tempmailAPI.set_password(mail=f'{prefix}@{domain}', password=old_password, new_password=password)
		await self.refresh_mail(ctx.message, prefix, domain, locale, password)
		if await self.test_if_locked(mail=f'{prefix}@{domain}', password=password):
			return await ctx.edit(content=i18n.t('tempmail.set_pass.failed', locale=locale))
		await ctx.respond(i18n.t('tempmail.set_pass.success', locale=locale), hidden=True)
		await insert_or_update_mail(clientid=ctx.author.id, mail=f'{prefix}@{domain}')

	async def test_if_locked(self, mail: str, password: str = None) -> bool:
		if password == 'None':
			password = None
		mails = await tempmailAPI.get_email(mail=f'{mail}', password=password)
		password_required = False

		if mails.get('response').__contains__('msg'):
			msg = mails.get('response').get('msg')
			password_required = (msg == 'Password required') or (msg == 'Wrong password')
		return password_required

	@commands.Cog.on_click('^mx-send:[a-z0-9._-]+@[0-9,a-z,.]+:[\S]+$')
	async def send_email_click(self, ctx: ComponentInteraction, _):
		domain, prefix = ctx.data.custom_id.split(':')[1].split('@')
		password = ctx.data.custom_id.split(':')[2]
		await ctx.respond_with_modal(modal=Modal(
			custom_id=f'mx-send-email-modal:{domain}@{prefix}:{password}',
			title=i18n.t('tempmail.send_email.modal.title', locale=map_locale(ctx.author_locale)),
			components=[[
				TextInput(
					label=i18n.t('tempmail.send_email.to.label', locale=map_locale(ctx.author_locale)),
					custom_id=f'mx-send-email-to',
					placeholder=i18n.t('tempmail.send_email.to.placeholder', locale=map_locale(ctx.author_locale)),
					min_length=1,
					max_length=100,
					required=True
				),
				TextInput(
					label=i18n.t('tempmail.send_email.subject.label', locale=map_locale(ctx.author_locale)),
					custom_id=f'mx-send-email-subject',
					placeholder=i18n.t('tempmail.send_email.subject.placeholder', locale=map_locale(ctx.author_locale)),
					min_length=1,
					max_length=100,
					required=True
				),
				TextInput(
					label=i18n.t('tempmail.send_email.text.label', locale=map_locale(ctx.author_locale)),
					custom_id=f'mx-send-email-text',
					placeholder=i18n.t('tempmail.send_email.text.placeholder', locale=map_locale(ctx.author_locale)),
					min_length=1,
					style=TextInputStyle.multiline,
					required=True
				)
			]]
		))

	@commands.Cog.on_submit('^mx-send-email-modal:[a-z0-9._-]+@[0-9,a-z,.]+:[\S]+$')
	async def send_email_submit(self, ctx: ModalSubmitInteraction):
		await ctx.defer(hidden=True)
		domain, prefix = ctx.data.custom_id.split(':')[1].split('@')
		password = ctx.data.custom_id.split(':')[2]
		locale = map_locale(ctx.author_locale)
		to = ctx.get_field('mx-send-email-to').value
		subject = ctx.get_field('mx-send-email-subject').value
		text = ctx.get_field('mx-send-email-text').value
		await tempmailAPI.send_email(mail=f'{prefix}@{domain}', password=password, to=to, subject=subject, text=text)
		await ctx.respond(i18n.t('tempmail.send_email.success', locale=locale), hidden=True)


def setup(bot):
	bot.add_cog(TempMailCommand(bot))
