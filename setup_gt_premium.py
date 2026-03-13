#!/usr/bin/env python
"""
Setup GT Premium contract type with same fields as GT Regular,
but with separate template for premium-specific products and rewards.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_clm.settings')
django.setup()

from contracts.models import ContractTypeDefinition, ContractField, ContractTemplate

# Get both contract types
gt_regular = ContractTypeDefinition.objects.get(code='GENERAL_TRADE')
gt_premium = ContractTypeDefinition.objects.get(code='GENERAL_TRADE_PREMIUM')

print("=== Setting up GT Premium ===\n")

# Step 1: Copy all fields from GT Regular to GT Premium
print("Step 1: Copying fields from GT Regular to GT Premium...")
regular_fields = ContractField.objects.filter(contract_type=gt_regular).order_by('position')

created_count = 0
updated_count = 0

for field in regular_fields:
    premium_field, created = ContractField.objects.update_or_create(
        contract_type=gt_premium,
        field_key=field.field_key,
        defaults={
            'label': field.label,
            'field_type': field.field_type,
            'required': field.required,
            'options': field.options,
            'position': field.position,
        }
    )
    if created:
        created_count += 1
    else:
        updated_count += 1

print(f"✓ Created {created_count} new fields")
print(f"✓ Updated {updated_count} existing fields")
print(f"✓ Total GT Premium fields: {gt_premium.fields.count()}\n")

# Step 2: Create template for GT Premium
print("Step 2: Creating GT Premium template...")

# Read the existing GT Regular template as base
try:
    regular_template = ContractTemplate.objects.filter(
        contract_type=gt_regular, 
        active=True
    ).first()
    
    if regular_template:
        base_html = regular_template.content
    else:
        base_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>General Trade Agreement - Premium</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }
        h1 { text-align: center; }
        .section { margin: 20px 0; }
    </style>
</head>
<body>
    <h1>PERJANJIAN KERJASAMA PERDAGANGAN UMUM - PREMIUM</h1>
    
    <div class="section">
        <p>Pada hari ini, {{ contract_start_date }}, telah dibuat dan ditandatangani Perjanjian Kerjasama ini oleh:</p>
        
        <p><strong>PIHAK PERTAMA:</strong><br>
        {{ party_a_name }}<br>
        {{ party_a_address }}</p>
        
        <p><strong>PIHAK KEDUA:</strong><br>
        {{ party_b_name }}<br>
        {{ party_b_address }}</p>
    </div>
    
    <div class="section">
        <h2>PASAL 1 - PRODUK PREMIUM</h2>
        <p><strong>Produk yang tercakup dalam perjanjian Premium ini:</strong></p>
        <ul>
            <li>Premium Product Category A</li>
            <li>Premium Product Category B</li>
            <li>Premium Product Category C</li>
        </ul>
        <p><em>Note: Customize this section with actual premium product list</em></p>
    </div>
    
    <div class="section">
        <h2>PASAL 2 - STRUKTUR REWARD PEMBELIAN</h2>
        <p><strong>Tier Reward Premium:</strong></p>
        <ul>
            <li><strong>D1 (Tier 1):</strong> Pembelian mencapai 80% dari target - Reward 2%</li>
            <li><strong>D2 (Tier 2):</strong> Pembelian mencapai 100% dari target - Reward 3%</li>
            <li><strong>D3 (Tier 3):</strong> Pembelian melebihi 120% dari target - Reward 5%</li>
        </ul>
        <p><em>Note: Customize D1/D2/D3 percentages and rewards for premium tier</em></p>
    </div>
    
    <div class="section">
        <h2>PASAL 3 - TARGET PENJUALAN</h2>
        <table border="1" cellpadding="10">
            <tr>
                <th>Kuartal</th>
                <th>Periode</th>
                <th>Target (Rp)</th>
            </tr>
            <tr>
                <td>Q1</td>
                <td>{{ quarter_1_period }}</td>
                <td>{{ sales_target_q1 }}</td>
            </tr>
            <tr>
                <td>Q2</td>
                <td>{{ quarter_2_period }}</td>
                <td>{{ sales_target_q2 }}</td>
            </tr>
            <tr>
                <td>Q3</td>
                <td>{{ quarter_3_period }}</td>
                <td>{{ sales_target_q3 }}</td>
            </tr>
            <tr>
                <td>Q4</td>
                <td>{{ quarter_4_period }}</td>
                <td>{{ sales_target_q4 }}</td>
            </tr>
            <tr>
                <th colspan="2">Total Target Tahunan</th>
                <th>{{ total_purchase_target }}</th>
            </tr>
        </table>
    </div>
    
    <div class="section">
        <h2>PASAL 4 - JANGKA WAKTU</h2>
        <p>Perjanjian ini berlaku sejak {{ contract_start_date }} hingga {{ contract_end_date }}.</p>
    </div>
    
    <div class="section">
        <h2>TANDA TANGAN</h2>
        <table width="100%">
            <tr>
                <td width="50%" align="center">
                    <p><strong>PIHAK PERTAMA</strong></p>
                    <br><br><br>
                    <p>_____________________</p>
                </td>
                <td width="50%" align="center">
                    <p><strong>PIHAK KEDUA</strong></p>
                    <br><br><br>
                    <p>_____________________<br>{{ party_b_representative }}</p>
                </td>
            </tr>
        </table>
    </div>
</body>
</html>
"""
    
    # Deactivate old GT Premium templates
    ContractTemplate.objects.filter(
        contract_type=gt_premium,
        active=True
    ).update(active=False)
    
    # Create new template
    template = ContractTemplate.objects.create(
        contract_type=gt_premium,
        name='GT Premium Agreement Template',
        content=base_html,
        active=True,
        version=1
    )
    
    print(f"✓ Created GT Premium template: {template.name}")
    print(f"✓ Template ID: {template.id}\n")
    
except Exception as e:
    print(f"Error creating template: {e}\n")

# Step 3: Summary
print("=== Setup Complete ===")
print(f"\nGT Regular: {gt_regular.fields.count()} fields")
print(f"GT Premium: {gt_premium.fields.count()} fields")
print("\nNext Steps:")
print("1. Edit the GT Premium template in Django Admin:")
print("   - Go to: Contracts > Contract templates")
print("   - Find 'GT Premium Agreement Template'")
print("   - Update PASAL 1 with actual premium products")
print("   - Update PASAL 2 with actual D1/D2/D3 reward structure")
print("\n2. Similarly, update GT Regular template with regular products/rewards")
print("\n3. Users will see both options when creating contracts:")
print("   - General Trade Agreement (Regular)")
print("   - General Trade Agreement - Premium")
