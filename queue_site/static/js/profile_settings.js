// queue_site/static/js/profile_settings.js

document.addEventListener('DOMContentLoaded', function() {
    console.log('profile_settings.js loaded');

    // Переменные для отслеживания изменений
    let hasChanges = false;
    const originalTelegramUsername = document.getElementById('telegram_username').value;
    const originalTheme = document.getElementById('theme').value;

    // Функция для показа уведомления
    function showNotification(message, type = 'success') {
        const toastEl = document.getElementById('notification-toast');
        const toastBody = document.getElementById('notification-toast-body');

        if (!toastEl || !toastBody) {
            console.error('Toast elements not found. Falling back to alert.');
            alert(message);
            return;
        }

        toastBody.textContent = message;
        toastEl.classList.remove('toast-success', 'toast-error');
        toastEl.classList.add(`toast-${type}`);

        const toast = new bootstrap.Toast(toastEl, {
            autohide: true,
            delay: 5000
        });
        toast.show();

        toastEl.addEventListener('mouseenter', function() {
            toast._config.autohide = false;
        });

        toastEl.addEventListener('mouseleave', function() {
            toast._config.autohide = true;
            toast.hide();
        });
    }

    // Предпросмотр темы
    document.getElementById('theme').addEventListener('change', function() {
        const selectedTheme = this.value;
        console.log('Theme changed to:', selectedTheme);
        // Удаляем все текущие классы темы
        document.body.classList.remove('theme-white', 'theme-blue', 'theme-purple', 'theme-orange');
        // Добавляем новый класс темы
        document.body.classList.add(`theme-${selectedTheme}`);
        // Отмечаем, что есть изменения
        hasChanges = true;
    });

    // Отслеживание изменений в Telegram Username
    document.getElementById('telegram_username').addEventListener('input', function() {
        console.log('Telegram username changed to:', this.value);
        hasChanges = true;
    });

    // Предупреждение при попытке покинуть страницу
    window.addEventListener('beforeunload', function(event) {
        if (hasChanges) {
            event.preventDefault();
            event.returnValue = 'У вас есть несохранённые изменения. Вы уверены, что хотите уйти?';
        }
    });

    // Показ модального окна при клике на ссылки
    document.querySelectorAll('a[href]').forEach(link => {
        link.addEventListener('click', function(event) {
            if (hasChanges) {
                event.preventDefault();
                const targetUrl = this.href;
                const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
                modal.show();

                document.getElementById('save-changes-btn').onclick = function() {
                    document.getElementById('settings-form').submit();
                    modal.hide();
                };

                document.getElementById('discard-changes-btn').onclick = function() {
                    hasChanges = false;
                    document.getElementById('telegram_username').value = originalTelegramUsername;
                    document.getElementById('theme').value = originalTheme;
                    // Восстанавливаем исходную тему
                    document.body.classList.remove('theme-white', 'theme-blue', 'theme-purple', 'theme-orange');
                    document.body.classList.add(`theme-${originalTheme}`);
                    modal.hide();
                    window.location.href = targetUrl;
                };
            }
        });
    });

    // Отправка формы через AJAX
    document.getElementById('settings-form').addEventListener('submit', function(event) {
        event.preventDefault();
        const formData = new FormData(this);
        console.log('Submitting form with data:', Object.fromEntries(formData)); // Логируем данные формы

        fetch(this.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            console.log('Response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Response data:', data);
            if (data.success) {
                hasChanges = false;
                // Обновляем исходные значения
                document.getElementById('telegram_username').value = data.telegram_username;
                document.getElementById('theme').value = data.theme;
                showNotification('Настройки успешно сохранены!', 'success');
            } else {
                showNotification('Ошибка при сохранении настроек: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error during fetch:', error);
            showNotification('Произошла ошибка при сохранении настроек.', 'error');
        });
    });
});