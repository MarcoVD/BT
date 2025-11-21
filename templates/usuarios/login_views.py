from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, logout, login
from django.shortcuts import render, redirect
from django.views import View
from login.forms import LoginForm
from django.urls import reverse
from django.conf import settings

Usuario = get_user_model()

class LoginView(View):
    """Vista para inicio de sesión de usuarios con verificación y roles (FK)."""

    def get(self, request):
        form = LoginForm()
        return render(request, 'login.html', {'form': form})

    def post(self, request):
        form = LoginForm(data=request.POST)
        if not form.is_valid():
            return render(request, 'login.html', {'form': form})

        # Si tu formulario usa 'username' para el correo, dejamos 'username'
        email = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')

        # Si tu backend es el estándar y USERNAME_FIELD='email', 'username' es correcto
        user = authenticate(request, username=email, password=password)

        if user is None:
            messages.error(request, 'Correo o contraseña incorrectos. Intenta nuevamente.')
            return render(request, 'login.html', {'form': form})

        # ¿Puede iniciar sesión?
        if not getattr(user, 'can_login', True):
            if not getattr(user, 'email_verified', False):
                messages.warning(
                    request,
                    'Debes verificar tu correo electrónico antes de iniciar sesión. '
                    'Revisa tu bandeja de entrada o solicita un nuevo enlace de verificación.'
                )
                return render(request, 'login.html', {
                    'form': form,
                    'show_resend_verification': True,
                    'user_email': user.email
                })
            else:
                messages.error(request, 'Tu cuenta no está activa.')
                return render(request, 'login.html', {'form': form})

        # Ok: iniciar sesión
        login(request, user)

        # --- Redirecciones por rol (FK) ---
        # Normalizamos el nombre del rol; si el usuario aún no tiene rol asignado, será cadena vacía
        rol_nombre = ''
        if getattr(user, 'rol', None):
            # user.rol es instancia de catalogo.Roles; su nombre está en el campo 'rol'
            rol_nombre = (getattr(user.rol,'rol', '') or '').strip().lower()

        # Admin (por rol, o por permisos staff/superuser)
        if rol_nombre in ('administrador', 'admin') or user.is_staff or user.is_superuser:
            return redirect(reverse('admin:index'))

        # Interesado
        if rol_nombre == 'interesado':
            return redirect('interesado:perfil_interesado')

        # Reclutador
        if rol_nombre == 'reclutador':
            # Si tienes un OneToOne/ForeignKey user → Reclutador, y un campo 'aprobado'
            aprobado = getattr(getattr(user, 'reclutador', None), 'aprobado', False)
            if aprobado:
                return redirect('reclutador:dashboard')
            messages.warning(request, 'Tu cuenta de reclutador está pendiente de aprobación por un administrador.')
            logout(request)
            # Redirigimos al login para evitar un loop hacia el dashboard
            return redirect(settings.LOGIN_URL if hasattr(settings, 'LOGIN_URL') else 'login')

        # Fallback si no hay rol o es desconocido
        if hasattr(settings, 'LOGIN_REDIRECT_URL') and settings.LOGIN_REDIRECT_URL:
            return redirect(settings.LOGIN_REDIRECT_URL)
        return redirect('/')  # última opción
