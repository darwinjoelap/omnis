"""Modelos propios de pediatría: datos que se grafican y se cuentan (guía de especialidades §3)."""
from django.db import models

from apps.core.tenancy import TenantModel


class MedicionCrecimiento(TenantModel):
    """
    Una medición antropométrica con su evaluación OMS. Se escribe al guardar la sección «Antropometría» de una
    consulta (una por consulta) y alimenta las curvas y los reportes de estado nutricional.
    """
    paciente = models.ForeignKey('pacientes.Paciente', on_delete=models.CASCADE, related_name='mediciones')
    consulta = models.OneToOneField('clinica.Consulta', on_delete=models.CASCADE, null=True, blank=True,
                                    related_name='medicion_crecimiento')
    fecha = models.DateField('Fecha', db_index=True)
    edad_meses = models.DecimalField('Edad (meses)', max_digits=6, decimal_places=2, null=True, blank=True)
    peso_kg = models.DecimalField('Peso (kg)', max_digits=6, decimal_places=3, null=True, blank=True)
    talla_cm = models.DecimalField('Talla (cm)', max_digits=5, decimal_places=1, null=True, blank=True)
    pc_cm = models.DecimalField('Perímetro cefálico (cm)', max_digits=4, decimal_places=1, null=True, blank=True)
    imc = models.DecimalField('IMC', max_digits=5, decimal_places=2, null=True, blank=True)
    z_peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    p_peso = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    z_talla = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    p_talla = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    z_pc = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    p_pc = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    z_imc = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    p_imc = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    estado_nutricional = models.CharField('Estado nutricional (peso/edad)', max_length=40, blank=True, db_index=True)
    clasificacion_imc = models.CharField('Clasificación OMS (IMC/edad)', max_length=40, blank=True)
    clasificacion_talla = models.CharField('Talla para la edad', max_length=40, blank=True)

    class Meta:
        verbose_name = 'Medición de crecimiento'
        verbose_name_plural = 'Mediciones de crecimiento'
        ordering = ['paciente', 'fecha']
        indexes = [models.Index(fields=['tenant', 'paciente', 'fecha'], name='medicion_paciente_fecha')]

    def __str__(self):
        return f'{self.paciente} · {self.fecha:%d/%m/%Y}'


# ── Vacunas y pesquisas (de Pediae) ───────────────────────────────────────────

class CatalogoQuerySet(models.QuerySet):
    def visibles(self, tenant=None):
        """Las del sistema (esquema oficial) + las propias del consultorio activo."""
        from apps.core.tenancy import tenant_actual
        tenant = tenant or tenant_actual()
        filtro = models.Q(tenant__isnull=True)
        if tenant is not None:
            filtro |= models.Q(tenant=tenant)
        return self.filter(filtro, activa=True)


class Vacuna(models.Model):
    """Catálogo: sin consultorio = esquema del sistema (Pediae 0017); con consultorio = vacuna propia."""
    tenant = models.ForeignKey('plataforma.Tenant', on_delete=models.CASCADE, null=True, blank=True, related_name='+',
                               editable=False)
    nombre = models.CharField('Vacuna', max_length=100)
    enfermedad = models.CharField('Protege contra', max_length=200, blank=True)
    dosis = models.PositiveSmallIntegerField('N.º de dosis', default=1)
    edad_meses = models.PositiveSmallIntegerField('Edad recomendada (meses)', help_text='0 = al nacer.')
    edad_max_meses = models.PositiveSmallIntegerField('Edad máxima (meses)', null=True, blank=True,
                                                      help_text='Pasada esta edad sin aplicarse, queda atrasada.')
    grupo = models.CharField('Grupo / etapa', max_length=60, blank=True)
    anual = models.BooleanField('Anual', default=False, help_text='Admite una aplicación por año (p. ej. influenza).')
    orden = models.PositiveSmallIntegerField('Orden', default=100)
    activa = models.BooleanField('Activa', default=True)

    objects = CatalogoQuerySet.as_manager()

    class Meta:
        verbose_name = 'Vacuna'
        verbose_name_plural = 'Vacunas'
        ordering = ['edad_meses', 'orden', 'dosis']

    def __str__(self):
        return f'{self.nombre} (dosis {self.dosis})'

    @property
    def edad_texto(self):
        m = self.edad_meses
        if m == 0:
            return 'Al nacer'
        if m < 12:
            return f'{m} meses'
        a, r = divmod(m, 12)
        return f'{a} año{"s" if a > 1 else ""}' + (f' y {r} m' if r else '')


class VacunaAplicada(TenantModel):
    paciente = models.ForeignKey('pacientes.Paciente', on_delete=models.CASCADE, related_name='vacunas_aplicadas')
    vacuna = models.ForeignKey(Vacuna, on_delete=models.PROTECT, related_name='aplicaciones')
    fecha = models.DateField('Fecha de aplicación', null=True, blank=True)
    lote = models.CharField('Lote / laboratorio', max_length=60, blank=True)
    observaciones = models.CharField('Observaciones', max_length=300, blank=True)
    registrada_por = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='+')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Vacuna aplicada'
        verbose_name_plural = 'Vacunas aplicadas'
        ordering = ['vacuna__edad_meses', 'fecha']

    def __str__(self):
        return f'{self.paciente} · {self.vacuna}'


class Pesquisa(models.Model):
    tenant = models.ForeignKey('plataforma.Tenant', on_delete=models.CASCADE, null=True, blank=True, related_name='+',
                               editable=False)
    nombre = models.CharField('Pesquisa', max_length=100)
    descripcion = models.CharField('Descripción', max_length=200, blank=True)
    orden = models.PositiveSmallIntegerField('Orden', default=100)
    activa = models.BooleanField('Activa', default=True)

    objects = CatalogoQuerySet.as_manager()

    class Meta:
        verbose_name = 'Pesquisa'
        verbose_name_plural = 'Pesquisas'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre


class PesquisaRealizada(TenantModel):
    paciente = models.ForeignKey('pacientes.Paciente', on_delete=models.CASCADE, related_name='pesquisas_realizadas')
    pesquisa = models.ForeignKey(Pesquisa, on_delete=models.PROTECT, related_name='realizaciones')
    fecha = models.DateField('Fecha', null=True, blank=True)
    resultado = models.CharField('Resultado / comentario', max_length=300, blank=True)
    registrada_por = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='+')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pesquisa realizada'
        verbose_name_plural = 'Pesquisas realizadas'
        constraints = [models.UniqueConstraint(fields=['paciente', 'pesquisa'], name='pesquisa_unica_por_paciente')]

    def __str__(self):
        return f'{self.paciente} · {self.pesquisa}'
