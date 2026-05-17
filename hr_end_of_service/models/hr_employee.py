# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    end_of_service_request_ids = fields.One2many(
        'hr.end.of.service', 'employee_id', string='End of Service Requests')
    end_of_service_request_count = fields.Integer(
        string='End of Service Request Count',
        compute='_compute_end_of_service_request_count')

    def _compute_end_of_service_request_count(self):
        for record in self:
            record.end_of_service_request_count = len(
                record.end_of_service_request_ids)

    def action_view_end_of_service_requests(self):
        self.ensure_one()
        action = self.env.ref(
            'hr_end_of_service.action_hr_end_of_service').read()[0]
        action['domain'] = [('employee_id', '=', self.id)]
        action['context'] = {'default_employee_id': self.id}
        return action
