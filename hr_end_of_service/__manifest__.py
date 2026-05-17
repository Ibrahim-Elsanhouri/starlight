# -*- coding: utf-8 -*-
{
    'name': 'HR End Of Service',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Compute Saudi end of service benefits by contract, service length and termination reason.',
    'description': 'Calculate end of service benefits in a structured request record using Saudi labor law conventions. Supports multiple termination reasons, employee relation states and contract-based salary.',
    'author': 'Gemini',
    'company': 'Gemini',
    'maintainer': 'Gemini',
    'website': 'https://example.com',
    'depends': ['hr', 'hr_contract'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_end_of_service_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'OPL-1',
}
