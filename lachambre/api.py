from tastypie_nonrel.resources import MongoResource
from tastypie.constants import ALL
from models import Deputy, Document, Commission, WrittenQuestion
#from json import loads, dumps

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

    def dehydrate_deputies(self, bundle):
        #return map(lambda x: "/api/v1/deputy/" + x, bundle.data["deputies"])
        #print loads(bundle.data["deputies"])
        return bundle.data["deputies"]

class WrittenQuestionResource(MongoResource):
    class Meta:
        queryset = WrittenQuestion.objects.all()
        filtering = {
            "lachambre_id": ALL,
        }
