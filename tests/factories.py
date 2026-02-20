import factory
from django.contrib.auth import get_user_model
from collects.models import Collect
from payments.models import Payment
from django.utils import timezone
from decimal import Decimal

User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker("user_name")
    email = factory.Faker("email")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")

class CollectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Collect

    title = factory.Faker("sentence", nb_words=3)
    occasion = Collect.Occasion.BIRTHDAY
    description = factory.Faker("paragraph")
    goal_amount = Decimal("1000.00")
    created_by = factory.SubFactory(UserFactory)

class PaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Payment

    collect = factory.SubFactory(CollectFactory)
    payer = factory.SubFactory(UserFactory)
    amount = Decimal("100.00")
    transaction_id = factory.Sequence(lambda n: f"trans_{n}")
    status = Payment.Status.PENDING
