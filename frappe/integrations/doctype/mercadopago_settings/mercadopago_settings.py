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

    def get_user_id(self):
        if not self.access_token:
            return None

        return self.access_token.split('-')[-1]

    def get_payment_url(self, **kwargs):
        """
        Url para solicitudes de pago
        """
        mercadopago_settings = get_payment_gateway_controller("Mercadopago")
        mp = mercadopago.SDK(mercadopago_settings.access_token)
        payment_request = frappe.get_doc(kwargs["reference_doctype"], kwargs["reference_docname"])
        notification_url = get_url("/api/method/frappe.integrations.doctype.mercadopago_settings.mercadopago_settings.ipn")  # ?source_news=webhook

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
            }
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


def get_sucursales():
    """
    {
        "paging":{
            "total":1,
            "offset":0,
            "limit":50
        },
        "results":[
            {
                "id":"44253934",
                "name":"Casa Central",
                "date_creation":"2022-01-03T13:12:04.972Z",
                "business_hours":{
                    "monday":[
                        {
                            "open":"09:00",
                            "close":"18:00"
                        }
                    ],
                    "tuesday":[
                        {
                            "open":"09:00",
                            "close":"18:00"
                        }
                    ],
                    "wednesday":[
                        {
                            "open":"09:00",
                            "close":"18:00"
                        }
                    ],
                    "thursday":[
                        {
                            "open":"09:00",
                            "close":"18:00"
                        }
                    ],
                    "friday":[
                        {
                            "open":"09:00",
                            "close":"18:00"
                        }
                    ]
                },
                "location":{
                    "address_line":"Bv. Presidente Julio A. Roca 882, Rafaela, Santa Fe",
                    "reference":"Oficina 5",
                    "latitude":-31.2509236,
                    "longitude":-61.5011729
                }
            }
        ]
    }
    """
    mercadopago_settings = get_payment_gateway_controller("Mercadopago")
    mp = mercadopago.SDK(mercadopago_settings.access_token)
    response = mp.http_client.get(url=f"https://api.mercadopago.com/users/{mercadopago_settings.get_user_id()}/stores/search", headers={"Authorization": f"Bearer {mercadopago_settings.access_token}"})

    if response.get('status') != 200:
        return

    paging = response['response']['paging']
    results = response['response']['results']
    return results


def get_cajas():
    """
    {
        "paging":{
            "total":2,
            "offset":0,
            "limit":30
        },
        "results":[
            {
                "user_id":1046842243,
                "name":"Caja 1",
                "store_id":"44253934",
                "id":38991493,
                "qr":{
                    "image":"https://www.mercadopago.com/instore/merchant/qr/38991493/bc1583fc667c4dfea916c1b07e169ce639b41f415b6646f9bc688e7d61125de8.png",
                    "template_document":"https://www.mercadopago.com/instore/merchant/qr/38991493/template_bc1583fc667c4dfea916c1b07e169ce639b41f415b6646f9bc688e7d61125de8.pdf",
                    "template_image":"https://www.mercadopago.com/instore/merchant/qr/38991493/template_bc1583fc667c4dfea916c1b07e169ce639b41f415b6646f9bc688e7d61125de8.png"
                },
                "date_created":"2022-01-03T09:12:05.000-04:00",
                "date_last_updated":"2022-01-03T09:12:05.000-04:00"
            },
            {
                "user_id":1046842243,
                "name":"Caja 2",
                "store_id":"44253934",
                "id":38991494,
                "qr":{
                    "image":"https://www.mercadopago.com/instore/merchant/qr/38991494/cee583fc58584c09b5e8ca66d558d80f30b947e1aa3d40bda51b1ba38cad616b.png",
                    "template_document":"https://www.mercadopago.com/instore/merchant/qr/38991494/template_cee583fc58584c09b5e8ca66d558d80f30b947e1aa3d40bda51b1ba38cad616b.pdf",
                    "template_image":"https://www.mercadopago.com/instore/merchant/qr/38991494/template_cee583fc58584c09b5e8ca66d558d80f30b947e1aa3d40bda51b1ba38cad616b.png"
                },
                "date_created":"2022-01-03T09:12:21.000-04:00",
                "date_last_updated":"2022-01-03T09:12:21.000-04:00"
            }
        ]
    }
    """
    mercadopago_settings = get_payment_gateway_controller("Mercadopago")
    mp = mercadopago.SDK(mercadopago_settings.access_token)
    response = mp.http_client.get(url=f"https://api.mercadopago.com/pos", headers={"Authorization": f"Bearer {mercadopago_settings.access_token}"})

    if response.get('status') != 200:
        return

    paging = response['response']['paging']
    results = response['response']['results']
    return results