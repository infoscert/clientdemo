from odoo import api, fields, models, _

class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends('partner_id')
    def _compute_invoice_payment_term_id(self):
        for move in self:
            if not move.invoice_payment_term_id:
                if move.is_sale_document(include_receipts=True) and move.partner_id.property_payment_term_id:
                    move.invoice_payment_term_id = move.partner_id.property_payment_term_id
                elif move.is_purchase_document(include_receipts=True) and move.partner_id.property_supplier_payment_term_id:
                    move.invoice_payment_term_id = move.partner_id.property_supplier_payment_term_id

    @api.depends('needed_terms')
    def _compute_invoice_date_due(self):
        today = fields.Date.context_today(self)
        for move in self:
            if not move.invoice_date_due:
                move.invoice_date_due = move.needed_terms and max(
                    (k['date_maturity'] for k in move.needed_terms.keys() if k),
                    default=False,
                ) or move.invoice_date_due or today
                