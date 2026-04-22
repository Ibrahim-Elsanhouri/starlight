from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_saudi = fields.Boolean(string='Is Saudi?', default=False)
