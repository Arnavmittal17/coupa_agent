"""
Script to replace placeholder rejection comments in form_1_intake, form_2_input, and form_3_tax
with realistic Coupa Supplier Onboarding rejection reasons specific to each form type.
"""
import sqlite3
import random
import os

# ─── Form 1: Intake Form (Supplier Information) ───────────────────────────────
FORM1_REJECTION_COMMENTS = [
    "Supplier legal name on the intake form does not match the name on the W-9. Please resubmit with the correct legal entity name.",
    "The supplier's registered business address is incomplete. Please include street, city, state/province, and postal code.",
    "Duplicate supplier entry detected — this supplier already exists in the Coupa portal under a different ID. Please verify and update the existing record.",
    "The supplier type selected (Individual) does not align with the attached business registration documents. Please correct and resubmit.",
    "EIN/Tax ID format is invalid. Please provide a valid 9-digit EIN in the format XX-XXXXXXX.",
    "DUNS number provided could not be verified against Dun & Bradstreet records. Please confirm or leave blank if not applicable.",
    "The supplier's country of incorporation is missing. This is required for tax classification purposes.",
    "Business registration documents uploaded are expired. Please provide documents valid within the last 12 months.",
    "Primary supplier contact email is invalid or returned a delivery failure. Please provide an active email address.",
    "Supplier contact name field is populated with a generic title (e.g., 'Accounts Payable') rather than an individual's name. Please provide a named contact.",
    "Phone number provided is not reachable. Please confirm the correct contact number for the supplier representative.",
    "Multiple contact entries have the same email address. Each contact must have a unique email for portal access.",
    "Vendor screening has not been completed for this supplier. Screening approval is mandatory before intake can be approved.",
    "Supplier is flagged in our third-party risk screening tool. Please review the risk report and provide justification to proceed.",
    "Sanctions check returned a potential match. This intake has been escalated to the Procurement Compliance team for review.",
    "Supplier has an outstanding compliance hold from a prior engagement. Please contact the Vendor Compliance team before resubmitting.",
    "The supplier does not meet our minimum insurance coverage requirements. Please attach a valid Certificate of Insurance (COI) and resubmit.",
    "Anti-bribery and anti-corruption (ABAC) certification has not been acknowledged by the supplier. Please ensure the supplier completes the ABAC acknowledgement.",
    "Business justification for onboarding this supplier is insufficient. Please provide a clear description of the goods/services and business need.",
    "The requestor's department code entered does not exist in the system. Please verify the correct cost center and resubmit.",
    "This request appears to be for a supplier that falls under a preferred vendor category. Please confirm that no existing preferred vendor can meet this need.",
    "The estimated annual spend indicated appears unusually low. Please confirm the expected engagement value before proceeding.",
    "Supplier category selected does not align with the supplier's described services. Please correct the category.",
    "The request is missing a valid purchase requisition number. A PR must be created and linked before intake approval.",
    "No supporting documents were attached. Please upload the signed supplier engagement letter or SOW before resubmitting.",
    "The uploaded NDA is unsigned. Please obtain a countersigned copy from the supplier and reattach.",
    "Certificate of Insurance uploaded is not addressed to our company. Please request an updated COI naming the correct entity as the certificate holder.",
    "This intake was submitted for a supplier in a region where a regional procurement team manages onboarding. Please resubmit through the correct regional portal.",
    "Intake form was submitted before the mandatory Supplier Diversity screening was completed. Please complete the diversity assessment and resubmit.",
    "The form was routed to the wrong approver group. Please verify the correct commodity owner and resubmit with the appropriate routing.",
    "Intake cannot be processed as the linked project code has been closed. Please provide an active project or cost center reference.",
    "Supplier's legal entity type (LLC) does not match the tax classification selected (S-Corp). Please review and align the entity type and tax classification.",
    "The supplier has not accepted the Coupa Supplier Portal (CSP) invitation. Please have the supplier register on the portal before this intake can proceed.",
    "Website URL provided for the supplier returns a 404 error. Please verify the supplier's website is active and accurate.",
]

