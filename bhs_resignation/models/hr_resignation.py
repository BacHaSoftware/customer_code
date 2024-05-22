# -*- coding: utf-8 -*-
import datetime
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

date_format = "%Y-%m-%d"
RESIGNATION_TYPE = [('resigned', 'Normal Resignation'),
                    ('fired', 'Fired by the company'),
                    ('retired', 'Retired')]

class ResignationChecklist(models.Model):
    _name = 'hr.resignation.checklist'
    _description = 'Checklist by employee for the resignation'

    resignation_id = fields.Many2one('hr.resignation')
    check_box = fields.Boolean(default=False)
    name = fields.Char(string='Title', required=True, index=True)
    sequence = fields.Integer('Sequence', default=0)
    type = fields.Selection([('employee', 'By employee'),
                    ('manager', 'By manager'),
                    ('hr', 'By HR')], string='Type', default='employee')

    def write(self, vals):
        for checklist in self:
            if checklist.type == 'manager':
                if not self.env.user.has_group('hr.group_hr_user'):
                    raise ValidationError(_('You are not authorized to complete the checklist for manager!'))

            if checklist.type == 'hr':
                if not self.env.user.has_group('hr.group_hr_manager'):
                    raise ValidationError(_('You are not authorized to complete the checklist for HR manager!'))
        return super(ResignationChecklist, self).write(vals)

class ResignationChecklistTemplate(models.Model):
    _name = 'hr.resignation.checklist.template'
    _description = 'Template Checklist by employee for the resignation'

    name = fields.Char(string='Title', required=True, index=True)
    sequence = fields.Integer('Sequence', default=0)
    use_for = fields.Selection([('employee', 'For employee'),
                             ('trainee', 'For trainee')], string='Type', default='employee')
    type = fields.Selection([('employee', 'By employee'),
                    ('manager', 'By manager'),
                    ('hr', 'By HR')], string='Type', default='employee')

