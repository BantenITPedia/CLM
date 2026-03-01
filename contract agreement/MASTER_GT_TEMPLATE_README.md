# General Trade Agreement (GT) - Master Template Documentation

## File: MASTER_GT_TEMPLATE.htm

This is the **official master template** for all General Trade Agreement contracts.  
Use this template for all future GT contracts. It has been tested and verified to work correctly.

## Template Variable Reference

All variables use Django template syntax: `{{ variable_name }}`

### Party Information
| Variable | Description | Source |
|----------|-------------|--------|
| `{{ party_b_legal_name }}` | Party B company legal name | Form input: "Legal Entity Name" |
| `{{ party_b_registered_address }}` | Party B registered legal address | Form input: "Party B - Address" |
| `{{ party_b_delivery_address }}` | Party B delivery/operational address | Form input: "Delivery Address" |
| `{{ party_b_authorized_representative_name }}` | Name of authorized representative | Form input: "Party B - Representative Name" |
| `{{ party_b_authorized_representative_title }}` | Title of authorized representative | Form input: "Party B - Representative Title" |
| `{{ party_b_business_form }}` | Business form (CV/PT/etc) | Form input: "Business Form" |
| `{{ customer_partner_code }}` | CVCODE number | Form input: "CV Code Number" |
| `{{ party_b_business_location_name }}` | Name of business location | Optional field |

### Contract Information
| Variable | Description | Source |
|----------|-------------|--------|
| `{{ contract_number }}` | Contract ID number | Auto-generated from contract.id |
| `{{ contract_signing_date }}` | Contract signing date | Auto-generated from current date |
| `{{ contract_effective_start_date }}` | Contract effective start date | Form input: start_date |
| `{{ contract_effective_end_date }}` | Contract effective end date | Form input: end_date |
| `{{ total_annual_purchase_target }}` | Total annual purchase target (IDR) | Form input: "Target Value" |

### Quarterly Information
| Variable | Description | Source |
|----------|-------------|--------|
| `{{ q1_period }}` | Q1 period dates (e.g., "06 Feb 2026 - 05 May 2026") | Auto-calculated from dates |
| `{{ q1_sales_target }}` | Q1 sales target amount (IDR) | Auto-calculated from total ÷ 4 |
| `{{ q2_period }}` | Q2 period dates | Auto-calculated from dates |
| `{{ q2_sales_target }}` | Q2 sales target amount | Auto-calculated |
| `{{ q3_period }}` | Q3 period dates | Auto-calculated from dates |
| `{{ q3_sales_target }}` | Q3 sales target amount | Auto-calculated |
| `{{ q4_period }}` | Q4 period dates | Auto-calculated from dates |
| `{{ q4_sales_target }}` | Q4 sales target amount | Auto-calculated |

### Incentive Information
(Optional fields - populate if applicable)
| Variable | Description |
|----------|-------------|
| `{{ incentive_yearly_non_commodity_d1 }}` | D1 yearly non-commodity incentive % |
| `{{ incentive_yearly_non_commodity_d2 }}` | D2 yearly non-commodity incentive % |
| `{{ incentive_yearly_non_commodity_d3 }}` | D3 yearly non-commodity incentive % |
| `{{ incentive_quarterly_non_commodity_d1 }}` | D1 quarterly non-commodity incentive % |
| `{{ incentive_quarterly_non_commodity_d2 }}` | D2 quarterly non-commodity incentive % |
| `{{ incentive_quarterly_non_commodity_d3 }}` | D3 quarterly non-commodity incentive % |
| `{{ incentive_yearly_commodity_d1 }}` | D1 yearly commodity incentive % |
| `{{ incentive_yearly_commodity_d2 }}` | D2 yearly commodity incentive % |
| `{{ incentive_yearly_commodity_d3 }}` | D3 yearly commodity incentive % |
| `{{ authorized_product_categories }}` | List of authorized product categories |

## How to Use

1. **For new contracts**: The system automatically uses this master template
2. **Form fields that populate the template**:
   - Legal Entity Name → {{ party_b_legal_name }}
   - Party B - Address → {{ party_b_registered_address }}
   - Delivery Address → {{ party_b_delivery_address }}
   - Business Form → {{ party_b_business_form }}
   - CV Code Number → {{ customer_partner_code }}
   - Party B - Representative Name → {{ party_b_authorized_representative_name }}
   - Party B - Representative Title → {{ party_b_authorized_representative_title }}
   - Start Date & End Date → Quarterly period calculations
   - Target Value (IDR) → Total annual target + quarterly breakdown

3. **Auto-populated fields**:
   - Contract number, dates, quarterly targets, and periods are calculated automatically
   - No manual entry needed for these

## Technical Notes

- Template encoding: UTF-8
- Language: Indonesian (id)
- CSS includes proper table styling for all Lampiran sections
- Variables are auto-aliased in services.py for backward compatibility
- All amounts in Indonesian Rupiah (IDR)

## Version Control

- **Created**: February 3, 2026
- **Status**: Approved & Production Ready
- **Last Updated**: 2026-02-03
- **File Size**: ~6.5 KB
