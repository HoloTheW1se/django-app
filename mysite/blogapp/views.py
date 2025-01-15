from django.shortcuts import render
from django.contrib.syndication.views import Feed
from django.views.generic import ListView, DetailView
from django.urls import reverse, reverse_lazy

from .models import Article


class ArticlesListView(ListView):
    queryset = (
        Article.objects.defer("content", "author__bio")
        .filter(pub_date__isnull=False)
        .order_by("-pub_date")
        .select_related("author", "category")
        .prefetch_related("tags")
    )


class ArticleDetailView(DetailView):
    model = Article


class LatestArticlesFeed(Feed):
    title = "Blog articles (latest)"
    description = "Updates on changes and addition blog articles"
    link = reverse_lazy("blogapp:articles")

    def items(self):
        return (
            Article.objects.defer("content", "author__bio")
            .filter(pub_date__isnull=False)
            .order_by("-pub_date")
            .select_related("author", "category")
            .prefetch_related("tags")[:5]
        )

    def item_title(self, item: Article):
        return item.title

    def item_description(self, item: Article):
        return item.content[:200]

    # def item_link(self, item: Article):
    #     return reverse("blogapp:article", kwargs={"pk": item.pk})