class HrResignation(models.Model):
    _inherit = 'hr.resignation'

    resignation_type = fields.Selection(selection=RESIGNATION_TYPE, help="Select the type of resignation: normal "
                                        "resignation or fired by the company", default='resigned')

    # checklist
    checklist_ids = fields.One2many('hr.resignation.checklist', 'resignation_id', required=True, ondelete="cascade")

    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirm'), ('manager_approved', 'Manager Approved'), ('handed_over', 'Handed over'),('approved', 'HR Approved'), ('cancel', 'Rejected')],
        string='Status', default='draft', track_visibility="always")

    complete_employee_checklist = fields.Boolean('Complete Employee Checklist')
    complete_manager_checklist = fields.Boolean('Complete Manager Checklist')
    complete_checklist = fields.Boolean('Complete Checklist')

    @api.model
    def create(self, vals):
        # assigning the sequence for the record
        if not vals.get('reason_html'):
            raise ValidationError(_('Reason is required!'))

        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.resignation') or _('New')
        res = super(HrResignation, self).create(vals)
        return res

    def confirm_resignation(self):
        if self.joined_date:
            if self.joined_date >= self.expected_revealing_date:
                raise ValidationError(_('Last date of the Employee must be anterior to Joining date'))
            for rec in self:
                rec.state = 'confirm'
                rec.resign_confirm_date = str(datetime.now())
                # TODO: gui mail thong bao xin nghi cua nhan vien cho manager va hr
                # SEND MAIL
                resignation_request_mail = self.env.ref('bhs_resignation.mail_template_confirm_resignation',
                                                  raise_if_not_found=False)
                if resignation_request_mail:
                    resignation_request_mail.sudo().send_mail(rec.id,
                                                        email_values={'email_to': rec.employee_id.parent_id.work_email},
                                                        force_send=True)
        else:
            raise ValidationError(_('Please set joining date for employee'))

    def manager_approved_resignation(self):
        if self.joined_date:
            if self.joined_date >= self.expected_revealing_date:
                raise ValidationError(_('Last date of the Employee must be anterior to Joining date'))
            for rec in self:
                # chuyen trang thai
                rec.state = 'manager_approved'
                #tao checklist ban giao cho nhan vien
                use_for = 'trainee' if rec.employee_id.employee_type != 'employee' else 'employee'

                checklist = self.env['hr.resignation.checklist.template'].search([('use_for','=',use_for),('type','=','employee')])
                checlist_vals = []
                for chk in checklist:
                    checlist_value = {
                        "name": chk.name,
                        "sequence": chk.sequence,
                        "type": chk.type
                    }
                    checlist_vals.append((0, 0, checlist_value))

                rec.checklist_ids = checlist_vals
                #TODO: gui mail thong bao don xin nghi da duoc duyet cho nhan vien
                #SEND MAIL
                resignation_mail = self.env.ref('bhs_resignation.mail_template_resignation_manager_approved',
                                                        raise_if_not_found=False)
                if resignation_mail:
                    resignation_mail.sudo().send_mail(rec.id,
                                                              email_values={
                                                                  'email_to': rec.employee_id.work_email},
                                                              force_send=True)

                # rec.resign_confirm_date = str(datetime.now())
        else:
            raise ValidationError(_('Please set joining date for employee'))

    def complete_hand_over_resignation(self):
        if self.joined_date:
            if self.joined_date >= self.expected_revealing_date:
                raise ValidationError(_('Last date of the Employee must be anterior to Joining date'))
            for rec in self:
                rec.complete_employee_checklist = True
                # check hoan thanh tat ca cac checklist employee
                for chk_emp in rec.checklist_ids:
                    if chk_emp.type == "employee":
                        chk_emp.check_box = True

                rec.state = 'handed_over'
                # tao checklist ban giao cho quan ly
                if not rec.checklist_ids.filtered(lambda r: r.type != 'employee'):
                    use_for = 'trainee' if rec.employee_id.employee_type != 'employee' else 'employee'

                    checklist = self.env['hr.resignation.checklist.template'].search(
                        [('use_for', '=', use_for), ('type', 'in', ('manager', 'hr'))])
                    checlist_vals = []
                    for chk in checklist:
                        checlist_value = {
                            "name": chk.name,
                            "sequence": chk.sequence,
                            "type": chk.type,
                            "check_box": False
                        }
                        checlist_vals.append((0, 0, checlist_value))

                    rec.checklist_ids = checlist_vals
                    # TODO: gui mail thong bao nhan vien da hoan thanh ban giao => manager va hr vao thuc hien nhung checklist con lai
                    # SEND MAIL
                    resignation_mail = self.env.ref('bhs_resignation.mail_template_resignation_handed_over',
                                                    raise_if_not_found=False)
                    if resignation_mail:
                        resignation_mail.sudo().send_mail(rec.id,
                                                          email_values={
                                                              'email_to': rec.employee_id.parent_id.work_email},
                                                          force_send=True)
        else:
            raise ValidationError(_('Please set joining date for employee'))

    # HAM XAC NHAN HOAN THANH CHECKLIST NHAN VIEN, TAO CHECKLIST QUAN LY
    @api.onchange("complete_employee_checklist")
    def onchange_complete_employee_checklist(self):
        for rec in self:
            if rec.complete_employee_checklist:
                #check hoan thanh tat ca cac checklist employee
                for chk_old in rec.checklist_ids:
                    if chk_old.type == "employee":
                        chk_old.check_box = True
            else:
                for chk1 in rec.checklist_ids:
                    if chk1.type == "employee":
                        chk1.check_box = False

    @api.onchange("complete_checklist")
    def onchange_complete_checklist(self):
        for rec in self:
            if rec.complete_checklist:
                # check hoan thanh tat ca cac checklist
                for chk in rec.checklist_ids:
                    chk.check_box = True

    def confirm_complete_manager_checklist(self):
        for rec in self:
            rec.complete_manager_checklist = True

    def reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'
            rec.employee_id.active = True
            rec.employee_id.resigned = False
            rec.employee_id.fired = False
            # ADD
            rec.employee_id.retired = False
            #xóa hết check list sau khi reset
            rec.checklist_ids = False
            # DONE

    def approve_resignation(self):
        for rec in self:
            if rec.expected_revealing_date and rec.resign_confirm_date:
                # XÁC NHẬN HOÀN THÀNH CHECKLIST
                rec.complete_checklist = True
                for chk in rec.checklist_ids:
                    chk.check_box = True

                #CUSTOM
                rec.state = 'approved'
                rec.approved_revealing_date = rec.expected_revealing_date

                contracts = self.sudo().env['hr.contract'].sudo().search([('employee_id', '=', self.employee_id.id)])

                for contract in contracts:
                    if contract.state == 'open':
                        rec.employee_contract = contract.name
                        rec.state = 'approved'
                        rec.approved_revealing_date = rec.resign_confirm_date + timedelta(days=contract.notice_days)
                    else:
                        rec.approved_revealing_date = rec.expected_revealing_date

                # # nhân viên chưa có hợp đồng
                # if not no_of_contract:
                #     rec.state = 'approved'

                # Changing state of the employee if resigning today
                rec._update_employee_status()
            else:
                raise ValidationError(_('Please enter valid dates.'))

    def update_employee_status(self):
        resignation = self.env['hr.resignation'].search([('state', '=', 'approved')])
        for rec in resignation:
            rec._update_employee_status()

    def _update_employee_status(self):
        if self.expected_revealing_date <= fields.Date.today() and self.employee_id.active:
            self.employee_id.active = False
            # Changing fields in the employee table with respect to resignation
            self.employee_id.resign_date = self.expected_revealing_date
            if self.resignation_type == 'resigned':
                self.employee_id.resigned = True
            # ADD:
            elif self.resignation_type == 'retired':
                self.employee_id.retired = True
            # DONE
            else:
                self.employee_id.fired = True

            # Removing and deactivating user
            if self.employee_id.user_id:
                self.employee_id.user_id.active = False
                self.employee_id.user_id = None

            # Expire contract
            current_contract = self.sudo().employee_id.contract_id
            self.sudo().employee_id.contract_ids.filtered(lambda c: c.state == 'draft').write({'state': 'cancel'})
            if current_contract and current_contract.state in ['open', 'draft']:
                self.sudo().employee_id.contract_id.write({'date_end': self.expected_revealing_date})
            if current_contract.state == 'open':
                current_contract.state = 'close'

            # Cancel future leaves
            future_leaves = self.env['hr.leave'].search([('employee_id', '=', self.employee_id.id),
                                                         ('date_to', '>', self.expected_revealing_date),
                                                         ('state', '!=', 'refuse')])
            future_leaves.write({'state': 'refuse'})

            # Archive allocation
            employee_allocations = self.env['hr.leave.allocation'].search([('employee_id', '=', self.employee_id.id)])
            employee_allocations.write({'date_to': self.expected_revealing_date})
            employee_allocations.write({'state': 'refuse'})
            employee_allocations.action_archive()

    @api.onchange('employee_id')
    @api.depends('employee_id')
    def check_request_existence(self):
        # Check whether any resignation request already exists
        for rec in self:
            if rec.employee_id:
                resignation_request = self.env['hr.resignation'].search([('employee_id', '=', rec.employee_id.id),
                                                                         ('state', 'in', ['confirm', 'approved'])])
                if resignation_request:
                    raise ValidationError(_('There is a resignation request in confirmed or'
                                            ' approved state for this employee'))

                no_of_contract = self.env['hr.contract'].sudo().search([('employee_id', '=', self.employee_id.id), ('state', '=', 'open')])
                if no_of_contract:
                    rec.employee_contract = no_of_contract[0].name
                    rec.notice_period = no_of_contract[0].notice_days
                else:
                    rec.employee_contract = False
                    rec.notice_period = False
            else:
                rec.employee_contract = False
                rec.notice_period = False

    def get_resignation_url(self):
        result = self.env['ir.actions.act_window']._for_xml_id('hr_resignation.view_employee_resignation')
        web_base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')  # must be https if not localhost
        return web_base_url + '/web#id=%s&model=%s&action=%s&view_type=form' % (self.id, 'hr.resignation',result['id'])

    def cancel_resignation(self):
        for rec in self:
            rec.state = 'cancel'
            # TODO: gui mail thong bao tu choi don xin nghi
            # SEND MAIL
            resignation_mail = self.env.ref('bhs_resignation.mail_template_resignation_reject',
                                            raise_if_not_found=False)
            if resignation_mail:
                resignation_mail.sudo().send_mail(rec.id,
                                                  email_values={
                                                      'email_to': rec.employee_id.work_email},
                                                  force_send=True)

    def reject_resignation(self):
        for rec in self:
            rec.state = 'cancel'
            # TODO: gui mail thong bao tu choi don xin nghi
            # SEND MAIL
            resignation_mail = self.env.ref('bhs_resignation.mail_template_resignation_reject',
                                            raise_if_not_found=False)
            if resignation_mail:
                resignation_mail.sudo().send_mail(rec.id,
                                                  email_values={
                                                      'email_to': rec.employee_id.work_email},
                                                  force_send=True)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # ADD
    retired = fields.Boolean(string="Retired", default=False, store=True, help="If checked then employee has retired")
