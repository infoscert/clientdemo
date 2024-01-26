# -*- coding: utf-8 -*-

{
    "name" : "Approvals Customization",
    "version" : "16.0.0.0",
    'category' : "Customization",
    "summary" : "Approvals Customization",
    "description": """
                 Approvals Customization
    """,
    "author" : "Vrushparva Vaishnav",
    "website" : "",
    "depends" : ['approvals', 'isn_approval_custom','ag_field_service'],
    "data" :[
        'data/product_data.xml',
        'views/approvals.xml',
        'views/account.xml',
        'views/sale_order.xml',
        'reports/report_purchase_order.xml',
        'reports/report_account_move.xml',
        'reports/report_sale_order.xml',
        'reports/report_rfq.xml',

    ],
    "auto_install": False,
    "installable": True,
}

