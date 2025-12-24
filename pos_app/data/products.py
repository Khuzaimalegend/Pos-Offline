# Product data management
import json
import os

PRODUCTS_FILE = os.path.join(os.path.dirname(__file__), 'products.json')

def cache_products_from_session(session):
	"""Cache products to the local PC using an existing DB session.

	This is intended for CLIENT machines: after connecting to the server DB,
	download products and store them locally so the client has data even if
	the connection drops later.
	"""
	try:
		from pos_app.models.database import Product
		products_query = session.query(Product).all() if session is not None else []
		products = []
		for p in (products_query or []):
			try:
				cat = p.categories[0].name if getattr(p, 'categories', None) else 'Uncategorized'
			except Exception:
				cat = 'Uncategorized'
			products.append({
				'id': getattr(p, 'id', None),
				'name': getattr(p, 'name', None),
				'sku': getattr(p, 'sku', None),
				'barcode': getattr(p, 'barcode', None),
				'description': getattr(p, 'description', None),
				'retail_price': getattr(p, 'retail_price', 0),
				'wholesale_price': getattr(p, 'wholesale_price', 0),
				'purchase_price': getattr(p, 'purchase_price', 0),
				'warehouse_stock': getattr(p, 'warehouse_stock', 0),
				'retail_stock': getattr(p, 'retail_stock', 0),
				'stock_level': getattr(p, 'stock_level', 0),
				'reorder_level': getattr(p, 'reorder_level', 0),
				'unit': getattr(p, 'unit', None),
				'brand': getattr(p, 'brand', None),
				'category': cat,
			})

		# Primary cache: DataSync cache in user profile
		try:
			from pos_app.utils.data_sync import get_data_sync
			get_data_sync().cache_table_data('products', products)
		except Exception:
			pass

		# Secondary cache: existing products.json file
		try:
			save_products(products)
		except Exception:
			pass

		return products
	except Exception as e:
		print(f"[Products] Error caching products from session: {e}")
		return []

def load_products_from_db():
	"""Load products from database (server/client mode)"""
	try:
		from pos_app.database.connection import Database
		from pos_app.models.database import Product
		
		db = Database()
		
		if db._is_offline:
			print("[Products] Database offline, falling back to local cache")
			return load_products_from_file()
		
		# Query products from database using SQLAlchemy
		products_query = db.session.query(Product).all()
		
		if products_query:
			print(f"[Products] Loaded {len(products_query)} products from database")
			# Convert to dict format and cache locally
			products = []
			for p in products_query:
				products.append({
					'id': p.id,
					'name': p.name,
					'sku': p.sku,
					'barcode': p.barcode,
					'description': p.description,
					'retail_price': p.retail_price,
					'wholesale_price': p.wholesale_price,
					'purchase_price': p.purchase_price,
					'warehouse_stock': p.warehouse_stock,
					'retail_stock': p.retail_stock,
					'stock_level': p.stock_level,
					'reorder_level': p.reorder_level,
					'unit': p.unit,
					'brand': p.brand,
					'category': p.categories[0].name if p.categories else 'Uncategorized'
				})
			save_products(products)
			return products
		else:
			print("[Products] No products in database, using local cache")
			return load_products_from_file()
	except Exception as e:
		print(f"[Products] Error loading from database: {e}, falling back to local cache")
		return load_products_from_file()

def load_products_from_file():
	"""Load products from local JSON file (fallback/offline)"""
	if not os.path.exists(PRODUCTS_FILE):
		return []
	try:
		with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
			return json.load(f)
	except Exception as e:
		print(f"[Products] Error loading from file: {e}")
		return []

def load_products():
	"""Load products - tries database first, falls back to file"""
	return load_products_from_db()

def save_products(products):
	"""Save products to local file (cache)"""
	try:
		with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
			json.dump(products, f, indent=2, ensure_ascii=False)
		print(f"[Products] Cached {len(products)} products to local file")
	except Exception as e:
		print(f"[Products] Error saving products: {e}")

def save_products_to_db(products):
	"""Save products to database"""
	try:
		from pos_app.database.connection import Database
		db = Database()
		
		if db._is_offline:
			print("[Products] Database offline, saving to local cache only")
			save_products(products)
			return False
		
		# Clear existing products
		db.execute("DELETE FROM products")
		
		# Insert new products
		for product in products:
			query = """
				INSERT INTO products (name, sku, category, price, quantity, description)
				VALUES (%s, %s, %s, %s, %s, %s)
			"""
			db.execute(query, (
				product.get('name'),
				product.get('sku'),
				product.get('category'),
				product.get('price'),
				product.get('quantity'),
				product.get('description')
			))
		
		print(f"[Products] Saved {len(products)} products to database")
		# Also cache locally
		save_products(products)
		return True
	except Exception as e:
		print(f"[Products] Error saving to database: {e}")
		# Fallback to local save
		save_products(products)
		return False

def get_products():
	"""Get all products"""
	return load_products()

