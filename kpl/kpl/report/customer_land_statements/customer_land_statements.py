# Copyright (c) 2023, Pointershub and contributors
# For license information, please see license.txt

import frappe
from frappe import throw, _


def execute(filters=None):
    data = []
    columns = get_columns()
    sales_order = frappe.get_all("Sales Order", filters={'sales_type': 'Land Sales', 'docstatus': 1, 'customer': filters.get('customer'), 'company': filters.get('company')}, order_by='creation asc', fields=['name'])
    balance = total_balance = total_amt = total_paid = 0

    for so in sales_order:
        so_doc = frappe.get_doc("Sales Order", so.name)
        itm_desc = ""
        for item in so_doc.get("items"):
            itm_desc += item.item_code
        data.append({
            "date": so_doc.transaction_date,
            "transaction": so_doc.name,
            "detail": "Purchase of Plot No " + itm_desc,
            "amount": so_doc.grand_total,
            "payment": "",
            "balance": so_doc.grand_total
        })
        amt = float(so_doc.grand_total)
        total_amt += amt

        # Process payment entries
        payment_entries = frappe.get_all("Payment Entry Reference",
            filters={
                "reference_name": so_doc.name,
                "reference_doctype": "Sales Order"
            },
            fields=["parent", 'total_amount', 'allocated_amount', 'creation'],
            order_by='creation asc'
        )

        for entry in payment_entries:
            total_paid += float(entry.allocated_amount)
            balance = amt - total_paid
            pe = frappe.get_doc("Payment Entry", entry.parent)
            data.append({
                "date": pe.posting_date,
                "transaction": pe.name,
                "detail": "Payment Received for Plot No " + itm_desc,
                "amount": "",
                "payment": entry.allocated_amount,
                "balance": balance
            })

        # Process journal entries
        journal_entries = frappe.get_all("Journal Entry Account",
            filters={
                "reference_name": so_doc.name,
                "reference_type": "Sales Order"
            },
            fields=["parent", 'credit_in_account_currency', 'debit_in_account_currency', 'creation'],
            order_by='creation asc'
        )

        for entry in journal_entries:
            je_doc = frappe.get_doc("Journal Entry", entry.parent)
            payment_amount = float(entry.credit_in_account_currency)
            total_paid += payment_amount
            balance = amt - total_paid
            data.append({
                "date": je_doc.posting_date,
                "transaction": je_doc.name,
                "detail": "Payment Received for Plot No " + itm_desc,
                "amount": "",
                "payment": payment_amount,
                "balance": balance
            })

    total_balance = total_amt - total_paid
    data.append({
        "date": "",
        "transaction": "",
        "detail": "<b>Total(s)</b>",
        "amount": total_amt,
        "payment": total_paid,
        "balance": total_balance
    })
    data.append({
        "date": "",
        "transaction": "",
        "detail": "<b>Balance Due</b>",
        "amount": "",
        "payment": "",
        "balance": total_balance
    })

    return columns, data



def get_columns():
    columns = [
        {
            'label': _('Date'),
            'fieldname': 'date',
            'fieldtype': 'Date',
            'width': 150
        },
        {
            'label': _('Reference'),
            'fieldname': 'transaction',
            'fieldtype': 'Data',
            'width': 250
        },
        {
            'label': _('Details'),
            'fieldname': 'detail',
            'fieldtype': 'Data',
            'width': 250
        },
        {
            'label': _('Debit'),
            'fieldname': 'amount',
            'fieldtype': 'Currency',
            'width': 180
        },
        {
            'label': _('Credit'),
            'fieldname': 'payment',
            'fieldtype': 'Currency',
            'width': 180
        },
        {
            'label': _('Balance (Dr - Cr)'),
            'fieldname': 'balance',
            'fieldtype': 'Currency',
            'width': 180
        }
    ]

    return columns
