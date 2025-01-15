from string import ascii_letters
from random import choices

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from shopapp.models import Product, Order
from shopapp.utils import add_two_numbers


class AddTwoNumbersTestCase(TestCase):
    def test_add_two_numbers(self):
        result = add_two_numbers(2, 3)
        self.assertEqual(result, 5)


class ProductCreateViewTestCase(TestCase):
    def setUp(self) -> None:
        self.product_name = "".join(choices(ascii_letters, k=10))
        Product.objects.filter(name=self.product_name).delete()

    def test_create_product(self):
        response = self.client.post(
            reverse("shopapp:product_create"),
            {
                "name": self.product_name,
                "price": "123.45",
                "description": "A good table",
                "discount": "10",
            }
        )
        self.assertRedirects(response, reverse("shopapp:products_list"))
        self.assertTrue(
            Product.objects.filter(name=self.product_name).exists()
        )


class ProductDetailsViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.product = Product.objects.create(name="Best Product")

    # def setUp(self) -> None:
    #     self.product = Product.objects.create(name="Best Product")

    def test_get_product(self):
        response = self.client.get(
            reverse('shopapp:product_details', kwargs={"pk": self.product.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_get_product_and_check_content(self):
        response = self.client.get(
            reverse('shopapp:product_details', kwargs={"pk": self.product.pk})
        )
        self.assertContains(response, self.product.name)

    @classmethod
    def tearDownClass(cls):
        cls.product.delete()

    # def tearDown(self) -> None:
    #     self.product.delete()


class ProductsListViewTestCase(TestCase):
    fixtures = [
        'products-fixture.json',
    ]

    def test_products(self):
        response = self.client.get(reverse('shopapp:products_list'))

        # for product in Product.objects.filter(archived=False).all():
        #     self.assertContains(response, product.name)

        # products = Product.objects.filter(archived=False).all()
        # products_ = response.context["products"]
        # for p, p_ in zip(products, products_):
        #     self.assertEqual(p.pk, p_.pk)

        self.assertQuerysetEqual(
            qs=Product.objects.filter(archived=False).all(),
            values=(p.pk for p in response.context["products"]),
            transform=lambda p: p.pk
        )
        self.assertTemplateUsed(response, 'shopapp/products-list.html')


class OrdersListViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        # cls.credentials = dict(username="bob-test", password="qwerty")
        # cls.user = User.objects.create_user(**cls.credentials)

        cls.user = User.objects.create_user(username="bob-test", password="qwerty")

    def setUp(self):
        # self.client.login(**self.credentials)

        self.client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()

    def test_orders_view(self):
        response = self.client.get(reverse("shopapp:orders_list"))
        self.assertContains(response, "Orders")

    def test_orders_view_not_authenticated(self):
        self.client.logout()
        response = self.client.get(reverse("shopapp:orders_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(str(settings.LOGIN_URL), response.url)


class ProductsExportViewTestCase(TestCase):
    fixtures = [
        'products-fixture.json'
    ]

    def test_get_products_view(self):
        response = self.client.get(
            reverse('shopapp:products-export')
        )
        self.assertEqual(response.status_code, 200)
        products = Product.objects.order_by("pk").all()
        expected_data = [
            {
                "pk": product.pk,
                "name": product.name,
                "price": str(product.price),
                "archived": product.archived,
            }
            for product in products
        ]
        products_data = response.json()
        self.assertEqual(
            products_data["products"],
            expected_data
        )


class OrderDetailViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username="bob-test", password="qwerty")
        content_type = ContentType.objects.get_for_model(Order)
        permission = Permission.objects.get(codename='view_order', content_type=content_type)
        cls.user.user_permissions.add(permission)

    def setUp(self):
        self.client.force_login(self.user)
        self.order = Order.objects.create(
            pk=1,
            delivery_address="New order",
            promocode="",
            user=self.user,
        )

    def test_get_order_detail_view(self):
        response = self.client.get(
            reverse("shopapp:order_details",
                    kwargs={"pk": self.order.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["order"].pk, self.order.pk)
        self.assertContains(response, self.order.delivery_address)
        self.assertContains(response, self.order.promocode)

    def tearDown(self):
        self.order.delete()

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()


class OrdersExportTestCase(TestCase):
    fixtures = [
        'orders-fixture.json',
        'products-fixture.json',
        'users-fixture.json',
    ]

    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username="bob-test", password="qwerty")
        cls.user.is_staff = True
        cls.user.save()

    def setUp(self):
        self.client.force_login(self.user)

    def test_get_orders_view(self):
        response = self.client.get(
            reverse('shopapp:orders-export')
        )
        self.assertEqual(response.status_code, 200)
        orders = Order.objects.select_related("user").prefetch_related("products").all()
        expected_data = [
            {
                "pk": order.pk,
                "delivery_address": order.delivery_address,
                "promocode": order.promocode,
                "products": [product.id for product in order.products.all()],
                "user": order.user.id
            }
            for order in orders
        ]
        orders_data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            orders_data["orders"],
            expected_data
        )

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()
