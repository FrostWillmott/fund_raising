import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from collects.models import Collect
from payments.models import Payment

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate mock data for testing'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=50)
        parser.add_argument('--collects', type=int, default=100)
        parser.add_argument('--payments', type=int, default=5000)

    def handle(self, *args, **options):
        # Create users
        self.stdout.write('Creating users...')
        users = []
        for i in range(options['users']):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='password'
            )
            users.append(user)

        self.stdout.write('Creating collects...')
        collects = []
        occasions = list(Collect.Occasion.values)

        for i in range(options['collects']):
            author = random.choice(users)
            goal = None if random.random() > 0.7 else Decimal(random.randint(1000, 100000))

            collect = Collect.objects.create(
                title=f'Collect {i}',
                occasion=random.choice(occasions),
                description=f'Description for collect {i}',
                goal_amount=goal,
                created_by=author,
                end_date=timezone.now() + timezone.timedelta(days=random.randint(10, 100))
            )
            collects.append(collect)

        # Create payments
        self.stdout.write('Creating payments...')
        for i in range(options['payments']):
            payer = random.choice(users)
            collect = random.choice(collects)
            amount = Decimal(random.randint(100, 5000))

            payment = Payment.objects.create(
                collect=collect,
                payer=payer,
                amount=amount,
                transaction_id=f'tx-{i}',
                status=Payment.Status.COMPLETED
            )

        self.stdout.write(self.style.SUCCESS(f'Successfully created {options["users"]} users, {options["collects"]} collects, and {options["payments"]} payments'))
