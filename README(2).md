
# ElectroQuery

Этот проект представляет собой веб-приложение "Электронная очередь", разработанное на Django. Ниже приведены инструкции для локального запуска, тестирования, настройки Telegram-бота и работы с админ-панелью.

## Оглавление

- [Первый запуск с нуля](#первый-запуск-с-нуля)
- [Запуск после обновления репозитория](#запуск-после-обновления-репозитория)
- [Настройка и запуск Telegram-бота](#настройка-и-запуск-telegram-бота)
- [Работа с админ-панелью](#работа-с-админ-панелью)
- [Дополнительные замечания](#дополнительные-замечания)

## Первый запуск с нуля

Если вы запускаете проект впервые, следуйте этим шагам, чтобы настроить всё с нуля:

### Клонирование репозитория

Склонируйте репозиторий с GitHub на вашу локальную машину:

```bash
git clone https://github.com/YellowCytrus/ElectroQueryVEnv.git
cd ElectroQueryVEnv
```

### Настройка виртуального окружения

Создайте и активируйте виртуальное окружение, чтобы изолировать зависимости проекта:

**Для Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**Для macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### Установка зависимостей

```bash
pip install -r requirements.txt
```

Если файл `requirements.txt` отсутствует, обратитесь к разработчику.

### Настройка базы данных

```bash
python manage.py makemigrations
python manage.py migrate
```

Если вы хотите создать суперпользователя, смотрите раздел [Работа с админ-панелью](#работа-с-админ-панелью).

### Сбор статических файлов

```bash
python manage.py collectstatic
```

### Запуск сервера

```bash
python manage.py runserver
```

Сайт будет доступен по адресу: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

### Тестирование

- Регистрация: `/register/`
- Вход: `/login/`
- Главная: `/`
- Профиль: `/profile/`
- Сброс пароля: `/password_reset/`
- Добавление предметов: `/add-subject/`

---

## Запуск после обновления репозитория

Если у вас уже есть локальный репозиторий, и вы обновляете его через `git pull`:

### Переход в папку проекта

```bash
cd путь/к/ElectroQueryVEnv
```

### Активация виртуального окружения

**Windows:**

```bash
venv\Scripts\activate
```

**macOS/Linux:**

```bash
source venv/bin/activate
```

### Обновление проекта

```bash
git pull origin main
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver
```

Проверьте функциональность сайта.

---

## Настройка и запуск Telegram-бота

### Получение токена

- Обратитесь к разработчику или создайте бота через @BotFather

### Настройка .env

Создайте файл `.env`:

```env
TELEGRAM_BOT_TOKEN=ваш_токен_бота
```

Убедитесь, что установлен пакет:

```bash
pip install python-dotenv
```

### Настройки в `settings.py`

```python
from dotenv import load_dotenv
import os

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
```

### Запуск бота

```bash
python bot.py
```

### Тестирование бота

- Укажите Telegram-username в профиле
- Выполните сброс пароля
- Проверьте Telegram

---

## Работа с админ-панелью

### Создание суперпользователя

```bash
python manage.py createsuperuser
```

### Запуск сервера

```bash
python manage.py runserver
```

Перейдите по адресу [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

### Что можно делать в админке:

- Управление пользователями
- Добавление предметов и лабораторных
- Просмотр очередей
- Отслеживание прогресса пользователей

---

## Дополнительные замечания

- Убедитесь, что Telegram-username указан
- Проверьте зависимости (например, `aiogram`)
- В админке будьте осторожны с удалением данных
