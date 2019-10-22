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


class ProductTemplateInherit(models.Model):

	_inherit = 'product.template'

	def calculate_list_price_pack(self, pack_line_ids, list_price, i):

		if i == -1:
			return 0

		if pack_line_ids[i].product_id.pack:

			pack_line = pack_line_ids[i].product_id.pack_line_ids
			list_price += self.calculate_list_price_pack(pack_line, list_price, len(pack_line)-1)

		else:
			list_price = (pack_line_ids[i].product_id.list_price * pack_line_ids[i].quantity) + ((pack_line_ids[i].product_id.list_price * pack_line_ids[i].quantity) * (pack_line_ids[i].discount)/100)

		return list_price + self.calculate_list_price_pack(pack_line_ids, list_price, i=i-1)

	@api.model
	def update_all_product_pack(self):

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

ProductTemplateInherit()
