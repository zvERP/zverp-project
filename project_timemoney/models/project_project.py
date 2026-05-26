from odoo import models, fields, api, _


class ProjectProject(models.Model):
    _inherit = 'project.project'

    # store=True to allow sorting in list view
    analytic_account_balance = fields.Monetary(
        related='analytic_account_id.balance',
    )

    project_total_hours = fields.Float(
        string='Total Hours',
        compute='_compute_project_total_hours',
        compute_sudo=True,
        help='Sum of hours logged in timesheets for this project',
    )

    project_budget = fields.Monetary(
        string='Budget',
        compute='_compute_project_budget',
        compute_sudo=True,
        help='Untaxed amount of the sale order linked to this project',
    )

    @api.depends('timesheet_ids.unit_amount')
    def _compute_project_total_hours(self):
        data = self.env['account.analytic.line'].read_group(
            [('project_id', 'in', self.ids)],
            ['project_id', 'unit_amount'],
            ['project_id'],
        )
        mapped = {d['project_id'][0]: d['unit_amount'] for d in data}
        for project in self:
            project.project_total_hours = mapped.get(project.id, 0.0)

    @api.depends('analytic_account_id')
    def _compute_project_budget(self):
        for project in self:
            confirmed_orders = project._get_project_sale_orders().filtered(
                lambda so: so.state in ('sale', 'done')
            )
            project.project_budget = sum(confirmed_orders.mapped('amount_untaxed'))

    def _get_project_sale_orders(self):
        self.ensure_one()
        return (self.sale_order_id | self.task_ids.sale_order_id)

    def action_open_analytic_lines(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'analytic.account_analytic_line_action'
        )
        analytic_id = self.analytic_account_id.id
        action['name'] = 'Gross Margin — %s' % self.name
        action['domain'] = [('account_id', '=', analytic_id)]
        action['context'] = {
            'search_default_group_date': 1,
            'default_account_id': analytic_id,
        }
        return action

    def action_view_confirmed_budgets(self):
        self.ensure_one()
        confirmed_orders = self._get_project_sale_orders().filtered(
            lambda so: so.state in ('sale', 'done')
        )
        action = self.env['ir.actions.act_window']._for_xml_id('sale.action_orders')
        action['name'] = _("%(name)s's Confirmed Budgets", name=self.name)
        action['domain'] = [('id', 'in', confirmed_orders.ids)]
        action['context'] = {'create': False}
        return action
