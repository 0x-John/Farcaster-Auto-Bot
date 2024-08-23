# Telegram API (Получить https://my.telegram.org/auth)
API_ID = ''
API_HASH = ''
SESSION_NAME = 'Telegram_session'

# ChatGPT API (Получить https://platform.openai.com/api-keys)
GPT_API_KEY = ""
GPT_MODEL = "gpt-3.5-turbo"

# Конфигурация действий
WORK = {
    'POST': 'GPT',  # Возможные значения: "TG", "GPT", "NO"
    'LIKE': 'YES',   # Возможные значения: "YES", "NO"
    'COMMENT': 'GPT',  # Возможные значения: "FILE", "GPT", "NO"
    'FOLLOW': 'YES', # Возможные значения: "YES", "NO"
    'RECAST': 'YES' # Возможные значения: "YES", "NO"
}

# В каком разделе искать посты. Доступны 'home', 'trending', 'trending-frames', 'all-channels'.
FEED_KEY = "trending"

# Конфигурация генерации постов и комментариев с помощью ChatGPT. 
GPT_MAX_SYMBOL_COMMENT = 50
GPT_MAX_SYMBOL_POST = 320
GPT_LANGUAGE = "en"
GPT_THEMES = "криптовалюта"
GPT_PROXY = "http://"  # Прокси для работы с GPT http://username:password@host:port

# Лимит постов и задержка
DELAY_RANGE = [30, 45]  # Рандомная задержка между случайными действиями
POST_DELAY = [300, 600]  # Рандомная задержка между постами от и до (работает в режиме GPT)
POST_LIMIT = [2, 2]  # Рандомное количество постов от и до (работает в режиме GPT)

# Не трогай, убьет!
GPT_TEMPERATURE = 0.7
# Cтоп слова для gpt
GPT_STOP_WORDS = ["Комментарий:", "#"]


