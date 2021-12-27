# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.integrations.utils import create_payment_gateway, get_payment_gateway_controller
from frappe.utils import get_url, call_hook_method
from frappe import _
import mercadopago


class MercadopagoSettings(Document):

    supported_currencies = ["ARS", "USD"]

    def validate_transaction_currency(self, currency):
        if currency not in self.supported_currencies:
            frappe.throw(_("Please select another payment method. Mercadopago does not support transactions in currency '{0}'").format(currency))

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
        """
        Url para solicitudes de pago
        """
        mercadopago_settings = get_payment_gateway_controller("Mercadopago")
        mp = mercadopago.SDK(mercadopago_settings.access_token)
        payment_request = frappe.get_doc(kwargs["reference_doctype"], kwargs["reference_docname"])
        notification_url = get_url("/api/method/frappe.integrations.doctype.mercadopago_settings.mercadopago_settings.ipn")

        if mercadopago_settings.sandbox:
            notification_url = "https://webhook.site/c5bc1aba-2504-4919-8b4b-b0a6c9c73180"

        preference_data = {
            "items": [
                {
                    "id": kwargs["reference_docname"],
                    "title": kwargs["title"].decode("utf-8"),
                    "description": kwargs["description"].decode("utf-8"),
                    "quantity": 1,
                    "currency_id": kwargs["currency"].decode("utf-8"),
                    "unit_price": kwargs["amount"],
                }
            ],
            "back_urls": {
                "success": mercadopago_settings.success_url or get_url(),
                "failure": mercadopago_settings.failure_url or get_url(),
                "pending": mercadopago_settings.pending_url or get_url()
            },
            "auto_return": "approved",
            "notification_url": notification_url,
            "external_reference": payment_request.name,
            "payer": {
                "name": kwargs["payer_name"].decode("utf-8"),
                "email": kwargs["payer_email"]
            },
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


def crear_notificacion_mercadopago(payment):
    import json
    notificacion = frappe.get_doc({
        "doctype": "Notificacion Mercadopago",
        "payment_id": payment.get('id', 0),
    })

    payer = payment.get("payer", {})
    transaction_details = payment.get("transaction_details", {})

    notificacion.payment_external_reference = payment.get("external_reference", "")
    notificacion.payment_status = payment.get("status", "")
    notificacion.payment_status_detail = payment.get("status_detail", "")
    notificacion.payment_description = payment.get("description", "")
    notificacion.payment_date_created = payment.get("date_created", "")
    notificacion.payment_date_approved = payment.get("date_approved", "")

    notificacion.payment_currency_id = payment.get("currency_id", "")
    notificacion.payment_transaction_amount = payment.get("transaction_amount", 0)
    notificacion.payment_total_paid_amount = transaction_details.get("total_paid_amount", 0)
    notificacion.payment_net_received_amount = transaction_details.get("net_received_amount", 0)
    notificacion.payment_installments = payment.get("installments", 0)
    notificacion.payment_installment_amount = transaction_details.get("installment_amount", 0)

    notificacion.payer_id = payer.get("id", 0)
    notificacion.payer_email = payer.get("email", "")
    notificacion.payer_identification_type = payer.get("identification", {}).get("type", "")
    notificacion.payer_identification_number = payer.get("identification", {}).get("number", "")

    notificacion.data_json = json.dumps(payment)
    notificacion.save(ignore_permissions=True)
    frappe.db.commit()


@frappe.whitelist(allow_guest=True, xss_safe=True)
def ipn(**args):
    """
    /api/method/frappe.integrations.doctype.mercadopago_settings.mercadopago_settings.ipn?topic=payment&id=123456789
    """
    webhook_type = args['type']
    webhook_topic_id = args["data"]["id"]

    mercadopago_settings = get_payment_gateway_controller("Mercadopago")
    mp = mercadopago.SDK(mercadopago_settings.access_token)

    if webhook_type == "payment":
        payment = mp.payment().get(webhook_topic_id)['response']

        if payment['status'] == "approved" and payment["status_detail"] == "accredited":
            payment_request = frappe.get_doc("Payment Request", payment['external_reference'])
            payment_request.run_method("on_payment_authorized", "Completed")

        crear_notificacion_mercadopago(payment)

    return {
        "webhook_type": webhook_type,
        "webhook_topic_id": webhook_topic_id
    }
