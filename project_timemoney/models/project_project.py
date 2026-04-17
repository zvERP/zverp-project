from odoo import models, fields, api


class ProjectProject(models.Model):
    _inherit = 'project.project'

    zverp_total_hours = fields.Float(
        string='Total Horas',
        compute='_compute_zverp_total_hours',
        compute_sudo=True,
        store=True,
        help='Suma de horas imputadas en partes de trabajo del proyecto',
    )

    @api.depends('timesheet_ids.unit_amount')
    def _compute_zverp_total_hours(self):
        data = self.env['account.analytic.line'].read_group(
            [('project_id', 'in', self.ids)],
            ['project_id', 'unit_amount'],
            ['project_id'],
        )
        mapped = {d['project_id'][0]: d['unit_amount'] for d in data}
        for project in self:
            project.zverp_total_hours = mapped.get(project.id, 0.0)

    def action_open_analytic_lines(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'analytic.account_analytic_line_action'
        )
        analytic_id = self.analytic_account_id.id
        action['name'] = 'Margen Bruto — %s' % self.name
        action['domain'] = [('account_id', '=', analytic_id)]
        action['context'] = {
            'search_default_group_date': 1,
            'default_account_id': analytic_id,
        }
        return action
