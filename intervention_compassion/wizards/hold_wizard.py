# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import models, fields, api, _
from openerp.exceptions import Warning


class HoldWizard(models.TransientModel):
    """
    Class used for searching interventions in the Mi3 Portal.
    """
    _name = 'compassion.intervention.hold.wizard'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    intervention_id = fields.Many2one(
        'compassion.global.intervention', 'Intervention'
    )
    created_intervention_id = fields.Many2one('compassion.intervention')
    hold_amount = fields.Float(required=True)
    usd = fields.Many2one(related='intervention_id.currency_usd')
    expiration_date = fields.Date(required=True)
    next_year_opt_in = fields.Boolean()
    primary_owner = fields.Many2one(
        'res.users', default=lambda s: s.env.user,
        domain=[('share', '=', False)], required=True
    )
    secondary_owner = fields.Char()
    service_level = fields.Selection([
        ("Level 1", _("Level 1")),
        ("Level 2", _("Level 2")),
        ("Level 3", _("Level 3")),
    ], required=True, default='Level 2')

    @api.multi
    def hold_sent(self, hold_vals):
        """ Called when hold is created """
        intervention_vals = self.intervention_id.get_vals()
        intervention_vals.update(hold_vals)
        intervention_vals.update({
            'expiration_date': self.expiration_date,
            'next_year_opt_in': self.next_year_opt_in,
            'primary_owner': self.primary_owner.id,
            'secondary_owner': self.secondary_owner,
            'service_level': self.service_level,
        })
        intervention = self.env['compassion.intervention'].search([
            ('intervention_id', '=', self.intervention_id.intervention_id)])
        if intervention:
            intervention.write(intervention_vals)
        else:
            # Grant create access rights to create intervention
            intervention = self.env[
                'compassion.intervention'].with_context(
                async_mode=True).sudo().create(intervention_vals)
            # Replace author of record to avoid having admin
            intervention.message_ids.sudo().write({
                'author_id': self.env.user.partner_id.id})
        self.created_intervention_id = intervention

    @api.multi
    def make_hold(self):
        self.ensure_one()
        create_hold = self.env.ref(
            'intervention_compassion.intervention_create_hold_action')
        message = self.env['gmc.message.pool'].with_context(
            async_mode=False).create({
                'action_id': create_hold.id,
                'object_id': self.id,
            })
        if message.state == 'failure':
            raise Warning(message.failure_reason)

        return {
            'name': _('Intervention'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'compassion.intervention',
            'context': self.env.context,
            'res_id': self.created_intervention_id.id,
            'target': 'current',
        }
