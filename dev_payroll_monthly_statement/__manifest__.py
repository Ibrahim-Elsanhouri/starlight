# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

{
    'name': 'Payroll Monthly Statement in PDF or Excel',
    'version': '18.0.1.0',
    'sequence': 1,
    'category': 'Human Resources',
    'description':
        """
        This Module add below functionality into odoo

        Payroll Monthly Statement

    """,
    'summary': 'Payroll Monthly Statement Payroll Statement Report Payroll Monthly Excel Report Payroll Monthly Pdf Statement Odoo Payroll Statement Odoo Report',
    'depends': ['hr', 'hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'report/payroll_statement_report_template.xml',
        'report/payroll_statement_report_menu.xml',
        'wizard/monthly_statement.xml',
        ],
	'demo': [],
    'test': [],
    'css': [],
    'qweb': [],
    'js': [],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    
    #author and support Details
    'author': 'DevIntelle Consulting Service Pvt.Ltd',
    'website': 'https://www.devintellecs.com',    
    'maintainer': 'DevIntelle Consulting Service Pvt.Ltd', 
    'support': 'devintelle@gmail.com',
    'price':11.0,
    'currency':'EUR',
    #'live_test_url':'https://youtu.be/A5kEBboAh_k',
    'pre_init_hook' :'pre_init_check',

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
