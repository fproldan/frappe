// Copyright (c) 2016, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Auto Email Report', {
	refresh: function(frm) {
		frm.trigger('fetch_report_filters');
		if(!frm.is_new()) {
			frm.add_custom_button(__('Download'), function() {
				var w = window.open(
					frappe.urllib.get_full_url(
						"/api/method/frappe.email.doctype.auto_email_report.auto_email_report.download?"
						+"name="+encodeURIComponent(frm.doc.name)));
				if(!w) {
					frappe.msgprint(__("Please enable pop-ups")); return;
				}
			});
			frm.add_custom_button(__('Send Now'), function() {
				frappe.call({
					method: 'frappe.email.doctype.auto_email_report.auto_email_report.send_now',
					args: {name: frm.doc.name},
					callback: function() {
						frappe.msgprint(__('Scheduled to send'));
					}
				});
			});
		} else {
			if(!frm.doc.user) {
				frm.set_value('user', frappe.session.user);
			}
			if(!frm.doc.email_to) {
				frm.set_value('email_to', frappe.session.user);
			}
		}
		frm.trigger('setup_queries');
		manage_filters(frm);
		
	},
	onload: function(frm) {
		frm.trigger('setup_queries');
	},
	party: function(frm) {
		frm.trigger('clear_recipients_table');
		manage_filters(frm);
	},
	report: function(frm) {
		frm.set_value('filters', '');
		frm.trigger('fetch_report_filters');
	},
	fetch_report_filters(frm) {
		if (frm.doc.report
			&& frm.doc.report_type !== 'Report Builder'
			&& frm.script_setup_for !== frm.doc.report
		) {
			frappe.call({
				method: "frappe.desk.query_report.get_script",
				args: {
					report_name: frm.doc.report
				},
				callback: function(r) {
					frappe.dom.eval(r.message.script || "");
					frm.script_setup_for = frm.doc.report;
					frm.trigger('show_filters');
					frm.trigger('populate_filter_to_override_options');
				}
			});
		} else {
			frm.trigger('show_filters');
			frm.trigger('populate_filter_to_override_options');
		}
	},
	show_filters: function(frm) {
		var wrapper = $(frm.get_field('filters_display').wrapper);
		wrapper.empty();
		if(frm.doc.report_type === 'Custom Report' || (frm.doc.report_type !== 'Report Builder'
			&& frappe.query_reports[frm.doc.report]
			&& frappe.query_reports[frm.doc.report].filters)) {

			// make a table to show filters
			var table = $('<table class="table table-bordered" style="cursor:pointer; margin:0px;"><thead>\
				<tr><th style="width: 50%">'+__('Filter')+'</th><th>'+__('Value')+'</th></tr>\
				</thead><tbody></tbody></table>').appendTo(wrapper);
			$('<p class="text-muted small">' + __("Click table to edit") + '</p>').appendTo(wrapper);

			var filters = JSON.parse(frm.doc.filters || '{}');

			let report_filters;

			if (frm.doc.report_type === 'Custom Report'
				&& frappe.query_reports[frm.doc.reference_report]
				&& frappe.query_reports[frm.doc.reference_report].filters) {
				report_filters = frappe.query_reports[frm.doc.reference_report].filters;
			} else {
				report_filters = frappe.query_reports[frm.doc.report].filters;
			}

			if(report_filters && report_filters.length > 0) {
				frm.set_value('filter_meta', JSON.stringify(report_filters));
				if (frm.is_dirty()) {
					frm.save();
				}
			}

			var report_filters_list = []
			$.each(report_filters, function(key, val){
				// Remove break fieldtype from the filters
				if(val.fieldtype != 'Break') {
					report_filters_list.push(val)
				}
			})
			report_filters = report_filters_list;

			const mandatory_css = {
				"background-color": "var(--error-bg)",
				"font-weight": "bold"
			};

			report_filters.forEach(f => {
				const css = f.reqd ? mandatory_css : {};
				const row = $("<tr></tr>").appendTo(table.find("tbody"));
				$("<td>" + f.label + "</td>").appendTo(row);
				$("<td>" + frappe.format(filters[f.fieldname], f) +"</td>")
					.css(css)
					.appendTo(row);
			});

			table.on('click', function() {
				var dialog = new frappe.ui.Dialog({
					fields: report_filters,
					primary_action: function() {
						var values = this.get_values();
						if(values) {
							this.hide();
							frm.set_value('filters', JSON.stringify(values));
							frm.trigger('show_filters');
						}
					}
				});
				dialog.show();
				dialog.set_values(filters);
			})

			// populate dynamic date field selection
			let date_fields = report_filters
				.filter(df => df.fieldtype === 'Date')
				.map(df => ({ label: df.label, value: df.fieldname }));
			frm.set_df_property('from_date_field', 'options', date_fields);
			frm.set_df_property('to_date_field', 'options', date_fields);
			frm.toggle_display('dynamic_report_filters_section', date_fields.length > 0);
		}
	},
	setup_queries: function(frm) {
		frm.set_query("party", function() {
			return {
				query: "frappe.contacts.address_and_contact.filter_dynamic_link_doctypes",
				filters: {
					fieldtype: ["in", ["HTML", "Text Editor"]],
					fieldname: ["in", ["contact_html", "company_description"]],
				}
			};
		});
		frm.fields_dict['recipients'].grid.get_field('link_doctype').get_query = function() {
			return {
				filters: {
					name: frm.doc.party
				}
			};
		};
	},
	clear_recipients_table: function(frm) {
		let party_value = frm.doc.party;
		if (party_value) {
			frm.clear_table('recipients');
			frm.refresh_field('recipients');
		}
	},
	populate_filter_to_override_options: function(frm) {
		if (!frm.doc.filters) {
			frm.fields_dict['filter_to_override'].df.options = '';
        	frm.fields_dict['filter_to_override'].refresh();
		} else {
			let report_filters;
			if (frm.doc.report_type === 'Custom Report'
				&& frappe.query_reports[frm.doc.reference_report]
				&& frappe.query_reports[frm.doc.reference_report].filters) {
				report_filters = frappe.query_reports[frm.doc.reference_report].filters;
			} else {
				report_filters = frappe.query_reports[frm.doc.report].filters;
			}
			const keys = report_filters.map(item => item.fieldname);
			keys.unshift('');
			frm.fields_dict['filter_to_override'].df.options = keys.join('\n');
			frm.fields_dict['filter_to_override'].refresh();
		}
	}
});


