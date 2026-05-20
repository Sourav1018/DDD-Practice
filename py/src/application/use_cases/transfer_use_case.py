from src.domain.repositories.wallet_repository import WalletRepository
from src.domain.services.transfer_service import TransferService
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.money import Money
from src.application.dtos.transfer_dto import TransferMoneyCommand, TransferMoneyResponse
from src.application.repositories.idempotency_repository import IdempotencyRepository

class TransferMoneyUseCase:
    def __init__(
        self,
        wallet_repository: WalletRepository,
        idempotency_repository: IdempotencyRepository,
        transfer_service: TransferService,
        use_idempotency: bool = True
    ):
        self.wallet_repository = wallet_repository
        self.idempotency_repository = idempotency_repository
        self.transfer_service = transfer_service
        self.use_idempotency = use_idempotency

    def execute(self, command: TransferMoneyCommand) -> TransferMoneyResponse:
        # 1. Check idempotency if enabled
        if self.use_idempotency and command.idempotency_key:
            cached_response = self.idempotency_repository.find(command.idempotency_key)
            if cached_response:
                return cached_response

        try:
            # 2. Parse and validate inputs
            currency = Currency(command.currency)
            amount = Money(command.amount, currency)

            # 3. Load aggregates
            source_wallet = self.wallet_repository.find_by_id(command.source_wallet_id)
            if not source_wallet:
                raise ValueError(f"Source wallet not found: {command.source_wallet_id}")

            target_wallet = self.wallet_repository.find_by_id(command.target_wallet_id)
            if not target_wallet:
                raise ValueError(f"Target wallet not found: {command.target_wallet_id}")

            # 4. Delegate to Domain Service
            transaction = self.transfer_service.transfer(source_wallet, target_wallet, amount)

            # 5. Persist aggregates
            self.wallet_repository.save(source_wallet)
            self.wallet_repository.save(target_wallet)

            response = TransferMoneyResponse(
                success=True,
                transaction_id=transaction.id,
                balance_after_transfer=source_wallet.balance.amount
            )

            # 6. Cache response if idempotency enabled
            if self.use_idempotency and command.idempotency_key:
                self.idempotency_repository.save(command.idempotency_key, response)

            return response

        except Exception as e:
            return TransferMoneyResponse(
                success=False,
                error=str(e)
            )
