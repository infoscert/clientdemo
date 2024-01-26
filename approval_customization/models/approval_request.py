# -*- coding: utf-8 -*-

from odoo import fields, models, _


class ApprovalAmountLine(models.Model):
    _inherit = 'approval.amount.line'
    _description = 'Approval Amount Line'

    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', related="company_id.currency_id", string="Currency", readonly=True)
    amount = fields.Monetary("Amount", required=True)

