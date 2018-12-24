from rest_framework import status
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from authors.apps.articles.models import Article
from authors.apps.articles.serializers import GetArticlesSerializer
from authors.apps.bookmark.models import Bookmark
from authors.apps.bookmark.renderers import BookmarksJSONRenderer
from authors.apps.bookmark.serializers import BookmarkSerializer


class BookmarkArticleCreateDestroyAPIView(CreateAPIView, DestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BookmarkSerializer
    renderer_classes = (BookmarksJSONRenderer,)

    class Meta:
        model = Bookmark
        fields = ('user', 'article',)

    def post(self, request, *args, **kwargs):
        article_slug = kwargs.get('slug', None)
        user = request.user.id
        data = {'user': user, 'slug': article_slug}

        serializer = self.serializer_class(data=data)
        serializer.is_valid()
        serializer.save()

        # TODO Return the article with the bookmarked field as `true`
        return Response('Bookmark successful', status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        article_slug = kwargs.get('slug', None)

        self.perform_destroy(Bookmark.objects.filter(slug=article_slug))

        return Response('Unbookmark successful', status.HTTP_204_NO_CONTENT)


class BookmarkListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = GetArticlesSerializer
    renderer_classes = (BookmarksJSONRenderer,)

    def get_queryset(self):
        slugs = Bookmark.objects.filter(user_id=self.request.user.id).values_list('slug', flat=True)
        articles = Article.objects.filter(slug__in=slugs)
        return articles
