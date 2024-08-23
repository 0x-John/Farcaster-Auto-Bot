import random
from utils import starter
from utils.core import get_all_lines
from itertools import zip_longest
import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import PeerChannel
from utils.core.logger import logger
from data.config import API_ID, API_HASH, SESSION_NAME, WORK, POST_LIMIT, POST_DELAY
from eth_account import Account
import aiohttp
import time
import base64
from eth_account.messages import encode_defunct
import canonicaljson
from utils.warpcast import Warpcast
from utils.gpt_client import GptClient
from datetime import datetime, timezone

async def create_warpcast_session(mnemonic: str, proxy: str, thread: int, old_session: aiohttp.ClientSession = None) -> Warpcast:
    if old_session:
        await old_session.close()

    Account.enable_unaudited_hdwallet_features()
    account = Account.from_mnemonic(mnemonic)
    
    headers = {'User-Agent': 'Android Client'}
    session = aiohttp.ClientSession(headers=headers, trust_env=True, connector=aiohttp.TCPConnector(ssl=False))
    
    timestamp = int(time.time()) * 1000
    payload = {"method": "generateToken", "params": {"timestamp": timestamp, "expires_at": 86400000 + timestamp}}
    signed_message = account.sign_message(encode_defunct(primitive=canonicaljson.encode_canonical_json(payload)))
    session.headers['Authorization'] = "Bearer eip191:" + base64.b64encode(signed_message.signature).decode()
    
    async with session.put("https://api.warpcast.com/v2/auth", json=payload, proxy=f"http://{proxy}" if proxy else None) as resp:
        resp_json = await resp.json()
        session.headers['Authorization'] = "Bearer " + resp_json['result']['token']['secret']
    
    warpcast = Warpcast(session, account)
    logger.info(f"Создана сессия для аккаунта {thread + 1}")

    # Проверяем сессию сразу после создания
    if await warpcast.check_session():
        return warpcast
    else:
        logger.warning(f"Сессия для аккаунта {thread + 1} невалидна, создаем новую...")
        return await create_warpcast_session(mnemonic, proxy, thread, session)

async def start_gpt_posts(warpcast: Warpcast, thread: int):
    gpt_client = GptClient()
    initial_delay = random.uniform(5, 60)
    await asyncio.sleep(initial_delay)
    logger.info(f"Аккаунт {thread + 1} | Запуск GPT постов.")
    
    post_limit = random.randint(*POST_LIMIT)
    for _ in range(post_limit):
        text = await gpt_client.get_post()
        await starter.action_post_from_gpt(warpcast, thread, text)
        
        delay = random.uniform(*POST_DELAY)
        await asyncio.sleep(delay)

async def start_telegram_client(warpcasts, start_time):
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    @client.on(events.NewMessage)
    async def handler(event):
        if not event.is_private and event.is_channel:
            if event.message.date < start_time:
                return

            channel_id = event.chat_id
            message = event.message

            try:
                channel = await client.get_entity(PeerChannel(channel_id))
                channel_username = channel.username
            except Exception as e:
                logger.error(f"Ошибка получения имени пользователя канала: {e}")
                return

            if channel_username:
                logger.info(f"Найден новый пост на канале @{channel_username}")

                tg_channels = get_all_lines("data/tg_channels.txt")

                if f"@{channel_username}" in tg_channels:
                    index = tg_channels.index(f"@{channel_username}")
                    warpcast = warpcasts[index]
                    logger.info(f"Канал @{channel_username} находится в списке, обрабатываем публикацию.")
                    await starter.action_post_from_telegram(warpcast, index, message)

    await client.start()
    logger.info("Telegram сессия активирована!")
    await client.run_until_disconnected()

async def main():
    logger.info("Автор софта: https://t.me/x_0xJohn")

    mnemonics = get_all_lines("data/mnemonics.txt")
    proxys = get_all_lines("data/proxy.txt")

    accounts = [[mnemonic, thread, proxy] for thread, (mnemonic, proxy) in enumerate(zip_longest(mnemonics, proxys)) if mnemonic]
    
    warpcasts = [await create_warpcast_session(mnemonic, proxy, thread) for mnemonic, thread, proxy in accounts]

    tasks = []
    start_time = datetime.now(timezone.utc)

    if WORK['POST'] == 'TG':
        tasks.append(asyncio.create_task(start_telegram_client(warpcasts, start_time)))
    
    elif WORK['POST'] == 'GPT':
        tasks.extend([asyncio.create_task(start_gpt_posts(warpcast, thread)) for thread, warpcast in enumerate(warpcasts)])
    
    else:
        logger.info("Режим написания постов отключен.")

    if any(action != 'NO' for key, action in WORK.items() if key != 'POST'):
        tasks.extend([asyncio.create_task(starter.random_actions(warpcast, thread)) for thread, warpcast in enumerate(warpcasts)])

    if tasks:
        await asyncio.gather(*tasks)

    for warpcast in warpcasts:
        await warpcast.logout()

if __name__ == '__main__':
    asyncio.run(main())
