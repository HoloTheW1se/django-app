from typing import Sequence

from django.core.management import BaseCommand
from django.db import transaction
from blogapp.models import Author, Category, Tag, Article


class Command(BaseCommand):
    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Create article with other info")

        tag_names = [
            "Classic",
            "Fantasy",
            "Roman",
        ]
        for tag_name in tag_names:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            self.stdout.write(f"Created tag: {tag.name}")

        author, author_created = Author.objects.get_or_create(
            name="Pushkin",
            bio="Great author"
        )
        category, category_created = Category.objects.get_or_create(
            name="Nashi izdaniya"
        )

        article, created = Article.objects.get_or_create(
            title="Ruslan i lydmila",
            content="Kniga pro lubov",
            author=author,
            category=category
        )

        tags: Sequence[Tag] = Tag.objects.all()
        for tag in tags:
            article.tags.add(tag)

        article.save()
        self.stdout.write(f"Done")
