import base64

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

	async def set_password(self, mail: str, password: str, new_password: str = None):
		if new_password is None:
			return await self.post({
				"act": "setpw",
				"mail": mail,
				"pw": str(base64.b64encode(password.encode('utf-8')).decode('utf-8'))
			})
		return await self.post({
			"act": "setpw",
			"mail": mail,
			"oldpw": str(base64.b64encode(password.encode('utf-8')).decode('utf-8')),
			"pw": str(base64.b64encode(new_password.encode('utf-8')).decode('utf-8'))
		})

	async def get_email(self, mail: str, password: str = None):
		if password is None:
			return await self.post({
				"act": "mails",
				"mail": mail
			})

		return await self.post({
			"act": "mails",
			"mail": mail,
			"pw": str(base64.b64encode(password.encode('utf-8')).decode('utf-8'))
		})

	async def send_email(self, mail: str, password: str, to: str, subject: str, text: str):
		return await self.post({
			"act": "send",
			"mail": mail,
			"to": to,
			"subject": subject,
			"body": text,
			"pw": str(base64.b64encode(password.encode('utf-8')).decode('utf-8'))
		})
