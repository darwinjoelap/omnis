"""Fase 09: cargos, pagos, saldo a favor, caja y por cobrar."""
from datetime import time, timedelta
from decimal import Decimal

from django.utils import timezone

from apps.agenda.models import Cita, TipoCita
from apps.cobros import servicios as srv
from apps.cobros.models import Cargo, Pago, Servicio
from apps.core.excepciones import ErrorDeNegocio
from apps.core.permisos import Rol
from apps.equipo import servicios as equipo
from apps.equipo.models import Membresia
from apps.pacientes.models import Paciente
from apps.tasas.models import TasaCambio

from .base import BaseTest

D = Decimal


class CobrosTest(BaseTest):
    def setUp(self):
        super().setUp()
        TasaCambio.objects.create(fecha=timezone.localdate(), bs_por_usd=D('40'), fuente='MANUAL')
        with self.en_tenant():
            self.paciente = Paciente.objects.create(nombres='Elena', apellidos='Paz', sexo='F')
            self.consulta_srv = Servicio.objects.create(nombre='Consulta', precio_usd=D('50'))

    def test_pago_parcial_y_saldo(self):
        with self.en_tenant():
            cargo = srv.crear_cargo(paciente=self.paciente, servicio=self.consulta_srv, descripcion='',
                                    precio_usd=D('50'), descuento_usd=D('10'))
            self.assertEqual(cargo.tasa, D('40'))
            self.assertEqual(cargo.monto_usd, D('40.00'))
            srv.registrar_pago(paciente=self.paciente, monto=D('800'), moneda='BS', metodo='PAGO_MOVIL')
            cargo.refresh_from_db()
            self.assertEqual(cargo.estado, Cargo.Estado.PARCIAL)
            self.assertEqual(cargo.saldo_usd, D('20.00'))
            srv.registrar_pago(paciente=self.paciente, monto=D('20'), moneda='USD', metodo='EFECTIVO')
            cargo.refresh_from_db()
            self.assertEqual(cargo.estado, Cargo.Estado.PAGADO)
            self.assertEqual(srv.estado_cuenta(self.paciente)['saldo'], D('0'))

    def test_saldo_a_favor_se_aplica_al_proximo_cargo(self):
        with self.en_tenant():
            srv.registrar_pago(paciente=self.paciente, monto=D('100'), moneda='USD', metodo='ZELLE')
            self.assertEqual(srv.estado_cuenta(self.paciente)['a_favor'], D('100'))
            c = srv.crear_cargo(paciente=self.paciente, descripcion='Eco', precio_usd=D('60'))
            c.refresh_from_db()
            self.assertEqual(c.estado, Cargo.Estado.PAGADO)
            self.assertEqual(srv.estado_cuenta(self.paciente)['a_favor'], D('40'))

    def test_anular_pago_reabre_cargo(self):
        with self.en_tenant():
            c = srv.crear_cargo(paciente=self.paciente, descripcion='Consulta', precio_usd=D('50'))
            p = srv.registrar_pago(paciente=self.paciente, monto=D('50'), moneda='USD', metodo='EFECTIVO')
            with self.assertRaises(ErrorDeNegocio):
                srv.anular_cargo(c, 'error')
            with self.assertRaises(ErrorDeNegocio):
                srv.anular_pago(p, '')
            srv.anular_pago(p, 'Billete falso')
            c.refresh_from_db()
            self.assertEqual(c.estado, Cargo.Estado.PENDIENTE)
            srv.anular_cargo(c, 'Cortesía')
            self.assertEqual(srv.estado_cuenta(self.paciente)['saldo'], D('0'))

    def test_exonerado_queda_pagado(self):
        with self.en_tenant():
            c = srv.crear_cargo(paciente=self.paciente, descripcion='Control', precio_usd=D('30'), exonerado=True)
            self.assertEqual(c.estado, Cargo.Estado.PAGADO)
            self.assertEqual(srv.por_cobrar(), [])

    def test_descuento_mayor_al_precio(self):
        with self.en_tenant(), self.assertRaises(ErrorDeNegocio):
            srv.crear_cargo(paciente=self.paciente, descripcion='X', precio_usd=D('10'), descuento_usd=D('20'))

    def test_vistas_cuenta_caja_por_cobrar(self):
        url = f'/cobros/pacientes/{self.paciente.pk}/'
        self.assertEqual(self.cliente.get(url).status_code, 200)
        r = self.cliente.post(url, {'accion': 'cargo', 'servicio': self.consulta_srv.pk, 'descripcion': ''})
        self.assertEqual(r.status_code, 302)
        with self.en_tenant():
            self.assertEqual(Cargo.objects.get().precio_usd, D('50'))
        self.assertContains(self.cliente.get('/cobros/por-cobrar/'), 'Elena')
        r = self.cliente.post(url, {'accion': 'pago', 'monto': '1.000,00', 'moneda': 'BS', 'metodo': 'PAGO_MOVIL',
                                    'referencia': '1234'})
        self.assertEqual(r.status_code, 302)
        with self.en_tenant():
            self.assertEqual(Pago.objects.get().monto_usd, D('25.00'))
        r = self.cliente.get('/cobros/caja/')
        self.assertContains(r, 'Pago móvil')
        self.assertContains(r, 'Bs 1.000,00')
        self.assertContains(self.cliente.get(url), 'Debe $ 25,00')

    def test_atender_cita_con_servicio_genera_cargo(self):
        with self.en_tenant():
            perfil = Membresia.objects.get(usuario=self.titular).perfil
            tipo = TipoCita.objects.create(nombre='Consulta', duracion_min=30, servicio=self.consulta_srv)
            cita = Cita.objects.create(paciente=self.paciente, profesional=perfil, especialidad=perfil.especialidad,
                                       fecha=timezone.localdate() + timedelta(days=1), hora_inicio=time(9),
                                       hora_fin=time(9, 30), tipo=tipo)
        self.cliente.post(f'/agenda/citas/{cita.pk}/atender/')
        self.cliente.post(f'/agenda/citas/{cita.pk}/atender/')     # repetir no duplica
        with self.en_tenant():
            cargo = Cargo.objects.get()
            self.assertEqual(cargo.cita, cita)
            self.assertIsNotNone(cargo.consulta)
            self.assertEqual(cargo.monto_usd, D('50.00'))

    def test_asistente_puede_cobrar(self):
        actor = Membresia.objects.get(usuario=self.titular)
        m, clave = equipo.agregar(self.tenant, actor, 'caja', 'Ana', 'Gil', Rol.ASISTENTE)
        m.usuario.debe_cambiar_clave = False
        m.usuario.save()
        c = self.entrar(self.tenant, 'caja', clave)
        self.assertEqual(c.get('/cobros/caja/').status_code, 200)
        self.assertEqual(c.get(f'/cobros/pacientes/{self.paciente.pk}/').status_code, 200)
