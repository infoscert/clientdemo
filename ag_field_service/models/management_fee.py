# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class ManagementFee(models.Model):
    _name = "management.fee"
    _description = 'Management Fee'

    @api.model
    def year_selection(self):
        select_year = 2021
        year_list = []
        while select_year <= fields.date.today().year:
            year_list.append((str(select_year), str(select_year)))
            select_year += 1
        return year_list

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related="company_id.currency_id", string="Currency", readonly=True)
    year = fields.Selection(selection=year_selection, string="Year")
    amount = fields.Monetary("Amount")
    # branch_id = fields.Many2one("res.branch", string="Site")

    # @api.constrains('branch_id', 'year')
    @api.constrains('year')
    def _check_management_year(self):
        for rec in self:
            management_fee_id = self.search([('id', '!=', rec.id), ('year', '=', rec.year)])
            if management_fee_id:
                raise ValidationError("Management Fee must be unique for each Year!")

    def _update_cost_entries_management_fee(self):
        year = datetime.now().year
        # site_ids = self.env['res.branch'].sudo().search([])
        # for site in site_ids:
        # management_fee_id = self.search([('branch_id', '=', site.id), ('year', '=', year)], limit=1)
        management_fee_id = self.search([('year', '=', year)], limit=1)
        cost_category_id = self.env['cost.category'].search([('name', '=', 'Management Fee')])
        if not cost_category_id:
            cost_category_id = self.env['cost.category'].create({
                                                'name': 'Management Fee'
                                            })
        if management_fee_id:
            cost_entry_id = self.env['cost.entry'].sudo().search([('cost_category_id', '=', cost_category_id.id)]) #, ('branch_id', '=', site.id)])
            current_month_year = datetime.now().strftime("%b-%Y")
            if cost_entry_id:
                effective_date_month_year = cost_entry_id.effective_date.strftime("%b-%Y")
            else:
                effective_date_month_year = False
            if not cost_entry_id or effective_date_month_year != current_month_year:
                cost_entry_id = self.env['cost.entry'].create({
                        'partner_id': False,
                        'currency_id': self.currency_id.id,
                        'cost_category_id': cost_category_id.id,
                        'amount': (management_fee_id.amount/12),
                        'effective_date': datetime.now(),
                        'purchase_id': False,
                        # 'branch_id': site.id
                    })
