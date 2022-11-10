import re

from discord import Locale


def map_locale(locale: Locale) -> str:
	if locale == Locale.en_US:
		return 'en'
	elif locale == Locale.german:
		return 'de'
	else:
		return 'en'


valid_email_prefix = re.compile(r'[a-zA-Z0-9._-]+')


def repair_email_prefix(prefix: str) -> str:
	valid = valid_email_prefix.findall(prefix)
	return ''.join(valid)

