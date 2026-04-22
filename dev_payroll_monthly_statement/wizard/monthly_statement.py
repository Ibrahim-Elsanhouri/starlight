# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import models, fields, _
from odoo.exceptions import ValidationError
import calendar
from odoo.tools.misc import xlwt
from io import BytesIO
from odoo import api, fields, models
from xlwt import easyxf
import base64
from datetime import date, datetime
from collections import OrderedDict
from dateutil import rrule


class PayrollMonthlyStatement(models.TransientModel):
    _name = 'payroll.monthly.statement'

    def get_start_date(self):
        start_date = self.start_date.replace(day=1)
        return start_date

    def get_end_date(self):
        last_day_of_month = calendar.monthrange(self.end_date.year, self.end_date.month)[1]
        end_date = self.end_date.replace(day=last_day_of_month)
        return end_date

    def get_payslip_ids(self, employee_ids):
        start_date = self.get_start_date()
        end_date = self.get_end_date()
        payslip_ids = self.env['hr.payslip'].search([('employee_id', 'in', employee_ids),
                                                     ('date_from', '>=', start_date),
                                                     ('date_to', '<=', end_date),
                                                     ('state', 'in', ['done', 'paid'])])
        return payslip_ids

    def get_employee_ids(self):
        employee_ids = []
        if self.filter_by == 'employee':
            employee_ids = self.employee_ids.ids
        elif self.filter_by == 'department':
            employee_ids = self.env['hr.employee'].search([('department_id', 'in', self.department_ids.ids)]).ids
        else:
            employee_ids = self.env['hr.employee'].search([]).ids
        return employee_ids


    def print_monthly_payroll_statement(self):
        if self.filter_by == 'employee' and not self.employee_ids:
            raise ValidationError(_('''Please select Employees'''))
        if self.filter_by == 'department' and not self.department_ids:
            raise ValidationError(_('''Please select Departments'''))
        employee_ids = self.get_employee_ids()
        payslip_ids = self.get_payslip_ids(employee_ids)
        if not payslip_ids:
            raise ValidationError(_('''Payslip Not Found !'''))
        return self.env.ref('dev_payroll_monthly_statement.menu1_tmpl1_dev_payroll_monthly_statement').report_action(self)

    def _get_default_start_date(self):
        start_date = date.today().replace(day=1)
        return start_date

    def _get_default_end_date(self):
        last_day_of_month = calendar.monthrange(date.today().year, date.today().month)[1]
        end_date = date.today().replace(day=last_day_of_month)
        return end_date

    def get_rule_list(self):
        employee_ids = self.get_employee_ids()
        payslip_ids = self.get_payslip_ids(employee_ids)
        sql_query = """select psl.salary_rule_id as rule_id from hr_payslip_line as psl join hr_payslip as ps on ps.id = psl.slip_id join hr_salary_rule as salaryrule on psl.salary_rule_id = salaryrule.id  where ps.id in %s and salaryrule.appears_on_payslip = 't'"""
        params = (tuple(payslip_ids.ids),)
        self.env.cr.execute(sql_query, params)
        results = self.env.cr.dictfetchall()
        rule_lst = [line.get('rule_id') for line in results]
        rule_ids = self.env['hr.salary.rule'].search([('id','in',rule_lst)], order='sequence')
        lst = []
        for rule in rule_ids:
            lst.append(rule.code)
        if lst:
            lst = list(OrderedDict.fromkeys(lst))
        return lst

    def get_month_wise_data(self, rule_list):
        month_wise = {}
        start_date = self.get_start_date()
        end_date = self.get_end_date()
        for month_date in rrule.rrule(rrule.MONTHLY, dtstart=start_date, until=end_date):
            month_wise.update({month_date.date(): rule_list})
        return month_wise

    def get_rule_total(self, mw_rule, m_date):
        start_date = m_date
        last_day_of_month = calendar.monthrange(m_date.year, m_date.month)[1]
        end_date = start_date.replace(day=last_day_of_month)
        employee_ids = self.get_employee_ids()
        sql_query = """select sum(hpl.total) from hr_payslip_line as hpl join hr_payslip as slip on hpl.slip_id=slip.id
         join hr_salary_rule as sr on hpl.salary_rule_id=sr.id where slip.employee_id in %s and slip.date_from >= %s and slip.date_to<= %s and slip.state in %s and sr.code = %s"""
        params = (tuple(employee_ids), start_date, end_date, ('paid', 'done'), mw_rule)
        self.env.cr.execute(sql_query, params)
        results = self.env.cr.dictfetchall()
        amount = results[0]['sum'] or 0.00
        return amount

    def get_all_total(self, code_name):
        start_date = self.get_start_date()
        end_date = self.get_end_date()
        employee_ids = self.get_employee_ids()
        sql_query = """select sum(hpl.total) from hr_payslip_line as hpl join hr_payslip as slip on hpl.slip_id=slip.id
                 join hr_salary_rule as sr on hpl.salary_rule_id=sr.id where slip.employee_id in %s and slip.date_from >= %s and slip.date_to<= %s and slip.state in %s and sr.code = %s"""
        params = (tuple(employee_ids), start_date, end_date, ('paid', 'done'), code_name)
        self.env.cr.execute(sql_query, params)
        results = self.env.cr.dictfetchall()
        amount = results[0]['sum'] or 0.00
        return amount

    def export_payroll_monthly_statement(self):
        employee_ids = self.get_employee_ids()
        payslip_ids = self.get_payslip_ids(employee_ids)
        if not payslip_ids:
            raise ValidationError(_('''Payslip Not Found !'''))
        filename = 'Payroll Statement Report.xls'
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Payroll Statement Report')
        worksheet.show_grid = False

        # defining various font styles
        header_style = easyxf('font:height 400; align: horiz center;font:bold True;')
        content = easyxf('font:height 200;')
        content_border_bold = easyxf('font:height 190;font:bold True;''borders: top thin,bottom thin,left thin, right thin;')
        content_border_right = easyxf('font:height 190;align: horiz right;''borders: top thin,bottom thin,left thin, right thin;')
        content_border_center = easyxf('font:height 190;align: horiz center;''borders: top thin,bottom thin,left thin, right thin;')
        sub_header = easyxf('font:height 210;align: horiz center;pattern: pattern solid, fore_color silver_ega;font:bold True;''borders: top thin,bottom thin,left thin, right thin')
        sub_header_right = easyxf('font:height 210;align: horiz right;pattern: pattern solid, fore_color silver_ega;font:bold True;''borders: top thin,bottom thin,left thin, right thin')
        # setting with of the column
        worksheet.col(0).width = 1200
        worksheet.col(1).width = 6500
        row_counter = 1
        if self.filter_by == 'employee':
            if len(self.employee_ids) == 1:
                worksheet.write(row_counter, 1, 'Employee', sub_header)
                worksheet.write(row_counter, 2, self.employee_ids.name, content)
                if self.employee_ids.barcode:
                    row_counter += 1
                    worksheet.write(row_counter, 1, 'Badge', sub_header)
                    worksheet.write(row_counter, 2, self.employee_ids.barcode, content)
        row_counter += 1
        worksheet.write_merge(row_counter, row_counter+1, row_counter, 7, 'Payroll Statement Report', header_style)
        row_counter += 2
        start = datetime.strptime(str(self.start_date), "%Y-%m-%d").strftime('%d-%m-%Y')
        end = datetime.strptime(str(self.end_date), "%Y-%m-%d").strftime('%d-%m-%Y')
        worksheet.write(row_counter, 1, 'From', sub_header)
        worksheet.write(row_counter, 2, start, content)
        row_counter += 1
        worksheet.write(row_counter, 1, 'To', sub_header)
        worksheet.write(row_counter, 2, end, content)

        column_counter = 0
        row_counter += 2
        worksheet.write(row_counter, column_counter, 'Sr.', sub_header)
        column_counter += 1
        worksheet.write(row_counter, column_counter, 'Month', sub_header)
        rule_list = self.get_rule_list()
        column_counter += 1
        for rule in rule_list:
            worksheet.write(row_counter, column_counter, rule, sub_header_right)
            worksheet.col(column_counter).width = 4500
            column_counter += 1
        row_counter += 1
        month_wise_data = self.get_month_wise_data(rule_list)
        sr_no = 1
        for m_date in month_wise_data:
            column_counter = 0
            worksheet.write(row_counter, column_counter, sr_no, content_border_center)
            sr_no += 1
            column_counter += 1
            m_name = m_date.strftime("%B")
            m_name = m_name + ' - ' + str(m_date.year)[-2:]
            worksheet.write(row_counter, column_counter, m_name, content_border_bold)
            column_counter += 1
            for mw_rule in month_wise_data[m_date]:
                amount = self.get_rule_total(mw_rule, m_date)
                worksheet.write(row_counter, column_counter, '{0:,.2f}'.format(amount), content_border_right)
                column_counter += 1
            row_counter += 1
        worksheet.write_merge(row_counter, row_counter, 0, 1, 'Total', sub_header)
        column_counter = 2
        for rule_code in rule_list:
            total = self.get_all_total(rule_code)
            worksheet.write(row_counter, column_counter, '{0:,.2f}'.format(total), sub_header_right)
            column_counter+= 1


        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        excel_file = base64.encodebytes(fp.read())
        fp.close()
        self.write({'excel_file': excel_file})
        active_id = self.ids[0]
        url = ('web/content/?model=payroll.monthly.statement&download=true&field=excel_file&id=%s&filename=%s' % (active_id, filename))
        if self.excel_file:
            return {'type': 'ir.actions.act_url',
                    'url': url,
                    'target': 'new'
                    }

    employee_ids = fields.Many2many('hr.employee', string='Employees')
    department_ids = fields.Many2many('hr.department', string='Departments')
    start_date = fields.Date(string='Start Date', required=True, default=_get_default_start_date)
    end_date = fields.Date(string='End Date', required=True, default=_get_default_end_date)
    filter_by = fields.Selection(string='Filter By', selection=[('employee', 'Employee'),
                                                                ('department', 'Department'),
                                                                ('all', 'All Employees')], default='all', requried=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id)
    excel_file = fields.Binary(string='Excel File')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: