import base64

import aiohttp

TEMPMAIL_API_URL = 'https://api.tempmail.mx/'


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
		raw = await self.post({
			"act": "list_domains",
			"avail": True
		})
		if not raw.get('success'):
			return []
		domains = []
		for domain in raw.get('response'):
			domains.append(domain.get('domain'))
		return domains

	async def unlock_mail(self, mail: str, password: str = None):
		if password is None:
			return await self.post({
				"act": "unlock_mail",
				"mail": mail
			})
		return await self.post({
			"act": "unlock_mail",
			"mail": mail,
			"pw": str(base64.b64encode(password.encode('utf-8')).decode('utf-8'))
		})

	async def set_password(self, mail: str, new_password: str, hash: str = None):
		if hash is None:
			return await self.post({
				"act": "claim_mail",
				"mail": mail,
				"pw": str(base64.b64encode(new_password.encode('utf-8')).decode('utf-8'))
			})
		return await self.post({
			"act": "claim_mail",
			"mail": mail,
			"hash": hash,
			"pw": str(base64.b64encode(new_password.encode('utf-8')).decode('utf-8'))
		})

	async def get_email(self, mail: str, hash: str):
		return await self.post({
			"act": "get_mails",
			"mail": mail,
			"hash": hash
		})

	async def send_email(self, mail: str, hash: str, to: str, subject: str, text: str):
		return await self.post({
			"act": "send_mail",
			"mail": mail,
			"to": to,
			"subject": subject,
			"body": text,
			"hash": hash
		})
