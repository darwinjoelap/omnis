from django.contrib import admin

from apps.core.admin import TenantModelAdmin

from .models import Servicio


@admin.register(Servicio)
class ServicioAdmin(TenantModelAdmin):
    list_display = ['nombre', 'tenant', 'precio_usd', 'activo']


from .models import Cargo, Pago, PagoAplicado  # noqa: E402

for modelo in (Cargo, Pago, PagoAplicado):
    admin.site.register(modelo, TenantModelAdmin)
