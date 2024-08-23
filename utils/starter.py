import random
import asyncio
import os
from utils.core import logger, random_line
from data.config import WORK, DELAY_RANGE
from telethon.tl.types import MessageMediaPhoto
from utils.warpcast import Warpcast
from utils.gpt_client import GptClient

ALLOWED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif']

async def action_post_from_gpt(warpcast: Warpcast, thread: int, text: str):
    media_url = None  # No media for GPT-generated posts

    if text:
        hash_, username = await warpcast.write_post(text, media_url)
        if hash_ and username:
            logger.success(f"Аккаунт {thread + 1} | Опубликован пост https://warpcast.com/{username}/{hash_} : {text}")
        else:
            logger.error(f"Аккаунт {thread + 1} | Ошибка публикации поста")
    else:
        logger.warning(f"Аккаунт {thread + 1} | Нет текста в посте")

async def action_post_from_telegram(warpcast: Warpcast, thread: int, message):
    media_url = None

    if message.media:
        try:
            # Создаем директорию для медиафайлов, если ее еще нет
            os.makedirs('img', exist_ok=True)

            # Проверяем тип файла перед загрузкой
            if isinstance(message.media, MessageMediaPhoto) or any(
                message.file.ext.lower() == ext for ext in ALLOWED_EXTENSIONS
            ):
                # Загружаем медиафайл
                file_path = await message.download_media(file="img/")
                
                if file_path:
                    logger.info(f"Медиафайл успешно сохранен: {file_path}")
                    media_url = await warpcast.get_random_img(file_path)
                else:
                    logger.error("Ошибка: download_media() вернула None")
            else:
                logger.warning(f"Аккаунт {thread + 1} | Недопустимый формат файла: {message.file.ext}")
        except Exception as e:
            logger.error(f"Ошибка при загрузке медиафайла: {e}")
    else:
        logger.info("Медиафайл отсутствует")

    if message.raw_text or media_url:
        hash_, username = await warpcast.write_post(message.raw_text.replace('\\n', '\n') if message.raw_text else '', media_url)
        if hash_ and username:
            logger.success(f"Аккаунт {thread + 1} | Опубликован пост https://warpcast.com/{username}/{hash_} : {message.raw_text}")
        else:
            logger.error(f"Аккаунт {thread + 1} | Ошибка публикации поста")
    else:
        logger.warning(f"Аккаунт {thread + 1} | Нет текста или изображения в посте")


async def random_actions(warpcast: Warpcast, thread: int):
    await asyncio.sleep(random.uniform(5, 60))
    logger.info(f"Аккаунт {thread + 1} | Запуск рандомных действий.")

    actions = {
        'LIKE': action_like,
        'COMMENT': action_comment,
        'FOLLOW': action_follow,
        'RECAST': action_recast
    }

    while True:
        available_actions = [action for action in actions if WORK.get(action, 'NO') != 'NO' and action != 'POST']
        if not available_actions:
            logger.warning(f"Аккаунт {thread + 1} | В конфигурации нет доступных действий для выполнения.")
            break

        action_name = random.choice(available_actions)
        action_function = actions[action_name]

        await action_function(warpcast, thread)

        delay = random.uniform(*DELAY_RANGE)
        await asyncio.sleep(delay)

async def action_like(warpcast, thread):
    exclude_item_id_prefixes = []
    latest_main_cast_timestamp = 0
    items, latest_main_cast_timestamp = await warpcast.get_feed_items_for_likes_and_comments(
        latest_main_cast_timestamp=latest_main_cast_timestamp,
        exclude_item_id_prefixes=exclude_item_id_prefixes
    )

    if items:
        item = random.choice(items)
        item_id, author_fid, item_text = item
        username, status = await warpcast.like(item_id)
        if status:
            logger.success(f"Аккаунт {thread + 1} | Лайкнул {item_id}")
        else:
            logger.error(f"Аккаунт {thread + 1} | {username}")

async def action_comment(warpcast, thread):
    exclude_item_id_prefixes = []
    latest_main_cast_timestamp = 0
    items, latest_main_cast_timestamp = await warpcast.get_feed_items_for_likes_and_comments(
        latest_main_cast_timestamp=latest_main_cast_timestamp,
        exclude_item_id_prefixes=exclude_item_id_prefixes
    )

    if items:
        item = random.choice(items)
        item_id, author_fid, item_text = item
        if len(item_text) < 50:
            logger.warning(f"Аккаунт {thread + 1} | Пост слишком короткий для комментария: {item_text}")
            return

        if WORK['COMMENT'] == 'GPT':
            gpt_client = GptClient()
            random_comment = await gpt_client.get_context_comment(item_text)
        elif WORK['COMMENT'] == 'FILE':
            random_comment = random_line("data/comments.txt", True)
        else:
            random_comment = None

        if random_comment:
            hash_, username = await warpcast.write_post(random_comment.replace('\\n', '\n'), parent_hash=item_id)
            logger.success(f"Аккаунт {thread + 1} | Написал комментарий https://warpcast.com/{username}/{hash_} :{random_comment}")
        else:
            logger.warning(f"Аккаунт {thread + 1} | Нет доступных комментов")

async def action_follow(warpcast, thread):
    fids_l = []
    cursor = ''
    fids, cursor = await warpcast.get_suggested_users(cursor)

    if fids:
        fid = random.choice(fids)
        msg, status = await warpcast.follow(fid)
        if status:
            logger.success(f"Аккаунт {thread + 1} | Подписался {fid}")
        else:
            logger.error(f"Аккаунт {thread + 1} | {msg}")

async def action_recast(warpcast, thread):
    exclude_item_id_prefixes = []
    latest_main_cast_timestamp = 0
    items, latest_main_cast_timestamp = await warpcast.get_feed_items_for_reposts(
        latest_main_cast_timestamp=latest_main_cast_timestamp,
        exclude_item_id_prefixes=exclude_item_id_prefixes
    )

    if items:
        item = random.choice(items)
        item_id, author_fid = item
        msg, status = await warpcast.recast(item_id)
        if status:
            logger.success(f"Аккаунт {thread + 1} | Репостнул {item_id}")
        else:
            logger.error(f"Аккаунт {thread + 1} | {msg}")
