# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.integrations.utils import create_payment_gateway, get_payment_gateway_controller
from frappe.utils import get_url, call_hook_method
from frappe import _
import mercadopago


class MercadopagoSettings(Document):

    supported_currencies = ["ARS"]

    def validate_transaction_currency(self, currency):
        if currency not in self.supported_currencies:
            frappe.throw(_("Please select another payment method. Pagos360 does not support transactions in currency '{0}'").format(currency))

    def validate(self):
        create_payment_gateway("Mercadopago")
        call_hook_method('payment_gateway_enabled', gateway="Mercadopago")
        if not self.flags.ignore_mandatory:
            self.validate_mercadopago_credentials()

    def validate_mercadopago_credentials(self):
        try:
            mercadopago_settings = get_payment_gateway_controller("Mercadopago")
            mp = mercadopago.SDK(mercadopago_settings.access_token)
            mp.user().get()
        except Exception:
            frappe.throw(_("Invalid payment gateway credentials"))

    def get_payment_url(self, **kwargs):
        """Url para solicitudes de pago"""
        mercadopago_settings = get_payment_gateway_controller("Mercadopago")
        mp = mercadopago.SDK(mercadopago_settings.access_token)
        payment_request = frappe.get_doc(kwargs["reference_doctype"], kwargs["reference_docname"])
        reference_doc = frappe.get_doc(payment_request.reference_doctype, payment_request.reference_name)

        preference_data = {
            "items": [
                {
                    "title": item.item_code,
                    "description": item.description,
                    "category_id": "otros",  # https://api.mercadopago.com/item_categories
                    "quantity": item.qty,
                    "currency_id": reference_doc.currency,
                    "unit_price": item.rate,  # really?
                } for item in reference_doc.items
            ],
            "back_urls": {  # TODO: configurables?
                "success": get_url(),
                "failure": get_url(),
                "pending": get_url()
            },
            "auto_return": "approved",
            "notification_url": "{}/api/method/frappe.integrations.doctype.mercadopago_settings.mercadopago_settings.ipn".format(get_url()),
            "external_reference": payment_request.name,
            # "payer": {
            #     "name": "Charles",
            #     "surname": "Luevano",
            #     "email": "charles@hotmail.com",
            #     "phone": {
            #         "area_code": "",
            #         "number": "949 128 866"
            #     },
            #     "identification": {
            #         "type": "DNI",
            #         "number": "12345678"
            #     },
            #     "address": {
            #         "street_name": "Street",
            #         "street_number": 123,
            #         "zip_code": "5700"
            #     }
            # }
        }

        preference_response = mp.preference().create(preference_data)
        preference = preference_response["response"]

        if mercadopago_settings.sandbox:
            return preference['sandbox_init_point']
        return preference['init_point']


@frappe.whitelist(allow_guest=True, xss_safe=True)
def ipn(**args):
    """
    /api/method/frappe.integrations.doctype.mercadopago_settings.mercadopago_settings.ipn
    """
    return "IPNeado"