# ─── Form 2: Input Form (Supplier Portal / Operational Details) ───────────────
FORM2_REJECTION_COMMENTS = [
    "Bank account number provided does not match the format required for the supplier's country. Please verify and resubmit.",
    "The IBAN entered is invalid — checksum verification failed. Please provide the correct IBAN from the supplier's bank statement.",
    "Routing number (ABA) could not be validated. Please confirm the 9-digit ABA routing number with your bank.",
    "Bank name and account number combination could not be verified. Please attach a voided cheque or official bank letter as supporting documentation.",
    "The payment currency selected (EUR) does not match the supplier's registered banking country (US). Please clarify the payment arrangement.",
    "Swift/BIC code provided is not recognised. Please verify the correct SWIFT code with the supplier's financial institution.",
    "Supplier has provided a personal bank account instead of a business account. Payment must be made to a business entity account.",
    "Bank details have been entered for a country that is subject to payment restrictions. Please contact the Treasury team before proceeding.",
    "Remittance email address provided is invalid. Please supply a valid email address where payment notifications should be sent.",
    "Payment terms selected (Net 90) exceed the maximum allowed for this supplier category (Net 60). Please align with the approved payment terms.",
    "The supplier contact listed for accounts receivable does not match the primary contact on the intake form. Please clarify or update accordingly.",
    "A Purchase Order (PO) is required for this supplier but 'No PO' was selected. Please update to reflect the correct PO requirement.",
    "Supplier's preferred delivery method (Electronic Funds Transfer) is not currently supported for this region. Please select an alternative payment method.",
    "Supplier portal access details were not completed. The supplier must log in and confirm their profile before this form can be approved.",
    "Operational contact information is missing for after-hours support. Please provide an emergency contact name and number.",
    "The supplier's accounts receivable email is a shared distribution list. An individual contact email is required for audit purposes.",
    "Currency mismatch detected — supplier invoices in GBP but the account provided is a USD account. Please resolve the discrepancy.",
    "Supplier's payment address differs from the registered business address without explanation. Please provide written confirmation from the supplier.",
    "Virtual account details cannot be accepted per our internal payment policy. Please provide standard bank account details.",
    "The intermediary bank details provided are incomplete. Please include full correspondent bank name, SWIFT code, and account number.",
    "Payment terms requested by the supplier conflict with the contracted terms. Please escalate to the Procurement team to resolve.",
    "The supplier has flagged their account as requiring dual-authorisation for payments but no second authoriser has been named. Please complete this field.",
    "Supplier's billing address is in a jurisdiction under active trade sanctions. This transaction requires Compliance team sign-off before approval.",
    "Bank account details uploaded as an image are not legible. Please resubmit a clear, high-resolution copy of the bank confirmation document.",
    "The supplied account is a savings account. Only current or business checking accounts are accepted for supplier payments.",
    "No preferred payment method was selected. Please indicate whether the supplier accepts ACH, Wire, or Cheque.",
    "Supplier has changed banking details within the last 30 days. Per our fraud prevention policy, a secondary verification call is required before this update can be approved.",
    "The billing contact provided has not completed the mandatory payment portal registration. Please have them complete registration at the link provided.",
]

