from odoo import models, fields, api
from datetime import datetime


class ResignationAuto(models.TransientModel):
    _inherit = 'hr.departure.wizard'

    # def action_register_departure(self):
    #     super(ResignationAuto, self).action_register_departure()
    #     vals = {
    #         'employee_id': self.employee_id.id,
    #         'expected_revealing_date': self.departure_date,
    #         'reason': self.departure_description,
    #         'reason_html': self.departure_description,
    #         'joined_date': self.sudo().employee_id.first_contract_date or self.employee_id.create_date,
    #         'employee_contract': self.sudo().employee_id.contract_id.name,
    #         'resignation_type': self.departure_reason_id.departure_code,
    #         'approved_revealing_date': datetime.now(),
    #         'notice_period': "0",
    #     }
    #     if self.employee_id.user_id:
    #         self.employee_id.user_id.active = False
    #     for equipment in self.employee_id.equipment_ids:
    #         if equipment.equipment_assign_to == 'employee':
    #             equipment.employee_id = None
    #             equipment.assign_date = None
    #         elif equipment.equipment_assign_to == 'other':
    #             equipment.employee_id = None
    #             equipment.department_id = None
    #             equipment.assign_date = None
    #     self.employee_id.equipment_ids = None
    #     ret = self.env['hr.resignation'].create(vals)
    #     ret.confirm_resignation()
    #     ret.approve_resignation()