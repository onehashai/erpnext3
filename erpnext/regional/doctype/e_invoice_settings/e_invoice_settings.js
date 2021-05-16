// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('E Invoice Settings', {
	refresh(frm) {
		const docs_link = 'https://help.onehash.ai/en/article/regional-india-129ofew/';
		frm.dashboard.set_headline(
			__("Read {0} for more information on E Invoicing features.", [`<a href='${docs_link}'>documentation</a>`])
		);
	}
});
