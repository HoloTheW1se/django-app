"""
В этом модуле лежат различные наборы представлений.

Разные view интернет-магазина: по товарам, заказам и т.д.
"""

import logging
from csv import DictWriter
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse
)
from django.core.cache import cache
from django.contrib.auth.models import User
from django.contrib.syndication.views import Feed
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.contrib.auth.models import Group
from django.views.decorators.cache import cache_page
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin
)
from django.utils.decorators import method_decorator
from rest_framework.parsers import MultiPartParser
from rest_framework.viewsets import ModelViewSet
from rest_framework.mixins import ListModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .common import save_csv_products
from .forms import GroupForm, ProductForm
from .models import Product, Order, ProductImage
from .serializers import ProductSerializer, OrderSerializer
from timeit import default_timer


log = logging.getLogger(__name__)


@extend_schema(description="Product views CRUD")
class ProductViewSet(ModelViewSet):
    """
    Набор представлений для действий над Product.

    Полный CRUD для сущностей товара
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [
        SearchFilter,
        DjangoFilterBackend,
        OrderingFilter,
    ]
    search_fields = ["name", "description"]
    filterset_fields = [
        "name",
        "description",
        "price",
        "discount",
        "archived",
    ]
    ordering_fields = [
        "name",
        "price",
        "discount",
    ]

    @action(methods=["get"], detail=False)
    def download_csv(self, request: Request):

        response = HttpResponse(content_type="text/csv")
        filename = "products-export.csv"
        response["Content-Disposition"] = f"attachment; filename={filename}"
        queryset = self.filter_queryset(self.get_queryset())
        fields = [
            "name",
            "description",
            "price",
            "discount",
        ]
        queryset = queryset.only(*fields)
        writer = DictWriter(response, fieldnames=fields)
        writer.writeheader()

        for product in queryset:
            writer.writerow({
                field: getattr(product, field)
                for field in fields
            })

        return response

    @action(
        detail=False,
        methods=["post"],
        parser_classes=[MultiPartParser],
    )
    def upload_csv(self, request: Request):
        products = save_csv_products(
            request.FILES["file"],
            encoding=request.encoding,
        )
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)



    @extend_schema(
        summary="Получить список товаров",
        description="Возвращает **список товаров**; вернёт пустой список, если товаров нет",
    )
    @method_decorator(cache_page(60 * 2))
    def list(self, request, *args, **kwargs):
        print("Hello products list")
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Создать новый товар",
        description="Создаёт новый товар на основе **тела запроса**",
        responses={
            201: ProductSerializer,
            400: OpenApiResponse(description="В теле запроса есть ошибка, возвращает ошибку"),
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Получить товар по id",
        description="Возвращает **товар**; вернёт 404, если товар не найден",
        responses={
            200: ProductSerializer,
            404: OpenApiResponse(description="Пустой ответ, товар с этим id не найден"),
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Изменить товар по id",
        description="**Изменяет** товар на основе тела запроса",
        responses={
            200: ProductSerializer,
            404: OpenApiResponse(description="Пустой ответ, товар с этим id не найден"),
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Изменить детали товара по id",
        description="Изменяет **деталь** товара на основе тела запроса",
        responses={
            200: ProductSerializer,
            404: OpenApiResponse(description="Пустой ответ, товар с этим id не найден"),
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Удалить товар по id",
        description="Удаляет **товар** по id; вернёт 404, если товар не найден",
        responses={
            204: OpenApiResponse(description="Пустой ответ, товар удалён"),
            404: OpenApiResponse(description="Пустой ответ, товар с этим id не найден"),
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class OrderViewSet(ModelViewSet):
    """
    Набор представлений для действий над Order.

    Полный CRUD для сущностей заказа
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = [
        SearchFilter,
        DjangoFilterBackend,
        OrderingFilter,
    ]
    search_fields = ["delivery_address", "promocode"]
    filterset_fields = [
        "delivery_address",
        "promocode",
        "user",
        "products",

    ]
    ordering_fields = [
        "delivery_address",
        "promocode",
        "created_at",
    ]

    @extend_schema(
        summary="Получить список заказов",
        description="Возвращает **список заказов**; вернёт пустой список, если заказов нет",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Создать новый заказ",
        description="Создаёт новый заказ на основе **тела запроса**",
        responses={
            201: OrderSerializer,
            400: OpenApiResponse(description="В теле запроса есть ошибка, возвращает ошибку"),
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Получить заказ по id",
        description="Возвращает **заказ**; вернёт 404, если заказ не найден",
        responses={
            200: OrderSerializer,
            404: OpenApiResponse(description="Пустой ответ, заказ с этим id не найден"),
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Изменить заказ по id",
        description="**Изменяет** заказ на основе тела запроса",
        responses={
            200: OrderSerializer,
            404: OpenApiResponse(description="Пустой ответ, заказ с этим id не найден"),
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Изменить детали заказа по id",
        description="Изменяет **деталь** заказа на основе тела запроса",
        responses={
            200: OrderSerializer,
            404: OpenApiResponse(description="Пустой ответ, заказ с этим id не найден"),
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Удалить заказ по id",
        description="Удаляет **заказ** по id; вернёт 404, если заказ не найден",
        responses={
            204: OpenApiResponse(description="Пустой ответ, заказ удалён"),
            404: OpenApiResponse(description="Пустой ответ, заказ с этим id не найден"),
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class ShopIndexView(View):

    # @method_decorator(cache_page(60 * 2))
    def get(self, request: HttpRequest) -> HttpResponse:
        products = [
            ('Laptop', 1999),
            ('Desktop', 2999),
            ('Smartphone', 999),
        ]
        context = {
            "time_running": default_timer(),
            "products": products,
            "items": 1,
        }
        print("shop index context:", context)
        log.debug("Products for shop index: %s", products)
        log.info("Rendering shop index")
        return render(request, 'shopapp/shop-index.html', context=context)


class GroupsListView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        context = {
            "form": GroupForm(),
            "groups": Group.objects.prefetch_related('permissions').all(),
        }
        return render(request, 'shopapp/groups-list.html', context=context)

    def post(self, request: HttpRequest) -> HttpResponse:
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()

        return redirect(request.path)


class ProductDetailsView(DetailView):
    template_name = "shopapp/product-details.html"
    queryset = Product.objects.prefetch_related('images')
    context_object_name = "product"


class ProductsListView(ListView):
    template_name = 'shopapp/products-list.html'
    # model = Product
    queryset = Product.objects.filter(archived=False)
    context_object_name = "products"


class ProductCreateView(CreateView):
    # def test_func(self):
    #     # return self.request.user.groups.filter("secret-group").exists()
    #     # return self.request.user.is_superuser
    #     return self.request.user.has_perm("shopapp.add_product")

    # def form_valid(self, form):
    #     form.instance.created_by = self.request.user
    #     return super().form_valid(form)

    def form_valid(self, form):
        response = super().form_valid(form)
        for image in form.files.getlist("images"):
            ProductImage.objects.create(
                product=self.object,
                image=image,
            )
        return response

    model = Product
    # fields = "name", "price", "description", "discount", "preview"
    form_class = ProductForm
    success_url = reverse_lazy("shopapp:products_list")


class ProductUpdateView(UpdateView):
    model = Product
    # fields = "name", "price", "description", "discount", "preview"
    form_class = ProductForm
    template_name_suffix = "_update_form"

    def form_valid(self, form):
        response = super().form_valid(form)
        for image in form.files.getlist("images"):
            ProductImage.objects.create(
                product=self.object,
                image=image,
            )
        return response

    def get_success_url(self):
        return reverse(
            "shopapp:product_details",
            kwargs={"pk": self.object.pk},
        )


class ProductDeleteView(DeleteView):
    model = Product
    success_url = reverse_lazy("shopapp:products_list")

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.object.archived = True
        self.object.save()
        return HttpResponseRedirect(success_url)


class OrdersListView(LoginRequiredMixin, ListView):
    queryset = (
        Order.objects
        .select_related("user")
        .prefetch_related("products")
    )


class OrdersDetailView(PermissionRequiredMixin, DetailView):
    permission_required = "shopapp.view_order"
    queryset = (
        Order.objects
        .select_related("user")
        .prefetch_related("products")
    )


class OrderCreateView(CreateView):
    model = Order
    fields = "delivery_address", "promocode", "user", "products"
    # form_class = OrderForm
    success_url = reverse_lazy("shopapp:orders_list")


class OrderUpdateView(UpdateView):
    model = Order
    fields = "delivery_address", "promocode", "user", "products"
    template_name_suffix = "_update_form"

    def get_success_url(self):
        return reverse(
            "shopapp:order_details",
            kwargs={"pk": self.object.pk},
        )


class OrderDeleteView(DeleteView):
    model = Order
    success_url = reverse_lazy("shopapp:orders_list")


class ProductsDataExportView(View):
    def get(self, request: HttpRequest) -> JsonResponse:
        cache_key = "products_data_export"
        products_data = cache.get(cache_key)
        if products_data is None:
            products = Product.objects.order_by("pk").all()
            products_data = [
                {
                    "pk": product.pk,
                    "name": product.name,
                    "price": product.price,
                    "archived": product.archived
                }
                for product in products
            ]
            cache.set(cache_key, products_data, 300)
        return JsonResponse({"products": products_data})


class OrdersDataExportView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

    def get(self, request: HttpRequest) -> JsonResponse:
        orders = (
            Order.objects
            .select_related("user").
            prefetch_related("products")
            .all()
        )
        orders_data = [
            {
                "pk": order.pk,
                "delivery_address": order.delivery_address,
                "promocode": order.promocode,
                "products": [product.id for product in order.products.all()],
                "user": order.user.id
            }
            for order in orders
        ]
        return JsonResponse({"orders": orders_data})


class LatestProductsFeed(Feed):
    title = "Shop products (latest)"
    description = "Updates on changes and addition shop products"
    link = reverse_lazy("shopapp:products_list")

    def items(self):
        return (
            Product.objects.defer("preview", "images")
            .filter(archived=False)
            .order_by("-created_at")
            [:5]
        )

    def item_title(self, item: Product):
        return item.name

    def item_description(self, item: Product):
        return item.description[:50]

    # def item_link(self, item: Product):
    #     return reverse("shopapp:product_details", kwargs={"pk": item.pk})


class UserOrdersListView(LoginRequiredMixin, ListView):
    template_name = "shopapp/user_orders_list.html"
    context_object_name = "orders"

    def get_queryset(self):
        user_id = self.kwargs.get("user_id")
        self.user = get_object_or_404(User, pk=user_id)
        return Order.objects.filter(user=self.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["owner"] = self.user
        return context


class UserOrdersExportView(View):
    def get(self, request, user_id):
        cache_key = f"user_orders_{user_id}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return JsonResponse(cached_data, safe=False)

        user = get_object_or_404(User, pk=user_id)
        orders = Order.objects.filter(user=user).order_by("pk")
        serializer = OrderSerializer(orders, many=True)
        data = serializer.data
        cache.set(cache_key, data, 60 * 2)
        return JsonResponse(data, safe=False)
