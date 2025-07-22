from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from .models import Usuario, RegistroSesion, VerificacionCorreo, Emocion, Sueno

from Aplicaciones.Sistema.models import Usuario, Emocion, Sueno

from django.db.models import Count
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
import random
import json


# ------------------------ LOGIN ------------------------

def login(request):
    return render(request, "login/login.html")

def cerrarSesion(request):
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
    # Crear admin si no existe
    if not Usuario.objects.filter(username='admin').exists():
        Usuario.objects.create(
            username='admin',
            first_name='Admin',
            last_name='Root',
            email='admin@ejemplo.com',
            telefono='0000000000',
            direccion='-',
            rol='Administrador',
            verificado=True,
            bloqueado=False,
            password=make_password('12345')
        )

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

        # Registro de sesión
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        registro_sesion = RegistroSesion.objects.create(
            usuario=usuario,
            user_agent=user_agent,
            exitoso=True
        )
        request.session['registro_sesion_id'] = registro_sesion.id

        # Sesión
        request.session['usuario_id'] = usuario.id
        request.session['usuario_rol'] = usuario.rol
        request.session['usuario_username'] = usuario.username

        if usuario.rol == 'Administrador':
            return render(request, 'admin/panel_admin.html', {'usuario': usuario})
        elif usuario.rol == 'Usuario':
            return render(request, 'usuario/panel_usuario.html', {'usuario': usuario})
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
        foto_perfil = request.FILES.get('foto_perfil')

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
            password=make_password(password),
            foto_perfil=foto_perfil
        )

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

# ------------------------ PANELES POR ROL ------------------------

