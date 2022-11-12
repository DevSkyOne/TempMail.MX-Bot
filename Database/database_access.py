from typing import Any

import aiomysql

from Bot.TempMailAPI import TempMailAPI
from Database import get_pool

tempmailAPI = TempMailAPI()


async def insert_or_update_mail(clientid: str, mail: str):
	pool: aiomysql.Pool = await get_pool()
	async with pool.acquire() as connection:
		connection: aiomysql.Connection
		cursor: aiomysql.Cursor = await connection.cursor()
		await cursor.execute("INSERT INTO discord_emails (clientid, mail) VALUES (%s, %s) ON DUPLICATE KEY UPDATE "
		                     "latest_usage=CURRENT_TIMESTAMP", (clientid, mail))
		await connection.commit()
	pool.close()
	await pool.wait_closed()


async def get_mails(clientid: str) -> list:
	pool: aiomysql.Pool = await get_pool()
	async with pool.acquire() as connection:
		connection: aiomysql.Connection
		cursor: aiomysql.Cursor = await connection.cursor()
		await cursor.execute("SELECT mail FROM discord_emails WHERE clientid=%s", (clientid,))
		mails = await cursor.fetchall()
	pool.close()
	await pool.wait_closed()
	#  check if mails are valid
	valid_domains = (await tempmailAPI.get_domains()).get('response')
	return [mail[0] for mail in mails if mail[0].split('@')[1] in valid_domains]
