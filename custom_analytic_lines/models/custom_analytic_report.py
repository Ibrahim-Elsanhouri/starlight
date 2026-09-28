from odoo import fields, models, tools

class CustomAnalyticReport(models.Model):
    _name = 'custom.analytic.report'
    _description = 'تقرير بنود المبيعات والمشتريات التحليلي'
    _auto = False
    _order = 'date desc'

    analytic_account_id = fields.Many2one('account.analytic.account', string='الحساب التحليلي', readonly=True)
    doc_type = fields.Selection([('sale', 'مبيعات'), ('purchase', 'مشتريات')], string='نوع العملية', readonly=True)
    partner_id = fields.Many2one('res.partner', string='العميل / المورد', readonly=True)
    product_id = fields.Many2one('product.product', string='المنتج', readonly=True)
    product_uom_qty = fields.Float(string='الكمية', readonly=True)
    price_subtotal = fields.Float(string='الإجمالي (بدون ضريبة)', readonly=True)
    date = fields.Date(string='التاريخ', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT 
                    sl.id AS id,
                    sl.custom_analytic_account_id AS analytic_account_id,
                    'sale' AS doc_type,
                    so.partner_id AS partner_id,
                    sl.product_id AS product_id,
                    sl.product_uom_qty AS product_uom_qty,
                    sl.price_subtotal AS price_subtotal,
                    so.date_order::date AS date
                FROM sale_order_line sl
                JOIN sale_order so ON sl.order_id = so.id
                WHERE sl.custom_analytic_account_id IS NOT NULL 
                  AND so.state IN ('sale', 'done')

                UNION ALL

                SELECT 
                    pl.id + 100000000 AS id,
                    pl.custom_analytic_account_id AS analytic_account_id,
                    'purchase' AS doc_type,
                    po.partner_id AS partner_id,
                    pl.product_id AS product_id,
                    pl.product_qty AS product_uom_qty,
                    pl.price_subtotal AS price_subtotal,
                    po.date_order::date AS date
                FROM purchase_order_line pl
                JOIN purchase_order po ON pl.order_id = po.id
                WHERE pl.custom_analytic_account_id IS NOT NULL 
                  AND po.state IN ('purchase', 'done')
            )
        """)