def panel_admin(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return redirect('login')

    return render(request, 'admin/panel_admin.html', {'usuario': usuario})

def panel_usuario(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return redirect('login')

    return render(request, 'usuario/panel_usuario.html', {'usuario': usuario})






# ------------------------------ # DASHBOARDS POR ROL ---------------------------------

def dashboard_admin(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return redirect('login')

    if usuario.rol != 'Administrador':
        messages.error(request, "No tienes permisos para acceder al panel de administrador.")
        return redirect('login')

    contexto = {
        'usuario': usuario,
        'mensaje': 'Bienvenido al panel del administrador',
    }
    return render(request, 'admin/panel_admin.html', contexto)


def dashboard_usuario(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return redirect('login')

    if usuario.rol != 'Usuario':
        messages.error(request, "No tienes permisos para acceder al panel de usuario.")
        return redirect('login')

    contexto = {
        'usuario': usuario,
        'mensaje': 'Bienvenido al panel de usuario',
    }
    return render(request, 'usuario/panel_usuario.html', contexto)


# -------------------- Perfil ------------------------

def ver_perfil(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return redirect('login')

    plantilla = 'admin/perfiladmin.html' if usuario.rol == 'Administrador' else 'usuario/perfilusuario.html'
    return render(request, plantilla, {'usuario': usuario})


def editar_perfil(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return redirect('login')

    if request.method == 'POST':
        usuario.first_name = request.POST.get('first_name')
        usuario.last_name = request.POST.get('last_name')
        usuario.email = request.POST.get('email')
        usuario.telefono = request.POST.get('telefono')
        usuario.direccion = request.POST.get('direccion')

        if request.FILES.get('foto_perfil'):
            usuario.foto_perfil = request.FILES.get('foto_perfil')

        usuario.save()
        messages.success(request, "Perfil actualizado correctamente.")
        return redirect('ver_perfil')

    plantilla = 'admin/editar_perfil_admin.html' if usuario.rol == 'Administrador' else 'usuario/editar_perfil_usuario.html'
    return render(request, plantilla, {'usuario': usuario})


def eliminar_perfil(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return redirect('login')

    if request.method == 'POST':
        usuario.delete()
        request.session.flush()
        messages.success(request, "Perfil eliminado correctamente.")
        return redirect('login')

    plantilla = 'admin/eliminar_perfil_admin.html' if usuario.rol == 'Administrador' else 'usuario/eliminar_perfil_usuario.html'
    return render(request, plantilla, {'usuario': usuario})




# ---------- VISTAS PARA EMOCIONES (Solo Admin) ------------

def listar_emociones(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = Usuario.objects.filter(id=usuario_id).first()
    if not usuario or usuario.rol != 'Administrador':
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('panel_usuario')

    emociones = Emocion.objects.all()
    return render(request, 'admin/emociones/listarEmociones.html', {'emociones': emociones})


def nueva_emocion(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = Usuario.objects.filter(id=usuario_id).first()
    if not usuario or usuario.rol != 'Administrador':
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('panel_usuario')

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()

        if not nombre:
            messages.error(request, "El nombre es obligatorio.")
            return render(request, 'admin/emociones/nuevaEmocion.html')

        if Emocion.objects.filter(nombre__iexact=nombre).exists():
            messages.warning(request, "Esa emoción ya existe.")
            return render(request, 'administrador/emociones/nuevaEmocion.html')

        Emocion.objects.create(nombre=nombre, descripcion=descripcion)
        messages.success(request, "Emoción registrada correctamente.")
        return redirect('listar_emociones')

    return render(request, 'admin/emociones/nuevaEmocion.html')


def editar_emocion(request, emocion_id):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = Usuario.objects.filter(id=usuario_id).first()
    if not usuario or usuario.rol != 'Administrador':
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('panel_usuario')

    emocion = get_object_or_404(Emocion, id=emocion_id)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()

        if not nombre:
            messages.error(request, "El nombre es obligatorio.")
            return render(request, 'admin/emociones/editarEmocion.html', {'emocion': emocion})

        emocion.nombre = nombre
        emocion.descripcion = descripcion
        emocion.save()

        messages.success(request, "Emoción actualizada correctamente.")
        return redirect('listar_emociones')

    return render(request, 'admin/emociones/editarEmocion.html', {'emocion': emocion})


def eliminar_emocion(request, emocion_id):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = Usuario.objects.filter(id=usuario_id).first()
    if not usuario or usuario.rol != 'Administrador':
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('panel_usuario')

    emocion = get_object_or_404(Emocion, id=emocion_id)
    emocion.delete()
    messages.success(request, "Emoción eliminada correctamente.")
    return redirect('listar_emociones')





# --------- VISTAS DE SUEÑOS (Usuario) ---------

def listar_suenos(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = Usuario.objects.get(id=usuario_id)
    suenos = Sueno.objects.filter(usuario=usuario)

    return render(request, 'usuario/sueno/listarSuenos.html', {'suenos': suenos})


def nuevo_sueno(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = Usuario.objects.get(id=usuario_id)
    emociones = Emocion.objects.all()

    if request.method == 'POST':
        titulo = request.POST['titulo']
        descripcion = request.POST['descripcion']
        emocion_id = request.POST.get('emocion')

        emocion = Emocion.objects.get(id=emocion_id) if emocion_id else None

        Sueno.objects.create(
            usuario=usuario,
            titulo=titulo,
            descripcion=descripcion,
            emocion=emocion
        )
        messages.success(request, "Sueño registrado correctamente.")
        return redirect('listar_suenos')

    return render(request, 'usuario/sueno/nuevoSueno.html', {'emociones': emociones})


def editar_sueno(request, sueno_id):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = Usuario.objects.get(id=usuario_id)
    sueno = get_object_or_404(Sueno, id=sueno_id)

    if sueno.usuario != usuario:
        messages.error(request, "No puedes editar sueños que no te pertenecen.")
        return redirect('listar_suenos')

    emociones = Emocion.objects.all()

    if request.method == 'POST':
        sueno.titulo = request.POST['titulo']
        sueno.descripcion = request.POST['descripcion']
        emocion_id = request.POST.get('emocion')

        sueno.emocion = Emocion.objects.get(id=emocion_id) if emocion_id else None
        sueno.save()

        messages.success(request, "Sueño actualizado correctamente.")
        return redirect('listar_suenos')

    return render(request, 'usuario/sueno/editarSueno.html', {'sueno': sueno, 'emociones': emociones})


def eliminar_sueno(request, sueno_id):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    sueno = get_object_or_404(Sueno, id=sueno_id)

    if sueno.usuario_id != usuario_id:
        messages.error(request, "No puedes eliminar sueños que no te pertenecen.")
        return redirect('listar_suenos')

    sueno.delete()
    messages.success(request, "Sueño eliminado correctamente.")
    return redirect('listar_suenos')





# --------------------------- Chart js -------------------------------

def dashboard_suenos_por_emocion(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = Usuario.objects.get(id=usuario_id)
    if usuario.rol != 'Administrador':
        messages.error(request, "No tienes permisos para esta sección.")
        return redirect('login')

    # Conteo de sueños agrupados por emocion
    datos = Sueno.objects.values('emocion__nombre').annotate(total=Count('id')).order_by('emocion__nombre')

    # Preparar listas para labels y datos
    etiquetas = [item['emocion__nombre'] if item['emocion__nombre'] else 'Sin emoción' for item in datos]
    cantidades = [item['total'] for item in datos]

    contexto = {
        'usuario': usuario,
        'etiquetas': etiquetas,
        'cantidades': cantidades,
    }
    return render(request, 'admin/emociones/dashboard_suenos.html', contexto)




# ------------------------ Calendario ----------------------

def calendario_suenos(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    admin = Usuario.objects.get(id=usuario_id)
    if admin.rol != 'Administrador':
        messages.error(request, "No tienes permisos para esta sección.")
        return redirect('login')

    suenos = Sueno.objects.select_related('usuario').all()
    eventos = []

    for sueno in suenos:
        eventos.append({
            'id': sueno.id,
            'title': sueno.usuario.username,
            'start': sueno.fecha_creacion.isoformat()
        })

    return render(request, 'admin/calendario/calendario.html', {
        'usuario': admin,
        'eventos_json': json.dumps(eventos)
    })


# NUEVA FUNCIÓN: Visualizar/editar un sueño desde el calendario
def verSueno(request, id):
    sueno = get_object_or_404(Sueno, id=id)
    usuarios = Usuario.objects.all()

    if request.method == 'POST':
        sueno.usuario_id = request.POST.get('usuario')
        sueno.titulo = request.POST.get('titulo')
        sueno.descripcion = request.POST.get('descripcion')
        sueno.fecha_creacion = request.POST.get('fecha_creacion')
        sueno.save()
        messages.success(request, "Sueño actualizado correctamente.")
        return redirect('calendario_suenos')

    return render(request, 'admin/calendario/verSueno.html', {
        'sueno': sueno,
        'usuarios': usuarios
    })


