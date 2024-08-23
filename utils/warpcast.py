import random
import aiohttp
import os
from eth_account import Account
import canonicaljson
from eth_account.messages import encode_defunct
import base64
from data.config import FEED_KEY
from utils.core import logger

API_V1_URL = "https://client.warpcast.com/v1/"
UPLOAD_URL_ENDPOINT = "generate-image-upload-url"

class Warpcast:
    def __init__(self, session, account):
        self.account = account
        self.session = session

    async def logout(self):
        await self.session.close()

    async def me(self):
        resp = await self.session.get('https://api.warpcast.com/v2/me')
        return (await resp.json())['result']['user']

    async def check_session(self):
        try:
            user = await self.me()
            username = user['username']
            logger.info(f"Проверка сессии успешна, получено имя пользователя: {username}")
            return True
        except Exception as e:
            logger.error(f"Ошибка проверки сессии")
            return False

    async def write_post(self, text: str, media_url: str = '', parent_hash: str = ''):
        json_data = {'embeds': [], 'text': text}

        if media_url:
            json_data['embeds'].append(media_url)
            logger.info(f"Embeds set to: {json_data['embeds']}")

        if parent_hash:
            json_data['parent'] = {'hash': parent_hash}

        resp = await self.session.post('https://client.warpcast.com/v2/casts', json=json_data)
        resp_json = await resp.json()

        if 'result' in resp_json and 'cast' in resp_json['result']:
            return resp_json['result']['cast']['hash'][:10], resp_json['result']['cast']['author']['username']
        else:
            logger.error(f"Error: {resp_json}")
            return None, None

    async def get_feed_items_for_likes_and_comments(self, viewed_cast_hashes: str = '', latest_main_cast_timestamp: int = 0,
                                                    exclude_item_id_prefixes=None):
        exclude_item_id_prefixes = [] if exclude_item_id_prefixes is None else exclude_item_id_prefixes

        json_data = {"feedKey": FEED_KEY, "feedType": "default", "viewedCastHashes": viewed_cast_hashes, "updateState": True}

        if latest_main_cast_timestamp:
            json_data['latestMainCastTimestamp'] = latest_main_cast_timestamp
            json_data['olderThan'] = latest_main_cast_timestamp
            json_data['excludeItemIdPrefixes'] = exclude_item_id_prefixes

        resp = await self.session.post('https://client.warpcast.com/v2/feed-items', json=json_data)
        resp_json = await resp.json()

        items = []
        for item in resp_json.get("result", {}).get("items", []):
            items.append((item['cast']['hash'], item['cast']['author']['fid'], item['cast'].get('text', '')))

        return items, resp_json.get('result', {}).get('latest_main_cast_timestamp', 0)
    
    async def get_feed_items_for_reposts(self, viewed_cast_hashes: str = '', latest_main_cast_timestamp: int = 0,
                                        exclude_item_id_prefixes=None):
        exclude_item_id_prefixes = [] if exclude_item_id_prefixes is None else exclude_item_id_prefixes

        json_data = {"feedKey": FEED_KEY, "feedType": "default", "viewedCastHashes": viewed_cast_hashes, "updateState": True}

        if latest_main_cast_timestamp:
            json_data['latestMainCastTimestamp'] = latest_main_cast_timestamp
            json_data['olderThan'] = latest_main_cast_timestamp
            json_data['excludeItemIdPrefixes'] = exclude_item_id_prefixes

        resp = await self.session.post('https://client.warpcast.com/v2/feed-items', json=json_data)
        resp_json = await resp.json()

        items = []
        for item in resp_json.get("result", {}).get("items", []):
            items.append((item['cast']['hash'], item['cast']['author']['fid']))

        return items, resp_json.get('result', {}).get('latest_main_cast_timestamp', 0)



    async def like(self, cast_hash: str):
        json_data = {"castHash": cast_hash}
        resp = await self.session.put('https://client.warpcast.com/v2/cast-likes', json=json_data)

        resp_json = await resp.json()
        if resp_json.get('result') is not None:
            return resp_json['result'].get("like").get("reactor").get("username"), True
        else:
            return resp_json.get('errors', [{}])[0].get('message', 'Unknown error'), False

    async def get_suggested_users(self, cursor: str = ''):
        url = 'https://client.warpcast.com/v2/suggested-users?limit=100&randomized=false'

        if cursor:
            url += "&cursor=" + cursor

        resp = await self.session.get(url)
        resp_json = await resp.json()

        fids = []
        for user in resp_json.get('result', {}).get("users", []):
            if user['fid'] not in fids: fids.append(user['fid'])

        next_cursor = resp_json.get("next", {}).get('cursor', '') 
        return fids, next_cursor

    async def follow(self, fid: int):
        json_data = {"targetFid": fid}
        resp = await self.session.put('https://client.warpcast.com/v2/follows', json=json_data)
        resp_json = await resp.json()

        if resp_json.get('result'):
            return resp_json['result'].get("success"), True
        else:
            return resp_json.get('errors', [{}])[0].get('message', 'Unknown error'), False

    async def recast(self, cast_hash: str):
        json_data = {"castHash": cast_hash}
        resp = await self.session.put('https://client.warpcast.com/v2/recasts', json=json_data)

        resp_json = await resp.json()
        if 'result' in resp_json and 'castHash' in resp_json['result']:
            cast_hash = resp_json['result']['castHash']
            return cast_hash, True
        else:
            logger.error(f"Error in recast: {resp_json}")
            return resp_json.get('errors', [{}])[0].get('message', 'Unknown error'), False

    async def get_img_upload_url(self):
        resp = await self.session.post(f"{API_V1_URL}{UPLOAD_URL_ENDPOINT}", json={})
        resp_json = await resp.json()
        return resp_json["result"]["url"]

    async def upload_img(self, file_path: str):
        upload_url = await self.get_img_upload_url()
        async with aiohttp.ClientSession() as session:
            async with session.post(upload_url, data={"file": open(file_path, "rb")}) as resp:
                resp_json = await resp.json()
                return next(
                    (url for url in resp_json["result"]["variants"] if "original" in url),
                    None,
                )

    async def get_random_img(self, file_path):
        if file_path:
            uploaded_img_url = await self.upload_img(file_path)
            return uploaded_img_url
        else:
            return None

