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
from math import sqrt
import statistics as stats
import math

class ProductPriceListItem(models.Model):

	_inherit = 'product.pricelist.item'


	update_price = fields.Boolean(string="Actualizar Precio")


	@api.model
	def create(self, vals):

		res = super(ProductPriceListItem, self).create(vals)

		return res

	def write(self, vals):

		res= super(ProductPriceListItem,self).write(vals)

		model_product_template= self.env['product.template']
#		model_product_template.update_all_product_price_list()
#		model_product_template.update_all_product_pack()

		return res
ProductPriceListItem()
