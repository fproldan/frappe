$(function() {
	var company = frappe.defaults.get_user_default('company');

	if (company) {
		$('#navbar-default-company').text(company);

		frappe.db.get_value('Company', company, 'color', (values) => {
			let value = "3px solid " + values.color;
			$('#navbar-default-company-item').css('border-bottom', value);
		});
	}
});