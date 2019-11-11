##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models, api
import odoo.addons.decimal_precision as dp


class ProductPackLineInherit(models.Model):
    _inherit = 'product.pack.line'

    @api.multi
    def get_sale_order_line_vals(self, line, order):
        self.ensure_one()
        quantity = self.quantity * line.product_uom_qty
        line_vals = {
            'order_id': order.id,
            'product_id': self.product_id.id or False,
            'pack_parent_line_id': line.id,
            'pack_depth': line.pack_depth + 1,
            #'sequence': sequence,
            'company_id': order.company_id.id,
        }
        sol = line.new(line_vals)
        sol.product_id_change()
        sol.product_uom_qty = quantity
        sol.product_uom_change()
        sol._onchange_discount()
        vals = sol._convert_to_write(sol._cache)

        discount = 0.0
        if line.product_id.pack_price_type not in [
                'fixed_price', 'totalice_price']:
            discount = 100.0 - (
                (100.0 - sol.discount) * (100.0 - self.discount) / 100.0)

        vals.update({
            'discount': discount,
            'is_pack': False,
            'name': '%s%s' % (
                '> ' * (line.pack_depth + 1), sol.name
            ),
        })
        return vals

ProductPackLineInherit()
