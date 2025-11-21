from odoo.fields import Command

from odoo.addons.sale.tests.test_sale_to_invoice import TestSaleToInvoice

def test_invoice_analytic_rule_with_account_prefix(self):
        """
        Patch original test to insert product_uom_qty = 1 at order line creation due to removing 
        default value on field
        """
        self.env.user.groups_id += self.env.ref('analytic.group_analytic_accounting')
        analytic_plan_default = self.env['account.analytic.plan'].create({
            'name': 'default',
            'applicability_ids': [Command.create({
                'business_domain': 'invoice',
                'applicability': 'optional',
            })]
        })
        analytic_account_default = self.env['account.analytic.account'].create({'name': 'default', 'plan_id': analytic_plan_default.id})

        analytic_distribution_model = self.env['account.analytic.distribution.model'].create({
            'account_prefix': '400000',
            'analytic_distribution': {analytic_account_default.id: 100},
            'product_id': self.product_a.id,
        })

        so = self.env['sale.order'].create({'partner_id': self.partner_a.id})
        self.env['sale.order.line'].create({
            'order_id': so.id,
            'name': 'test',
            'product_id': self.product_a.id,
            'product_uom_qty': 1.0
        })
        self.assertFalse(so.order_line.analytic_distribution, "There should be no tag set.")
        so.action_confirm()
        so.order_line.qty_delivered = 1
        aml = so._create_invoices().invoice_line_ids
        self.assertRecordValues(aml, [{'analytic_distribution': analytic_distribution_model.analytic_distribution}])    

def test_so_create_multicompany(self):
        """Check that only taxes of the right company are applied on the lines."""
        # Preparing test Data
        product_shared = self.env['product.template'].create({
            'name': 'shared product',
            'invoice_policy': 'order',
            'taxes_id': [(6, False, (self.company_data['default_tax_sale'] + self.company_data_2['default_tax_sale']).ids)],
            'property_account_income_id': self.company_data['default_account_revenue'].id,
        })

        so_1 = self.env['sale.order'].with_user(self.company_data['default_user_salesman']).create({
            'partner_id': self.env['res.partner'].create({'name': 'A partner'}).id,
            'company_id': self.company_data['company'].id,
        })
        so_1.write({
            'order_line': [Command.create({
                    'product_id': product_shared.product_variant_id.id,
                    'product_uom_qty': 1.0  
                })],
        })
        self.assertEqual(so_1.order_line.product_uom_qty, 1)

        self.assertEqual(so_1.order_line.tax_id, self.company_data['default_tax_sale'],
            'Only taxes from the right company are put by default')
        so_1.action_confirm()
        # i'm not interested in groups/acls, but in the multi-company flow only
        # the sudo is there for that and does not impact the invoice that gets created
        # the goal here is to invoice in company 1 (because the order is in company 1) while being
        # 'mainly' in company 2 (through the context), the invoice should be in company 1
        inv = so_1.sudo().with_context(
            allowed_company_ids=(self.company_data['company'] + self.company_data_2['company']).ids
        )._create_invoices()
        self.assertEqual(
            inv.company_id,
            self.company_data['company'],
            'invoices should be created in the company of the SO, not the main company of the context')

TestSaleToInvoice.test_invoice_analytic_rule_with_account_prefix = test_invoice_analytic_rule_with_account_prefix
TestSaleToInvoice.test_so_create_multicompany = test_so_create_multicompany
