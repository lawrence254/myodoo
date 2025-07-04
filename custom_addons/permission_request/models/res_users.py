from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    access_request_ids = fields.One2many('access.request', 'user_id', string='Access Requests')
    access_request_count = fields.Integer(string='Total Access Requests', compute='_compute_access_request_counts')
    pending_access_request_count = fields.Integer(string='Pending Requests', compute='_compute_access_request_counts')
    approved_access_request_count = fields.Integer(string='Approved Requests', compute='_compute_access_request_counts')
    rejected_access_request_count = fields.Integer(string='Rejected Requests', compute='_compute_access_request_counts')

    @api.depends('access_request_ids.state')
    def _compute_access_request_counts(self):
        for user in self:
            requests = user.access_request_ids
            user.access_request_count = len(requests)
            user.pending_access_request_count = len(requests.filtered(lambda r: r.state == 'submitted'))
            user.approved_access_request_count = len(requests.filtered(lambda r: r.state == 'approved'))
            user.rejected_access_request_count = len(requests.filtered(lambda r: r.state == 'rejected'))

    def action_view_access_requests(self):
        """ Action to view all access requests for the user """
        self.ensure_one()
        action = self.env.ref('access_request.action_user_access_requests').read()[0]
        action['domain'] = [('user_id', '=', self.id)]
        action['context'] = {
            'default_user_id': self.id,
        }
        return action
