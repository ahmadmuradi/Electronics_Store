import os
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.sql import func
from pydantic import BaseModel
from datetime import datetime

# --- FastAPI App Setup ---

app = FastAPI()

# --- Database Configuration ---

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./inventory.db") # Use SQLite for simplicity, can be changed
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}) # Needed for SQLite

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- SQLAlchemy Models (based on previous schema design) ---

class Supplier(Base):
    __tablename__ = "Suppliers"

    supplier_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    contact_person = Column(String)
    phone = Column(String)
    email = Column(String)
    address = Column(Text)

class Category(Base):
    __tablename__ = "Categories"

    category_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class Product(Base):
    __tablename__ = "Products"

    product_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    price = Column(Float)
    cost = Column(Float)
    stock_quantity = Column(Integer, default=0)
    sku = Column(String, unique=True, index=True)
    upc = Column(String, unique=True, index=True)
    supplier_id = Column(Integer, ForeignKey("Suppliers.supplier_id"))
    category_id = Column(Integer, ForeignKey("Categories.category_id"))

class Customer(Base):
    __tablename__ = "Customers"

    customer_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    phone = Column(String)
    email = Column(String)

class Sale(Base):
    __tablename__ = "Sales"

    sale_id = Column(Integer, primary_key=True, index=True)
    sale_date = Column(DateTime, server_default=func.now())
    customer_id = Column(Integer, ForeignKey("Customers.customer_id"))
    total_amount = Column(Float)

class SaleItem(Base):
    __tablename__ = "SaleItems"

    sale_item_id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("Sales.sale_id"))
    product_id = Column(Integer, ForeignKey("Products.product_id"))
    quantity = Column(Integer)
    price = Column(Float)

class InventoryTransaction(Base):
    __tablename__ = "InventoryTransactions"

    transaction_id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("Products.product_id"))
    transaction_type = Column(String)
    quantity_change = Column(Integer)
    transaction_date = Column(DateTime, server_default=func.now())
    notes = Column(Text)

class PurchaseOrder(Base):
    __tablename__ = "PurchaseOrders"

    po_id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("Suppliers.supplier_id"))
    order_date = Column(DateTime)
    expected_delivery_date = Column(DateTime)
    status = Column(String)
    total_amount = Column(Float)

class PurchaseOrderItem(Base):
    __tablename__ = "PurchaseOrderItem"

    po_item_id = Column(Integer, primary_key=True, index=True)
    po_id = Column(Integer, ForeignKey("PurchaseOrders.po_id"))
    product_id = Column(Integer, ForeignKey("Products.product_id"))
    quantity = Column(Integer)
    unit_cost = Column(Float)

# Create tables in the database
Base.metadata.create_all(bind=engine)

# --- Pydantic Models (for data validation and serialization) ---

