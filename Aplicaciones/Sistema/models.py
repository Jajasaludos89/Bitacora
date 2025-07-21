from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, Group, Permission

# --- ROL DE USUARIO ---
ROL_CHOICES = (
    ('Usuario', 'Usuario'),
    ('Administrador', 'Administrador'),
)

# --- MODELO PERSONALIZADO DE USUARIO ---
class Usuario(AbstractUser):
    telefono = models.CharField(max_length=10)
    direccion = models.TextField()
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='Usuario')
    verificado = models.BooleanField(default=False) 
    bloqueado = models.BooleanField(default=False)
    foto_perfil = models.ImageField(upload_to='usuarios/perfil/', null=True, blank=True)

    # Permisos y grupos (por compatibilidad)
    groups = models.ManyToManyField(
        Group,
        related_name='usuarios',
        blank=True,
        help_text='Grupos a los que pertenece el usuario.',
        verbose_name='grupos',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='usuarios_permisos',
        blank=True,
        help_text='Permisos específicos para el usuario.',
        verbose_name='permisos de usuario',
    )

    def __str__(self):
        return f"{self.username} ({self.rol})"

# --- EMOCIONES DOMINANTES ---
class Emocion(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']

# --- SUEÑOS REGISTRADOS POR USUARIOS ---
class Sueno(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, limit_choices_to={'rol': 'Usuario'})
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    emocion = models.ForeignKey(Emocion, on_delete=models.SET_NULL, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} - {self.usuario.username}"

    class Meta:
        ordering = ['-fecha_creacion']

from django.db import models
from django.utils import timezone
from datetime import timedelta

class VerificacionCorreo(models.Model):
    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE)
    codigo = models.CharField(max_length=6)
    creado_en = models.DateTimeField(auto_now_add=True)
    expirado = models.BooleanField(default=False)

    def esta_expirado(self):
        # El código expira a los 10 minutos
        return self.expirado or (timezone.now() > self.creado_en + timedelta(minutes=10))

    def __str__(self):
        return f"Verificación {self.codigo} para {self.usuario.username}"

# Modelo para registrar sesiones de usuario
class RegistroSesion(models.Model):
    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE)
    fecha_login = models.DateTimeField(auto_now_add=True)
    fecha_logout = models.DateTimeField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    exitoso = models.BooleanField(default=True)  # Por si quieres registrar intentos fallidos

    def __str__(self):
        estado = "cerrada" if self.fecha_logout else "abierta"
        fecha_str = self.fecha_login.strftime('%Y-%m-%d %H:%M:%S')
        return f"Sesión {estado} de {self.usuario.username} - {fecha_str}"

    class Meta:
        ordering = ['-fecha_login']
