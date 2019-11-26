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

	_inherit = 'stock.rule'
	
	@api.model
	def _prepare_purchase_request_line(self, request_id, product_id, product_qty, product_uom, values):
		procurement_uom_po_qty = product_uom._compute_quantity(product_qty, product_id.uom_po_id)
		order_lines = []
		model_order = self.env['sale.order']

		vals_order_lines = []


		_logger.info('############################')
		_logger.info('entrando en la funcon _prepare_purchase_request_line')

		if product_id.pack:
			_logger.info('estamos validando que es un paquete')

			if values['origin']:

				_logger.info('estamos capturando el origin de la venta')

				sale_order_id = model_order.sudo().search([('name', '=', values['origin'])])
				_logger.info(sale_order_id)

				for order_line in sale_order_id.order_line:
					order_lines = model_order.generate_order_line(order_line.pack_aux_ids, [], len(order_line.pack_aux_ids)-1, procurement_uom_po_qty, sale_order_id, False, True)


				_logger.info('esto es lo que va a crear')
				for x in order_lines:
					vals =  {
						'product_id': x['product_id'],
						'name': x['name'],
						'date_required': 'date_planned' in values and values['date_planned'] or fields.Datetime.now(),
						'product_uom_id': x['product_uom_po'],
						'product_qty': procurement_uom_po_qty,
						'request_id': request_id.id,
						'move_dest_ids': [(4, x.id) for x in values.get('move_dest_ids', [])],
						'orderpoint_id': values.get('orderpoint_id', False) and values.get('orderpoint_id').id,
						}
						
					vals_order_lines.append(vals)

				print(vals_order_lines)

				return vals_order_lines

				_logger.info("#################")

		_logger.info("----------")
		_logger.info("Estamos por fuera de un paquete")
		return {
			'product_id': product_id.id,
			'name': product_id.name,
			'date_required': 'date_planned' in values and values['date_planned'] or fields.Datetime.now(),
			'product_uom_id': product_id.uom_po_id.id,
			'product_qty': procurement_uom_po_qty,
			'request_id': request_id.id,
			'move_dest_ids': [(4, x.id) for x in values.get('move_dest_ids', [])],
			'orderpoint_id': values.get('orderpoint_id', False) and values.get('orderpoint_id').id,
		}



	@api.multi
	def create_purchase_request(self, product_id, product_qty, product_uom,
								origin, values):
		"""
		Create a purchase request containing procurement order product.
		"""
		purchase_request_model = self.env['purchase.request']
		purchase_request_line_model = self.env['purchase.request.line']
		cache = {}
		pr = self.env['purchase.request']
		domain = self._make_pr_get_domain(values)
		if domain in cache:
			pr = cache[domain]
		elif domain:
			pr = self.env['purchase.request'].sudo().search([dom for dom in domain])
			pr = pr[0] if pr else False
			cache[domain] = pr
		if not pr:
			request_data = self._prepare_purchase_request(origin, values)
			pr = purchase_request_model.create(request_data)
			cache[domain] = pr
		elif not pr.origin or origin not in pr.origin.split(', '):
			if pr.origin:
				if origin:
					pr.write({'origin': pr.origin + ', ' + origin})
				else:
					pr.write({'origin': pr.origin})
			else:
				pr.write({'origin': origin})

		# Create Line
		values['origin']=origin
		request_line_data = self._prepare_purchase_request_line(pr, product_id, product_qty, product_uom, values)
		#creanto request line

		_logger.info('Finamente creamos todo')
		_logger.info(request_line_data)
		for x in request_line_data:
			purchase_request_line_model.create(x)


SaleOrderInherit()