def add_product(product):
	"""Add product to database and cache"""
	try:
		from pos_app.database.connection import Database
		from pos_app.models.database import Product
		
		db = Database()
		
		if not db._is_offline:
			# Save to database using SQLAlchemy (schema-safe)
			product_kwargs = {
				'name': product.get('name'),
				'sku': product.get('sku'),
				'barcode': product.get('barcode'),
				'description': product.get('description'),
				'retail_price': product.get('retail_price', 0),
				'wholesale_price': product.get('wholesale_price', 0),
				'purchase_price': product.get('purchase_price'),
				'warehouse_stock': product.get('warehouse_stock', 0),
				'retail_stock': product.get('retail_stock', 0),
				'stock_level': product.get('stock_level', 0),
				'reorder_level': product.get('reorder_level', 0),
				'unit': product.get('unit'),
				'brand': product.get('brand'),
				'colors': product.get('colors'),
				'product_type': product.get('product_type'),
				'low_stock_alert': product.get('low_stock_alert'),
				'weight': product.get('weight'),
				'warranty': product.get('warranty'),
				'product_category_id': product.get('product_category_id'),
				'product_subcategory_id': product.get('product_subcategory_id'),
				'packaging_type_id': product.get('packaging_type_id'),
				'supplier_id': product.get('supplier_id'),
			}

			allowed_keys = None
			try:
				allowed_keys = set(getattr(getattr(Product, '__table__', None), 'columns', {}).keys())
			except Exception:
				allowed_keys = None

			if allowed_keys:
				product_kwargs = {k: v for k, v in product_kwargs.items() if k in allowed_keys}
			else:
				product_kwargs = {k: v for k, v in product_kwargs.items() if v is not None}

			# Remove keys with None values to avoid unique constraint issues with empty strings
			try:
				for _k in list(product_kwargs.keys()):
					if product_kwargs.get(_k) in ("", None):
						if _k in ('barcode',):
							product_kwargs[_k] = None
						elif product_kwargs.get(_k) is None:
							product_kwargs.pop(_k, None)
			except Exception:
				pass

			new_product = None
			try:
				new_product = Product(**product_kwargs)
			except TypeError:
				# Defensive: iteratively drop unknown keys
				try:
					kwargs2 = dict(product_kwargs)
					while True:
						try:
							new_product = Product(**kwargs2)
							break
						except TypeError as te:
							msg = str(te)
							bad_key = None
							try:
								if "'" in msg and "invalid keyword argument" in msg:
									bad_key = msg.split("'")[1]
							except Exception:
								bad_key = None
							if bad_key and bad_key in kwargs2:
								kwargs2.pop(bad_key, None)
								continue
							raise
				except Exception:
					raise
			db.session.add(new_product)
			db.session.commit()
			print(f"[Products] Added product '{product.get('name')}' to database")
		
		# Also update local cache
		products = load_products_from_file()
		products.append(product)
		save_products(products)
	except Exception as e:
		print(f"[Products] Error adding product: {e}")
		# Fallback to local only
		products = load_products_from_file()
		products.append(product)
		save_products(products)

def remove_product(product_name):
	"""Remove product from database and cache"""
	try:
		from pos_app.database.connection import Database
		from pos_app.models.database import Product
		
		db = Database()
		
		if not db._is_offline:
			# Remove from database using SQLAlchemy
			product = db.session.query(Product).filter(Product.name == product_name).first()
			if product:
				db.session.delete(product)
				db.session.commit()
				print(f"[Products] Removed product '{product_name}' from database")
		
		# Also update local cache
		products = load_products_from_file()
		products = [p for p in products if p.get('name') != product_name]
		save_products(products)
	except Exception as e:
		print(f"[Products] Error removing product: {e}")
		# Fallback to local only
		products = load_products_from_file()
		products = [p for p in products if p.get('name') != product_name]
		save_products(products)

def edit_product(old_name, new_product):
	"""Edit product in database and cache"""
	try:
		from pos_app.database.connection import Database
		from pos_app.models.database import Product
		
		db = Database()
		
		if not db._is_offline:
			# Update in database using SQLAlchemy
			product = db.session.query(Product).filter(Product.name == old_name).first()
			if product:
				product.name = new_product.get('name', product.name)
				product.sku = new_product.get('sku', product.sku)
				product.barcode = new_product.get('barcode', product.barcode)
				product.description = new_product.get('description', product.description)
				product.retail_price = new_product.get('retail_price', product.retail_price)
				product.wholesale_price = new_product.get('wholesale_price', product.wholesale_price)
				product.purchase_price = new_product.get('purchase_price', product.purchase_price)
				product.warehouse_stock = new_product.get('warehouse_stock', product.warehouse_stock)
				product.retail_stock = new_product.get('retail_stock', product.retail_stock)
				product.stock_level = new_product.get('stock_level', product.stock_level)
				product.unit = new_product.get('unit', product.unit)
				product.brand = new_product.get('brand', product.brand)
				db.session.commit()
				print(f"[Products] Updated product '{old_name}' in database")
		
		# Also update local cache
		products = load_products_from_file()
		for i, p in enumerate(products):
			if p.get('name') == old_name:
				products[i] = new_product
				break
		save_products(products)
	except Exception as e:
		print(f"[Products] Error editing product: {e}")
		# Fallback to local only
		products = load_products_from_file()
		for i, p in enumerate(products):
			if p.get('name') == old_name:
				products[i] = new_product
				break
		save_products(products)
