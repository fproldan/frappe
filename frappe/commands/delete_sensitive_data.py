import frappe

def delete_sensitive_data():
    installed_apps = frappe.get_installed_apps()

    if "erpnext_argentina" in installed_apps:
        for company in frappe.get_all("Company", pluck="name"):
            frappe.db.set_value("Company", company, "certificado_publico", "")
            frappe.db.set_value("Company", company, "certificado_privado", "")
            frappe.db.set_value("Company", company, "tipo_de_conexion_afip", "Homologacion")
            frappe.db.commit()


    if "ecommerce_integrations" in installed_apps:
        print("TODO disable sync")
