# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import api, fields, models, _

class SHMailActivitySchedule(models.TransientModel):
    _inherit = 'mail.activity.schedule'
    
    supervisor_id = fields.Many2one('res.users', default=lambda self: self.env.user, string="Supervisor",domain=[('share','=',False)])
    sh_activity_tags = fields.Many2many(
        "sh.activity.tags", string='Activity Tags')
    
    sh_display_multi_user = fields.Boolean(
        compute='_compute_sh_display_multi_user')
    sh_user_ids = fields.Many2many('res.users', string="Assign Multi Users",domain=[('share','=',False)])
    sh_create_individual_activity = fields.Boolean(
        'Individual activities for multi users ?')
    
    
    @api.depends('company_id')
    def _compute_sh_display_multi_user(self):
        if self:
            for rec in self:
                rec.sh_display_multi_user = False
                if rec.company_id and rec.company_id.sh_display_multi_user:
                    rec.sh_display_multi_user = True
                    
    def _action_schedule_activities(self):
        result = super()._action_schedule_activities()
        result.update({'company_id':self.company_id,
                       'sh_user_ids':self.sh_user_ids.ids,
                       'sh_activity_tags':self.sh_activity_tags.ids,
                       'sh_display_multi_user':self.sh_display_multi_user,
                       'supervisor_id':self.supervisor_id.id,
                       'sh_create_individual_activity':self.sh_create_individual_activity,
                       })
        return result