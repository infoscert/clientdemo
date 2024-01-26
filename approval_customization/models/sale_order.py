# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from collections import defaultdict
from odoo.tools.misc import formatLang


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _description = 'Sale Order'

    tax_id = fields.Many2many('account.tax', string='Taxes')
    discount = fields.Float(string='Discount (%)')

    @api.onchange('tax_id', 'discount')
    def update_order_line_taxes_and_discount(self):
        if self.order_line:
            tax_ids_to_add = self.tax_id - self.order_line.mapped('tax_id')
            tax_ids_to_remove = self.order_line.mapped('tax_id') - self.tax_id

            for line in self.order_line:
                if tax_ids_to_remove:
                    line.tax_id -= tax_ids_to_remove

                if line.product_template_id.name != 'Refundable Deposit':
                    line.tax_id |= tax_ids_to_add

            for line in self.order_line:
                if line.product_template_id.name != 'Refundable Deposit':
                    line.discount = self.discount

    discount_amount = fields.Monetary(
        string='Discount Amount',
        compute='_compute_discount_amount',
        store=True,
        digits='Product Price'
    )
    refundable_deposit_1 = fields.Monetary(
        string='Refundable Deposit',
        compute='_compute_refundable_deposit',
        store=True,
        digits='Product Price'
    )
    refundable_deposit = fields.Monetary(
        string='Refundable Deposit',
        digits='Product Price',
        compute='_compute_refundable_deposite',
        store=True,  # Optional, use it if you want to store the computed value in the database
    )

    @api.depends('order_line', 'order_line.price_unit')
    def _compute_refundable_deposite(self):
        for order in self:
            refundable_deposit_total = sum(
                line.price_unit for line in order.order_line
                if line.product_template_id.name == 'Refundable Deposit'
            )
            order.refundable_deposit = refundable_deposit_total

    @api.depends('payment_term_id')
    def _compute_note(self):
        for order in self:
            if order.payment_term_id:
                order.note = order.payment_term_id.note
            else:
                order.note = False

    pt_percent_due_receipt = fields.Monetary(
        string='Deposit', compute='_compute_custom_payment_terms_amount')
    balance_amount_due_days = fields.Monetary(
        string='Balance', compute='_compute_custom_payment_terms_amount')

    @api.depends('refundable_deposit')
    def _compute_refundable_deposit(self):
        for order in self:
            order.refundable_deposit_1 = order.refundable_deposit

    @api.depends('order_line.discount', 'order_line.product_uom_qty', 'order_line.price_unit', 'order_line.price_subtotal')
    def _compute_discount_amount(self):
        for order in self:
            order.discount_amount = sum(
                (line.product_uom_qty * line.price_unit) - line.price_subtotal for line in order.order_line)

    @api.depends('order_line.price_subtotal', 'order_line.price_tax', 'order_line.price_total', 'order_line.price_unit', 'refundable_deposit')
    def _compute_amounts(self):
        """Compute the total amounts of the SO."""
        for order in self:
            order_lines = order.order_line.filtered(
                lambda x: not x.display_type)

            if order.company_id.tax_calculation_rounding_method == 'round_globally':
                tax_results = self.env['account.tax']._compute_taxes([
                    line._convert_to_tax_base_line_dict()
                    for line in order_lines
                ])
                totals = tax_results['totals']
                amount_untaxed = totals.get(
                    order.currency_id, {}).get('amount_untaxed', 0.0)
                amount_tax = totals.get(
                    order.currency_id, {}).get('amount_tax', 0.0)
            else:
                amount_untaxed = sum(order_lines.mapped('price_subtotal'))
                amount_tax = sum(order_lines.mapped('price_tax'))

            order.amount_untaxed = amount_untaxed
            order.amount_tax = amount_tax
            order.amount_total = order.amount_untaxed + \
                order.amount_tax + order.refundable_deposit

    custom_payment_terms_amount = fields.Float(
        string='Payment Terms Amount',
        compute='_compute_custom_payment_terms_amount',
        store=True,
    )

    @api.depends('payment_term_id', 'amount_total')
    def _compute_custom_payment_terms_amount(self):
        for order in self:
            calculated_amount = 0.0
            if order.payment_term_id:
                for line in order.payment_term_id.line_ids:
                    if line.value == 'balance':
                        calculated_amount += 0
                    elif line.value == 'fixed':
                        calculated_amount += line.fixed_amount
                    elif line.value == 'percent':
                        calculated_amount += (order.amount_total *
                                              line.value_amount) / 100

            order.pt_percent_due_receipt = calculated_amount
            order.balance_amount_due_days = order.amount_total - calculated_amount



    custom_field = fields.Monetary(string="Custom Field", compute='_compute_custom_field', store=True)

    @api.depends('amount_total', 'refundable_deposit_1')
    def _compute_custom_field(self):
        for record in self:
            record.custom_field = record.amount_total + record.refundable_deposit_1        


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _description = 'Sale Order Line'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string="Resource",
        change_default=True, ondelete='restrict', check_company=True, index='btree_not_null',
        domain="[('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    product_template_id = fields.Many2one(
        string="Resource",
        comodel_name='product.template',
        compute='_compute_product_template_id',
        readonly=False,
        search='_search_product_template_id',
        domain=[('sale_ok', '=', True)])

    product_uom_qty = fields.Float(
        string="Days",
        compute='_compute_product_uom_qty',
        digits='Product Unit of Measure', default=1.0,
        store=True, readonly=False, required=True, precompute=True)

    @api.onchange('product_template_id', 'price_unit')
    def _onchange_set_price_unit(self):
        for line in self:
            if line.product_template_id.detailed_type == 'service' and line.product_template_id.name == "Refundable Deposit":
                line.order_id.refundable_deposit = line.price_unit


