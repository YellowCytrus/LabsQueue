
# ElectroQuery

Проект представляет собой веб-приложение "Электронная очередь", разработанное на Django.

## 📋 Оглавление

- [Первый запуск с нуля](#первый-запуск-с-нуля)
- [Запуск после обновления репозитория](#запуск-после-обновления-репозитория)
- [Настройка и запуск Telegram-бота](#настройка-и-запуск-telegram-бота)
- [Работа с админ-панелью](#работа-с-админ-панелью)
- [Тестирование регистрации и привязки Telegram](#тестирование-регистрации-и-привязки-telegram)
- [Тестирование уведомлений через Telegram](#тестирование-уведомлений-через-telegram)

---

## 🚀 Первый запуск с нуля

### 1. Клонирование репозитория

```bash
git clone https://github.com/YellowCytrus/ElectroQueryVEnv.git
cd ElectroQueryVEnv
```

### 2. Настройка виртуального окружения

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

> ⚠️ Если файл `requirements.txt` отсутствует, обратитесь к разработчику.

### 4. Настройка базы данных

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Сбор статических файлов

```bash
python manage.py collectstatic
```

### 6. Запуск сервера

```bash
python manage.py runserver
```

Сайт будет доступен по адресу: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 🔁 Запуск после обновления репозитория

### 1. Переход в папку проекта

```bash
cd путь/к/ElectroQueryVEnv
```

### 2. Активация виртуального окружения

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 3. Обновление проекта

```bash
git pull origin main
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver
```

Проверьте работоспособность сайта.

---

## 🤖 Настройка и запуск Telegram-бота

### 1. Получение токена

Создайте бота через [@BotFather](https://t.me/BotFather) и получите токен.

### 2. Создание файла `.env`

```env
TELEGRAM_BOT_TOKEN=ваш_токен_бота
```

Убедитесь, что установлен пакет `python-dotenv`:

```bash
pip install python-dotenv
```

### 3. Подключение переменных окружения

В `settings.py` добавьте:

```python
from dotenv import load_dotenv
import os

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
```

### 4. Запуск бота

```bash
python manage.py runbot
```

---

## 🔐 Работа с админ-панелью

### 1. Создание суперпользователя

```bash
python manage.py createsuperuser
```

### 2. Запуск сервера

```bash
python manage.py runserver
```

Панель доступна по адресу: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

### Возможности админки:

- Управление пользователями (включая Telegram ID)
- Добавление предметов и лабораторных
- Просмотр очередей и прогресса

---

## 🧪 Тестирование регистрации и привязки Telegram

### Регистрация

1. Перейдите на `/register/`
2. Заполните форму (email, пароль, username)
3. Подтвердите email через ссылку в письме
4. Перейдите на `/register/telegram-prompt/` (можно пропустить)
5. Вход через `/login/`

### Привязка Telegram

1. Перейдите на `/link-telegram/` (авторизуйтесь)
2. Нажмите "Привязать Telegram"
3. Перейдите в Telegram, нажмите `/start`
4. Получите подтверждение
5. Обновите страницу — должно быть сообщение об успешной привязке

---

## 📩 Тестирование уведомлений через Telegram

1. Привяжите Telegram (см. выше)
2. Перейдите на `/password_reset/`
3. Введите email и отправьте форму
4. Проверьте Telegram — придёт уведомление

---
