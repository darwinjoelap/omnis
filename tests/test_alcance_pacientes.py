"""Alcance de pacientes: el médico ve los suyos; asistente y titular ven todos; la configuración puede abrirlo."""
from datetime import time, timedelta

from django.utils import timezone

from apps.agenda.models import Cita
from apps.clinica.consultas import abrir_consulta
from apps.core.permisos import Rol
from apps.equipo import servicios as equipo
from apps.equipo.models import Membresia
from apps.pacientes.models import Paciente
from apps.plataforma.models import Especialidad

from .base import BaseTest


class AlcancePacientesTest(BaseTest):
    def setUp(self):
        super().setUp()
        esp = Especialidad.objects.get(codigo='medicina_general')
        actor = Membresia.objects.get(usuario=self.titular)
        self.m_medico, clave = equipo.agregar(self.tenant, actor, 'drdos', 'Luis', 'Mar', Rol.MEDICO, especialidad=esp)
        self.m_medico.usuario.debe_cambiar_clave = False
        self.m_medico.usuario.save()
        self.medico = self.entrar(self.tenant, 'drdos', clave)
        m_asis, clave_a = equipo.agregar(self.tenant, actor, 'recepcion', 'Ana', 'Gil', Rol.ASISTENTE)
        m_asis.usuario.debe_cambiar_clave = False
        m_asis.usuario.save()
        self.asistente = self.entrar(self.tenant, 'recepcion', clave_a)
        perfil_titular = actor.perfil
        with self.en_tenant():
            self.de_titular = Paciente.objects.create(nombres='Ana', apellidos='Titular', sexo='F',
                                                      numero_documento='11222333')
            abrir_consulta(paciente=self.de_titular, profesional=perfil_titular)
            self.citado = Paciente.objects.create(nombres='Beto', apellidos='Citado', sexo='M')
            abrir_consulta(paciente=self.citado, profesional=perfil_titular)
            Cita.objects.create(paciente=self.citado, profesional=self.m_medico.perfil,
                                especialidad=self.m_medico.perfil.especialidad,
                                fecha=timezone.localdate() + timedelta(days=1), hora_inicio=time(9), hora_fin=time(9, 30))
            self.nuevo = Paciente.objects.create(nombres='Caro', apellidos='Nueva', sexo='F')
            self.del_medico = Paciente.objects.create(nombres='Dora', apellidos='Delmedico', sexo='F')
            abrir_consulta(paciente=self.del_medico, profesional=self.m_medico.perfil)

    def test_medico_ve_solo_sus_pacientes(self):
        r = self.medico.get('/pacientes/')
        self.assertContains(r, 'Citado')
        self.assertNotContains(r, 'Titular, Ana')
        self.assertNotContains(r, 'Ana Titular')
        self.assertNotContains(r, 'Mis pacientes')       # sin autorización no hay filtro «Todos»
        self.assertEqual(self.medico.get(f'/pacientes/{self.de_titular.pk}/').status_code, 403)
        self.assertEqual(self.medico.get(f'/pacientes/{self.citado.pk}/').status_code, 200)
        self.assertEqual(self.medico.get(f'/pacientes/{self.nuevo.pk}/').status_code, 200)   # nuevo, sin historia

    def test_paciente_nuevo_aparece_y_el_ajeno_no(self):
        r = self.medico.get('/pacientes/?q=a')
        self.assertContains(r, 'Nueva')               # sin historia: lo puede atender
        self.assertNotContains(r, 'Titular')          # con historia de otro médico y sin cita con él

    def test_asistente_y_titular_ven_todo(self):
        for cliente in (self.asistente, self.cliente):
            r = cliente.get('/pacientes/?ver=todos')
            self.assertContains(r, 'Titular')
            self.assertContains(r, 'Delmedico')
        self.assertContains(self.asistente.get('/pacientes/'), 'Delmedico')    # el asistente arranca en «todos»
        # el titular también es profesional: arranca en «mis pacientes» con opción «Todos»
        r = self.cliente.get('/pacientes/')
        self.assertContains(r, 'Mis pacientes')
        self.assertNotContains(r, 'Delmedico')

    def test_configuracion_autoriza_ver_todos(self):
        cfg = self.tenant.configuracion
        cfg.medicos_ven_todos_pacientes = True
        cfg.save()
        r = self.medico.get('/pacientes/')
        self.assertContains(r, 'Mis pacientes')
        self.assertNotContains(r, 'Titular')
        self.assertContains(self.medico.get('/pacientes/?ver=todos'), 'Titular')
        self.assertEqual(self.medico.get(f'/pacientes/{self.de_titular.pk}/').status_code, 200)