class AccountTax(models.Model):
    _inherit = 'account.tax'
 
    @api.model
    def _prepare_tax_totals(self, base_lines, currency, tax_lines=None):
        print("CUSTOM CALLING")
        """ Compute the tax totals details for the business documents.
        :param base_lines:  A list of python dictionaries created using the '_convert_to_tax_base_line_dict' method.
        :param currency:    The currency set on the business document.
        :param tax_lines:   Optional list of python dictionaries created using the '_convert_to_tax_line_dict' method.
                            If specified, the taxes will be recomputed using them instead of recomputing the taxes on
                            the provided base lines.
        :return: A dictionary in the following form:
            {
                'amount_total':                 The total amount to be displayed on the document, including every total
                                                types.
                'amount_untaxed':               The untaxed amount to be displayed on the document.
                'formatted_amount_total':       Same as amount_total, but as a string formatted accordingly with
                                                partner's locale.
                'formatted_amount_untaxed':     Same as amount_untaxed, but as a string formatted accordingly with
                                                partner's locale.
                'groups_by_subtotals':          A dictionary formed liked {'subtotal': groups_data}
                                                Where total_type is a subtotal name defined on a tax group, or the
                                                default one: 'Untaxed Amount'.
                                                And groups_data is a list of dict in the following form:
                    {
                        'tax_group_name':                   The name of the tax groups this total is made for.
                        'tax_group_amount':                 The total tax amount in this tax group.
                        'tax_group_base_amount':            The base amount for this tax group.
                        'formatted_tax_group_amount':       Same as tax_group_amount, but as a string formatted accordingly
                                                            with partner's locale.
                        'formatted_tax_group_base_amount':  Same as tax_group_base_amount, but as a string formatted
                                                            accordingly with partner's locale.
                        'tax_group_id':                     The id of the tax group corresponding to this dict.
                    }
                'subtotals':                    A list of dictionaries in the following form, one for each subtotal in
                                                'groups_by_subtotals' keys.
                    {
                        'name':                             The name of the subtotal
                        'amount':                           The total amount for this subtotal, summing all the tax groups
                                                            belonging to preceding subtotals and the base amount
                        'formatted_amount':                 Same as amount, but as a string formatted accordingly with
                                                            partner's locale.
                    }
                'subtotals_order':              A list of keys of `groups_by_subtotals` defining the order in which it needs
                                                to be displayed
            }
        """

        # ==== Compute the taxes ====

        to_process = []
        for base_line in base_lines:
            to_update_vals, tax_values_list = self._compute_taxes_for_single_line(
                base_line)
            to_process.append((base_line, to_update_vals, tax_values_list))

        def grouping_key_generator(base_line, tax_values):
            source_tax = tax_values['tax_repartition_line'].tax_id
            return {'tax_group': source_tax.tax_group_id}

        global_tax_details = self._aggregate_taxes(
            to_process, grouping_key_generator=grouping_key_generator)

        tax_group_vals_list = []
        for tax_detail in global_tax_details['tax_details'].values():
            tax_group_vals = {
                'tax_group': tax_detail['tax_group'],
                'base_amount': tax_detail['base_amount_currency'],
                'tax_amount': tax_detail['tax_amount_currency'],
            }

            # Handle a manual edition of tax lines.
            if tax_lines is not None:
                matched_tax_lines = [
                    x
                    for x in tax_lines
                    if x['tax_repartition_line'].tax_id.tax_group_id == tax_detail['tax_group']
                ]
                if matched_tax_lines:
                    tax_group_vals['tax_amount'] = sum(
                        x['tax_amount'] for x in matched_tax_lines)

            tax_group_vals_list.append(tax_group_vals)

        tax_group_vals_list = sorted(tax_group_vals_list, key=lambda x: (
            x['tax_group'].sequence, x['tax_group'].id))

        # ==== Partition the tax group values by subtotals ====

        amount_untaxed = global_tax_details['base_amount_currency']
        amount_tax = 0.0

        subtotal_title = ("Untaxed Amount")

        subtotal_order = {}
        groups_by_subtotal = defaultdict(list)
        for tax_group_vals in tax_group_vals_list:
            tax_group = tax_group_vals['tax_group']

            subtotal_title = tax_group.preceding_subtotal or _(
                "Untaxed Amount")
            sequence = tax_group.sequence

            subtotal_order[subtotal_title] = min(
                subtotal_order.get(subtotal_title, float('inf')), sequence)
            groups_by_subtotal[subtotal_title].append({
                'group_key': tax_group.id,
                'tax_group_id': tax_group.id,
                'tax_group_name': tax_group.name,
                'tax_group_amount': tax_group_vals['tax_amount'],
                'tax_group_base_amount': tax_group_vals['base_amount'],
                'formatted_tax_group_amount': formatLang(self.env, tax_group_vals['tax_amount'], currency_obj=currency),
                'formatted_tax_group_base_amount': formatLang(self.env, tax_group_vals['base_amount'], currency_obj=currency),
            })

        # ==== Build the final result ====

        subtotals = []
        for subtotal_title in sorted(subtotal_order.keys(), key=lambda k: subtotal_order[k]):
            amount_total = amount_untaxed + amount_tax
            subtotals.append({
                'name': subtotal_title,
                'amount': amount_total,
                'formatted_amount': formatLang(self.env, amount_total, currency_obj=currency),
            })
            amount_tax += sum(x['tax_group_amount']
                              for x in groups_by_subtotal[subtotal_title])
        model_in_context = self.env.context.get('params', {}).get('model', '')
        id_in_context = self.env.context.get('params', {}).get('id', '')

        # Custom code
        if model_in_context == 'sale.order':
            sale_order = self.env['sale.order'].browse(id_in_context)
            amount_total = amount_untaxed + amount_tax + sale_order.refundable_deposit
            groups_by_subtotal[subtotal_title].append({
                'tax_group_name': "Refundable Deposit",
                'tax_group_amount': sale_order.refundable_deposit_1,
                'tax_group_base_amount': sale_order.refundable_deposit_1,
                'formatted_tax_group_amount': formatLang(self.env, sale_order.refundable_deposit_1, currency_obj=currency),
                'formatted_tax_group_base_amount': formatLang(self.env, sale_order.refundable_deposit_1, currency_obj=currency),
            })
        elif model_in_context == 'account.move':
            move_id = self.env['account.move'].browse(id_in_context)
            amount_total = amount_untaxed + amount_tax + move_id.refundable_deposit_1
            groups_by_subtotal[subtotal_title].append({
                'tax_group_name': "Refundable Deposit",
                'tax_group_amount': move_id.refundable_deposit_1,
                'tax_group_base_amount': move_id.refundable_deposit_1,
                'formatted_tax_group_amount': formatLang(self.env, move_id.refundable_deposit_1, currency_obj=currency),
                'formatted_tax_group_base_amount': formatLang(self.env, move_id.refundable_deposit_1, currency_obj=currency),
            })
        else:
            amount_total = amount_untaxed + amount_tax

        display_tax_base = (len(global_tax_details['tax_details']) == 1 and currency.compare_amounts(tax_group_vals_list[0]['base_amount'], amount_untaxed) != 0)\
            or len(global_tax_details['tax_details']) > 1
        vals = {
            'amount_untaxed': currency.round(amount_untaxed) if currency else amount_untaxed,
            'amount_total': currency.round(amount_total) if currency else amount_total,
            'formatted_amount_total': formatLang(self.env, amount_total, currency_obj=currency),
            'formatted_amount_untaxed': formatLang(self.env, amount_untaxed, currency_obj=currency),
            'groups_by_subtotal': groups_by_subtotal,
            'subtotals': subtotals,
            'subtotals_order': sorted(subtotal_order.keys(), key=lambda k: subtotal_order[k]),
            'display_tax_base': display_tax_base
        }

        return {
            'amount_untaxed': currency.round(amount_untaxed) if currency else amount_untaxed,
            'amount_total': currency.round(amount_total) if currency else amount_total,
            'formatted_amount_total': formatLang(self.env, amount_total, currency_obj=currency),
            'formatted_amount_untaxed': formatLang(self.env, amount_untaxed, currency_obj=currency),
            'groups_by_subtotal': groups_by_subtotal,
            'subtotals': subtotals,
            'subtotals_order': sorted(subtotal_order.keys(), key=lambda k: subtotal_order[k]),
            'display_tax_base': display_tax_base
        }
