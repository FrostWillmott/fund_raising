import json
import random
from pathlib import Path
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from users.models import User
from collects.models import Collect
from payments.models import Payment


class Command(BaseCommand):
    help = 'Генерирует тестовые данные или импортирует их из JSON-файла'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-file',
            type=str,
            help='Путь к JSON-файлу с тестовыми данными'
        )
        parser.add_argument(
            '--users-count',
            type=int,
            default=50,
            help='Количество случайных пользователей для генерации'
        )
        parser.add_argument(
            '--collects-count',
            type=int,
            default=20,
            help='Количество случайных сборов для генерации'
        )
        parser.add_argument(
            '--payments-per-collect',
            type=int,
            default=5,
            help='Среднее число платежей на сбор при генерации'
        )

    def handle(self, *args, **options):
        fake = Faker()
        data_file = options.get('data_file')
        users_map = {}
        collects_map = {}

        if data_file:
            path = Path(data_file)
            if not path.exists():
                self.stderr.write(self.style.ERROR(f'Файл не найден: {data_file}'))
                return
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Импорт пользователей
            for u in data.get('users', []):
                user = User.objects.create_user(
                    username=u['username'],
                    email=u.get('email', ''),
                    password=u.get('password', fake.password())
                )
                users_map[u['username']] = user

            # Импорт сборов
            for c in data.get('collects', []):
                author = users_map.get(c['author'])
                if not author:
                    self.stderr.write(self.style.WARNING(f"Автор не найден: {c['author']}"))
                    continue
                collect = Collect.objects.create(
                    author=author,
                    title=c.get('title', fake.sentence()),
                    reason=c.get('reason', ''),
                    description=c.get('description', ''),
                    target_amount=c.get('target_amount', 0),
                    cover_image=c.get('cover_image', None),
                    end_date=c.get('end_date', timezone.now())
                )
                collects_map[c.get('title')] = collect

            # Импорт платежей
            for p in data.get('payments', []):
                collect = collects_map.get(p['collect'])
                user = users_map.get(p['user'])
                if not collect or not user:
                    self.stderr.write(self.style.WARNING(
                        f"Пропущен платеж: collect={p.get('collect')} или user={p.get('user')} не найдены"
                    ))
                    continue
                Payment.objects.create(
                    collect=collect,
                    user=user,
                    amount=p.get('amount', 0),
                    created_at=p.get('created_at', timezone.now())
                )

            self.stdout.write(self.style.SUCCESS('Данные импортированы из JSON-файла'))
        else:
            # Генерация случайных данных
            self.stdout.write('Генерация случайных тестовых данных...')
            # Пользователи
            users = [
                User.objects.create_user(
                    username=fake.user_name(),
                    email=fake.email(),
                    password='test1234'
                ) for _ in range(options['users_count'])
            ]
            self.stdout.write(self.style.SUCCESS(f'Создано пользователей: {len(users)}'))

            # Сборы
            for _ in range(options['collects_count']):
                author = random.choice(users)
                collect = Collect.objects.create(
                    author=author,
                    title=fake.sentence(nb_words=4),
                    reason=random.choice(['день рождения', 'свадьба', 'благотворительность']),
                    description=fake.text(max_nb_chars=200),
                    target_amount=random.randint(1000, 100000),
                    cover_image=None,
                    end_date=timezone.now() + fake.time_delta(days=30)
                )
                collects_map[collect.id] = collect

                # Платежи для каждого сбора
                for __ in range(random.randint(1, options['payments_per_collect'])):
                    Payment.objects.create(
                        collect=collect,
                        user=random.choice(users),
                        amount=random.randint(10, 1000),
                        created_at=timezone.now() - fake.time_delta(days=random.randint(0, 30))
                    )
            self.stdout.write(self.style.SUCCESS(
                f'Создано сборов: {len(collects_map)}, с платежами.'
            ))

        self.stdout.write(self.style.SUCCESS('Команда generate_test_data завершена.'))
