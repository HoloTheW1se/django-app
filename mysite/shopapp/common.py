from csv import DictReader
from io import TextIOWrapper

from django.contrib.auth.models import User

from shopapp.models import Product, Order


def save_csv_products(file, encoding):
    csv_file = TextIOWrapper(
        file, encoding
    )
    reader = DictReader(csv_file)

    products = [
        Product(**row)
        for row in reader
    ]
    Product.objects.bulk_create(products)
    return products


def save_csv_orders(file, encoding):
    csv_file = TextIOWrapper(
        file,
        encoding
    )
    reader = DictReader(csv_file)

    orders = []
    products_names = {product.name: product for product in Product.objects.all()}
    users_names = {user.username: user for user in User.objects.all()}

    for row in reader:
        username = row.pop("user")
        products_from_file = row.pop("products").split(",")
        user = users_names.get(username)

        if not user:
            print(f"User {username} not found")
            continue

        order_data = {**row, "user": user}
        order = Order(**order_data)
        order.save()

        for name in products_from_file:
            product = products_names.get(name)
            if not product:
                print(f"Product {name} not found")
                continue
            order.products.add(product)
        orders.append(order)
    return orders
