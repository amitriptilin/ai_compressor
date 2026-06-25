import getpass
import os

def get_api_key(interactive: bool = True, env_var: str = "OPENROUTER_API_KEY") -> str:
    if not interactive:
        key = os.getenv(env_var)
        if key:
            return key
        raise ValueError(f"Переменная окружения {env_var} не установлена, а интерактивный режим отключён.")
    
    print("\n" + "="*55)
    print("🔑  Для работы с нейросетью нужен API-ключ OpenRouter.")
    print("📌  Как получить ключ (бесплатно):")
    print("    1. Зарегистрируйся на https://openrouter.ai")
    print("    2. Перейди в раздел 'Keys' (https://openrouter.ai/keys)")
    print("    3. Нажми 'Create Key' и скопируй ключ (начинается с sk-or-v1-)")
    print("="*55)
    
    while True:
        key = getpass.getpass("👉 Введи API-ключ: ").strip()
        if key:
            return key
        print("❌ Ключ не может быть пустым. Попробуй снова.\n")