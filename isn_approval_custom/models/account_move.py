# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError



class AccountMove(models.Model):
    _inherit = 'account.move'
    
    isn_approval_id = fields.Many2one('approval.request', readonly=True, string='Approval')
    department_id = fields.Many2one('hr.department', copy=False)

# y
    # ag_debit = fields.Monetary(string='Debit', default=0.0, currency_field='currency_id')
    # ag_credit = fields.Monetary(string='Credit', default=0.0, currency_field='currency_id')


    # @api.onchange('ag_debit')
    # def _onchange_ag_debit(self):
    #     if self.ag_debit:
    #         self.ag_credit = 0.0
    #         self.amount_currency = self.ag_debit

    # @api.onchange('ag_credit')
    # def _onchange_ag_credit(self):
    #     if self.ag_credit:
    #         self.ag_debit = 0.0
    #         self.amount_currency = -self.ag_credit

    # @api.onchange('amount_currency')
    # def _onchange_amount_currency(self):
    #     for line in self:
    #         company = line.move_id.company_id
    #         balance = line.currency_id._convert(line.amount_currency, company.currency_id, company, line.move_id.date or fields.Date.context_today(line))
    #         line.ag_debit = line.amount_currency if balance > 0.0 else 0.0
    #         line.ag_credit = -line.amount_currency if balance < 0.0 else 0.0
    #         line.debit = balance if balance > 0.0 else 0.0
    #         line.credit = -balance if balance < 0.0 else 0.0

    #         if not line.move_id.is_invoice(include_receipts=True):
    #             continue

    #         line.update(line._get_fields_onchange_balance())
    #         line.update(line._get_price_total_and_subtotal())

    # @api.onchange('currency_id')
    # def _onchange_currency(self):
    #     for line in self:
    #         company = line.move_id.company_id

    #         if line.move_id.is_invoice(include_receipts=True):
    #             line._onchange_price_subtotal()
    #         elif not line.move_id.reversed_entry_id:
    #             balance = line.currency_id._convert(line.amount_currency, company.currency_id, company, line.move_id.date or fields.Date.context_today(line))
    #             line.ag_debit = line.amount_currency if balance > 0.0 else 0.0
    #             line.ag_credit = -line.amount_currency if balance < 0.0 else 0.0
    #             line.debit = balance if balance > 0.0 else 0.0
    #             line.credit = -balance if balance < 0.0 else 0.0