class SupplierBase(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

class SupplierCreate(SupplierBase):
    pass

class Supplier(SupplierBase):
    supplier_id: int

    class Config:
        from_attributes = True # Updated from orm_mode

class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    category_id: int

    class Config:
        from_attributes = True # Updated from orm_mode

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    cost: Optional[float] = None
    stock_quantity: int = 0
    sku: Optional[str] = None
    upc: Optional[str] = None
    supplier_id: Optional[int] = None
    category_id: Optional[int] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    name: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None

class Product(ProductBase):
    product_id: int

    class Config:
        from_attributes = True # Updated from orm_mode

class CustomerBase(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    customer_id: int

    class Config:
        from_attributes = True # Updated from orm_mode

class SaleItemBase(BaseModel):
    product_id: int
    quantity: int
    price: float

class SaleItemCreate(SaleItemBase):
    pass

class SaleItem(SaleItemBase):
    sale_item_id: int
    sale_id: int
    product_name: Optional[str] = None
    total_price: Optional[float] = None

    class Config:
        from_attributes = True # Updated from orm_mode

class SaleBase(BaseModel):
    customer_id: Optional[int] = None
    total_amount: float

class SaleCreate(SaleBase):
    items: List[SaleItemCreate] # For creating a sale with items

class Sale(SaleBase):
    sale_id: int
    sale_date: datetime
    items: List[SaleItem] = [] # To include sale items in the response

    class Config:
        from_attributes = True # Updated from orm_mode

class InventoryTransactionBase(BaseModel):
    product_id: int
    transaction_type: str
    quantity_change: int
    notes: Optional[str] = None

class InventoryTransactionCreate(InventoryTransactionBase):
    pass

class InventoryTransaction(InventoryTransactionBase):
    transaction_id: int
    transaction_date: datetime

    class Config:
        from_attributes = True # Updated from orm_mode

class PurchaseOrderItemBase(BaseModel):
    product_id: int
    quantity: int
    unit_cost: Optional[float] = None

class PurchaseOrderItemCreate(PurchaseOrderItemBase):
    pass

class PurchaseOrderItem(PurchaseOrderItemBase):
    po_item_id: int
    po_id: int

    class Config:
        from_attributes = True # Updated from orm_mode

class PurchaseOrderBase(BaseModel):
    supplier_id: Optional[int] = None
    order_date: Optional[datetime] = None
    expected_delivery_date: Optional[datetime] = None
    status: Optional[str] = None
    total_amount: Optional[float] = None

class PurchaseOrderCreate(PurchaseOrderBase):
    items: List[PurchaseOrderItemCreate]

class PurchaseOrder(PurchaseOrderBase):
    po_id: int
    items: List[PurchaseOrderItem] = []

    class Config:
        from_attributes = True # Updated from orm_mode

# --- API Endpoints ---

# Product Endpoints
@app.post("/products/", response_model=Product)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    try:
        db_product = Product(**product.model_dump())
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating product: {str(e)}")

@app.get("/products/", response_model=List[Product])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = db.query(Product).offset(skip).limit(limit).all()
    return products

@app.get("/products/{product_id}", response_model=Product)
def read_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.put("/products/{product_id}", response_model=Product)
def update_product(product_id: int, product_update: ProductUpdate, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.product_id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = product_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)

    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.product_id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(db_product)
    db.commit()
    return {"detail": "Product deleted successfully"}

# Inventory Endpoints
@app.put("/inventory/update_stock/{product_id}")
def update_stock(product_id: int, quantity_change: int, notes: Optional[str] = None, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.product_id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    new_stock = db_product.stock_quantity + quantity_change
    if new_stock < 0:
         raise HTTPException(status_code=400, detail="Stock quantity cannot be negative")

    db_product.stock_quantity = new_stock

    transaction_type = "adjustment"
    if quantity_change > 0:
        transaction_type = "receipt"
    elif quantity_change < 0:
        transaction_type = "sale" # Or 'adjustment' depending on context

    db_transaction = InventoryTransaction(
        product_id=product_id,
        transaction_type=transaction_type,
        quantity_change=quantity_change,
        notes=notes
    )

    db.add(db_product)
    db.add(db_transaction)
    db.commit()
    db.refresh(db_product)
    db.refresh(db_transaction)

    return {"product_id": product_id, "new_stock_quantity": db_product.stock_quantity, "transaction_id": db_transaction.transaction_id}

@app.get("/inventory/", response_model=List[Product])
def view_inventory(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # This endpoint is the same as reading products, but semantically different for inventory view
    products = db.query(Product).offset(skip).limit(limit).all()
    return products

# Supplier Endpoints
@app.post("/suppliers/", response_model=Supplier)
def create_supplier(supplier: SupplierCreate, db: Session = Depends(get_db)):
    db_supplier = Supplier(**supplier.model_dump())
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier

@app.get("/suppliers/", response_model=List[Supplier])
def read_suppliers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    suppliers = db.query(Supplier).offset(skip).limit(limit).all()
    return suppliers

@app.get("/suppliers/{supplier_id}", response_model=Supplier)
def read_supplier(supplier_id: int, db: Session = Depends(get_db)):
    supplier = db.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier

@app.put("/suppliers/{supplier_id}", response_model=Supplier)
def update_supplier(supplier_id: int, supplier_update: SupplierCreate, db: Session = Depends(get_db)):
    db_supplier = db.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()
    if db_supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")

    update_data = supplier_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_supplier, key, value)

    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier

@app.delete("/suppliers/{supplier_id}")
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    db_supplier = db.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()
    if db_supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")

    db.delete(db_supplier)
    db.commit()
    return {"detail": "Supplier deleted successfully"}

# Basic Sales Data Access (Product Price and Availability)
# This is covered by the read_product and read_products endpoints which include price and stock_quantity.
# No separate endpoints are strictly needed for this basic requirement.

# Category Endpoints
@app.post("/categories/", response_model=Category)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    db_category = Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@app.get("/categories/", response_model=List[Category])
def read_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    categories = db.query(Category).offset(skip).limit(limit).all()
    return categories

@app.get("/categories/{category_id}", response_model=Category)
def read_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@app.put("/categories/{category_id}", response_model=Category)
def update_category(category_id: int, category_update: CategoryCreate, db: Session = Depends(get_db)):
    db_category = db.query(Category).filter(Category.category_id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    update_data = category_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)

    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@app.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    db_category = db.query(Category).filter(Category.category_id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(db_category)
    db.commit()
    return {"detail": "Category deleted successfully"}

# Customer Endpoints
@app.post("/customers/", response_model=Customer)
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    db_customer = Customer(**customer.model_dump())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

@app.get("/customers/", response_model=List[Customer])
def read_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    customers = db.query(Customer).offset(skip).limit(limit).all()
    return customers

@app.get("/customers/{customer_id}", response_model=Customer)
def read_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@app.put("/customers/{customer_id}", response_model=Customer)
def update_customer(customer_id: int, customer_update: CustomerCreate, db: Session = Depends(get_db)):
    db_customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    update_data = customer_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_customer, key, value)

    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

@app.delete("/customers/{customer_id}")
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    db_customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    db.delete(db_customer)
    db.commit()
    return {"detail": "Customer deleted successfully"}

# Sales Endpoints
@app.post("/sales/", response_model=Sale)
def create_sale(sale: SaleCreate, db: Session = Depends(get_db)):
    total_amount = 0
    db_sale_items = []

    for item in sale.items:
        db_product = db.query(Product).filter(Product.product_id == item.product_id).first()
        if db_product is None:
            raise HTTPException(status_code=404, detail=f"Product with id {item.product_id} not found")
        if db_product.stock_quantity < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for product {db_product.name}")

        item_price = item.price if item.price is not None else db_product.price
        total_amount += item_price * item.quantity

        db_sale_item = SaleItem(
            product_id=item.product_id,
            quantity=item.quantity,
            price=item_price
        )
        db_sale_items.append(db_sale_item)

        # Update product stock
        db_product.stock_quantity -= item.quantity
        db.add(db_product)

        # Create inventory transaction
        db_transaction = InventoryTransaction(
            product_id=item.product_id,
            transaction_type="sale",
            quantity_change=-item.quantity,
            notes=f"Sale transaction for Sale ID (will be assigned later)"
        )
        db.add(db_transaction)

    db_sale = Sale(customer_id=sale.customer_id, total_amount=total_amount)
    db.add(db_sale)
    db.flush() # To get the sale_id before adding sale items

    for db_sale_item in db_sale_items:
        db_sale_item.sale_id = db_sale.sale_id
        db.add(db_sale_item)

    # Update notes for inventory transactions with the new Sale ID
    for db_transaction in db.query(InventoryTransaction).filter(InventoryTransaction.notes == "Sale transaction for Sale ID (will be assigned later)").all():
         db_transaction.notes = f"Sale transaction for Sale ID {db_sale.sale_id}"
         db.add(db_transaction)

    db.commit()
    db.refresh(db_sale)

    # Load sale items for the response model
    db_sale.items = db.query(SaleItem).filter(SaleItem.sale_id == db_sale.sale_id).all()

    return db_sale

@app.get("/sales/", response_model=List[Sale])
def read_sales(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    sales = db.query(Sale).offset(skip).limit(limit).all()
    
    # Get all sale IDs to fetch items in one query
    sale_ids = [sale.sale_id for sale in sales]
    if sale_ids:
        items = db.query(SaleItem, Product.name).join(Product).filter(SaleItem.sale_id.in_(sale_ids)).all()
        
        # Group items by sale_id
        items_by_sale = {}
        for item, product_name in items:
            if item.sale_id not in items_by_sale:
                items_by_sale[item.sale_id] = []
            item.product_name = product_name
            item.total_price = item.price * item.quantity
            items_by_sale[item.sale_id].append(item)
        
        # Assign items to sales
        for sale in sales:
            sale.items = items_by_sale.get(sale.sale_id, [])
    
    return sales

@app.get("/sales/{sale_id}", response_model=Sale)
def read_sale(sale_id: int, db: Session = Depends(get_db)):
    sale = db.query(Sale).filter(Sale.sale_id == sale_id).first()
    if sale is None:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    # Get items with product names in one query
    items = db.query(SaleItem, Product.name).join(Product).filter(SaleItem.sale_id == sale_id).all()
    sale.items = []
    for item, product_name in items:
        item.product_name = product_name
        item.total_price = item.price * item.quantity
        sale.items.append(item)
    
    return sale

# Inventory Transaction Endpoints
@app.get("/inventory/transactions/", response_model=List[InventoryTransaction])
def read_inventory_transactions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    transactions = db.query(InventoryTransaction).offset(skip).limit(limit).all()
    return transactions

@app.get("/inventory/transactions/{transaction_id}", response_model=InventoryTransaction)
def read_inventory_transaction(transaction_id: int, db: Session = Depends(get_db)):
    transaction = db.query(InventoryTransaction).filter(InventoryTransaction.transaction_id == transaction_id).first()
    if transaction is None:
        raise HTTPException(status_code=404, detail="Inventory transaction not found")
    return transaction

# Purchase Order Endpoints
@app.post("/purchase_orders/", response_model=PurchaseOrder)
def create_purchase_order(po: PurchaseOrderCreate, db: Session = Depends(get_db)):
    total_amount = 0
    db_po_items = []

    for item in po.items:
        db_product = db.query(Product).filter(Product.product_id == item.product_id).first()
        if db_product is None:
            raise HTTPException(status_code=404, detail=f"Product with id {item.product_id} not found")

        item_cost = item.unit_cost if item.unit_cost is not None else db_product.cost
        if item_cost is None:
             raise HTTPException(status_code=400, detail=f"Unit cost not provided for product {db_product.name} and not available in product data.")

        total_amount += item_cost * item.quantity

        db_po_item = PurchaseOrderItem(
            product_id=item.product_id,
            quantity=item.quantity,
            unit_cost=item_cost
        )
        db_po_items.append(db_po_item)

    db_po = PurchaseOrder(
        supplier_id=po.supplier_id,
        order_date=po.order_date if po.order_date else datetime.now(),
        expected_delivery_date=po.expected_delivery_date,
        status=po.status if po.status else "pending",
        total_amount=total_amount
    )

    db.add(db_po)
    db.flush() # To get the po_id before adding po items

    for db_po_item in db_po_items:
        db_po_item.po_id = db_po.po_id
        db.add(db_po_item)

    db.commit()
    db.refresh(db_po)

    # Load PO items for the response model
    db_po.items = db.query(PurchaseOrderItem).filter(PurchaseOrderItem.po_id == db_po.po_id).all()

    return db_po

@app.get("/purchase_orders/", response_model=List[PurchaseOrder])
def read_purchase_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    pos = db.query(PurchaseOrder).offset(skip).limit(limit).all()
    return pos

@app.get("/purchase_orders/{po_id}", response_model=PurchaseOrder)
def read_purchase_order(po_id: int, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_id == po_id).first()
    if po is None:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    po.items = db.query(PurchaseOrderItem).filter(PurchaseOrderItem.po_id == po_id).all()
    return po
