import openai
from data.config import GPT_API_KEY, GPT_MODEL, GPT_LANGUAGE, GPT_MAX_SYMBOL_COMMENT, GPT_MAX_SYMBOL_POST, GPT_PROXY, GPT_TEMPERATURE, GPT_STOP_WORDS, GPT_THEMES

openai.api_key = GPT_API_KEY
if GPT_PROXY:
    openai.proxy = GPT_PROXY

class GptClient:
    def __init__(self):
        pass

    async def get_post(self):
        response = await openai.ChatCompletion.acreate(
            model=GPT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": f"Напиши пост на {GPT_LANGUAGE} языке. Максимальная длина поста {GPT_MAX_SYMBOL_POST} символов. Тематика - {GPT_THEMES}."
                },
                {
                    "role": "user",
                    "content": f"Напиши мне пост на {GPT_LANGUAGE} языке без каких-либо дополнительных комментариев. Не используй хэштеги и символ решётки. Не нужно оборачивать текст в кавычки."
                },
            ],
            temperature=GPT_TEMPERATURE,
            stop=GPT_STOP_WORDS,
        )
        return response.choices[0].message["content"]

    async def get_context_comment(self, post: str):
        response = await openai.ChatCompletion.acreate(
            model=GPT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": f"Напиши комментарий на основе следующего поста на оригинальном языке поста. Максимальная длина комментария {GPT_MAX_SYMBOL_COMMENT} символов."
                },
                {
                    "role": "user",
                    "content": f"Пост: {post}\n\nКомментарий:"
                },
            ],
            temperature=GPT_TEMPERATURE,
            stop=GPT_STOP_WORDS,
        )
        return response.choices[0].message["content"]
