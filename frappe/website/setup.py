from __future__ import unicode_literals

import frappe


def setup_website():
    add_dashboard()


def add_dashboard():
    dashboard_charts_and_number_cards = [
        {
            "chart_name": "Website Analytics",
            "chart_type": "Report",
            "custom_options": "{\"type\": \"line\", \"lineOptions\": {\"regionFill\": 1}, \"axisOptions\": {\"shortenYAxisNumbers\": 1}, \"tooltipOptions\": {}}",
            "doctype": "Dashboard Chart",
            "filters_json": "{}",
            "group_by_type": "Count",
            "is_custom": 1,
            "is_public": 1,
            "name": "Website Analytics",
            "number_of_groups": 0,
            "report_name": "Website Analytics",
            "time_interval": "Yearly",
            "timeseries": 0,
            "timespan": "Last Year",
            "type": "Line"
        }
    ]

    for widget in dashboard_charts_and_number_cards:
        doc = frappe.new_doc(widget['doctype'])
        doc.update(widget)
        try:
            doc.insert()
        except Exception:
            continue

    frappe.db.commit()
