{
    'name': 'Custom Order Lines Analytic Tracker',
    'version': '18.0.1.0.0',
    'category': 'Sales/Purchases',
    'summary': 'تتبع الحسابات التحليلية على مستوى بنود المبيعات والمشتريات بدون تأثير محاسبي',
    'depends': ['sale', 'purchase', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/custom_analytic_report_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}