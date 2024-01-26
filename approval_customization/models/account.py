# -*- coding: utf-8 -*-

from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    discount_amount = fields.Monetary(
        string='Discount Amount',
        store=True,
        digits='Product Price',
        compute='_compute_discount_amount'
    )
    refundable_deposit_1 = fields.Monetary(
        string='Refundable Deposit',
        compute='_compute_refundable_deposit',
        store=True,
        digits='Product Price')
    

    custom_field = fields.Monetary(string="Custom Field", compute='_compute_custom_field', store=True)

    @api.depends('amount_total', 'refundable_deposit_1')
    def _compute_custom_field(self):
        for record in self:
            record.custom_field = record.amount_total + record.refundable_deposit_1        

    @api.depends('amount_total', 'invoice_line_ids.price_unit')
    def _compute_refundable_deposit(self):
        for move in self:
            if move.invoice_origin:
                sale_order = self.env['sale.order'].search(
                    [('name', '=', move.invoice_origin)], limit=1)
                if sale_order:
                    move.refundable_deposit_1 = sale_order.refundable_deposit
                else:
                    move.refundable_deposit_1 = 0.0
            else:
                move.refundable_deposit_1 = 0.0

    @api.depends('invoice_origin')
    def _compute_discount_amount(self):
        for move in self:
            if move.invoice_origin:
                sale_order = self.env['sale.order'].search(
                    [('name', '=', move.invoice_origin)], limit=1)
                if sale_order:
                    move.discount_amount = sale_order.discount_amount
                else:
                    move.discount_amount = 0.0
            else:
                move.discount_amount = 0.0

    pt_percent_due_receipt = fields.Monetary(
        string='Deposite', compute='_compute_pt_percent_due')
    balance_amount_due_days = fields.Monetary(
        string='Balance', compute='_compute_pt_percent_due')

    def _compute_pt_percent_due(self):
        for move in self:
            if move.invoice_origin:
                sale_order = self.env['sale.order'].search(
                    [('name', '=', move.invoice_origin)], limit=1)
                if sale_order:
                    move.pt_percent_due_receipt = sale_order.pt_percent_due_receipt
                    move.balance_amount_due_days = sale_order.balance_amount_due_days
                else:
                    move.pt_percent_due_receipt = 0
                    move.balance_amount_due_days = 0
            else:
                move.pt_percent_due_receipt = 0
                move.balance_amount_due_days = 0


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Resource',
        inverse='_inverse_product_id',
        ondelete='restrict',
    )

    quantity = fields.Float(
        string='Days',
        compute='_compute_quantity', store=True, readonly=False, precompute=True,
        digits='Product Unit of Measure',
        help="The optional quantity expressed by this line, eg: number of product sold. "
             "The quantity is not a legal requirement but is very useful for some reports.",
    )
