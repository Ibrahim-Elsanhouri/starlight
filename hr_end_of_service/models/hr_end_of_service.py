# -*- coding: utf-8 -*-
from datetime import date

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _


def _to_date(value):
    if isinstance(value, str):
        return fields.Date.from_string(value)
    return value


class HrEndOfService(models.Model):
    _name = 'hr.end.of.service'
    _description = 'HR End of Service Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True, tracking=True)
    contract_id = fields.Many2one(
        'hr.contract', string='Contract', readonly=True,
        compute='_compute_contract_id', store=True)
    request_date = fields.Date(
        string='Request Date', default=fields.Date.context_today,
        required=True, tracking=True)
    termination_date = fields.Date(
        string='Termination Date', required=True,
        default=fields.Date.context_today, tracking=True)
    relation_state = fields.Selection(
        [
            ('active', 'Active'),
            ('probation', 'Probation'),
            ('notice', 'Notice Period'),
            ('terminated', 'Terminated'),
        ],
        string='Employment Relationship', default='active',
        required=True, tracking=True)
    termination_reason = fields.Selection(
        [
            ('employer_termination', 'Termination by Employer'),
            ('employee_resignation', 'Employee Resignation'),
            ('fixed_term_end', 'End of Fixed Term'),
            ('mutual_agreement', 'Mutual Agreement'),
            ('dismissal_with_cause', 'Dismissal with Cause'),
        ],
        string='Termination Reason', required=True,
        default='employer_termination', tracking=True)
    salary = fields.Float(
        string='Basic Salary', required=True, tracking=True,
        help='Salary used to compute the end of service benefit.')
    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True,
        default=lambda self: self.env.company.currency_id)
    service_years = fields.Integer(
        string='Completed Years', compute='_compute_service_length',
        store=True)
    service_months = fields.Integer(
        string='Completed Months', compute='_compute_service_length',
        store=True)
    service_days = fields.Integer(
        string='Completed Days', compute='_compute_service_length',
        store=True)
    gross_entitlement = fields.Monetary(
        string='Gross End of Service', compute='_compute_entitlement',
        store=True)
    deductions = fields.Monetary(
        string='Deductions', default=0.0)
    net_entitlement = fields.Monetary(
        string='Net End of Service', compute='_compute_entitlement',
        store=True)
    notes = fields.Text(string='Notes')
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status', default='draft', tracking=True)

    @api.model
    def default_get(self, fields_list):
        res = super(HrEndOfService, self).default_get(fields_list)
        employee = self.env.context.get('default_employee_id')
        if employee:
            employee_rec = self.env['hr.employee'].browse(employee)
            contract = employee_rec.contract_id
            if contract and contract.wage:
                res.update({'salary': contract.wage})
        return res

    @api.depends('employee_id')
    def _compute_contract_id(self):
        for record in self:
            record.contract_id = record.employee_id.contract_id

    @api.depends('contract_id', 'termination_date')
    def _compute_service_length(self):
        for record in self:
            record.service_years = 0
            record.service_months = 0
            record.service_days = 0
            if not record.contract_id or not record.contract_id.date_start or not record.termination_date:
                continue
            start_date = _to_date(record.contract_id.date_start)
            end_date = _to_date(record.termination_date)
            if not start_date or not end_date or end_date < start_date:
                continue
            delta = relativedelta(end_date, start_date)
            record.service_years = delta.years
            record.service_months = delta.months
            record.service_days = delta.days

    def _calculate_total_service_months(self, years, months, days):
        return years * 12 + months + days / 30.0

    def _compute_total_entitlement_days(self, years, months, days):
        total_months = self._calculate_total_service_months(years, months, days)
        if total_months <= 0:
            return 0.0
        if total_months <= 60.0:
            return 15.0 * total_months / 12.0
        extra_months = total_months - 60.0
        return 105.0 + (30.0 * extra_months / 12.0)

    @api.depends('salary', 'termination_reason', 'service_years',
                 'service_months', 'service_days', 'deductions')
    def _compute_entitlement(self):
        for record in self:
            record.gross_entitlement = 0.0
            record.net_entitlement = 0.0
            if record.salary <= 0.0:
                continue
            total_days = record._compute_total_entitlement_days(
                record.service_years, record.service_months, record.service_days)
            gross = record.salary * total_days / 30.0
            factor = 1.0
            if record.termination_reason == 'employee_resignation':
                if record.service_years < 2:
                    factor = 0.0
                elif record.service_years < 5:
                    factor = 0.5
            elif record.termination_reason == 'dismissal_with_cause':
                factor = 0.0
            record.gross_entitlement = gross * factor
            record.net_entitlement = max(record.gross_entitlement - record.deductions, 0.0)

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for record in self:
            if record.employee_id:
                contract = record.employee_id.contract_id
                record.contract_id = contract
                if contract and contract.wage:
                    record.salary = contract.wage
                if not record.currency_id:
                    record.currency_id = self.env.company.currency_id

    def action_confirm(self):
        for record in self:
            record.state = 'confirmed'

    def action_done(self):
        for record in self:
            record.state = 'done'

    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'

    def action_reset_draft(self):
        for record in self:
            record.state = 'draft'
