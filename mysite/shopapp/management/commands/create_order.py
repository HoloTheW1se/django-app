from typing import Sequence

from django.contrib.auth.models import User
from django.core.management import BaseCommand
from django.db import transaction
from shopapp.models import Order, Product


class Command(BaseCommand):
    @transaction.atomic
    def handle(self, *args, **options):
        # with transaction.atomic():
        #     pass

        self.stdout.write("Create order with products")
        user = User.objects.get(username="admin")
        order, created = Order.objects.get_or_create(
            delivery_address="ul. Ivanova, d 8",
            promocode="promo5",
            user=user,
        )
        self.stdout.write(f"Created order {order}")

        # products: Sequence[Product] = Product.objects.defer("description", "price", "created_at").all()
        products: Sequence[Product] = Product.objects.only("id").all()
        for product in products:
            order.products.add(product)

        order.save()
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully added products {order.products.all()} to order {order}"
            )
        )
