# dev_tools/management/commands/generate_test_data.py

import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import models
from django.utils import timezone
from faker import Faker

from collects.models import Collect
from payments.models import Payment

User = get_user_model()
fake = Faker(['ru_RU', 'en_US'])  # Use both Russian and English locales


class Command(BaseCommand):
    help = "Generate test data for the application"

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=10, help="Number of users to create")
        parser.add_argument("--collects", type=int, default=20, help="Number of collects to create")
        parser.add_argument("--payments", type=int, default=100, help="Number of payments to create")

    def handle(self, *args, **options):
        num_users = options["users"]
        num_collects = options["collects"]
        num_payments = options["payments"]

        # Step 1: Create users in bulk
        self.stdout.write(f"Creating {num_users} users...")
        existing_users = list(User.objects.all())
        num_existing = len(existing_users)

        # Only create new users if needed
        if num_existing < num_users:
            users_to_create = []
            for i in range(num_existing + 1, num_users + 1):
                profile = fake.profile()
                username = profile['username']

                # Make sure username is unique
                while User.objects.filter(username=username).exists() or any(u.username == username for u in users_to_create):
                    profile = fake.profile()
                    username = profile['username']

                users_to_create.append(User(
                    username=username,
                    email=profile['mail'],
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    is_active=True
                ))

            # Set password after bulk creation since it can't be hashed in bulk
            created_users = User.objects.bulk_create(users_to_create, batch_size=500)
            for user in created_users:
                user.set_password("testpassword")
                user.save()

            all_users = existing_users + created_users
        else:
            all_users = existing_users[:num_users]

        # Step 2: Create collects in bulk
        self.stdout.write(f"Creating {num_collects} collects...")
        existing_collects = list(Collect.objects.all())
        num_existing = len(existing_collects)

        occasions = list(Collect.Occasion.values)

        # Generate collect titles and descriptions that make sense for each occasion
        occasion_templates = {
            'birthday': {
                'titles': [
                    "День рождения {name}",
                    "{age}-летие {name}",
                    "Подарок на ДР {name}",
                    "Собираем на подарок {name}"
                ],
                'descriptions': [
                    "Собираем на подарок {name} в честь {age}-летия! Поможем сделать день рождения незабываемым!",
                    "{name} исполняется {age} лет, давайте вместе сделаем подарок",
                    "День рождения {name} уже скоро! Соберем на незабываемый подарок"
                ]
            },
            'wedding': {
                'titles': [
                    "Свадьба {name1} и {name2}",
                    "На свадебное путешествие {name1} и {name2}",
                    "Подарок молодоженам {name1} и {name2}"
                ],
                'descriptions': [
                    "Дорогие друзья! {date} состоится свадьба {name1} и {name2}. Вместо цветов и подарков молодожены будут рады вашему вкладу в их совместную жизнь!",
                    "Помогите {name1} и {name2} начать семейную жизнь с незабываемого свадебного путешествия!",
                    "{name1} и {name2} соединяют свои судьбы {date}. Мы собираем на подарок, который поможет им в их новой жизни."
                ]
            },
            'new_year': {
                'titles': [
                    "Новогодний корпоратив {company}",
                    "Новогодние подарки детям",
                    "Корпоративный Новый Год {year}"
                ],
                'descriptions': [
                    "Собираем на корпоративный новогодний праздник компании {company}. Сделаем этот Новый Год незабываемым!",
                    "Давайте вместе порадуем детей новогодними подарками! Каждый ребенок должен получить праздник.",
                    "Новый {year} год уже скоро! Соберем деньги на отличный корпоратив для всей команды {company}."
                ]
            },
            'other': {
                'titles': [
                    "{activity} для команды {team}",
                    "Подарок коллеге {name}",
                    "Благотворительный сбор: {cause}",
                    "Сбор на {item} для {purpose}"
                ],
                'descriptions': [
                    "Мы собираем средства на {activity} для нашей команды {team}. Это отличная возможность для укрепления командного духа!",
                    "Наш коллега {name} {reason}. Давайте вместе поможем и поддержим!",
                    "Благотворительный сбор в поддержку {cause}. Ваша помощь очень важна!",
                    "Собираем на {item}, который будет использован для {purpose}. Любая помощь ценна!"
                ]
            }
        }

        if num_existing < num_collects:
            collects_to_create = []
            for i in range(num_existing + 1, num_collects + 1):
                # Randomly select parameters
                user = random.choice(all_users)
                occasion = random.choice(occasions)
                goal_amount = Decimal(str(random.randint(1000, 100000))) if random.random() > 0.2 else None
                start_date = timezone.now() - timedelta(days=random.randint(1, 180))
                end_date = start_date + timedelta(days=random.randint(10, 90)) if random.random() > 0.3 else None

                # Generate title and description based on occasion
                templates = occasion_templates.get(occasion, occasion_templates['other'])

                # Prepare template variables
                template_vars = {
                    'name': fake.first_name(),
                    'name1': fake.first_name(),
                    'name2': fake.first_name(),
                    'age': random.randint(1, 90),
                    'company': fake.company(),
                    'team': fake.bs().title(),
                    'year': timezone.now().year + 1,
                    'activity': random.choice(['Тимбилдинг', 'Поход', 'Квест', 'Экскурсия', 'Мастер-класс']),
                    'reason': random.choice(['уходит на пенсию', 'переезжает в другой город', 'стал родителем', 'защитил диссертацию']),
                    'cause': random.choice(['детского дома', 'приюта для животных', 'больницы', 'школы']),
                    'item': random.choice(['оборудование', 'мебель', 'компьютер', 'инструменты', 'книги']),
                    'purpose': random.choice(['обучения', 'лечения', 'развития', 'исследований']),
                    'date': fake.date_this_year(before_today=False, after_today=True).strftime('%d.%m.%Y')
                }

                title_template = random.choice(templates['titles'])
                description_template = random.choice(templates['descriptions'])

                title = title_template.format(**template_vars)
                description = description_template.format(**template_vars)

                collects_to_create.append(Collect(
                    title=title,
                    occasion=occasion,
                    description=description,
                    goal_amount=goal_amount,
                    collected_amount=Decimal('0.00'),
                    start_date=start_date,
                    end_date=end_date,
                    created_by=user,
                    is_active=True
                ))

            created_collects = Collect.objects.bulk_create(collects_to_create, batch_size=500)
            all_collects = existing_collects + created_collects
        else:
            all_collects = existing_collects[:num_collects]

        # Step 3: Create payments in bulk
        self.stdout.write(f"Creating {num_payments} payments...")
        payment_statuses = list(Payment.Status.values)

        # Generate all payments at once in chunks to prevent memory issues
        payments_created = 0
        batch_size = 1000  # Process 1000 payments at a time

        while payments_created < num_payments:
            batch_amount = min(batch_size, num_payments - payments_created)
            payments_to_create = []

            for _ in range(batch_amount):
                collect = random.choice(all_collects)
                user = random.choice(all_users)
                status = random.choice(payment_statuses)
                # More realistic amounts - most people donate smaller amounts
                amount_distribution = [
                    (Decimal('10.00'), Decimal('100.00'), 0.5),    # 50% chance: small donation (10-100)
                    (Decimal('100.00'), Decimal('500.00'), 0.3),   # 30% chance: medium donation (100-500)
                    (Decimal('500.00'), Decimal('2000.00'), 0.15), # 15% chance: large donation (500-2000)
                    (Decimal('2000.00'), Decimal('10000.00'), 0.05) # 5% chance: very large donation (2000-10000)
                ]

                # Choose a range based on distribution
                rand = random.random()
                cumulative = 0
                min_amount, max_amount = Decimal('10.00'), Decimal('100.00')  # default

                for min_val, max_val, probability in amount_distribution:
                    cumulative += probability
                    if rand <= cumulative:
                        min_amount, max_amount = min_val, max_val
                        break

                # Generate a random amount within the selected range
                amount_int_part = random.randint(int(min_amount), int(max_amount))
                amount_decimal_part = Decimal(str(random.randint(0, 99) / 100))
                amount = Decimal(amount_int_part) + amount_decimal_part

                # More realistic transaction IDs
                processors = ['stripe', 'paypal', 'yoomoney', 'tinkoff', 'sber']
                processor = random.choice(processors)
                transaction_id = f"{processor}_{fake.uuid4()}"

                # Random date, but respect the collect's start date
                max_days_ago = min(90, (timezone.now() - collect.start_date).days)
                if max_days_ago > 0:
                    days_ago = random.randint(0, max_days_ago)
                else:
                    days_ago = 0

                payment_date = timezone.now() - timedelta(
                    days=days_ago,
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )

                # More realistic metadata
                metadata = {
                    "test_data": True,
                    "payment_processor": processor,
                    "ip_address": fake.ipv4(),
                    "user_agent": fake.user_agent(),
                    "currency": "RUB"
                }

                # Add some randomness to metadata
                if random.random() > 0.7:
                    metadata["comment"] = fake.text(max_nb_chars=100)
                if random.random() > 0.9:
                    metadata["is_anonymous"] = True

                payments_to_create.append(Payment(
                    collect=collect,
                    payer=user,
                    amount=amount,
                    transaction_id=transaction_id,
                    status=status,
                    payment_date=payment_date,
                    metadata=metadata
                ))

            # Bulk create this batch of payments
            Payment.objects.bulk_create(payments_to_create, batch_size=500)

            # Update collected amounts for completed payments
            if Payment.Status.COMPLETED in payment_statuses:
                completed_payments = [p for p in payments_to_create if p.status == Payment.Status.COMPLETED]

                # Group by collect to update collected amounts
                collect_amounts = {}
                for payment in completed_payments:
                    collect_id = payment.collect_id
                    if collect_id in collect_amounts:
                        collect_amounts[collect_id] += payment.amount
                    else:
                        collect_amounts[collect_id] = payment.amount

                # Update each collect with the total amount from this batch
                for collect_id, amount in collect_amounts.items():
                    Collect.objects.filter(id=collect_id).update(
                        collected_amount=models.F('collected_amount') + amount
                    )

            payments_created += batch_amount
            self.stdout.write(f"  Created {payments_created} of {num_payments} payments...")

        self.stdout.write(self.style.SUCCESS(
            f"Successfully created {num_users} users, {num_collects} collects, and {num_payments} payments!"
        ))
