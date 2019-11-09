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

	_inherit = 'sale.order.line'

	is_pack = fields.Boolean(string="Is pack?", default=True)

	def return_product_pack(self):

		"""
		Funcion que retorna la informacion de los productos que hacen parte del pack

		"""

		result = []
		if self.product_id.pack:

			#validamos si el product pack tiene productos hijos
			if len(self.product_id.pack_line_ids) > 0:

				#recorremos los productos que contiene el pack
				for data_product in self.product_id.pack_line_ids:


					product = data_product.product_id.id
					quantity_product = data_product.quantity

					vals = {
					'product_pack_id': self.product_id.id,
					'product_id': product,
					'product_qty': quantity_product
					}

					result.append(vals)

		return result

	pack_aux_ids = fields.One2many('sale.order_pack_aux', 'sale_order_line_id', string="Product Pack")

	@api.depends('pack_aux_ids')
	def return_data_pack_aux(self):

		"""
		Funcion que retorna la informacion de los productos que estan en el pack order line

		"""

		data= []

		if self.pack_aux_ids:

			for x in self.pack_aux_ids:

				vals = {
							'product_pack_id': x.product_pack_id.id,
							'product_id': x.product_id.id,
							'product_qty': x.product_qty
							}

				data.append(vals)

		return data


	@api.onchange('product_id')
	def load_pack_aux(self):
		"""
		Funcion que permite cargar el pack_aux_ids con los productos que contienen el pack
		"""
		data = []

		if self.product_id:

			result = self.return_product_pack()

			_logger.info(result)

			if len(result) > 0:

				for x in result:
					data.append( (0, 0, x))

		if len(data) > 0:
			self.pack_aux_ids = None
			self.pack_aux_ids = result


	def return_data_products(self):

		"""
			Funcion que permite retonar todos los productos de la linea auxiliar de packs,
			con su respectivo id, cantidad y precio unitario
		"""

		products = []

		if self.pack_aux_ids:

			for x in self.pack_aux_ids:

				vals = {
				'product_id' : x.product_id.id,
				'product_uom_qty': x.product_qty,
				'price_unit': x.product_qty * x.product_id.list_price
				}

				products.append(vals)

		return products



	def search_product_pack_line(self, product_id, products):

		"""
			Funcion que permite retornar los valores del producto a buscar
			x -> Contiene el valor como id producto, cantidad y precio unitario
			0 -> No se encontro el producto
		"""

		if products:
			for x in products:

				if x['product_id'] == product_id:
					return x

		return 0



	def update_order_line(self):

		"""
			Funcion que permite actualizar la cantidad del componente o pack en la orden de linea
		"""

		sale_order_id = None

		for x in self:
			sale_order_id = x.order_id.id



		order_id = self.env['sale.order'].search([('id', '=', self.order_id.id)])

		if order_id:

			products = self.return_data_products()

			for x in order_id.order_line:

				search_product = self.search_product_pack_line(x.product_id.id, products)

				if search_product != 0:

					vals = {

					'product_uom_qty': search_product['product_uom_qty'],

					}
					x.write(vals)

			price_unit_pack = 0

			for x in products:
				price_unit_pack += x['price_unit']

			self.price_unit = price_unit_pack


	def update_order_line_(self):
		"""
			Funcion que permite accionar el boton Actualizar en la linea de la orden
		"""
		self.update_order_line()



	@api.constrains('product_id', 'product_uom_qty')
	def expand_pack_line(self):
		detailed_packs = ['components_price', 'totalice_price', 'fixed_price']
		# if we are using update_pricelist or checking out on ecommerce we
		# only want to update prices
		do_not_expand = self._context.get('update_prices') or \
			self._context.get('update_pricelist', False)

		if self.order_id.state in ['sale']:
			detailed_packs.append('none_detailed_assited_price')
			detailed_packs.append('none_detailed_totaliced_price')

			for subline in self.product_id.pack_line_ids:
				vals = subline.get_sale_order_line_vals(
					self, self.order_id)
				vals['sequence'] = self.sequence
				existing_subline = self.search([
					('product_id', '=', subline.product_id.id),
					('pack_parent_line_id', '=', self.id),
				], limit=1)
				# if subline already exists we update, if not we create
				if existing_subline:
					if do_not_expand:
						vals.pop('product_uom_qty')
					existing_subline.write(vals)
				elif not do_not_expand:
					self.create(vals)      

		else:
			if (
					self.state == 'draft' and
					self.product_id.pack and
					self.pack_type in detailed_packs):


				for subline in self.product_id.pack_line_ids:
					vals = subline.get_sale_order_line_vals(
						self, self.order_id)
					vals['sequence'] = self.sequence
					existing_subline = self.search([
						('product_id', '=', subline.product_id.id),
						('pack_parent_line_id', '=', self.id),
					], limit=1)
					
					if existing_subline:
						if do_not_expand:
							vals.pop('product_uom_qty')
						existing_subline.write(vals)
					elif not do_not_expand:
						self.create(vals)


SaleOrderInherit()
