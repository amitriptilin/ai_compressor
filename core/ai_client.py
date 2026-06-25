import asyncio
import logging
import aiohttp
from constants import CHUNK_SEPARATOR, API_TIMEOUT, MAX_RETRIES

logger = logging.getLogger(__name__)

async def process_chunks(
    chunks: list[str],
    compression_prompt: str,
    simplicity_prompt: str,
    api_key: str,
    progress_callback=None,
    max_concurrent: int = 5
) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    semaphore = asyncio.Semaphore(max_concurrent)
    results = [None] * len(chunks)
    total = len(chunks)
    completed = 0
    
    async def process_one(idx: int, chunk: str):
        nonlocal completed
        prompt = _build_prompt(chunk, compression_prompt, simplicity_prompt)
        payload = {
            "model": "deepseek/deepseek-chat",
            "messages": [{"role": "user", "content": prompt}]
        }
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with semaphore:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=API_TIMEOUT)) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                answer = data['choices'][0]['message']['content']
                                if answer:
                                    results[idx] = answer
                                    break
                            else:
                                text = await resp.text()
                                logger.warning(f"Ошибка API {resp.status}, попытка {attempt}/{MAX_RETRIES}: {text[:100]}")
                                await asyncio.sleep(3 * attempt)
            except asyncio.TimeoutError:
                logger.warning(f"Таймаут, попытка {attempt}/{MAX_RETRIES}")
                await asyncio.sleep(3 * attempt)
            except Exception as e:
                logger.warning(f"Сбой: {e}, попытка {attempt}/{MAX_RETRIES}")
                await asyncio.sleep(3 * attempt)
        else:
            logger.error(f"Не удалось обработать чанк {idx+1}")
            results[idx] = f"\n[Ошибка обработки фрагмента №{idx+1}]\n"
        
        completed += 1
        if progress_callback:
            progress_callback(completed, total)
    
    tasks = [process_one(i, chunk) for i, chunk in enumerate(chunks)]
    await asyncio.gather(*tasks)
    
    return CHUNK_SEPARATOR.join(results)

def _build_prompt(text: str, compression: str, simplicity: str) -> str:
    return f"""
Ты — профессиональный академический редактор. Твоя задача — переработать фрагмент научной/учебной работы.

ТРЕБОВАНИЯ К ОБРАБОТКЕ:
1. Степень сжатия: {compression}
2. Уровень сложности лексики: {simplicity}

Форматируй текст красиво: используй списки (знаки '-') и разделяй логические мысли абзацами.
Язык ответа: Русский.

Вот текст фрагмента для обработки:
---
{text}
---
"""