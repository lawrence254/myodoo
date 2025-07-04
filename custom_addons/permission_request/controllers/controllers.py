# -*- coding: utf-8 -*-
# from odoo import http


# class PermissionRequest(http.Controller):
#     @http.route('/permission_request/permission_request', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/permission_request/permission_request/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('permission_request.listing', {
#             'root': '/permission_request/permission_request',
#             'objects': http.request.env['permission_request.permission_request'].search([]),
#         })

#     @http.route('/permission_request/permission_request/objects/<model("permission_request.permission_request"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('permission_request.object', {
#             'object': obj
#         })

