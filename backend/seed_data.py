#!/usr/bin/env python
"""Seed database with dummy data for testing"""
import os
from app import create_app, db
from app.models import User, Role, Customer, Product, Plan
from datetime import datetime
from decimal import Decimal

app = create_app()

def seed_customers():
    """Add dummy customers"""
    print("🌱 Seeding customers...")
    
    customers_data = [
        {
            'name': 'Acme Corporation',
            'email': 'contact@acme.com',
            'status': 'active',
            'phone': '+1-555-0101'
        },
        {
            'name': 'TechStart Inc',
            'email': 'hello@techstart.com',
            'status': 'active',
            'phone': '+1-555-0102'
        },
        {
            'name': 'Global Solutions Ltd',
            'email': 'info@globalsolutions.com',
            'status': 'active',
            'phone': '+1-555-0103'
        },
        {
            'name': 'Innovation Labs',
            'email': 'contact@innovationlabs.io',
            'status': 'active',
            'phone': '+1-555-0104'
        },
        {
            'name': 'Digital Ventures',
            'email': 'hello@digitalventures.com',
            'status': 'active',
            'phone': '+1-555-0105'
        },
        {
            'name': 'CloudFirst Industries',
            'email': 'support@cloudfirst.io',
            'status': 'active',
            'phone': '+1-555-0106'
        },
        {
            'name': 'Enterprise Systems',
            'email': 'contact@enterprise.com',
            'status': 'active',
            'phone': '+1-555-0107'
        },
        {
            'name': 'Startup Garage',
            'email': 'hi@startupgarage.com',
            'status': 'active',
            'phone': '+1-555-0108'
        },
    ]
    
    for cust_data in customers_data:
        # Check if customer already exists
        existing = Customer.query.filter_by(email=cust_data['email']).first()
        if existing:
            print(f"  ✓ {cust_data['name']} already exists")
            continue
        
        customer = Customer(
            name=cust_data['name'],
            email=cust_data['email'],
            phone=cust_data.get('phone'),
            status=cust_data['status']
        )
        db.session.add(customer)
        print(f"  ✓ Added {cust_data['name']}")
    
    db.session.commit()
    print("✅ Customers seeded\n")

def seed_products():
    """Add dummy products"""
    print("🌱 Seeding products...")
    
    products_data = [
        {
            'name': 'Professional Plan',
            'sku': 'PROF-001',
            'description': 'Advanced features for growing businesses',
            'base_price': Decimal('99.99'),
            'status': 'active'
        },
        {
            'name': 'Enterprise Plan',
            'sku': 'ENT-001',
            'description': 'Full-featured solution for enterprises',
            'base_price': Decimal('299.99'),
            'status': 'active'
        },
        {
            'name': 'Starter Plan',
            'sku': 'START-001',
            'description': 'Perfect for small teams',
            'base_price': Decimal('29.99'),
            'status': 'active'
        },
        {
            'name': 'Premium Plus',
            'sku': 'PREM-PLUS-001',
            'description': 'Premium features with priority support',
            'base_price': Decimal('199.99'),
            'status': 'active'
        },
        {
            'name': 'API Access',
            'sku': 'API-001',
            'description': 'API access for integration',
            'base_price': Decimal('49.99'),
            'status': 'active'
        },
    ]
    
    for prod_data in products_data:
        # Check if product already exists
        existing = Product.query.filter_by(sku=prod_data['sku']).first()
        if existing:
            print(f"  ✓ {prod_data['name']} already exists")
            continue
        
        product = Product(
            name=prod_data['name'],
            sku=prod_data['sku'],
            description=prod_data['description'],
            base_price=prod_data['base_price'],
            status=prod_data['status']
        )
        db.session.add(product)
        print(f"  ✓ Added {prod_data['name']}")
    
    db.session.commit()
    print("✅ Products seeded\n")

def seed_plans():
    """Add dummy plans for products"""
    print("🌱 Seeding plans...")
    
    # Get first product
    product = Product.query.first()
    if not product:
        print("  ⚠️  No products found. Run seed_products first.")
        return
    
    plans_data = [
        {
            'product_id': product.id,
            'name': 'Monthly',
            'description': 'Monthly billing cycle',
            'price': Decimal('99.99'),
            'billing_cycle': 'monthly',
            'setup_fee': Decimal('0.00'),
            'status': 'active'
        },
        {
            'product_id': product.id,
            'name': 'Quarterly',
            'description': 'Quarterly billing cycle - 10% discount',
            'price': Decimal('269.97'),  # 10% off
            'billing_cycle': 'quarterly',
            'setup_fee': Decimal('0.00'),
            'status': 'active'
        },
        {
            'product_id': product.id,
            'name': 'Annual',
            'description': 'Annual billing cycle - 15% discount',
            'price': Decimal('1019.92'),  # 15% off
            'billing_cycle': 'annually',
            'setup_fee': Decimal('0.00'),
            'status': 'active'
        },
    ]
    
    for plan_data in plans_data:
        # Check if plan already exists
        existing = Plan.query.filter_by(
            product_id=plan_data['product_id'],
            name=plan_data['name']
        ).first()
        if existing:
            print(f"  ✓ {plan_data['name']} plan already exists")
            continue
        
        plan = Plan(
            product_id=plan_data['product_id'],
            name=plan_data['name'],
            description=plan_data['description'],
            price=plan_data['price'],
            billing_cycle=plan_data['billing_cycle'],
            setup_fee=plan_data['setup_fee'],
            status=plan_data['status']
        )
        db.session.add(plan)
        print(f"  ✓ Added {plan_data['name']} plan")
    
    db.session.commit()
    print("✅ Plans seeded\n")

if __name__ == '__main__':
    with app.app_context():
        try:
            seed_customers()
            seed_products()
            seed_plans()
            print("✨ All data seeded successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {e}")
