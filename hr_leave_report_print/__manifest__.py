{
    'name': 'Leave Request Print Report',
    'version': '1.0',
    'category': 'Human Resources/Time Off',
    'summary': 'Simple module to print Leave Request details in PDF for Odoo Enterprise',
    'author': 'Gemini',
    'depends': ['hr_holidays'],
    'data': [
        'report/hr_leave_report_templates.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
