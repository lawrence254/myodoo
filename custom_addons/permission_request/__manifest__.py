# -*- coding: utf-8 -*-
{
    'name': "Permission Request",

    'summary': "Permission-based approval system for restricted actions",

    'description': """
        This module implements an approval workflow system that:
            - Intercepts permission-denied scenarios
            - Allows users to request access from administrators
            - Provides admin interface for approving/rejecting requests
            - Sends notifications and maintains audit trail
    """,

    'author': "Lawrence Karanja",
    'website': "https://nowebsite.com",
    'category': 'administration',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/mail_templates.xml',
        'views/access_request_views.xml',
        'views/res_users_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

