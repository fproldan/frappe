$(function() {
	var company = frappe.defaults.get_user_default('company');

	$('#navbar-default-company').text(company);

	frappe.db.get_value('Company', company, 'color_de_fondo', (values) => {
		$('#navbar-default-company-item').css('background', values.color_de_fondo);
	});

	frappe.db.get_value('Company', company, 'color_de_letra', (values) => {
		$('#navbar-default-company-item').css('color', values.color_de_letra);
	});
});