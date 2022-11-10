from discord import Locale


def map_locale(locale: Locale) -> str:
	if locale == Locale.en_US:
		return 'en'
	elif locale == Locale.german:
		return 'de'
	else:
		return 'en'
