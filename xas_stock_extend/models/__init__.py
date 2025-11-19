# -*- coding: utf-8 -*-
# ----------------------------------------------------------------
# Company: Analytica Space
# Author: Wesley Ortiz (wessortiz@gmail.com)
# ----------------------------------------------------------------

# Nuevos objetos
from . import product_custom_mla
from . import scientific_variety_product
from . import commercial_variety_product
from . import tag_product
from . import quality_product
from . import caliber_product
from . import container_product
from . import package_product
from . import whole_sale_price_line
from . import product_pricelist_mla
from . import weight_mla
from . import product_alert
from . import product_move_line
from . import product

# Herencia de objetos nativos de Odoo
from . import res_company
from . import product_template
from . import product_product
from . import stock_picking
from . import res_config_settings
from . import pos_order
from . import pos_order_line
from . import stock_move
from . import stock_move_line
from . import mrp_production
from . import account_move_line

# Herencia de nuestros propios objetos
from . import trip_number