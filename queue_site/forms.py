from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .models import User, RegistrationToken
import uuid


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.registration_token = RegistrationToken.objects.create()
        print(f"Created RegistrationToken: {self.registration_token.token}")

class CustomPasswordResetForm(PasswordResetForm):
    email = None
    username = forms.CharField(
        max_length=150,
        required=True,
        label="Имя пользователя",
        help_text="Введите ваше имя пользователя для сброса пароля."
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not User.objects.filter(telegram_username=username).exists():
            raise forms.ValidationError("Пользователь с таким именем не найден.")
        return username

    def save(self, domain_override=None, use_https=False, token_generator=None, request=None, **kwargs):
        telegram_username = self.cleaned_data['username']
        user = User.objects.get(telegram_username=telegram_username)
        self.uid = urlsafe_base64_encode(force_bytes(user.pk))
        self.token = token_generator.make_token(user)
        return user

class UserAvatarForm(forms.Form):
    avatar = forms.ImageField(
        label="Загрузить свою аватарку",
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )
    default_avatar = forms.ChoiceField(
        label="Или выберите дефолтную аватарку",
        choices=[
            ('avatars/defaults/avatar1.jpg', 'Аватар 1'),
            ('avatars/defaults/avatar2.jpg', 'Аватар 2'),
            ('avatars/defaults/avatar3.jpg', 'Аватар 3'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class EmailForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Введите ваш email'}),
        help_text="Введите ваш email для подтверждения."
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Этот email уже используется другим пользователем.")
        return email


class EmailConfirmationForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ваш email'}),
        help_text="Вы можете изменить email, если допустили ошибку."
    )
    code = forms.CharField(
        label="Код подтверждения",
        max_length=6,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите 6-значный код'}),
        help_text="Введите код, который был отправлен на ваш email."
    )

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if not code.isdigit() or len(code) != 6:
            raise forms.ValidationError("Код должен состоять из 6 цифр.")
        return code