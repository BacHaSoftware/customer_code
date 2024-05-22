# -*- coding: utf-8 -*-

from datetime import timedelta
from odoo import models, fields, _, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.depends('contract_id', 'first_contract_date')
    def _compute_joining_date(self):
        for rec in self:
            rec.joining_date = rec.create_date.date() if rec.create_date else fields.Datetime.now()
            if rec.first_contract_date and rec.first_contract_date < rec.create_date.date():
                rec.joining_date = rec.first_contract_date

