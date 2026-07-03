from decimal import Decimal

import pytest
from django.db.models.deletion import ProtectedError
from rest_framework import exceptions

from payments.models import Payment
from payments.services import create_payment


@pytest.mark.django_db
class TestCreatePaymentService:
    def test_creates_completed_payment_and_increments_counter(
        self, user, collect_factory
    ):
        collect = collect_factory(collected_amount=Decimal("0.00"))

        payment = create_payment(
            payer=user,
            collect=collect,
            amount=Decimal("150.00"),
            transaction_id="svc_tx_1",
        )

        collect.refresh_from_db()
        assert payment.status == Payment.Status.COMPLETED
        assert collect.collected_amount == Decimal("150.00")

    def test_duplicate_transaction_id_raises_validation_error(
        self, user, collect_factory
    ):
        collect = collect_factory(collected_amount=Decimal("0.00"))
        create_payment(
            payer=user,
            collect=collect,
            amount=Decimal("10.00"),
            transaction_id="svc_tx_dup",
        )

        with pytest.raises(exceptions.ValidationError):
            create_payment(
                payer=user,
                collect=collect,
                amount=Decimal("20.00"),
                transaction_id="svc_tx_dup",
            )

        # The failed attempt must not leak into the counter.
        collect.refresh_from_db()
        assert collect.collected_amount == Decimal("10.00")

    def test_direct_orm_create_does_not_touch_counter(
        self, user, collect_factory
    ):
        """New contract: only the service maintains collected_amount."""
        collect = collect_factory(collected_amount=Decimal("0.00"))

        Payment.objects.create(
            collect=collect,
            payer=user,
            amount=Decimal("99.00"),
            transaction_id="orm_tx_pending",
            status=Payment.Status.PENDING,
        )

        collect.refresh_from_db()
        assert collect.collected_amount == Decimal("0.00")

    def test_collect_with_payments_is_protected_from_orm_delete(
        self, collect_factory, payment_factory
    ):
        collect = collect_factory()
        payment_factory(collect=collect)

        with pytest.raises(ProtectedError):
            collect.delete()
