$(function() {
	$('#navbar-default-company').text(frappe.defaults.get_user_default('company'));
});