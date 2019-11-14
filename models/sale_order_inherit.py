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
	
	def generate_order_line(self, pack_aux_ids, order_lines, flag, order_qty, order, is_pack, validation):

		"""
			Funcion recursiva para calcular los productos que van a ir en el request y purchase
		"""

		if flag == -1:
			return order_lines

		if pack_aux_ids[flag].product_id.pack:

			pack_line = pack_aux_ids[flag].product_id.pack_line_ids
			self.generate_order_line(pack_line, order_lines, len(pack_line)-1, order_qty, order, True, validation)
		else:

			product = pack_aux_ids[flag]

			is_pack_aux = is_pack

			if product.product_id.purchase_request == validation:

				vals = {'product_id': product.product_id.id,
						'name': product.product_id.name,
						'date_planned': datetime.now(),
						'product_qty': order_qty * (product.quantity if is_pack else product.product_qty),
						'price_unit': product.product_id.list_price,
						'product_uom': product.product_id.uom_id.id,
						'product_uom_po': product.product_id.uom_po_id.id,
						'currency_id': order.currency_id.id,
						'sale_line_id': order.order_line.id,
						'taxes_id': order.order_line.tax_id
						}
				
				order_lines.append(vals)
		flag=flag-1
		return self.generate_order_line(pack_aux_ids, order_lines, flag, order_qty, order, is_pack, validation)



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
				is_pack = False
				if line.product_id.pack:
					
					for x in line.product_id.pack_line_ids:
						vals={
							'product_pack_id': line.product_id.id,
							'product_id': x.product_id.id,
							'product_qty': x.quantity
						}
						data_pack.append((0, 0, vals))
					is_pack = True

				data.update({
					'price_unit': price,
					'discount': 100 - ((100 - discount) * (100 - line.discount) / 100),
					'product_uom_qty': line.product_uom_qty,
					'product_id': line.product_id.id,
					'product_uom': line.product_uom_id.id,
					'pack_aux_ids': data_pack,
					'pack': is_pack,
					'customer_lead': self._get_customer_lead(line.product_id.product_tmpl_id),
				})
				if self.pricelist_id:
					data.update(self.env['sale.order.line']._get_purchase_price(self.pricelist_id, line.product_id, line.product_uom_id, fields.Date.context_today(self)))
			order_lines.append((0, 0, data))

		self.order_line = order_lines
		self.order_line._compute_tax_id()

		for data_product in self.order_line:
			print(data_product)

			if data_product.product_id.pack:
				data_product.is_pack = True
			else:
				data_product.is_pack = False

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


	def update_order_line_(self):
		"""
			Funcion que permite accionar el boton Actualizar en la linea de la orden
		"""
		for value in self:

			qty_pack = 1

			for x in value.order_line:
				price_unit = x.product_id.list_price
				x.write({'price_unit': price_unit})
				
				if x.is_pack:

					qty_pack = x.product_uom_qty
					
					price = 0
					if x.product_id.pack:
						if x.pack_aux_ids:
							for value_product in x.pack_aux_ids:
								price += value_product.product_id.list_price * value_product.product_qty
							x.write({'price_unit': price})
						else:

							data_pack = []

							if x.product_id.pack_line_ids:
								price_pack = 0
								for pack_product in x.product_id.pack_line_ids:
									vals={
										'product_pack_id': x.product_id.id,
										'product_id': pack_product.product_id.id,
										'product_qty': pack_product.quantity
									}
									price_pack += pack_product.product_id.list_price * pack_product.quantity

									data_pack.append((0, 0, vals))
								x.write({'pack_aux_ids': data_pack, 'price_unit': price_pack})

		return self.env['sale.order.line'].search([('order_id', '=', self.id)])

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
							#for value in x.pack_aux_ids:
							#	data_product.append( (0, 0, {'product_id': value.product_id.id, 'product_uom_qty': value.product_qty, 'price_unit':0, 'is_pack': False}) )
							x.expand_pack_line()

				else:
					pass
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
