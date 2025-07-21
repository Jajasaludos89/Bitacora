from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from .models import Usuario, RegistroSesion, VerificacionCorreo
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
import random

# ------------------------ LOGIN ------------------------

def login(request):
    return render(request, "login/login.html")

def cerrarSesion(request):
    # Marcar logout en registro de sesión si existe
    registro_sesion_id = request.session.get('registro_sesion_id')
    if registro_sesion_id:
        try:
            registro = RegistroSesion.objects.get(id=registro_sesion_id)
            registro.fecha_logout = timezone.now()
            registro.save()
        except RegistroSesion.DoesNotExist:
            pass
    request.session.flush()
    return redirect('login')

def iniciarSesion(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            usuario = Usuario.objects.get(username=username)
        except Usuario.DoesNotExist:
            messages.error(request, "El usuario no existe.")
            return render(request, 'login/login.html')

        if not check_password(password, usuario.password):
            messages.error(request, "Contraseña incorrecta.")
            return render(request, 'login/login.html')

        if usuario.bloqueado:
            messages.error(request, "Tu cuenta está bloqueada.")
            return render(request, 'login/login.html')

        if not usuario.verificado:
            messages.error(request, "Primero debes verificar tu correo.")
            return render(request, 'login/login.html')

        # Crear registro de sesión (login exitoso)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        registro_sesion = RegistroSesion.objects.create(
            usuario=usuario,
            user_agent=user_agent,
            exitoso=True
        )
        request.session['registro_sesion_id'] = registro_sesion.id

        # Guardar datos en sesión
        request.session['usuario_id'] = usuario.id
        request.session['usuario_rol'] = usuario.rol
        request.session['usuario_username'] = usuario.username

        # Redirección según rol
        if usuario.rol == 'Administrador':
            return redirect('panel_administrador')  # Ajustar URL según proyecto
        elif usuario.rol == 'Usuario':
            return redirect('bitacora_usuario')     # Ajustar URL según proyecto
        else:
            messages.error(request, "Rol no reconocido.")
            return render(request, 'login/login.html')

    return render(request, 'login/login.html')

def generar_codigo():
    return str(random.randint(100000, 999999))

def registrarUsuario(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, 'login/registrarUsuario.html')

        if Usuario.objects.filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya está en uso.")
            return render(request, 'login/registrarUsuario.html')

        if Usuario.objects.filter(email=email).exists():
            messages.error(request, "El email ya está registrado.")
            return render(request, 'login/registrarUsuario.html')

        usuario = Usuario.objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            telefono=telefono,
            direccion=direccion,
            rol='Usuario',
            password=make_password(password)
        )

        # Crear y enviar código de verificación
        codigo = generar_codigo()
        VerificacionCorreo.objects.create(usuario=usuario, codigo=codigo)

        try:
            send_mail(
                subject='Verifica tu correo',
                message=f'Tu código de verificación es: {codigo}',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[usuario.email],
                fail_silently=False,
            )
        except Exception as e:
            print("Error enviando correo:", e)
            messages.error(request, "No se pudo enviar el código de verificación.")
            return render(request, 'login/registrarUsuario.html')

        messages.success(request, "Usuario registrado. Revisa tu correo para verificar la cuenta.")
        return redirect('verificar_correo', usuario_id=usuario.id)

    return render(request, 'login/registrarUsuario.html')

def verificarCorreo(request, usuario_id):
    usuario = Usuario.objects.get(id=usuario_id)

    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        try:
            verificacion = VerificacionCorreo.objects.filter(usuario=usuario, expirado=False).latest('creado_en')
        except VerificacionCorreo.DoesNotExist:
            messages.error(request, "No se encontró un código válido.")
            return render(request, 'login/verificar_correo.html', {'usuario': usuario})

        if verificacion.esta_expirado():
            messages.error(request, "El código ha expirado.")
            return render(request, 'login/verificar_correo.html', {'usuario': usuario})

        if verificacion.codigo == codigo:
            usuario.verificado = True
            usuario.save()
            verificacion.expirado = True
            verificacion.save()
            messages.success(request, "Correo verificado. Ya puedes iniciar sesión.")
            return redirect('login')
        else:
            messages.error(request, "Código incorrecto.")

    return render(request, 'login/verificar_correo.html', {'usuario': usuario})

def reenviar_codigo(request, usuario_id):
    usuario = Usuario.objects.get(id=usuario_id)
    codigo = generar_codigo()
    VerificacionCorreo.objects.create(usuario=usuario, codigo=codigo)

    send_mail(
        subject='Nuevo código de verificación',
        message=f'Tu nuevo código es: {codigo}',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[usuario.email],
        fail_silently=False,
    )

    messages.success(request, "Nuevo código enviado.")
    return redirect('verificar_correo', usuario_id=usuario.id)
