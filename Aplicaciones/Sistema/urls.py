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


    

    path('admin/dashboard/', views.dashboard_admin, name='dashboard_admin'),
    path('usuario/dashboard/', views.dashboard_usuario, name='dashboard_usuario'),

    # Perfil
    path('perfil/', views.ver_perfil, name='ver_perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('perfil/eliminar/', views.eliminar_perfil, name='eliminar_perfil'),


    path('administrador/emociones/', views.listar_emociones, name='listar_emociones'),
    path('administrador/emociones/nueva/', views.nueva_emocion, name='nueva_emocion'),
    path('administrador/emociones/editar/<int:emocion_id>/', views.editar_emocion, name='editar_emocion'),
    path('administrador/emociones/eliminar/<int:emocion_id>/', views.eliminar_emocion, name='eliminar_emocion'),

    # URLs para sueños (USUARIO)
    path('usuario/suenos/', views.listar_suenos, name='listar_suenos'),
    path('usuario/suenos/nuevo/', views.nuevo_sueno, name='nuevo_sueno'),
    path('usuario/suenos/editar/<int:sueno_id>/', views.editar_sueno, name='editar_sueno'),
    path('usuario/suenos/eliminar/<int:sueno_id>/', views.eliminar_sueno, name='eliminar_sueno'),




    # ... otras rutas
    path('administrador/emociones/resumen-emociones/', views.dashboard_suenos_por_emocion, name='dashboard_suenos'),




    path('administrador/calendario/', views.calendario_suenos, name='calendario_suenos'),
    path('verSueno/<int:id>/', views.verSueno, name='verSueno')

]
