from tastypie_nonrel.resources import MongoResource
from tastypie.constants import ALL
from models import Deputy, Document, Commission, WrittenQuestion

class DeputyResource(MongoResource):
    class Meta:
        queryset = Deputy.objects.all()
        filtering = {
            "lachambre_id": ALL,
        }

class DocumentResource(MongoResource):
    class Meta:
        queryset = Document.objects.all()
        filtering = {
            "lachambre_id": ALL,
        }

class CommissionResource(MongoResource):
    class Meta:
        queryset = Commission.objects.all()
        filtering = {
            "lachambre_id": ALL,
        }

class WrittenQuestionResource(MongoResource):
    class Meta:
        queryset = WrittenQuestion.objects.all()
        filtering = {
            "lachambre_id": ALL,
        }
