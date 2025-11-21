{
    "name": "Corporativo Xalostoc: delivery slip with groups",
    "summary":
        """
        Module to include a custom delivery slip which groups lines by product_id. 
        """,
    "description":
        """
        Module to include a custom delivery slip which groups lines by product_id.
        After a group of stock.move.lines with the same product_id, an additional row shows the sum of quantities.
        Developer: ralb
        Task ID: 3803001
        """,
    "author": "Odoo Development Services",
    "maintainer": "Odoo Development Services",
    "license": "OPL-1",
    "website": "https://www.odoo.com",
    "category": "Custom Modules",
    "version": "1.0.0",
    "installable": True,
    "depends": ["stock"],
    "data": [
        "views/report_deliveryslip_xalostoc.xml",
    ],
}