frappe.ui.form.on('Auto Email Report Party', {
    recipients_add: function(frm, cdt, cdn) {
        let party_value = frm.doc.party;
        if (party_value) {
            frappe.model.set_value(cdt, cdn, 'link_doctype', party_value);
        }
    }
});

const manage_filters = (frm) => {
	if (frm.doc.party) {
		frappe.model.with_doctype(frm.doc.party, () => set_field_options(frm));
	} else {
		reset_filter_and_field(frm);
	}
}

const reset_filter_and_field = (frm) => {
	const filter_wrapper = frm.fields_dict.filter_list.$wrapper;
	filter_wrapper.empty();
	frm.filter_list = [];
};

const set_field_options = (frm) => {
	const filter_wrapper = frm.fields_dict.filter_list.$wrapper;
	filter_wrapper.empty();
	frm.filter_list = new frappe.ui.FilterGroup({
		parent: filter_wrapper,
		doctype: frm.doc.party,
		on_change: () => { 
			frm.call({
				method: 'frappe.email.doctype.auto_email_report.auto_email_report.get_recipients_by_filter',
				args: {
					doctype: frm.doc.party,
					filters: get_filters(frm),
				},
				callback: function(response) {
					if (response.message) {
						frm.clear_table('recipients');
						let names = response.message;
						names.forEach(name => {
							frm.add_child('recipients', {
								link_doctype: frm.doc.party,
								link_name: name,
							});
						});
						frm.refresh_field('recipients');
					} else {
						frm.clear_table('recipients');
						frm.refresh_field('recipients');
					}
				}
			});
		},
	});
};

const get_filters = (frm) => {
	return frm.filter_list.get_filters().map(filter => {
		return filter.slice(0, 4);
	});
}