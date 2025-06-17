from rest_framework import generics, viewsets
from polls.models import Question
from polls.api.serializers import QuestionSerializer


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

