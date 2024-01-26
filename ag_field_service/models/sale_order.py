# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    """inherited sale order"""
    _inherit = 'sale.order'

    @api.model
    def _default_warehouse_id(self):
        """methode to get default warehouse id"""
        # !!! Any change to the default value may have to be repercuted
        # on _init_column() below.
        return self.env.user._get_default_warehouse_id()

    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse',
        required=True, readonly=True, states={'draft': [('readonly', False)],
                                              'sent': [('readonly', False)]},
        default=_default_warehouse_id, check_company=True,
        )
