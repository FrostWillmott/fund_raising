# dev_tools/management/commands/generate_test_data.py

import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import models
from django.utils import timezone
from faker import Faker

from collects.models import Collect
from payments.models import Payment

User = get_user_model()
fake = Faker(["ru_RU", "en_US"])


class Command(BaseCommand):
    help = "Generate test data for the application"

    def add_arguments(self, parser):
        parser.add_argument(
            "--users", type=int, default=10, help="Number of users to create"
        )
        parser.add_argument(
            "--collects",
            type=int,
            default=20,
            help="Number of collects to create",
        )
        parser.add_argument(
            "--payments",
            type=int,
            default=100,
            help="Number of payments to create",
        )

    def handle(self, *args, **options):
        num_users = options["users"]
        num_collects = options["collects"]
        num_payments = options["payments"]

        self.stdout.write(f"Creating {num_users} users...")
        existing_users = list(User.objects.all())
        num_existing_users = len(existing_users)

        if num_existing_users < num_users:
            hashed_password = make_password("testpassword")
            users_to_create = []
            for _ in range(num_existing_users + 1, num_users + 1):
                profile = fake.profile()
                username = profile["username"]

                while User.objects.filter(username=username).exists() or any(
                    u.username == username for u in users_to_create
                ):
                    profile = fake.profile()
                    username = profile["username"]

                users_to_create.append(
                    User(
                        username=username,
                        email=profile["mail"],
                        first_name=fake.first_name(),
                        last_name=fake.last_name(),
                        password=hashed_password,
                        is_active=True,
                    )
                )

            created_users = User.objects.bulk_create(
                users_to_create, batch_size=500
            )

            all_users = existing_users + created_users
        else:
            all_users = existing_users[:num_users]

        self.stdout.write(f"Creating {num_collects} collects...")
        existing_collects = list(Collect.objects.all())
        num_existing_collects = len(existing_collects)

        occasions = list(Collect.Occasion.values)

        occasion_templates = {
            "birthday": {
                "titles": [
                    "Birthday fundraise for {name}",
                    "{name}'s {age}th birthday",
                    "Birthday gift for {name}",
                    "Collecting for {name}'s gift",
                ],
                "descriptions": [
                    "We are collecting for {name}'s {age}th birthday gift! Let's make their birthday unforgettable!",
                    "{name} is turning {age} — let's chip in for a gift together.",
                    "{name}'s birthday is coming up! Let's collect for an unforgettable gift.",
                ],
            },
            "wedding": {
                "titles": [
                    "Wedding of {name1} and {name2}",
                    "Honeymoon trip for {name1} and {name2}",
                    "Wedding gift for {name1} and {name2}",
                ],
                "descriptions": [
                    "Dear friends! {name1} and {name2} are getting married on {date}. Instead of flowers or gifts, the couple would love your contribution to their new life together!",
                    "Help {name1} and {name2} start their married life with an unforgettable honeymoon!",
                    "{name1} and {name2} are tying the knot on {date}. We're collecting for a gift that will help them in their new life together.",
                ],
            },
            "new_year": {
                "titles": [
                    "New Year corporate party at {company}",
                    "New Year gifts for children",
                    "Corporate New Year {year}",
                ],
                "descriptions": [
                    "Collecting for the corporate New Year party at {company}. Let's make this New Year unforgettable!",
                    "Let's bring joy to children with New Year gifts! Every child deserves a celebration.",
                    "New Year {year} is right around the corner! Let's raise funds for a great corporate party for the {company} team.",
                ],
            },
            "other": {
                "titles": [
                    "{activity} for team {team}",
                    "Gift for colleague {name}",
                    "Charity fundraise: {cause}",
                    "Raising funds for {item} for {purpose}",
                ],
                "descriptions": [
                    "We are raising funds for {activity} for our team {team}. A great opportunity to strengthen team spirit!",
                    "Our colleague {name} {reason}. Let's come together to help and show our support!",
                    "Charity fundraise in support of {cause}. Your help matters greatly!",
                    "Collecting for {item} that will be used for {purpose}. Every contribution counts!",
                ],
            },
        }

        if num_existing_collects < num_collects:
            collects_to_create = []
            for _ in range(num_existing_collects + 1, num_collects + 1):
                user = random.choice(all_users)
                occasion = random.choice(occasions)
                goal_amount = (
                    Decimal(str(random.randint(1000, 100000)))
                    if random.random() > 0.2
                    else None
                )
                start_date = timezone.now() - timedelta(
                    days=random.randint(1, 180)
                )
                end_date = (
                    start_date + timedelta(days=random.randint(10, 90))
                    if random.random() > 0.3
                    else None
                )

                templates = occasion_templates.get(
                    occasion, occasion_templates["other"]
                )

                template_vars = {
                    "name": fake.first_name(),
                    "name1": fake.first_name(),
                    "name2": fake.first_name(),
                    "age": random.randint(1, 90),
                    "company": fake.company(),
                    "team": fake.bs().title(),
                    "year": timezone.now().year + 1,
                    "activity": random.choice(
                        [
                            "Team building",
                            "Hiking trip",
                            "Quest",
                            "Excursion",
                            "Masterclass",
                        ]
                    ),
                    "reason": random.choice(
                        [
                            "is retiring",
                            "is moving to another city",
                            "became a parent",
                            "defended their dissertation",
                        ]
                    ),
                    "cause": random.choice(
                        [
                            "an orphanage",
                            "an animal shelter",
                            "a hospital",
                            "a school",
                        ]
                    ),
                    "item": random.choice(
                        [
                            "equipment",
                            "furniture",
                            "a computer",
                            "tools",
                            "books",
                        ]
                    ),
                    "purpose": random.choice(
                        ["education", "treatment", "development", "research"]
                    ),
                    "date": fake.date_this_year(
                        before_today=False, after_today=True
                    ).strftime("%d.%m.%Y"),
                }

                title_template = random.choice(templates["titles"])
                description_template = random.choice(templates["descriptions"])

                title = title_template.format(**template_vars)
                description = description_template.format(**template_vars)

                collects_to_create.append(
                    Collect(
                        title=title,
                        occasion=occasion,
                        description=description,
                        goal_amount=goal_amount,
                        collected_amount=Decimal("0.00"),
                        start_date=start_date,
                        end_date=end_date,
                        created_by=user,
                        is_active=True,
                    )
                )

            created_collects = Collect.objects.bulk_create(
                collects_to_create, batch_size=500
            )
            all_collects = existing_collects + created_collects
        else:
            all_collects = existing_collects[:num_collects]

        self.stdout.write(f"Creating {num_payments} payments...")
        payment_statuses = list(Payment.Status.values)

        payments_created = 0
        batch_size = 1000

        while payments_created < num_payments:
            batch_amount = min(batch_size, num_payments - payments_created)
            payments_to_create = []

            for _ in range(batch_amount):
                collect = random.choice(all_collects)
                user = random.choice(all_users)
                if (
                    collect is None
                    or not collect.id
                    or user is None
                    or not user.id
                ):
                    continue

                status = random.choice(payment_statuses)
                amount_distribution = [
                    (Decimal("10.00"), Decimal("100.00"), 0.5),
                    (Decimal("100.00"), Decimal("500.00"), 0.3),
                    (Decimal("500.00"), Decimal("2000.00"), 0.15),
                    (Decimal("2000.00"), Decimal("10000.00"), 0.05),
                ]

                rand = random.random()
                cumulative = 0
                min_amount, max_amount = Decimal("10.00"), Decimal("100.00")

                for min_val, max_val, probability in amount_distribution:
                    cumulative += probability
                    if rand <= cumulative:
                        min_amount, max_amount = min_val, max_val
                        break

                amount_int_part = random.randint(
                    int(min_amount), int(max_amount)
                )
                amount_decimal_part = Decimal(str(random.randint(0, 99) / 100))
                amount = Decimal(amount_int_part) + amount_decimal_part

                processors = [
                    "stripe",
                    "paypal",
                    "yoomoney",
                    "tinkoff",
                    "sber",
                ]
                processor = random.choice(processors)
                transaction_id = f"{processor}_{fake.uuid4()}"

                max_days_ago = min(
                    90, (timezone.now() - collect.start_date).days
                )
                if max_days_ago > 0:
                    days_ago = random.randint(0, max_days_ago)
                else:
                    days_ago = 0

                payment_date = timezone.now() - timedelta(
                    days=days_ago,
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59),
                )

                metadata = {
                    "test_data": True,
                    "payment_processor": processor,
                    "ip_address": fake.ipv4(),
                    "user_agent": fake.user_agent(),
                    "currency": "RUB",
                }

                if random.random() > 0.7:
                    metadata["comment"] = fake.text(max_nb_chars=100)
                if random.random() > 0.9:
                    metadata["is_anonymous"] = True

                payment = Payment(
                    collect_id=collect.id,
                    payer_id=user.id,
                    amount=amount,
                    transaction_id=transaction_id,
                    status=status,
                    payment_date=payment_date,
                    metadata=metadata,
                )
                payments_to_create.append(payment)

            # Temporarily disable auto_now_add so the carefully
            # generated historical payment_date values survive bulk_create.
            payment_date_field = Payment._meta.get_field("payment_date")
            original_auto_now_add = payment_date_field.auto_now_add
            payment_date_field.auto_now_add = False
            try:
                Payment.objects.bulk_create(payments_to_create, batch_size=500)
            finally:
                payment_date_field.auto_now_add = original_auto_now_add

            if Payment.Status.COMPLETED in payment_statuses:
                completed_payments = [
                    p
                    for p in payments_to_create
                    if p.status == Payment.Status.COMPLETED
                ]

                collect_amounts = {}
                for payment in completed_payments:
                    collect_id = payment.collect_id
                    if collect_id in collect_amounts:
                        collect_amounts[collect_id] += payment.amount
                    else:
                        collect_amounts[collect_id] = payment.amount

                for collect_id, amount in collect_amounts.items():
                    Collect.objects.filter(id=collect_id).update(
                        collected_amount=models.F("collected_amount") + amount
                    )

            payments_created += len(payments_to_create)
            self.stdout.write(
                f"  Created {payments_created} of {num_payments} payments..."
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {num_users} users, {num_collects} collects, and {num_payments} payments!"
            )
        )
