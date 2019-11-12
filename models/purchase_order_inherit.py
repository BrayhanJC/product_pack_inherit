# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    Autor: Brayhan Andres Jaramillo Castaño
#    Correo: brayhanjaramillo@hotmail.com
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, api
from datetime import datetime

class PurchaseOrderInherit(models.Model):
	_inherit = 'purchase.order'
	_description = "Display Purchase Order Form View"

	@api.model
	def default_get(self, default_fields):
		if "active_model" in self._context and self._context.get('active_model') == 'sale.order':
			model_order = self.env['sale.order']
			order = model_order.browse(self._context['active_id'])
			order_lines = []
			for order_line in order.order_line:
				if order_line.product_id.pack:
					if order_line.pack_aux_ids:

						order_lines = model_order.generate_order_line(order_line.pack_aux_ids, [], len(order_line.pack_aux_ids)-1, order_line.product_uom_qty, order, False, False)
						
			contextual_self = self.with_context({
				'default_origin': order.name,
				'default_order_id': order.id,
				'default_order_line': order_lines
			})
			return super(PurchaseOrderInherit, contextual_self).default_get(default_fields)
		return super(PurchaseOrderInherit, self).default_get(default_fields)


PurchaseOrderInherit()


