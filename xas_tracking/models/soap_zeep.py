# -*- coding: utf-8 -*-
################################################################
#
# Author: Analytica Space
# Coder: Giovany Villarreal (giv@analytica.space)
#
################################################################

from odoo import models, fields, api, _
from zeep import Client, Settings
from zeep.exceptions import Fault
from lxml.etree import tostring

class SoapZeep(models.Model):
    _name = 'soap_zeep'
    _description = "Consumo SOAP con libreria zeep"

    @api.model
    def soap_request(self):
        wsdl = 'https://ws.smcmx.com.mx/wssmc_test/smcmx_service_test?wsdl'
        settings = Settings(strict=False, xml_huge_tree=True)
        print("wsdl", wsdl)
        client = Client(wsdl=wsdl, settings=settings)
        print("client", client)

        node = client.create_message(client.service, 'helloWorld')
        print("node", tostring(node))

        try:
            # Llama al método del servicio SOAP
            with client.settings(raw_response=True):
                response = client.service.helloWorld()
                print("response", response)
                print("response.content", response.content)
            # Maneja la respuesta aquí
            self.env['ir.logging'].create({
                'name': 'SOAP Response',
                'type': 'server',
                'level': 'info',
                'message': str(response.content),
                'path': 'xas_tracking',
                'line': '12',
                'func': 'soap_request'
            })
        except Fault as e:
            self.env['ir.logging'].create({
                'name': 'SOAP Error',
                'type': 'server',
                'level': 'error',
                'message': f"Error: {e}",
                'path': 'xas_tracking',
                'line': '19',
                'func': 'soap_request'
            })

    @api.model
    def soap_request2(self):
        wsdl = 'https://ws.smcmx.com.mx/wssmc_test/smcmx_service_test?wsdl'
        settings = Settings(strict=False, xml_huge_tree=True)
        print("wsdl", wsdl)
        client = Client(wsdl=wsdl, settings=settings)
        print("client", client)

        # node = client.create_message(client.service, 'enviarDetalleVenta',usuario="string", password="string", token="string", numeroDT=100, nombreDT="string")
        # print("node", tostring(node))

        # Datos para la solicitud
        data = {
            'usuario': 'tu_usuario',
            'password': 'tu_contraseña',
            'numeroDT': '12345',
            'nombreDT': 'Nombre del Distribuidor',
            'token': '12345678',
            'oListaClientes': {
                # 'clienteFinal': "hola mundo",
                # 'RFC': 'RFC123456',
                # 'razonSocial': 'Nombre del Cliente',
                # 'codigoPostal': '12345',
                # 'colonia': 'Colonia',
                # 'calle': 'Calle',
                # 'numeroExterior': '123',
                # 'tipoNegocioArea': 'ARMADORA',
                # 'areaEmpresarial': 'Planta Ensamble Final',
                # 'oListaFacturas': {
                #     'UUID': 'UUID123456',
                #     'folioFactura': '123',
                #     'serie': 'A',
                #     'fechaFactura': '2022-09-25',
                #     'tipoComprobante': 'I',
                #     'moneda': 'MXN',
                #     'tipoCambio': 1,
                #     'subtotal': 1000.00,
                #     'descuento': 0,
                #     'motivoDescuento': 'REBATE',
                #     'IVA': 160.00,
                #     'total': 1160.00,
                #     'oListaItems': [
                #         {
                #             'banderaFleteIncluidoEnPrecio': True,
                #             'codigoInterno': '003890',
                #             'codigoJapon': 'TU0805BU-100',
                #             'cantidad': 10,
                #             'codigoProductoDT': 'PROD123',
                #             'precioLista': 100.00,
                #             'precioVenta': 90.00,
                #             'montoUnitarioFlete': 0.00,
                #             'descuentoPorPartida': 10.00,
                #             'ordenCompra': 'OC123',
                #             'lineaFactura': 1
                #         }
                #     ]
                # }
            }
        }

        node = client.create_message(client.service, 'enviarDetalleVenta', **data)
        print("node", tostring(node))

        try:
            # Llama al método del servicio SOAP
            with client.settings(raw_response=True):
                oListaClientes = {
                    'clienteFinal':'string',
                }
                # response = client.service.enviarDetalleVenta(usuario="string", password="string", token="string", numeroDT=100, nombreDT="string", oListaClientes=oListaClientes)
                response = client.service.enviarDetalleVenta(**data)
                print("response", response)
                print("response.content", response.content)
            # Maneja la respuesta aquí
            self.env['ir.logging'].create({
                'name': 'SOAP Response',
                'type': 'server',
                'level': 'info',
                'message': str(response.content),
                'path': 'xas_tracking',
                'line': '12',
                'func': 'soap_request'
            })
        except Fault as e:
            self.env['ir.logging'].create({
                'name': 'SOAP Error',
                'type': 'server',
                'level': 'error',
                'message': f"Error: {e}",
                'path': 'xas_tracking',
                'line': '19',
                'func': 'soap_request'
            })

