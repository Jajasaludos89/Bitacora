from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path('iniciar-sesion/', views.iniciarSesion, name='iniciar_sesion'),
    path('cerrar-sesion/', views.cerrarSesion, name='cerrar_sesion'),

    path('registrar/', views.registrarUsuario, name='registrar_usuario'),

    path('verificar-correo/<int:usuario_id>/', views.verificarCorreo, name='verificar_correo'),
    path('reenviar-codigo/<int:usuario_id>/', views.reenviar_codigo, name='reenviar_codigo'),


    path('panel/admin/', views.panel_admin, name='panel_admin'),
    path('panel/usuario/', views.panel_usuario, name='panel_usuario'),

]
