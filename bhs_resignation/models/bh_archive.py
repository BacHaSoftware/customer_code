from odoo import models, fields, api


class DepartureCode(models.Model):
    _inherit = 'hr.departure.reason'

    departure_code = fields.Char(string='Code')


class ChangeReasonType(models.Model):
    _inherit = 'hr.resignation'

    reason_html = fields.Html(string="Reason", required=True)
    reason = fields.Html(string="Reason", required=False)
