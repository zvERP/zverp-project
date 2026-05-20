from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _recompute_project_budget_from_analytic(self, extra_analytic_ids=None):
        analytic_ids = set(self.mapped('analytic_account_id').ids)
        if extra_analytic_ids:
            analytic_ids |= set(extra_analytic_ids)
        analytic_ids.discard(False)
        if not analytic_ids:
            return
        projects = self.env['project.project'].search([
            ('analytic_account_id', 'in', list(analytic_ids))
        ])
        if projects:
            projects._compute_project_budget()

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._recompute_project_budget_from_analytic()
        return orders

    def write(self, vals):
        old_analytic_ids = set(self.mapped('analytic_account_id').ids)
        res = super().write(vals)
        trigger_fields = {'analytic_account_id', 'state', 'amount_untaxed', 'order_line'}
        if trigger_fields.intersection(vals):
            self._recompute_project_budget_from_analytic(extra_analytic_ids=old_analytic_ids)
        return res

    def unlink(self):
        analytic_ids = set(self.mapped('analytic_account_id').ids)
        res = super().unlink()
        if analytic_ids:
            self.env['project.project'].search([
                ('analytic_account_id', 'in', list(analytic_ids))
            ])._compute_project_budget()
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _recompute_project_budget_from_orders(self, extra_order_ids=None):
        orders = self.mapped('order_id')
        if extra_order_ids:
            orders |= self.env['sale.order'].browse(list(extra_order_ids))
        if orders:
            orders._recompute_project_budget_from_analytic()

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._recompute_project_budget_from_orders()
        return lines

    def write(self, vals):
        old_order_ids = set(self.mapped('order_id').ids)
        res = super().write(vals)
        trigger_fields = {
            'order_id', 'price_unit', 'discount', 'tax_id', 'product_uom_qty',
            'price_subtotal', 'price_total', 'price_tax'
        }
        if trigger_fields.intersection(vals):
            self._recompute_project_budget_from_orders(extra_order_ids=old_order_ids)
        return res

    def unlink(self):
        order_ids = set(self.mapped('order_id').ids)
        res = super().unlink()
        if order_ids:
            self.env['sale.order'].browse(list(order_ids))._recompute_project_budget_from_analytic()
        return res
