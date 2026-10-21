"""
Login por usuario dentro de un tenant.

- En el enlace de un tenant (/<slug>/) la vista deja `request.tenant_login`: se busca el usuario de ESE tenant.
- En la dirección principal y en /admin/ no hay tenant: solo entran cuentas de plataforma (sin tenant).
"""
from django.contrib.auth.backends import ModelBackend

from .models import Usuario, normalizar_usuario


class UsuarioPorTenantBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        tenant = getattr(request, 'tenant_login', None) if request is not None else None
        filtro = {'tenant_cuenta': tenant} if tenant is not None else {'tenant_cuenta__isnull': True}
        usuario = Usuario.objects.filter(username=normalizar_usuario(username), **filtro).first()
        if usuario is None:
            Usuario().set_password(password)      # mismo tiempo de respuesta exista o no
            return None
        if usuario.check_password(password) and self.user_can_authenticate(usuario):
            return usuario
        return None
