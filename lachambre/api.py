from tastypie_nonrel.resources import MongoResource
from tastypie.constants import ALL
from tastypie import fields
from models import Deputy, Document, Commission, WrittenQuestion, CommissionMembership, AnnualReport

class AnnualReportRessource(MongoResource):
    class Meta:
        queryset = AnnualReport.objects.all()
        resource_name = 'annual-report'

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

class CommissionMembershipRessource(MongoResource):
    deputy = fields.ForeignKey(DeputyResource, 'deputy')
    commission = fields.ForeignKey(CommissionResource, 'commission')
    class Meta:
        queryset = CommissionMembership.objects.all()

class WrittenQuestionResource(MongoResource):
    class Meta:
        queryset = WrittenQuestion.objects.all()
        filtering = {
            "lachambre_id": ALL,
        }
