from odoo import fields, models

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    custom_analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='الحساب التحليلي (تتبع)',
        index=True
    )