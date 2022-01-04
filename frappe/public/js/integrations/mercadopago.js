frappe.ui.form.on("Sales Order", {
    setup: function(frm) {
        
    },
    onload: function(frm) {
        
    },
    refresh: function(frm) {
        if (frappe.boot.active_domains.includes("Mercadopago")) {
            frm.add_custom_button('QR', function() {
                var d = new frappe.ui.Dialog({
                    title: __('Seleccionar Caja'),
                    fields: [
                        {
                            "label": "Caja",
                            "fieldname": "caja",
                            "fieldtype": "Select",
                            "options": get_cajas(),
                            "reqd": 1,
                        },
                        
                    ],
                    primary_action: function() {
                        var data = d.get_values();
                        frappe.dom.freeze();
                        frappe.call({
                            method: "frappe.integrations.doctype.mercadopago_settings.mercadopago_settings.create_order",
                            args: {
                                docname: frm.doc.name,
                                doctype: frm.doc.doctype,
                                caja: cstr(data.caja),
                            },
                            callback: function(r) {
                                if (r.message) {
                                    console.log(r.message)
                                } 
                                d.hide();
                                frappe.dom.unfreeze();
                            }
                        });
                        
                    },
                    primary_action_label: __('Enviar Orden')
                });
                d.show();
            }, __('Mercadopago'));
           
            frm.add_custom_button("URL de Pago", function() {
                alert("URL")
            }, __('Mercadopago'));
        }
    },
});


function get_cajas() {
    let cajas = null;
    frappe.call({
        method: "frappe.integrations.doctype.mercadopago_settings.mercadopago_settings.get_cajas_and_sucursales",
        async: false,
        callback: function(r, rt) {
            if (r.message) { 
                cajas = r.message;
            }
        }
    });
    return cajas;
}
