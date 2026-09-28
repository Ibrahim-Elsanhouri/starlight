from odoo import fields, models

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    custom_analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='الحساب التحليلي (تتبع)',
        index=True
    )