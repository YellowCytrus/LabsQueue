import json
import asyncio
import os
import random
from django.conf import settings  # Добавляем импорт настроек
from django.urls import reverse, reverse_lazy
from django.contrib.auth.views import PasswordResetView
from telegram import Bot
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from django.http import HttpResponseRedirect, JsonResponse
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, logger
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.views.generic import CreateView, View
from .forms import CustomUserCreationForm, CustomPasswordResetForm, UserAvatarForm, EmailConfirmationForm, EmailForm
from .models import User, Subject, LabSession, QueueEntry, Schedule, UserSubject, RegistrationToken, UserLabProgress, \
    SubjectLabWork
from .serializers import UserSerializer, SubjectSerializer, LabSessionSerializer, QueueEntrySerializer
from django.utils import timezone
import uuid
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Не создаём пользователя сразу, сохраняем данные в сессии
            request.session['pending_user'] = {
                'username': form.cleaned_data['username'],
                'password': form.cleaned_data['password1'],  # Пароль уже проверен на совпадение в форме
            }
            messages.success(request, 'Давай настроим твой email.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'queue_site/register.html', {'form': form})


def register_email(request):
    # Проверяем, есть ли данные пользователя в сессии
    if 'pending_user' not in request.session:
        messages.error(request, 'Сессия истекла. Пожалуйста, начните регистрацию заново.')
        return redirect('register')

    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            # Генерируем 6-значный код
            code = str(random.randint(100000, 999999))
            # Сохраняем email и код в сессии
            request.session['email_verification'] = {
                'email': email,
                'code': code,
            }
            # Отправляем email с кодом
            subject = 'Подтверждение email для ПЛАКИ-ПЛАКИ'
            message = (
                f"Здравствуйте,\n\n"
                f"Ваш код подтверждения: {code}\n\n"
                f"Введите этот код на странице подтверждения.\n\n"
                f"Если вы не запрашивали регистрацию, просто проигнорируйте это письмо.\n\n"
                f"С уважением,\nКоманда ПЛАКИ-ПЛАКИ"
            )
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                messages.success(request, 'Код подтверждения отправлен на ваш email!')
            except Exception as e:
                messages.error(request, f'Ошибка при отправке email: {str(e)}')
                return redirect('register_email')
            # Сохраняем время отправки email
            request.session['email_sent_time'] = datetime.now().isoformat()
            return redirect('register_confirm_email')
    else:
        # Если есть email в сессии, предзаполняем форму
        initial_email = request.session.get('email_verification', {}).get('email', '')
        form = EmailForm(initial={'email': initial_email})
    return render(request, 'queue_site/register_email.html', {'form': form})


def register_confirm_email(request):
    # Проверяем, есть ли данные в сессии
    if 'pending_user' not in request.session or 'email_verification' not in request.session:
        if request.is_ajax():  # Для AJAX-запросов
            return JsonResponse({'success': False, 'error': 'Сессия истекла. Пожалуйста, начните регистрацию заново.'}, status=400)
        messages.error(request, 'Сессия истекла. Пожалуйста, начните регистрацию заново.')
        return redirect('register')

    pending_user = request.session['pending_user']
    verification_data = request.session['email_verification']
    email_from_session = verification_data.get('email', '')
    correct_code = verification_data.get('code', '')

    # Вычисляем, сколько времени осталось до повторной отправки
    time_left = settings.TIME_LEFT_TO_REPEAT_SENDING_EMAIL
    can_resend = False
    if 'email_sent_time' in request.session:
        sent_time = datetime.fromisoformat(request.session['email_sent_time'])
        elapsed_seconds = (datetime.now() - sent_time).total_seconds()
        time_left = max(0, settings.TIME_LEFT_TO_REPEAT_SENDING_EMAIL - int(elapsed_seconds))
        if elapsed_seconds >= settings.TIME_LEFT_TO_REPEAT_SENDING_EMAIL:
            can_resend = True

    if request.method == 'POST':
        # Проверяем, является ли запрос AJAX для повторной отправки
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            if 'resend' in data and data['resend'] and can_resend:
                # Генерируем новый код
                new_code = str(random.randint(100000, 999999))
                verification_data['code'] = new_code
                request.session['email_verification'] = verification_data
                # Отправляем новый код
                subject = 'Подтверждение email для ПЛАКИ-ПЛАКИ (повторная отправка)'
                message = (
                    f"Здравствуйте,\n\n"
                    f"Ваш новый код подтверждения: {new_code}\n\n"
                    f"Введите этот код на странице подтверждения.\n\n"
                    f"Если вы не запрашивали регистрацию, просто проигнорируйте это письмо.\n\n"
                    f"С уважением,\nКоманда ПЛАКИ-ПЛАКИ"
                )
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [verification_data['email']],
                        fail_silently=False,
                    )
                    # Обновляем время отправки
                    request.session['email_sent_time'] = datetime.now().isoformat()
                    return JsonResponse({'success': True})
                except Exception as e:
                    return JsonResponse({'success': False, 'error': str(e)}, status=500)
            return JsonResponse({'success': False, 'error': 'Недостаточно времени прошло для повторной отправки.'}, status=400)

        # Обычная отправка формы
        form = EmailConfirmationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            code = form.cleaned_data['code']
            if code == correct_code:
                # Создаём пользователя
                user = User.objects.create_user(
                    username=pending_user['username'],
                    password=pending_user['password'],
                    email=email
                )
                # Автоматически логиним пользователя
                user = authenticate(request, username=pending_user['username'], password=pending_user['password'])
                login(request, user)
                # Очищаем сессию
                request.session.pop('pending_user', None)
                request.session.pop('email_verification', None)
                request.session.pop('email_sent_time', None)
                messages.success(request, 'Регистрация успешно завершена!')
                # Перенаправляем на страницу с предложением привязки Telegram
                return redirect('register_telegram_prompt')
            else:
                messages.error(request, 'Неверный код подтверждения.')
                # Если email изменили, обновляем его в сессии
                if email != email_from_session:
                    verification_data['email'] = email
                    request.session['email_verification'] = verification_data
        # Если форма не валидна, сохраняем введённые данные
    else:
        # Предзаполняем форму email из сессии
        form = EmailConfirmationForm(initial={'email': email_from_session})

    return render(request, 'queue_site/register_confirm_email.html', {
        'form': form,
        'time_left': time_left,
    })


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Неверный логин или пароль.')
    return render(request, 'queue_site/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


def home_view(request):
    create_sessions()
    if request.user.is_authenticated:
        # Получаем предметы пользователя через UserSubject
        subjects = Subject.objects.filter(users__user=request.user)
        # Получаем сессии, связанные с предметами пользователя
        sessions = LabSession.objects.filter(
            subject__in=subjects,
            status__in=['pending', 'active']
        )
        queue_entries = QueueEntry.objects.filter(
            lab_session__in=sessions,
            student=request.user
        ).select_related('lab_session__subject')
    else:
        subjects = []
        sessions = []
        queue_entries = []

    return render(request, 'queue_site/home.html', {
        'subjects': subjects,
        'sessions': sessions,
        'user_queues': queue_entries
    })


@login_required
def join_queue(request, subject_id):
    if request.method == 'POST':
        # Проверяем, что предмет привязан к пользователю
        subject = get_object_or_404(Subject, id=subject_id)
        if not UserSubject.objects.filter(user=request.user, subject=subject).exists():
            messages.error(request, "Этот предмет не привязан к вашему аккаунту.")
            return redirect('home')

        # Проверяем, есть ли активная сессия для этого предмета на сегодня
        session = LabSession.objects.filter(
            subject=subject,
            start_time__date=timezone.now().date()
        ).first()

        if not session:
            # Если сессии нет, создаём новую на основе расписания
            schedule = Schedule.objects.filter(subject=subject).first()
            if schedule:
                start_dt = datetime.combine(timezone.now().date(), schedule.start_time)
                start_dt = timezone.make_aware(start_dt)
                end_dt = start_dt + timedelta(minutes=schedule.duration_minutes)
                session = LabSession.objects.create(
                    subject=subject,
                    start_time=start_dt,
                    end_time=end_dt,
                    status='pending'
                )
            else:
                messages.error(request, "Для этого предмета нет расписания.")
                return redirect('home')

        # Проверяем, не находится ли пользователь уже в очереди
        if QueueEntry.objects.filter(
                lab_session=session,
                student=request.user,
                status__in=['waiting', 'submitting']
        ).exists():
            messages.error(request, "Вы уже в очереди на этот предмет!")
        else:
            # Создаём запись в очереди
            entry = QueueEntry.objects.create(lab_session=session, student=request.user)
            if not session.current_submitter and session.status == 'active':
                entry.status = 'submitting'
                entry.start_time = timezone.now()
                entry.save()
                session.current_submitter = entry
                session.save()
            messages.success(request, "Вы встали в конец очереди!")
        return redirect('home')
    return redirect('home')


@login_required
def add_subject(request):
    if request.method == 'POST':
        # Проверяем, хочет ли пользователь добавить или удалить предметы
        if 'add_subjects' in request.POST:
            # Добавление новых предметов
            subject_ids = request.POST.getlist('subjects')
            for subject_id in subject_ids:
                subject = Subject.objects.get(id=subject_id)
                UserSubject.objects.get_or_create(user=request.user, subject=subject)
            messages.success(request, "Предметы успешно добавлены!")
        elif 'remove_subject' in request.POST:
            # Удаление предмета
            subject_id = request.POST.get('subject_id')
            subject = Subject.objects.get(id=subject_id)
            UserSubject.objects.filter(user=request.user, subject=subject).delete()
            messages.success(request, f"Предмет '{subject.name}' удалён из вашего списка.")

        return redirect('add_subject')

    # Получаем текущие предметы пользователя
    current_subjects = Subject.objects.filter(users__user=request.user)
    # Получаем предметы, которые ещё не привязаны к пользователю
    user_subjects = UserSubject.objects.filter(user=request.user).values_list('subject_id', flat=True)
    available_subjects = Subject.objects.exclude(id__in=user_subjects)
    context = {
        'current_subjects': current_subjects,
        'available_subjects': available_subjects,
    }
    return render(request, 'queue_site/add_subject.html', context)

def check_current_events(schedule_id):
    """Проверяет активность расписания и рассчитывает следующую дату"""
    try:
        schedule = Schedule.objects.get(id=schedule_id)
    except Schedule.DoesNotExist:
        print("Schedule не найден")
        return False, None

    now = timezone.localtime(timezone.now())
    print(f"Сейчас: {now}")

    current_week_parity = 'odd' if now.isocalendar()[1] % 2 == 1 else 'even'
    print(f"Текущая неделя: {current_week_parity}")

    days_ahead = (schedule.day_of_week - now.isoweekday() + 7) % 7
    next_date = now + timedelta(days=days_ahead)

    if days_ahead == 0 and now.time() > schedule.start_time:
        next_date += timedelta(weeks=1)

    if schedule.week_parity != 'all':
        next_week_parity = 'odd' if next_date.isocalendar()[1] % 2 == 1 else 'even'
        if schedule.week_parity != next_week_parity:
            next_date += timedelta(weeks=1)

    next_event = timezone.make_aware(
        datetime.combine(next_date.date(), schedule.start_time)
    )
    print(f"Следующее событие: {next_event}")

    start_datetime = timezone.make_aware(
        datetime.combine(now.date(), schedule.start_time)
    )
    end_datetime = start_datetime + timedelta(minutes=schedule.duration_minutes)
    is_active = start_datetime <= now <= end_datetime

    return is_active, next_event


@login_required
def queue_detail(request, session_id):
    try:
        session = LabSession.objects.select_related('subject').get(id=session_id)
        # Проверяем, что сессия связана с предметом пользователя
        if not UserSubject.objects.filter(user=request.user, subject=session.subject).exists():
            messages.error(request, "У вас нет доступа к этой сессии.")
            return redirect('home')

        queue_entries = QueueEntry.objects.filter(
            lab_session=session
        ).select_related('student').order_by('join_time')

        schedule = Schedule.objects.filter(
            subject=session.subject
        ).first()

        if schedule:
            is_active, next_event_date = check_current_events(schedule.id)
        else:
            is_active = session.start_time <= timezone.now() <= (session.end_time or timezone.now())
            next_event_date = None

        user_entry = queue_entries.filter(student=request.user).first()
        is_first = user_entry and user_entry.get_position() == 1

        if request.method == 'POST' and user_entry:
            user_entry.delete()
            messages.success(request, "Вы вышли из очереди!")

            if is_first and session.status == 'active':
                next_entry = queue_entries.filter(status='waiting').order_by('join_time').first()
                if next_entry:
                    next_entry.status = 'submitting'
                    next_entry.start_time = timezone.now()
                    next_entry.save()
                    session.current_submitter = next_entry
                else:
                    session.current_submitter = None
                session.save()
            return redirect('queue_detail', session_id=session_id)

        return render(request, 'queue_site/queue_detail.html', {
            'session': session,
            'queue_entries': queue_entries,
            'user_entry': user_entry,
            'is_first': is_first,
            'is_active': is_active,
            'next_event_date': next_event_date,
            'schedule': schedule,
            'now': timezone.now()
        })

    except LabSession.DoesNotExist:
        raise Http404("Сессия не найдена")
    except Exception as e:
        logger.error(f"Ошибка в queue_detail: {str(e)}")
        raise


@login_required
def complete_submission(request, entry_id):
    if request.method == 'POST':
        entry = QueueEntry.objects.get(id=entry_id, student=request.user)
        if entry.status == 'submitting':
            entry.status = 'completed'
            entry.end_time = timezone.now()
            entry.save()
            session = entry.lab_session
            next_entry = QueueEntry.objects.filter(lab_session=session, status='waiting').order_by('join_time').first()
            if next_entry:
                next_entry.status = 'submitting'
                next_entry.start_time = timezone.now()
                next_entry.save()
                session.current_submitter = next_entry
            else:
                session.current_submitter = None
                if not QueueEntry.objects.filter(lab_session=session, status__in=['waiting', 'submitting']).exists():
                    session.status = 'completed'
            session.save()
            messages.success(request, "Вы отметили, что защитили лабу!")
        return redirect('home')
    return redirect('home')


def create_sessions():
    now = timezone.now()
    current_day = now.weekday() + 1  # weekday() возвращает 0-6, а у нас 1-7
    week_number = now.isocalendar()[1]
    is_even_week = week_number % 2 == 0

    # Удаляем завершённые сессии
    completed_sessions = LabSession.objects.filter(end_time__lte=now, status='active')
    for session in completed_sessions:
        session.delete()

    # Создаём новые сессии на основе расписания
    schedules = Schedule.objects.filter(day_of_week=current_day)
    for schedule in schedules:
        if (schedule.week_parity == 'all' or
                (schedule.week_parity == 'even' and is_even_week) or
                (schedule.week_parity == 'odd' and not is_even_week)):
            local_start_dt = timezone.make_aware(
                datetime.combine(now.date(), schedule.start_time),
                timezone.get_current_timezone()
            )
            local_end_dt = local_start_dt + timedelta(minutes=schedule.duration_minutes)

            # Удаляем старую сессию на сегодня, если она есть
            LabSession.objects.filter(
                subject=schedule.subject,
                start_time__date=now.date()
            ).delete()

            # Создаём новую сессию
            new_session = LabSession.objects.create(
                subject=schedule.subject,
                start_time=local_start_dt,
                end_time=local_end_dt,
                status='active' if local_start_dt <= now <= local_end_dt else 'pending'
            )
            print(
                f"Создана сессия: Start {timezone.localtime(new_session.start_time)}, End {timezone.localtime(new_session.end_time)}")


from .bot import chat_ids


class CustomPasswordResetView(PasswordResetView):
    template_name = 'queue_site/password_reset_form.html'
    form_class = CustomPasswordResetForm
    success_url = reverse_lazy('password_reset_done')

    def post(self, request, *args, **kwargs):
        print("POST request received")
        form = self.get_form()
        if form.is_valid():
            print("Form is valid")
            return self.form_valid(form)
        else:
            print("Form is invalid:", form.errors)
            return self.form_invalid(form)

    async def send_telegram_message(self, telegram_id, message):
        bot_token = '7951386321:AAHxpTDG6yhTRl9ap2uazpy7vX_-9mv1HPw'
        bot = Bot(token=bot_token)
        try:
            await bot.send_message(chat_id=telegram_id, text=message)
            return True
        except Exception as e:
            return str(e)

    def form_valid(self, form):
        print("Processing form_valid")
        telegram_username = form.cleaned_data['username']
        print(f"Telegram Username: {telegram_username}")

        try:
            user = User.objects.get(telegram_username=telegram_username)
            print(f"User found: {user}")
        except User.DoesNotExist:
            messages.error(self.request, "Пользователь с таким Telegram username не найден.")
            return HttpResponseRedirect(self.get_success_url())

        if not user.telegram_username:
            messages.error(self.request,
                           "У этого пользователя не указан Telegram username. Обратитесь к администратору.")
            return HttpResponseRedirect(self.get_success_url())

        telegram_id = chat_ids.get(user.telegram_username.lstrip('@'))
        print(f"Looking for telegram_id for {user.telegram_username.lstrip('@')}, found: {telegram_id}")
        if not telegram_id:
            messages.error(self.request, "Вы не активировали бота. Пожалуйста, отправьте /start боту в Telegram.")
            return HttpResponseRedirect(self.get_success_url())

        form.save(
            use_https=self.request.is_secure(),
            token_generator=self.token_generator,
            request=self.request
        )

        uid = form.uid
        token = form.token

        domain = self.request.get_host()
        protocol = 'https' if self.request.is_secure() else 'http'
        reset_url = f"{protocol}://{domain}{reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})}"
        print(f"Reset URL: {reset_url}")

        message = (
            "Здравствуйте,\n\n"
            "Вы запросили сброс пароля для вашей учетной записи в ПЛАКИ-ПЛАКИ.\n\n"
            f"Пожалуйста, перейдите по следующей ссылке, чтобы сбросить пароль:\n{reset_url}\n\n"
            "Если вы не запрашивали сброс пароля, просто проигнорируйте это сообщение.\n\n"
            "С уважением,\nКоманда ПЛАКИ-ПЛАКИ"
        )

        send_error = asyncio.run(self.send_telegram_message(telegram_id, message))

        if send_error is not True:
            messages.error(self.request, f"Ошибка при отправке сообщения в Telegram: {send_error}")
            return HttpResponseRedirect(self.get_success_url())

        messages.success(self.request, "Сообщение с ссылкой для сброса пароля отправлено в Telegram.")
        return HttpResponseRedirect(self.get_success_url())


class CompleteSubmissionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            queue_entry_id = request.data.get('queue_site/queue_entry_id')

            queue_entry = QueueEntry.objects.get(id=queue_entry_id, student=request.user)

            if queue_entry.status != 'submitting':
                return Response({"error": "Вы сейчас не сдаёте."}, status=status.HTTP_400_BAD_REQUEST)

            queue_entry.status = 'completed'
            queue_entry.end_time = timezone.now()
            queue_entry.save()

            session = queue_entry.lab_session
            next_entry = QueueEntry.objects.filter(
                lab_session=session, status='waiting'
            ).order_by('join_time').first()

            if next_entry:
                next_entry.status = 'submitting'
                next_entry.start_time = timezone.now()
                next_entry.save()
                session.current_submitter = next_entry
            else:
                session.current_submitter = None

                if not QueueEntry.objects.filter(lab_session=session, status__in=['waiting', 'submitting']).exists():
                    session.status = 'completed'
            session.save()

            return Response({"message": "Защита успешно завершена."}, status=status.HTTP_200_OK)

        except QueueEntry.DoesNotExist:
            return Response({"error": "Запись не найдена или доступ запрещён."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'queue_site/register.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        # Не создаём пользователя сразу, сохраняем данные в сессии
        self.request.session['pending_user'] = {
            'username': form.cleaned_data['username'],
            'password': form.cleaned_data['password1'],
        }
        registration_token = form.registration_token
        registration_token.is_used = True
        registration_token.save()
        messages.success(self.request, 'Давай настроим твой email.')
        return HttpResponseRedirect(reverse('register_email'))


class CheckTelegramUsernameView(View):
    def get(self, request, token):
        try:
            registration_token = RegistrationToken.objects.get(token=token, is_used=False)
            print(f"Found token: {registration_token}, telegram_username: {registration_token.telegram_username}")
            return JsonResponse({
                'telegram_username': registration_token.telegram_username
            })
        except RegistrationToken.DoesNotExist:
            print(f"Token {token} not found")
            return JsonResponse({
                'telegram_username': None
            }, status=404)


class SubjectListView(APIView):
    def get(self, request):
        if request.user.is_authenticated:
            # Возвращаем только предметы, привязанные к пользователю
            subjects = Subject.objects.filter(users__user=request.user)
        else:
            subjects = Subject.objects.none()  # Для неаутентифицированных пользователей возвращаем пустой список
        serializer = SubjectSerializer(subjects, many=True)
        return Response(serializer.data)


class JoinQueueView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        lab_session_id = request.data.get('lab_session_id')
        student_id = request.data.get('student_id')
        try:
            lab_session = LabSession.objects.get(id=lab_session_id)
            student = User.objects.get(id=student_id)

            # Проверяем, что предмет сессии привязан к пользователю
            if not UserSubject.objects.filter(user=student, subject=lab_session.subject).exists():
                return Response({"error": "Этот предмет не привязан к пользователю."}, status=status.HTTP_403_FORBIDDEN)

            queue_entry = QueueEntry.objects.create(lab_session=lab_session, student=student)
            serializer = QueueEntrySerializer(queue_entry)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except (LabSession.DoesNotExist, User.DoesNotExist):
            return Response({"error": "Session or student not found"}, status=status.HTTP_404_NOT_FOUND)


from django.conf import settings

# queue_site/views.py

@login_required
def profile_view(request):
    user = request.user

    # Получаем все предметы пользователя через промежуточную модель UserSubject
    user_subjects = user.subjects.all()

    # Создаём словарь для хранения прогресса по предметам
    progress_by_subject = {}
    for user_subject in user_subjects:
        # Получаем объект Subject из UserSubject
        subject = user_subject.subject
        # Получаем все SubjectLabWork для данного предмета
        subject_lab_works = subject.lab_works.all()
        # Извлекаем LabWork из SubjectLabWork
        lab_works = [subject_lab_work.lab_work for subject_lab_work in subject_lab_works]
        # Убедимся, что для каждой лабораторной работы есть запись в UserLabProgress
        for lab_work in lab_works:
            UserLabProgress.objects.get_or_create(
                user=user,
                lab_work=lab_work,
                defaults={'is_completed': False}
            )
        # Получаем прогресс пользователя по этим лабораторным работам
        progress = UserLabProgress.objects.filter(user=user, lab_work__in=lab_works)
        # Сортируем по номеру лабораторной работы в порядке убывания
        progress = progress.order_by('-lab_work__number')
        progress_by_subject[subject] = progress

    if request.method == 'POST':
        avatar = request.FILES.get('avatar')
        default_avatar = request.POST.get('default_avatar')

        # Проверяем, является ли запрос AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if avatar:
            user.avatar = avatar
            user.save()
            message = 'Аватар успешно обновлён!'
            messages.success(request, message)
        elif default_avatar:
            user.avatar = default_avatar
            user.save()
            message = 'Аватар успешно обновлён!'
            messages.success(request, message)
        else:
            message = 'Ошибка: не выбран аватар.'
            messages.error(request, message)

        if is_ajax:
            # Возвращаем JSON-ответ для AJAX-запроса
            return JsonResponse({
                'status': 'success' if (avatar or default_avatar) else 'error',
                'message': message,
                'avatar_url': user.get_avatar_url(),
            })
        else:
            # Для обычного POST-запроса делаем редирект
            return redirect('profile')

    return render(request, 'queue_site/profile.html', {
        'progress_by_subject': progress_by_subject,
    })


@login_required
def toggle_lab_progress(request, progress_id):
    progress = get_object_or_404(UserLabProgress, id=progress_id, user=request.user)
    progress.is_completed = not progress.is_completed
    progress.save()
    message = f"Статус лабораторной работы '{progress.lab_work.title}' изменён на {'сдана' if progress.is_completed else 'не сдана'}."

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': message,
            'is_completed': progress.is_completed,
        })
    else:
        messages.success(request, message)
        return redirect('profile')


@login_required
def profile_settings(request):
    if request.method == 'POST':
        user = request.user
        new_telegram_username = request.POST.get('telegram_username', '')
        new_theme = request.POST.get('theme', 'white')  # По умолчанию белая тема
        print(f"Received POST data: telegram_username={new_telegram_username}, theme={new_theme}")  # Логируем данные

        user.telegram_username = new_telegram_username
        user.theme = new_theme
        user.save()
        print(f"User updated: telegram_username={user.telegram_username}, theme={user.theme}")  # Логируем после сохранения

        # Если это AJAX-запрос, возвращаем JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'telegram_username': user.telegram_username,
                'theme': user.theme
            })
        # Обычный POST-запрос
        messages.success(request, 'Настройки успешно сохранены!')
        return redirect('profile_settings')
    return render(request, 'queue_site/profile_settings.html')


@login_required
def link_telegram(request):
    telegram_link = None
    bot_username = "plaki_plaki_prod_bot"

    if not request.user.telegram_id:  # Генерируем ссылку только если Telegram не привязан
        # Создаём токен в базе
        from .models import TelegramLinkToken  # Импортируем модель
        token_obj = TelegramLinkToken.objects.create(user=request.user)
        print(f"Generated token: {token_obj.token} for user {request.user.username}")  # Лог для отладки
        # Формируем ссылку для Telegram
        telegram_link = f"https://t.me/{bot_username}?start={token_obj.token}"

    return render(request, 'queue_site/link_telegram.html', {
        'telegram_link': telegram_link,
        'bot_username': bot_username
    })


@login_required
def register_telegram_prompt(request):
    if request.method == 'POST':
        if 'skip' in request.POST:
            # Если пользователь нажал "Пропустить", перенаправляем на главную
            messages.info(request, 'Вы можете привязать Telegram позже в настройках профиля.')
            return redirect('home')
        elif 'link_telegram' in request.POST:
            # Если пользователь нажал "Привязать Telegram", перенаправляем на страницу привязки
            return redirect('link_telegram')

    return render(request, 'queue_site/register_telegram_prompt.html')