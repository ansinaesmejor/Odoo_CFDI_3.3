# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import datetime
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)

class Contract(models.Model):
    _inherit = "hr.contract"
    
    periodicidad_pago = fields.Selection(
        selection=[('01', 'Diario'), 
                   ('02', 'Semanal'), 
                   ('03', 'Catorcenal'),
                   ('04', 'Quincenal'), 
                   ('05', 'Mensual'),
                   ('06', 'Bimensual'), 
                   ('07', 'Unidad obra'),
                   ('08', 'Comisión'), 
                   ('09', 'Precio alzado'), 
                   ('10', 'Pago por consignación'), 
                   ('99', 'Otra periodicidad'),],
        string=_('Periodicidad de pago CFDI'),
    )

    riesgo_puesto = fields.Selection(
        selection=[('1', 'Clase I'), 
                   ('2', 'Clase II'), 
                   ('3', 'Clase III'),
                   ('4', 'Clase IV'), 
                   ('5', 'Clase V'), 
                   ('99', 'No aplica'),],
        string=_('Riesgo del puesto'),
    )	
    sueldo_diario = fields.Float('Sueldo diario')
    sueldo_hora = fields.Float('Sueldo por hora')
    sueldo_diario_integrado = fields.Float('Sueldo diario integrado')
    sueldo_base_cotizacion = fields.Float('Sueldo base cotización')
    tablas_cfdi_id = fields.Many2one('tablas.cfdi','Tabla CFDI')

    bono_productividad = fields.Float('Bono productividad')
    bono_asistencia = fields.Float('Bono asistencia')
    bono_puntualidad = fields.Float('Bono puntualidad')

    infonavit_fijo = fields.Float('Infonavit (fijo)')
    infonavit_vsm = fields.Float('Infonavit (vsm)')

    infonavit_porc = fields.Float('Infonavit (%)')
    anticipo_sueldo = fields.Float('Anticipo sueldo')
    deduc_gral = fields.Float('Dedudcion general')
    prestamo_fonacot = fields.Float('Prestamo FONACOT')
    pago_de_serv = fields.Float('Pago de servicio')
    pens_alim = fields.Float('Pensión alimienticia')
    prest_financ = fields.Float('Prestamo financiero')
    prevision_social = fields.Float('Prevision Social')
    fondo_ahorro  = fields.Float('Fondo de ahorro')
#    dias_aguinaldo = fields.Float(string=_('Días de aguinaldo'), default='15')
    antiguedad_anos = fields.Float('Años de antiguedad', readonly=True)
    dias_base = fields.Float('Días base', default='90')
    dias_x_ano = fields.Float('Días por cada año trabajado', default='20')
    dias_totales = fields.Float('Total de días', readonly=True)
    indemnizacion = fields.Boolean("Indemnizar al empleado")
    dias_pendientes_pagar = fields.Float('Días a pagar')
    dias_vacaciones = fields.Float('Días de vacaciones')

    @api.multi
    @api.onchange('wage')
    def _compute_sueldo(self):
        if self.wage:
            values = {
            'sueldo_diario': self.wage/30,
            'sueldo_hora': self.wage/30/8,
            'sueldo_diario_integrado': self.calculate_sueldo_diario_integrado(),
            }
            self.update(values)
#    @api.one
#    @api.depends('dias_base', 'dias_x_ano', 'antiguedad_anos')
#    def _dias_totales(self):
#        self.dias_totales = self.antiguedad_anos * self.dias_x_ano + self.dias_base

    def calcular_liquidacion(self):
        if self.date_end:
            diff_date = (self.date_end - self.date_start + timedelta(days=1)).days
            years = diff_date /365.0
            self.antiguedad_anos = int(years)
            self.dias_totales = self.antiguedad_anos * self.dias_x_ano + self.dias_base

    @api.multi
    def button_dummy(self):
        self.calcular_liquidacion()
        return True
	
    @api.model 
    def calculate_sueldo_diario_integrado(self): 
        if self.date_start: 
            today = datetime.today().date()
            diff_date = (today - self.date_start + timedelta(days=1)).days
            years = diff_date /365.0
            #_logger.info('years ... %s', years)
            tablas_cfdi = self.tablas_cfdi_id 
            if not tablas_cfdi: 
                tablas_cfdi = self.env['tablas.cfdi'].search([],limit=1) 
            if not tablas_cfdi:
                return 
            if years < 1.0: 
                tablas_cfdi_lines = tablas_cfdi.tabla_antiguedades.filtered(lambda x: x.antiguedad >= years).sorted(key=lambda x:x.antiguedad) 
            else: 
                tablas_cfdi_lines = tablas_cfdi.tabla_antiguedades.filtered(lambda x: x.antiguedad <= years).sorted(key=lambda x:x.antiguedad, reverse=True) 
            if not tablas_cfdi_lines: 
                return 
            tablas_cfdi_line = tablas_cfdi_lines[0]
            max_sdi = tablas_cfdi.uma * 25
            sdi = ((365 + tablas_cfdi_line.aguinaldo + (tablas_cfdi_line.vacaciones)* (tablas_cfdi_line.prima_vac/100) ) / 365 ) * self.wage/30
            if sdi > max_sdi:
               sueldo_diario_integrado = max_sdi
            else:
               sueldo_diario_integrado = sdi
            #_logger.info('sueldo_diario_integrado ... %s max_sdi %s', tablas_cfdi.uma, max_sdi)
        else: 
            sueldo_diario_integrado = 0
        return sueldo_diario_integrado