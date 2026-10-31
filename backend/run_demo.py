"""Run SubscriptIQ in demo mode with in-memory database"""
import os
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['TESTING'] = 'True'
os.environ['CORS_ORIGINS'] = 'http://localhost:5173,http://127.0.0.1:5173'

from app import create_app
from app.extensions import db
from app.models import User, Role, Customer, Product, Plan, Subscription
from decimal import Decimal
from datetime import datetime, timedelta
import uuid

print("🚀 Starting SubscriptIQ in DEMO mode...")
print("=" * 60)

app = create_app('development')

with app.app_context():
    # Create all tables
    db.create_all()
    print("✅ Database tables created")
    
    # Create roles (skip if exist)
    roles_data = ['admin', 'finance', 'sales', 'customer']
    for role_name in roles_data:
        if not Role.query.filter_by(name=role_name).first():
            role = Role(name=role_name, description=f'{role_name} role')
            db.session.add(role)
    db.session.commit()
    print("✅ Roles created")
    
    # Create admin user
    admin_role = Role.query.filter_by(name='admin').first()
    admin = User(
        email='admin@local.dev',
        first_name='Admin',
        last_name='User',
        role_id=admin_role.id,
        is_active=True
    )
    admin.set_password('password123')
    db.session.add(admin)
    db.session.commit()
    print("✅ Admin user created")
    print(f"   📧 Email: admin@local.dev")
    print(f"   🔑 Password: password123")
    
    # Create sample customers
    customers_data = [
        {"name": "Acme Corporation", "email": "contact@acme.com", "phone": "555-1234"},
        {"name": "Tech Solutions Inc", "email": "hello@techsolutions.com", "phone": "555-5678"},
        {"name": "Global Enterprises", "email": "info@global.com", "phone": "555-9999"},
    ]
    
    for cust_data in customers_data:
        customer = Customer(
            name=cust_data["name"],
            email=cust_data["email"],
            phone=cust_data["phone"],
            status="active"
        )
        db.session.add(customer)
    db.session.commit()
    print(f"✅ Created {len(customers_data)} sample customers")
    
    # Create sample products
    products_data = [
        {"name": "Premium Software", "sku": "PREM-001", "description": "Premium subscription software", "base_price": "99.99"},
        {"name": "Enterprise Platform", "sku": "ENT-001", "description": "Enterprise-grade platform", "base_price": "299.99"},
        {"name": "Starter Package", "sku": "START-001", "description": "Perfect for startups", "base_price": "29.99"},
    ]
    
    for prod_data in products_data:
        product = Product(
            name=prod_data["name"],
            sku=prod_data["sku"],
            description=prod_data["description"],
            base_price=Decimal(prod_data["base_price"]),
            status="active"
        )
        db.session.add(product)
    db.session.commit()
    print(f"✅ Created {len(products_data)} sample products")
    
    # Create sample plans
    products = Product.query.all()
    for product in products:
        # Monthly plan
        plan_monthly = Plan(
            product_id=product.id,
            name=f"{product.name} - Monthly",
            description=f"Monthly subscription for {product.name}",
            price=product.base_price,
            billing_cycle="monthly",
            status="active"
        )
        db.session.add(plan_monthly)
        
        # Annual plan (with discount)
        annual_price = product.base_price * Decimal('10')  # 10 months price for annual
        plan_annual = Plan(
            product_id=product.id,
            name=f"{product.name} - Annual",
            description=f"Annual subscription for {product.name} (2 months free!)",
            price=annual_price,
            billing_cycle="annually",
            status="active"
        )
        db.session.add(plan_annual)
    
    db.session.commit()
    print(f"✅ Created 6 sample plans")
    
    # Create sample subscriptions
    customers = Customer.query.limit(2).all()
    plans = Plan.query.filter_by(billing_cycle='monthly').limit(2).all()
    
    for i, (customer, plan) in enumerate(zip(customers, plans)):
        subscription = Subscription(
            customer_id=customer.id,
            plan_id=plan.id,
            subscription_number=f"SUB-DEMO-{i+1:03d}",
            status="active",
            start_date=datetime.utcnow() - timedelta(days=30),
            next_billing_date=datetime.utcnow() + timedelta(days=30),
            monthly_recurring_revenue=plan.price,
            annual_contract_value=plan.price * 12,
            auto_renew=True
        )
        db.session.add(subscription)
    
    db.session.commit()
    print(f"✅ Created 2 sample active subscriptions")
    
    print("=" * 60)
    print("🎉 Demo data loaded successfully!")
    print()
    print("📊 Summary:")
    print(f"   • Customers: {Customer.query.count()}")
    print(f"   • Products: {Product.query.count()}")
    print(f"   • Plans: {Plan.query.count()}")
    print(f"   • Subscriptions: {Subscription.query.count()}")
    print()
    print("🌐 Starting Flask server...")
    print("   Backend: http://localhost:5000")
    print("   API Health: http://localhost:5000/api/v1/health")
    print()
    print("Press CTRL+C to stop the server")
    print("=" * 60)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
