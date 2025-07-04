# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class AccessRequest(models.Model):
    _name='access.request'
    _description = 'Access Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'display_name'

    @api.depends('user_id', 'model_name', 'action_type')
    def _compute_display_name(self):
        for record in self:
            record.display_name=f"{record.user_id.name} - {record.model_name} ({record.action_type})"

    display_name = fields.Char(compute='_compute_display_name', store=True)
    user_id = fields.Many2one('res.users', string='Requesting User', required=True, default=lambda self: self.env.user)
    model_name = fields.Char(string='Model', required=True)
    model_display_name = fields.Char(string='Model Display Name')
    record_id = fields.Integer(string='Record ID')
    action_type = fields.Selection([
        ('read', 'Read'),
        ('write', 'Write'),
        ('create', 'Create'),
        ('unlink', 'Delete'),
        ('action', 'Action'),
    ], string='Action Type', required=True)

    reason = fields.Text(string='Reason for Request', required=True)
    justification = fields.Text(string='Business Justification')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ], string='Status', default='draft', tracking=True)
    
    # Request Approval Details
    approver_id = fields.Many2one('res.users', string='Approver')
    approval_date = fields.Datetime(string='Approval Date')
    rejection_reason = fields.Text(string='Rejection Reason')

    # Temporary Access
    temporary_access = fields.Boolean(string='Temporary Access', default=True)
    access_duration = fields.Integer(string='Access Duration (hours)', default=24)
    access_expires_at = fields.Datetime(string='Access Expires At')

    # Contextual Information
    url = fields.Char(string='Original URL')
    menu_name = fields.Char(string='Menu/Action Name')
    error_message = fields.Text(string='Original Error Message')

    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], string='Priority', default='medium')

    # Computed Fields
    is_expired = fields.Boolean(string='Is Expired' ,compute='_compute_is_expired')
    can_approve= fields.Boolean(string='Can Approve', compute='_compute_can_approve')

    @api.depends('access_expires_at')
    def _compute_is_expired(self):
        now = fields.Datetime.now()
        for record in self:
            record.is_expired = bool(record.access_expires_at and record.access_expires_at < now)

    @api.depends('user_id')
    def _compute_can_approve(self):
        for record in self:
            record.can_approve = (
                self.env.user.has_group('access_request.group_access_request_admin') and
                record.user_id.id != self.env.user.id
            )


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('model_name') and not vals.get('model_display_name'):
                model_rec = self.env['ir.model'].sudo().search([('model', '=', vals['model_name'])], limit=1)
                vals['model_display_name'] = model_rec.name or vals['model_name']
        return super().create(vals_list)

    
    def action_submit(self):
        """       Submit the access request for approval
        """
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft requests can be sumbitted."))
        
        self.state = 'submitted'
        self._notify_approvers()
        self.message_post(
            body=_("Access request submitted for approval."),
            message_type='notification',
        )
    def action_approve(self):
        """       Approve the access request
        """
        self.ensure_one()
        if not self.can_approve:
            raise AccessError(_("You do not have permission to approve this request."))
        
        self.write({
            'state':'approved',
            'approver_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
        })

        # Notify the requester
        self.notify_user_approval()

        self.message_post(
            body=_('Access request approved by %s.' % self.env.user.name),
            message_type='notification',
        )
    def action_reject(self):
        """       Reject the access request
        """
        self.ensure_one()

        if not self.can_approve:
            raise AccessError(_("You do not have permission to reject this request."))
        
        return{
            'name': _('Reject Access Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'access.request.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_id': self.id}
        }
    def _reject_with_reason(self, reason):
        """       Internal method to handle rejection with a reason
        """
        self.write({
            'state':'rejected',
            'approver_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
            'rejection_reason':reason,
        })

        self._notify_user_rejection()
        self.message_post(
            body=_('Access request rejected by %s. Reason: %s' % (self.env.user.name, reason)),
            message_type='notification',
        )
    def _notify_approvers(self):
        """      Notify the approvers about the new request
        """
        admin_users = self.env.ref('access_request.group_access_request_admin').users
        if admin_users:
            template = self.env.ref('access_request.email_template_access_request_notification')
            for admin in admin_users:
                if admin != self.user_id: # Notification not sent if the user is already an admin
                    template.with_context(recipient_user=admin).send_mail(self.id, force_send=True)
    def _notify_user_approval(self):
        """       Notify the user about the approval
        """
        template = self.env.ref('access_request.email_template_access_request_approved')
        template.send_mail(self.id, force_send=True)

    def _notify_user_rejection(self):
        """       Notify the user about the rejection
        """
        template = self.env.ref('access_request.email_template_access_request_rejected')
        template.send_mail(self.id, force_send=True)


    @api.model
    def create_access_request(self, model_name, action_type, record_id=None, reason=None, **kwargs):
        """       Create a new access request
        """
        vals = {
            'model_name': model_name,
            'action_type':action_type,
            'record_id': record_id,
            'reason': reason or 'Access requested programatically',
            'state': 'submitted',
            **kwargs
        }
        request = self.create(vals)
        request._notify_approvers()
        return request
    @api.model
    def cleanup_expired_requests(self):
        """       Cleanup expired requests
        """
        expired_requests = self.search([
            ('state', '=', 'approved'),
            ('access_expires_at', '<', fields.Datetime.now()),
        ])
        expired_requests.write({'state': 'expired'})
        _logger.info(f'Marked {len(expired_requests)} requests as expired.')

class AccessRequestRejectWizard(models.TransientModel):
    _name = 'access.request.reject.wizard'
    _description = 'Access Request Rejection Wizard'

    request_id = fields.Many2one('access.request', string='Access Request', required=True)
    rejection_reason = fields.Text(string='Rejection Reason', required=True)

    def action_reject(self):
        """       Reject the access request with a reason
        """
        self.ensure_one()
        if not self.request_id.can_approve:
            raise AccessError(_("You do not have permission to reject this request."))
        
        self.request_id._reject_with_reason(self.rejection_reason)
        return {'type': 'ir.actions.act_window_close'}
    