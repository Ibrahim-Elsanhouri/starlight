# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import api, models
from datetime import datetime
import calendar


class PayrollStatementReport(models.AbstractModel):
    _name = 'report.dev_payroll_monthly_statement.tmpl1_prl_statement'

    def date_conversion(self, base_date):
        final_date = base_date
        if base_date:
            final_date = datetime.strptime(str(base_date), "%Y-%m-%d").strftime('%d-%m-%Y')
        return final_date

    def get_month_name(self, date):
        m_name = date.strftime("%B")
        m_name = m_name + ' - ' + str(date.year)[-2:]
        return m_name

    def _get_report_values(self, docids, data=None):
        docs = self.env['payroll.monthly.statement'].browse(docids)
        return {'doc_ids': docids,
                'doc_model': 'payroll.monthly.statement',
                'docs': docs,
                'date_conversion': self.date_conversion,
                'get_month_name': self.get_month_name,
                }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: