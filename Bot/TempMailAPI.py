import aiohttp

TEMPMAIL_API_URL = 'https://tempmail.mx/?api'


class TempMailAPI:

	def __init__(self):
		self.headers = {"Content-Type": "application/json",
		                "Accept": "application/json"}

	# Asynchronous requests

	async def post(self, data):
		async with aiohttp.ClientSession(headers=self.headers) as session:
			async with session.post(f"{TEMPMAIL_API_URL}", json=data) as response:
				if response.status == 204:
					return None
				else:
					return await response.json()

	async def get_domains(self):
		return await self.post({
		  "act": "domains",
		  "avail": True
		})

	async def get_email(self, mail: str, password: str = None):
		return await self.post({
		  "act": "mails",
		  "mail": mail,
		  "pw": password
		})
