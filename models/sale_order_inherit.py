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

from odoo import api, fields, models, _
import time
from datetime import datetime, timedelta, date
import logging
_logger = logging.getLogger(__name__)
from odoo import modules
from odoo.addons import decimal_precision as dp


class SaleOrderInherit(models.Model):

	_inherit = 'sale.order'


	@api.onchange('sale_order_template_id')
	def onchange_sale_order_template_id(self):
		if not self.sale_order_template_id:
			self.require_signature = self._get_default_require_signature()
			self.require_payment = self._get_default_require_payment()
			return
		template = self.sale_order_template_id.with_context(lang=self.partner_id.lang)

		order_lines = [(5, 0, 0)]
		for line in template.sale_order_template_line_ids:
			data = self._compute_line_data_for_template_change(line)
			if line.product_id:
				discount = 0
				if self.pricelist_id:
					price = self.pricelist_id.with_context(uom=line.product_uom_id.id).get_product_price(line.product_id, 1, False)
					if self.pricelist_id.discount_policy == 'without_discount' and line.price_unit:
						discount = (line.price_unit - price) / line.price_unit * 100
						price = line.price_unit

				else:
					price = line.price_unit

				data_pack = []
				if line.product_id.pack:
					print('es un pack')
					for x in line.product_id.pack_line_ids:
						vals={
							'product_pack_id': line.product_id.id,
							'product_id': x.product_id.id,
							'product_qty': x.quantity
						}
						data_pack.append((0, 0, vals))

				else:
					print('no es un pack')

				data.update({
					'price_unit': price,
					'discount': 100 - ((100 - discount) * (100 - line.discount) / 100),
					'product_uom_qty': line.product_uom_qty,
					'product_id': line.product_id.id,
					'product_uom': line.product_uom_id.id,
					'pack_aux_ids': data_pack,
					'customer_lead': self._get_customer_lead(line.product_id.product_tmpl_id),
					'is_pack': False,
				})
				if self.pricelist_id:
					data.update(self.env['sale.order.line']._get_purchase_price(self.pricelist_id, line.product_id, line.product_uom_id, fields.Date.context_today(self)))
			order_lines.append((0, 0, data))

		self.order_line = order_lines
		self.order_line._compute_tax_id()

		option_lines = []
		for option in template.sale_order_template_option_ids:
			data = self._compute_option_data_for_template_change(option)
			option_lines.append((0, 0, data))
		self.sale_order_option_ids = option_lines

		if template.number_of_days > 0:
			self.validity_date = fields.Date.to_string(datetime.now() + timedelta(template.number_of_days))

		self.require_signature = template.require_signature
		self.require_payment = template.require_payment

		if template.note:
			self.note = template.note

	@api.multi
	def action_confirm(self):

		_logger.info('confirmando la venta')
		data_product = []
		data_aux = []
		if self.order_line:
			for x in self.order_line:

				if x.product_id.pack:

					if x.product_id.pack_price_type in ['none_detailed_assited_price', 'none_detailed_totaliced_price']:

						if len(x.pack_aux_ids) > 0:
							#_logger.info('los productos del pack son:')
							for value in x.pack_aux_ids:
								data_product.append( (0, 0, {'product_id': value.product_id.id, 'product_uom_qty': value.product_qty, 'price_unit':0, 'is_pack': False}) )

				else:
					pass

		self.order_line = data_product

		if self._get_forbidden_state_confirm() & set(self.mapped('state')):
			raise UserError(_(
				'It is not allowed to confirm an order in the following states: %s'
			) % (', '.join(self._get_forbidden_state_confirm())))

		for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
			order.message_subscribe([order.partner_id.id])
		self.write({
			'state': 'sale',
			'confirmation_date': fields.Datetime.now()
		})
		self._action_confirm()
		if self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
			self.action_done()
		return True


SaleOrderInherit()
