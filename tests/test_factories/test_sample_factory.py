import pytest

from fairdm.core.models import Sample
from fairdm.factories import SampleFactory


@pytest.fixture
@pytest.mark.django_db
def sample():
    yield SampleFactory()


@pytest.mark.django_db
class TestSampleFactory:
    def test_factory_create(self, sample):
        assert isinstance(sample, Sample)
