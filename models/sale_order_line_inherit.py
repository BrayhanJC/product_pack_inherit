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

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError


class SaleOrderInherit(models.Model):

	_inherit = 'sale.order.line'

	is_pack = fields.Boolean(string="Is pack?", default=True)

	@api.multi
	def _prepare_procurement_values_pack_line(self, order_line_id, company_id, date_planned, route_ids, warehouse_id, partner_id, group_id=False):
		""" Prepare specific key for moves or other components that will be created from a stock rule
		comming from a sale order line. This method could be override in order to add other custom key that could
		be used in move/po creation.
		"""
		values = {}
		values.update({
			'company_id': company_id,
			'group_id': group_id,
			'sale_line_id': order_line_id,
			'date_planned': date_planned,
			'route_ids': route_ids,
			'warehouse_id': warehouse_id or False,
			'partner_id': partner_id,
			'group_id': group_id
		#	'partner_id': self.order_id.partner_shipping_id.id,
		})

		print(values)

		return values


	@api.multi
	def _action_launch_stock_rule(self):
		"""
		Launch procurement group run method with required/custom fields genrated by a
		sale order line. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
		depending on the sale order line product rule.
		"""
		precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
		errors = []
		order_lines = []
		model_order = self.env['sale.order']



		sale_order_id = 0
		for line in self:

			sale_order_id = line.order_id
			

		if sale_order_id:
			for line in sale_order_id.order_line:
				if line.product_id.pack:
					print('producto: ' + str(line.product_id.name))
					model_order._generate_order_line(line.pack_aux_ids, order_lines, len(line.pack_aux_ids)-1, line.product_uom_qty, line.order_id, False, True, line.id)

	#	print('los prductos son')
	#	print(order_lines)

		if order_lines:
			for x in order_lines:
				values = self._prepare_procurement_values_pack_line(x['sale_line_id'], self.env['res.company'].search([('id', '=', x['company_id'])]),  x['date_planned'], self.env['stock.location.route'].search([('id', '=', x['route_ids'])]), self.env['stock.warehouse'].search([('id', '=', x['warehouse_id'])]), x['partner_id'], x['group_id'])
			
			#	print(str(line.product_id.name) + ' - ' + str(product_qty) + ' - ' + str(procurement_uom) + ' - ' + str(line.order_id.partner_shipping_id.property_stock_customer) + ' - ' + str(line.name) + ' - ' + str(line.order_id.name) + ' - ' + str(values))
				#print(str(x['name']) + ' - ' + str(x['product_qty']) + ' - ' + str(self.env['uom.uom'].search([('id', '=', x['product_uom'])])) + ' - ' + str(x['stock_location']) + ' - ' + str(x['name']) + ' - ' + str(x['order_name']) + ' - ' + str(values))

				try:
					#pass
					self.env['procurement.group'].run(self.env['product.template'].search([('id', '=', x['product_id'])]), x['product_qty'], self.env['uom.uom'].search([('id', '=', x['product_uom'])]), x['stock_location'], x['name'], x['order_name'], values)
			
				except UserError as error:
					errors.append(error.name)
	
		for line in self:



			if line.state != 'sale' or not line.product_id.type in ('consu','product'):
				continue
			qty = line._get_qty_procurement()
			if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
				continue

			group_id = line.order_id.procurement_group_id
			if not group_id:
				group_id = self.env['procurement.group'].create({
					'name': line.order_id.name, 'move_type': line.order_id.picking_policy,
					'sale_id': line.order_id.id,
					'partner_id': line.order_id.partner_shipping_id.id,
				})
				line.order_id.procurement_group_id = group_id
			else:
				# In case the procurement group is already created and the order was
				# cancelled, we need to update certain values of the group.
				updated_vals = {}
				if group_id.partner_id != line.order_id.partner_shipping_id:
					updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
				if group_id.move_type != line.order_id.picking_policy:
					updated_vals.update({'move_type': line.order_id.picking_policy})
				if updated_vals:
					group_id.write(updated_vals)

			values = line._prepare_procurement_values(group_id=group_id)
			product_qty = line.product_uom_qty - qty

			procurement_uom = line.product_uom
			quant_uom = line.product_id.uom_id
			get_param = self.env['ir.config_parameter'].sudo().get_param
			if procurement_uom.id != quant_uom.id and get_param('stock.propagate_uom') != '1':
				product_qty = line.product_uom._compute_quantity(product_qty, quant_uom, rounding_method='HALF-UP')
				procurement_uom = quant_uom

			try:
	

				#print(str(line.product_id.name) + ' - ' + str(product_qty) + ' - ' + str(procurement_uom) + ' - ' + str(line.order_id.partner_shipping_id.property_stock_customer) + ' - ' + str(line.name) + ' - ' + str(line.order_id.name) + ' - ' + str(values))


				self.env['procurement.group'].run(line.product_id, product_qty, procurement_uom, line.order_id.partner_shipping_id.property_stock_customer, line.name, line.order_id.name, values)
			


			except UserError as error:
				errors.append(error.name)
		if errors:
			raise UserError('\n'.join(errors))
		return True



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
					product_discount = data_product.discount

					vals = {
					'product_pack_id': self.product_id.id,
					'product_id': product,
					'product_qty': quantity_product,
					'product_discount': product_discount
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
							'product_qty': x.product_qty,
							'product_discount': x.product_discount
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
				'product_discount': x.product_discount,
				'price_unit': (x.product_qty * x.product_id.list_price) + ((x.product_qty * x.product_id.list_price) * (x.product_discount/100)),
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



	@api.model
	def create(self, vals):

		if self.env['product.product'].search([('id', '=', vals['product_id'])]).pack:
			vals['is_pack'] = True
		else:
			vals['is_pack'] = False


		res = super(SaleOrderInherit, self).create(vals)

		return res

SaleOrderInherit()