# ─── Form 3: Tax Form (Tax ID / Classification) ───────────────────────────────
FORM3_REJECTION_COMMENTS = [
    "W-9 form submitted is outdated — please provide the most recent IRS W-9 version (rev. October 2018 or later).",
    "The name on the W-9 does not match the legal entity name on the intake form. Please ensure consistency across all documents.",
    "Tax classification on the W-9 is left blank. Please select the appropriate entity type (e.g., LLC, C-Corp, S-Corp, Individual/Sole Proprietor).",
    "EIN on the W-9 does not match the EIN provided during intake. Please clarify which is correct and resubmit.",
    "W-9 is missing a valid signature and/or date. Please have an authorised signatory complete and sign the form.",
    "For foreign suppliers, a W-8BEN or W-8BEN-E is required instead of a W-9. Please submit the correct IRS form.",
    "The W-8BEN-E submitted is for an entity type that does not qualify for the treaty benefit claimed. Please review Chapter 3 and Chapter 4 status and resubmit.",
    "Country of tax residency claimed in the W-8 does not have a tax treaty with the US that covers the services provided. Standard withholding rates will apply.",
    "The FATCA/Chapter 4 status box on the W-8BEN-E is incomplete. Please select the appropriate FATCA classification for your entity.",
    "Global Intermediary Identification Number (GIIN) provided could not be verified against the IRS FATCA registration database.",
    "VAT registration number is invalid for the supplier's declared country. Please verify the VAT number format with your local tax authority.",
    "The supplier has indicated they are VAT-exempt but has not provided supporting exemption documentation. Please attach the relevant certificate.",
    "GST/HST number is missing for a Canadian supplier. This is required for Canadian tax compliance. Please provide your 15-character GST/HST account number.",
    "Tax ID provided appears to be a Social Security Number (SSN) rather than an EIN. For business entities, please provide the company EIN.",
    "The supplier has selected 'Exempt Payee' on the W-9 but the exemption codes provided do not apply to their stated entity type. Please correct and resubmit.",
    "Form 1042-S withholding rate cannot be applied — the supplier's claimed treaty benefit requires a valid Limitation on Benefits (LOB) clause certification.",
    "Tax form is for a different legal entity than the one being onboarded. Please submit documentation specifically for the contracting entity.",
    "The submitted tax form appears to be a photocopy of a previously submitted document. An original or freshly completed form is required.",
    "Supplier's declared state of incorporation does not match the state tax ID provided. Please resolve this inconsistency.",
    "The tax classification selected (Partnership) requires an additional IRS Schedule K-1 for the year of record. Please attach the relevant document.",
    "Supplier is incorporated in a US territory (e.g., Puerto Rico) — specific tax forms apply. Please consult with the Tax team on the correct documentation.",
    "Foreign tax identification number (FTIN) is missing on the W-8. This field is mandatory unless a valid exception applies; please justify any omission.",
    "The supplier's tax form indicates a change of legal name, but no supporting evidence (e.g., Certificate of Amendment) has been attached.",
    "Withholding certificate expiry date has passed — W-8 forms are valid for 3 years. Please submit a renewed W-8 signed within the current period.",
    "The electronic signature on the W-9 does not meet IRS electronic signature requirements. Please resubmit with a wet signature or a compliant e-signature.",
    "The supplier's declared tax residency conflicts with the country of bank account registration. Please provide a letter of explanation from your tax advisor.",
    "The entity is registered as a disregarded entity for US tax purposes but no owner information has been provided. Please disclose the tax owner's details.",
    "State withholding exemption form is required in addition to the federal W-9 for suppliers operating in California. Please attach Form 590.",
    "Supplier has left the 'Backup Withholding' section uncertified on the W-9. All certifications must be completed to avoid mandatory 24% backup withholding.",
    "Tax documentation submitted contains redacted fields that are required for processing. Please submit an unredacted copy directly to the Tax Compliance team.",
]


def update_rejection_comments(db_path: str, table: str, comments: list, seed: int):
    """Replace all rejection comments in `table` with randomly sampled realistic comments."""
    random.seed(seed)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(f"SELECT FORM_ID FROM {table} WHERE IS_REJECTED = 'Yes'")
    rejected_ids = [row[0] for row in cursor.fetchall()]

    print(f"Updating {len(rejected_ids)} rejection comments in '{table}'...")
    updated = 0
    for form_id in rejected_ids:
        comment = random.choice(comments)
        cursor.execute(
            f"UPDATE {table} SET REJECTION_COMMENT = ? WHERE FORM_ID = ?",
            (comment, form_id)
        )
        updated += cursor.rowcount

    conn.commit()
    conn.close()
    print(f"  Done — {updated} rows updated in '{table}'.")


if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "coupa_data.db")

    update_rejection_comments(db_path, "form_1_intake", FORM1_REJECTION_COMMENTS, seed=42)
    update_rejection_comments(db_path, "form_2_input",  FORM2_REJECTION_COMMENTS, seed=43)
    update_rejection_comments(db_path, "form_3_tax",    FORM3_REJECTION_COMMENTS, seed=44)

    print("\nAll done — rejection comments updated for Form 1, Form 2, and Form 3.")
