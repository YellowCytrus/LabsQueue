document.addEventListener('DOMContentLoaded', function() {
    const avatarInput = document.getElementById('avatar-input');
    const avatarPreview = document.getElementById('avatar-preview');
    const saveAvatarBtn = document.getElementById('save-avatar-btn');
    const defaultAvatarSelect = document.getElementById('default-avatar-select');
    let avatarChanged = false;

    // Показываем кнопку "Сохранить изменения", если аватар изменён
    function showSaveButton() {
        saveAvatarBtn.style.display = 'block';
    }

    // Обработчик клика по аватарке для выбора файла
    avatarPreview.addEventListener('click', function() {
        avatarInput.click();
    });

    // Предпросмотр аватарки при выборе файла
    avatarInput.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                avatarPreview.src = e.target.result;
                avatarChanged = true;
                showSaveButton();
            };
            reader.readAsDataURL(file);
        }
    });

    // Обработчик выбора дефолтной аватарки
    defaultAvatarSelect.addEventListener('change', function() {
        const selectedAvatar = defaultAvatarSelect.value;
        avatarPreview.src = `/media/${selectedAvatar}`;
        avatarChanged = true;
        showSaveButton();
    });

    // Показ модального окна при попытке уйти со страницы с несохранёнными изменениями
    const settingsLink = document.querySelector('.settings-btn');
    if (settingsLink) {
        settingsLink.addEventListener('click', function(event) {
            if (avatarChanged) {
                event.preventDefault();
                const confirmModal = new bootstrap.Modal(document.getElementById('confirmModal'));
                confirmModal.show();

                // Обработчик кнопки "Сохранить" в модальном окне
                document.getElementById('save-changes-btn').onclick = function() {
                    saveAvatarBtn.click();
                    confirmModal.hide();
                    window.location.href = settingsLink.href;
                };

                // Обработчик кнопки "Отменить изменения"
                document.getElementById('discard-changes-btn').onclick = function() {
                    avatarChanged = false;
                    confirmModal.hide();
                    window.location.href = settingsLink.href;
                };
            }
        });
    }

    // Сохранение аватарки через AJAX
    saveAvatarBtn.addEventListener('click', function() {
        const form = document.getElementById('avatar-form');
        const formData = new FormData(form);

        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                avatarPreview.src = data.avatar_url;
                avatarChanged = false;
                saveAvatarBtn.style.display = 'none';
                showToast('Аватар успешно обновлён!', 'success');
            } else {
                showToast(data.message || 'Ошибка при обновлении аватара.', 'error');
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            showToast('Произошла ошибка при обновлении аватара.', 'error');
        });
    });

    // Инициализация tooltip-ов для кнопок
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(element => {
        new bootstrap.Tooltip(element);
    });

    // Обработчик для кнопок "Отметить как сданную"/"Отменить сдачу"
    document.querySelectorAll('.toggle-lab-btn').forEach(button => {
        button.addEventListener('click', function() {
            const progressId = this.getAttribute('data-id');
            const url = this.getAttribute('data-url');

            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCsrfToken(),
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const card = document.getElementById(`lab-${progressId.split('-')[1]}-${progressId.split('-')[2]}`);
                    const title = card.querySelector('span');
                    const statusIcon = card.querySelector('i') || document.createElement('i');
                    const statusText = card.querySelector('small');

                    if (data.is_completed) {
                        card.classList.add('bg-light');
                        title.classList.add('text-muted');
                        button.classList.remove('btn-success');
                        button.classList.add('btn-outline-danger');
                        button.innerHTML = '<i class="bi bi-x-circle me-1"></i> Отменить сдачу';
                        button.setAttribute('title', 'Отменить сдачу');
                        if (statusText) statusText.remove();
                        statusIcon.className = 'bi bi-check-circle-fill text-success ms-2';
                        statusIcon.setAttribute('title', 'Сдано');
                        title.parentNode.appendChild(statusIcon);
                    } else {
                        card.classList.remove('bg-light');
                        title.classList.remove('text-muted');
                        button.classList.remove('btn-outline-danger');
                        button.classList.add('btn-success');
                        button.innerHTML = '<i class="bi bi-check-circle me-1"></i> Отметить как сданную';
                        button.setAttribute('title', 'Отметить как сданную');
                        if (statusIcon) statusIcon.remove();
                        const newStatusText = document.createElement('small');
                        newStatusText.className = 'text-muted ms-2';
                        newStatusText.textContent = 'ещё не сдана';
                        title.parentNode.appendChild(newStatusText);
                    }
                    showToast(data.message, 'success');
                } else {
                    showToast('Произошла ошибка.', 'error');
                }
            })
            .catch(error => {
                console.error('Ошибка:', error);
                showToast('Произошла ошибка при обновлении статуса.', 'error');
            });
        });
    });

    // Функция для получения CSRF-токена
    function getCsrfToken() {
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        const inputToken = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (metaToken) {
            return metaToken.getAttribute('content');
        } else if (inputToken) {
            return inputToken.value;
        } else {
            console.error('CSRF token not found in the page.');
            return '';
        }
    }

    // Функция для показа toast-уведомлений
    function showToast(message, type) {
        const toastEl = document.getElementById('notification-toast');
        const toastBody = document.getElementById('notification-toast-body');
        const toastHeader = toastEl.querySelector('.toast-header');

        toastBody.textContent = message;
        toastHeader.classList.remove('toast-success', 'toast-error');
        toastHeader.classList.add(type === 'success' ? 'toast-success' : 'toast-error');

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
});