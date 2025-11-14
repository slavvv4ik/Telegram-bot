import os
import asyncio
import aiohttp
import logging
from telegram import Bot
from telegram.error import TelegramError
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeepSeekTelegramBot:
    def __init__(self):
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
        self.channel_id = '@FiveMinForYourself'  # Ваш канал
        
        # Проверка переменных окружения
        if not self.telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен")
        if not self.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY не установлен")
        
        self.bot = Bot(token=self.telegram_token)
        self.deepseek_url = "https://api.deepseek.com/chat/completions"  # Исправленный URL
        
    async def generate_rome_fact(self):
        """Генерация факта о Риме через DeepSeek API"""
        headers = {
            "Authorization": f"Bearer {self.deepseek_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user", 
                    "content": "сгенерируй текст для публикации его в телеграм-канал  под названием (5 минут на самосовершенствование) текст должен начинаться со слов (Потрать всего 5 минут на <что-то>.) и со следующего абзаца должен начинаться текст который расписывает как лучше это сделать, и почему это стоит сделать, примерно 80 слов. В следующем абзаце должны быть слова (Ты потратил всего лишь 5 минут, но стал намного лучше в <что-то о чем был текст>.) тематика этого текста должна быть о чем то таком, что действительно будет полезным для человека, и при повторной генерации текста его тема должна меняться в корне. в своем ответе не пиши ничего лишнего, только эти три абзаца которые я попросил"
                }
            ],
            "max_tokens": 300,
            "temperature": 0.7,
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.post(self.deepseek_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        fact = data['choices'][0]['message']['content'].strip()
                        logger.info("пост успешно сгенерирован")
                        return fact
                    else:
                        error_text = await response.text()
                        logger.error(f"DeepSeek API error: {response.status} - {error_text}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error("Timeout при обращении к DeepSeek API")
            return None
        except Exception as e:
            logger.error(f"Error generating fact: {e}")
            return None
    
    async def send_to_telegram_channel(self, message):
        """Отправка сообщения в Telegram канал"""
        try:
            # Обрезаем сообщение если оно слишком длинное для Telegram
            if len(message) > 4096:
                message = message[:4090] + "..."
                
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                parse_mode='HTML'
            )
            logger.info("Сообщение успешно отправлено в канал")
            return True
        except TelegramError as e:
            logger.error(f"Telegram error: {e}")
            return False
    
    async def scheduled_post(self):
        """Основная функция для планируемой публикации"""
        logger.info("Запуск плановой публикации...")
        
        # Генерация факта
        fact = await self.generate_rome_fact()
        
        if fact:
            # Форматируем сообщение для Telegram
            message = f"️ <b>5минут на себя.</b> ️\n\n{fact}\n\n<i>Обновлено: {datetime.now().strftime('%H:%M %d.%m.%Y')}</i>"
            
            # Отправка в канал
            success = await self.send_to_telegram_channel(message)
            
            if success:
                logger.info("Плановая публикация завершена успешно")
            else:
                logger.error("Не удалось отправить сообщение в канал")
        else:
            # Резервный факт на случай ошибки API
            backup_facts = [
                "Потрать всего 5 минут на то, чтобы очистить свой рабочий стол. Это простой, но действенный ритуал. Убери все лишнее, что отвлекает: пустые чашки, ненужные бумаги, старые заметки. Оставь только то, что необходимо для текущей задачи. Чистое рабочее пространство помогает сосредоточиться, снижает стресс и повышает продуктивность. Ты удивишься, насколько легче станет приступить к работе. Ты потратил всего лишь 5 минут, но стал намного лучше в организации своего рабочего пространства.."
            ]
            import random
            backup_fact = random.choice(backup_facts)
            message = f"️ <b>5 минут на себя.</b> ️\n\n{backup_fact}\n\n<i>Обновлено: {datetime.now().strftime('%H:%M %d.%m.%Y')}</i>"
            await self.send_to_telegram_channel(message)
            logger.info("Использован резервный факт")
    
    async def run_scheduler(self):
        """Бесконечный цикл с отправкой каждые 2 часа"""
        logger.info("Запуск планировщика...")
        while True:
            try:
                await self.scheduled_post()
                # Ожидание 2 часов (7200 секунд)
                logger.info("Ожидание 2 часа до следующей публикации...")
                await asyncio.sleep(7200)
            except Exception as e:
                logger.error(f"Критическая ошибка в планировщике: {e}")
                # Ждем 5 минут перед повторной попыткой
                await asyncio.sleep(300)

# Функция для запуска
async def main():
    try:
        bot = DeepSeekTelegramBot()
        await bot.run_scheduler()
    except Exception as e:
        logger.error(f"Не удалось запустить бота: {e}")

if __name__ == "__main__":
    asyncio.run(main())
