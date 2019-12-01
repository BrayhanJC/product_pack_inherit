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
from odoo.exceptions import UserError, ValidationError

class ProductTemplateInherit(models.Model):

	_inherit = 'product.template'


	@api.onchange('available_in_pos')
	def onchange_avalable_in_pos(self):

		product_template_id = self.search([('name', '=', self.name)]).id

		product_id = self.env['product.product'].search([('product_tmpl_id', '=', product_template_id)]).id

		if self.item_ids:
			for x in self.item_ids:
				print(x.pricelist_id.name)
				print(x.pricelist_id.price_get(product_id, 1, None))


	@api.onchange('item_ids')
	def onchange_item_ids(self):

		product_template_id = self.search([('name', '=', self.name)]).id

		product_id = self.env['product.product'].search([('product_tmpl_id', '=', product_template_id)]).id

		if self.item_ids:
			for x in self.item_ids:
				print(x.pricelist_id.name)
				print(x.pricelist_id.price_get(product_id, 1, None))

		if self.item_ids:
			flag= 0
			for x in self.item_ids:
				if x.update_price:
					flag+=1

			if flag > 1:
				raise ValidationError(_('Solamente se puede configurar un precio por lista. \n Por favor, en la lista de precio solamente seleccionar una unica vez el campo. \n Actualizar Precio  ') )


			else:
				list_price = 0
				if self.item_ids:
					for x in self.item_ids:
						
						if x.update_price:

							val_price = x.pricelist_id.price_get(product_id, 1, None)
							val_price_update = 0
							for key in val_price:
								val_price_update = val_price.get(key)

							print(x.pricelist_id.price_get(product_id, 1, None))
							list_price= val_price_update
					

				#if list_price:
					#raise ValidationError(_('No se encontro ningun item para Actualizar Precio ') )

				self.list_price = list_price


	def calculate_list_price_pack(self, pack_line_ids, list_price, i):

		product_price = list_price

		if i == -1:
			return 0

		if pack_line_ids[i].product_id.pack:

			pack_line = pack_line_ids[i].product_id.pack_line_ids


			product_price = self.calculate_list_price_pack(pack_line, list_price, len(pack_line)-1)

		else:
			product_price = (pack_line_ids[i].product_id.list_price * pack_line_ids[i].quantity) + ( (pack_line_ids[i].product_id.list_price * pack_line_ids[i].quantity) * (pack_line_ids[i].discount/100) )
			#print('el producto ' + pack_line_ids[i].product_id.name + ' el valor ' + str(product_price) + ' la cantidad ' + str(pack_line_ids[i].quantity))
		return product_price + self.calculate_list_price_pack(pack_line_ids, product_price, i=i-1)






	@api.model
	def update_product_pricelist_real_time(self):

		"""
			Funcion que permite actualizar todos los productos con el precio de lista de tarifa publica
		"""
		product_ids = self.search([])

		pricelist_id = self.env['product.pricelist'].search([('id', '=', 1)])

		product_template_id = self.search([('name', '=', self.name)]).id
		product_model = self.env['product.product']

		data_product_malo = []
		for x in product_ids:
			if x.pack == False:
				print('vamos bien')
				if x.item_ids:
					
					for value in x.item_ids:
						print(value.pricelist_id.name + str(value.pricelist_id.id))
						if value.pricelist_id.id == 1:
							product_product_id = product_model.search([('product_tmpl_id', '=', x.id)])
							_logger.info('El producto template es: ' + str(x.name) + ' con id: ' + str(x.id))
							_logger.info(product_product_id)
							_logger.info('El producto producto es: ' + str(product_product_id.id))
							list_price = 0
							val_price = 0
							if product_product_id.id:
								val_price = pricelist_id.price_get(product_product_id.id or x.id, 1, None)
								print('el val_price es:')
								print(val_price)
								val_price_update = 0
								for key in val_price:
									val_price_update = val_price.get(key)
									list_price= val_price_update
								vals={
								'pricelist_id': pricelist_id.id,
								'update_price': True,
								}

								x.write({'list_price': list_price})

				else:
					pass



	@api.model
	def update_all_product_price_list(self):

		"""
			Funcion que permite actualizar todos los productos con el precio de lista de tarifa publica
		"""
		product_ids = self.search([])

		pricelist_id = self.env['product.pricelist'].search([('id', '=', 1)])

		product_template_id = self.search([('name', '=', self.name)]).id
		product_model = self.env['product.product']

		data_product_malo = []
		for x in product_ids:
			if x.pack == False:
				print('vamos bien')
				flag= False
				if x.item_ids:
					
					for value in x.item_ids:
						print(value.pricelist_id.name + str(value.pricelist_id.id))
						if (value.pricelist_id.id == 1) and value.update_price:
							if flag==False:
								flag = True
							

				else:
					if flag == False: 
						product_product_id = product_model.search([('product_tmpl_id', '=', x.id)])
						_logger.info('El producto template es: ' + str(x.name) + ' con id: ' + str(x.id))
						_logger.info(product_product_id)
						_logger.info('El producto producto es: ' + str(product_product_id.id))
						list_price = 0
						val_price = 0
						if product_product_id.id:
							val_price = pricelist_id.price_get(product_product_id.id or x.id, 1, None)
							print('el val_price es:')
							print(val_price)
							val_price_update = 0
							for key in val_price:
								val_price_update = val_price.get(key)
								list_price= val_price_update
							vals={
							'pricelist_id': pricelist_id.id,
							'update_price': True,
							}

							x.write({'item_ids': [(0, 0, vals)], 'list_price': list_price})


						else:
							data_product_malo.append(x.id)
					else:

						product_product_id = product_model.search([('product_tmpl_id', '=', x.id)])
						_logger.info('El producto template es: ' + str(x.name) + ' con id: ' + str(x.id))
						_logger.info(product_product_id)
						_logger.info('El producto producto es: ' + str(product_product_id.id))
						list_price = 0
						val_price = 0
						if product_product_id.id:
							val_price = pricelist_id.price_get(product_product_id.id or x.id, 1, None)
							print('el val_price es:')
							print(val_price)
							val_price_update = 0
							for key in val_price:
								val_price_update = val_price.get(key)
								list_price= val_price_update
							vals={
							'pricelist_id': pricelist_id.id,
							'update_price': True,
							}

							x.write({'list_price': list_price})


		_logger.info('Al final estos productos no estan buenos')
		for x in self.search([('id', 'in', data_product_malo)]):
			print(x.name)




	@api.model
	def update_all_product_pack(self):

		"""
			Funcion que permite actualizar el precio de los paquetes de acuerdo a sus componentes
		"""
		product_pack_ids = self.search([('pack', '=', True)])

		for x in product_pack_ids:
			if x.pack_line_ids:

				list_price = 0
				list_price = self.calculate_list_price_pack(x.pack_line_ids, 0, len(x.pack_line_ids)-1)
				x.write({'list_price': list_price})


	@api.multi
	@api.onchange('pack_line_ids')
	def onchange_pack_line(self):

		if self.pack_line_ids:
			list_price = 0
			list_price = self.calculate_list_price_pack(self.pack_line_ids, 0, len(self.pack_line_ids)-1)

			for x in self:
				x.list_price = list_price


	@api.multi
	def button_update_pack(self):
		self.update_all_product_pack()


	@api.model
	def create(self, vals):

		res = super(ProductTemplateInherit, self).create(vals)
		product_model = self.env['product.product']

		pricelist_id = self.env['product.pricelist'].search([('id', '=', 1)])
		product_product_id = product_model.search([('product_tmpl_id', '=', res.id)])

		list_price = 0
		val_price = 0
		if product_product_id.id:
			val_price = pricelist_id.price_get(product_product_id.id, 1, None)

			val_price_update = 0
			for key in val_price:
				val_price_update = val_price.get(key)
				list_price= val_price_update
			vals={
			'pricelist_id': pricelist_id.id,
			'update_price': True,
			}

			res.write({'item_ids': [(0, 0, vals)], 'list_price': list_price})


		#self.update_all_product_pack()

		return res

	def write(self, vals):

		product_model = self.env['product.product']

		pricelist_id = self.env['product.pricelist'].search([('id', '=', 1)])
		product_product_id = product_model.search([('product_tmpl_id', '=', self.id)])

		list_price = 0
		val_price = 0
		if product_product_id.id:
			val_price = pricelist_id.price_get(product_product_id.id, 1, None)

			print('poraca')

			val_price_update = 0
			for key in val_price:
				val_price_update = val_price.get(key)
				print(val_price_update)
				list_price= val_price_update


		vals['list_price']= list_price

		print(list_price)


		res= super(ProductTemplateInherit,self).write(vals)

		print('estamos entrando')
		print(res)

		return res
ProductTemplateInherit()
