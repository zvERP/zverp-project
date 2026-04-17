from odoo import models, fields, api


class ProjectProject(models.Model):
    _inherit = 'project.project'

    # store=True to allow sorting in list view
    analytic_account_balance = fields.Monetary(store=True)

    project_total_hours = fields.Float(
        string='Total Hours',
        compute='_compute_project_total_hours',
        compute_sudo=True,
        store=True,
        help='Sum of hours logged in timesheets for this project',
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
