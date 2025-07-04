from odoo import models, api, _
from odoo.exceptions import AccessError
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class BaseModelAccessInterceptor(models.AbstractModel):
    _name = 'base.model.access.interceptor'
    _description = 'Access Interceptor for Permission Requests'

    def _handle_access_error(self, operation, model_name, record_ids=None):
        """ Handle access errors by creating access requests """
        if not self.env.context.get('access_request_enabled', True):
            return False
        
        # Don't create access requests for system models or own models
        if(model_name.startswith('ir.') or
           model_name.startswith('base.') or
           model_name.startswith('access.')):
            return False
        
        # Check if a user has the permission to create access requests
        if not self.env.user.has_group('base.group_user'):
            _logger.warning(
                "User %s attempted to create access request for %s but does not have permission.",
                self.env.user.login, model_name
            )
            return False
        
        # Get additional context information from the request if available
        url = None
        menu_name = None
        if hasattr(request, 'httprequest') and request.httprequest:
            url = request.httprequest.url
            # Extract menu name if available
            if hasattr(request, 'session') and 'menu_name' in request.session:
                menu_name = request.session.get('menu_name')
        # Create the access request record
        try:
            access_request= self.env['access.request'].create({
                'model_name':model_name,
                'action_type':operation,
                'record_id': record_ids[0] if record_ids and len(record_ids) == 1 else None,
                'reason': f'Access requested for {operation} operation on {model_name}',
                'url': url,
                'menu_name': menu_name,
                'state':'draft',
                'priority': 'medium',
            })

            return access_request.id
        except Exception as e:
            _logger.error(f'Failed to create access request for {model_name} ({record_ids}): {str(e)}')
            return False
        
class BaseModel(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        """ Override to intercept access rights checks and handle them """
        try:
            return super().check_access_rights(operation, raise_exception=raise_exception)
        except AccessError as e:
            if raise_exception and self.env.context.get('create_access_request_on_deny', False):
                interceptor = self.env['base.model.access.interceptor']
                request_id = interceptor._handle_access_error(operation, self._name)
                if request_id:
                    raise AccessRequestCreated(
                        _('Access Denied. An access request (#%s) has been created and sent to an administrator for review.') % request_id,
                        request_id=request_id) from e
            raise

    def check_access_rule(self, operation):
        """ Override to intercept access rule checks and handle them """
        try:
            return super().check_access_rule(operation)
        except AccessError as e:
            if self.env.context.get('create_access_request_on_deny', False):
                interceptor = self.env['base.model.access.interceptor']
                request_id = interceptor._handle_access_error(operation, self._name, self.ids)
                if request_id:
                    raise AccessRequestCreated(
                        _('Access Denied. An access request (#%s) has been created and sent to an administrator for review.') % request_id,
                        request_id=request_id) from e
            raise
class AccessRequestCreated(AccessError):
    """ Custom exception raised when an access request is created """
    def __init__(self, message, request_id=None):
        super().__init__(message)
        self.request_id = request_id

class AccessRequestHelper(models.AbstractModel):
    _name = 'access.request.helper'
    _description = 'Access Request Helper Methods'

    @api.model
    def request_access_for_action(self, model_name, action_type, reason, **kwargs):
        """ Helper method to create an access request from anywhere in the codebase """

        return self.env['access.request'].create_access_request(
            model_name=model_name,
            action_type=action_type,
            reason=reason,
            **kwargs
        )
    
    @api.model
    def check_temporary_access(self, model_name, action_type, record_id=None):
        """ Check if temporary access is granted for a specific action """
        user = self.env.user

        # Check for approved non-expired operation requests
        domain = [
            ('user_id', '=', user.id),
            ('model_name', '=', model_name),
            ('action_type', '=', action_type),
            ('state', '=', 'approved'),
            ('|', 'access_expires_at', '=', False),
            ('access_expires_at', '>', self.env.cr.now())
        ]

        if record_id:
            domain.extend(['|', ('record_id', '=', record_id), ('record_id', '=', False)])

        return bool(self.env['access.request'].search(domain, limit=1))
    @api.model
    def with_access_request_context(self):
        """ Return environment with access request context enabled """
        return self.with_context(
            create_access_request_on_deny=True,
            access_request_enabled=True
        )