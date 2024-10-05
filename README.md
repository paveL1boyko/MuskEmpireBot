[![Static Badge](https://img.shields.io/badge/Telegram-Channel-Link?style=for-the-badge&logo=Telegram&logoColor=white&logoSize=auto&color=blue)](https://t.me/hidden_coding)

[![Static Badge](https://img.shields.io/badge/Telegram-Chat-yes?style=for-the-badge&logo=Telegram&logoColor=white&logoSize=auto&color=blue)](https://t.me/hidden_codding_chat)

[![Static Badge](https://img.shields.io/badge/Telegram-Bot%20Link-Link?style=for-the-badge&logo=Telegram&logoColor=white&logoSize=auto&color=blue)](https://t.me/muskempire_bot/game?startapp=hero6695971335)

# Бот для [Musk Empire](https://t.me/muskempire_bot/game?startapp=hero6695971335)

![img1](.github/images/start.png)

# Делает все
1. Решает ребусы загадки
2. Смотрит видео на ютубе
3. Прокачивает скилы по профиту те доход в час / на стоимость
4. Прокачивает скилы с тапами все качает до 30 лвла, а восстановление энергии до 50
5. Тапает
6. Можно включить PVP
7. Делает фонды по максимальной ставке для этого сохраняет деньги(на максимальную ставку), что бы сделать ее
8. Сбирает все награды

## Функционал


| Функция                                 | Поддерживается |
|-----------------------------------------|:--------------:|
| Многопоточность                         |       ✅        |
| Привязка прокси к сессии                |       ✅        |
| Задержка перед запуском каждой сессии   |       ✅        |
| Получение ежедневной награды            |       ✅        |
| Получение награды за друзей             |       ✅        |
| Получение награды за выполненные квесты |       ✅        |
| Получение оффлайн бонуса                |       ✅        |
| Автоматические тапы                     |       ✅        |
| PvP переговоры                          |       ✅        |
| Решение ежедневной загадки и ребуса     |       ✅        |
| Инвестирование в фонды (комбо на доход) |       ✅        |
| Авто прокачка                           |       ✅        |
| Docker                                  |       ✅        |

## Настройки

| Опция                   | Описание                                                                                  |
|-------------------------|-------------------------------------------------------------------------------------------|
| **API_ID / API_HASH**   | Данные платформы для запуска сессии Telegram                                              |
| **TAPS_ENABLED**        | Тапы включены дефолт `True` возможно(`False`)                                             |
| **TAPS_PER_SECOND**     | Рандомное число тапов в секунду (дефолт`[20,30]`)                                         |
| **PVP_ENABLED**         | PvP переговоры включены дефолт `True` возможно(`False`)                                   |
| **PVP_LEAGUE**          | Лига в переговорах дефолт`bronze` (`bronze`, `silver`, `gold`, `platina`, `diamond`)      |
| **PVP_STRATEGY**        | Стратегия в переговорах дефолт `random` возоможно(`aggressive`, `flexible`, `protective`) |
| **PVP_COUNT**           | Кол-во переговоров за цикл дефолт `10`                                                    |
| **INVEST_AMOUNT**       | Сумма для инвестирования в фонды дефолт `1400000`                                         |
| **SLEEP_BETWEEN_START** | Задержка перед запуском каждой сессии дефолт `[20, 360]`                                  |
| **ERRORS_BEFORE_STOP**  | Количество неудачных запросов, по достижению которых, бот остановится  дефолт `3`         |
| **USE_PROXY_FROM_FILE** | Использовать-ли прокси из файла `proxies.txt` дефолт `False` Тrue                         |
| **RANDOM_SLEEP_TIME**   | Время сна между событиями  дефолт `5`                                                     |
| **SKILL_WEIGHT**        | Значимость навыка отношение профита к стоимости прокачки(`0.00005`)                       |
| **MONEY_TO_SAVE**       | Минимальное кол-во монет по дефолу `1_000_000`                                            |
| **RANDOM_SLEEP_TIME**   | Время сна после завершения всех действий бота дефолт `[1300, 1700]`                       |


## Быстрый старт 📚

Для быстрой установки и последующего запуска - запустите файл run.bat на Windows или run.sh на Линукс

## Предварительные условия
Прежде чем начать, убедитесь, что у вас установлено следующее:
- [Python](https://www.python.org/downloads/) **версии 3.10**

## Получение API ключей
1. Перейдите на сайт [my.telegram.org](https://my.telegram.org) и войдите в систему, используя свой номер телефона.
2. Выберите **"API development tools"** и заполните форму для регистрации нового приложения.
3. Запишите `API_ID` и `API_HASH` в файле `.env`, предоставленные после регистрации вашего приложения.

## Установка
Вы можете скачать [**Репозиторий**](https://github.com/paveL1boyko/MuskEmpireBot.git) клонированием на вашу систему и установкой необходимых зависимостей:
```shell
git clone https://github.com/paveL1boyko/MuskEmpireBot.git
cd MuskEmpireBot
INSTALL.sh
START.sh
```

Затем для автоматической установки введите:

Windows:
```shell
INSTALL.bat
```

Linux:
```shell
INSTALL.sh
```

# Linux ручная установка
```shell
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
cp .env-example .env
nano .env  # Здесь вы обязательно должны указать ваши API_ID и API_HASH , остальное берется по умолчанию
python3 main.py
```

Также для быстрого запуска вы можете использовать аргументы, например:
```shell
~/MuskEmpireBot >>> python3 main.py --action (1/2)
# Or
~/MuskEmpireBot >>> python3 main.py -a (1/2)

# 1 - Запускает кликер
# 2 - Создает сессию
```


# Windows ручная установка
```shell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env-example .env
# Указываете ваши API_ID и API_HASH, остальное берется по умолчанию
python main.py
```

Также для быстрого запуска вы можете использовать аргументы, например:
```shell
~/MuskEmpireBot >>> python main.py --action (1/2)
# Или
~/MuskEmpireBot >>> python main.py -a (1/2)

# 1 - Запускает кликер
# 2 - Создает сессию
```