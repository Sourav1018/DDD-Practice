import pytest
from concurrent.futures import ThreadPoolExecutor
from src.domain.services.transfer_service import TransferService
from src.application.dtos.transfer_dto import TransferMoneyCommand
from src.application.use_cases.transfer_use_case import TransferMoneyUseCase
from src.infrastructure.repositories.in_memory_idempotency_repository import InMemoryIdempotencyRepository
from src.infrastructure.repositories.in_memory_wallet_repository import InMemoryWalletRepository

@pytest.fixture
def setup_services():
    wallet_repo = InMemoryWalletRepository()
    idempotency_repo = InMemoryIdempotencyRepository()
    transfer_service = TransferService()
    return wallet_repo, idempotency_repo, transfer_service

def test_idempotency_disabled(setup_services):
    wallet_repo, idempotency_repo, transfer_service = setup_services
    
    # Seed wallets
    wallet_repo.seed("wallet-a", 100.0, "USD")
    wallet_repo.seed("wallet-b", 50.0, "USD")

    # Disable idempotency check
    use_case = TransferMoneyUseCase(
        wallet_repo, idempotency_repo, transfer_service, use_idempotency=False
    )

    command = TransferMoneyCommand(
        idempotency_key="dup-key-1",
        source_wallet_id="wallet-a",
        target_wallet_id="wallet-b",
        amount=30.0,
        currency="USD"
    )

    # First request
    res1 = use_case.execute(command)
    assert res1.success is True

    # Second identical request (retry simulation)
    res2 = use_case.execute(command)
    assert res2.success is True

    wallet_a = wallet_repo.find_by_id("wallet-a")
    wallet_b = wallet_repo.find_by_id("wallet-b")

    # Deducted twice ($100 - $30 - $30 = $40)
    assert wallet_a.balance.amount == 40.0
    assert wallet_b.balance.amount == 110.0


def test_idempotency_enabled(setup_services):
    wallet_repo, idempotency_repo, transfer_service = setup_services
    
    # Seed wallets
    wallet_repo.seed("wallet-a", 100.0, "USD")
    wallet_repo.seed("wallet-b", 50.0, "USD")

    # Enable idempotency check
    use_case = TransferMoneyUseCase(
        wallet_repo, idempotency_repo, transfer_service, use_idempotency=True
    )

    command = TransferMoneyCommand(
        idempotency_key="dup-key-2",
        source_wallet_id="wallet-a",
        target_wallet_id="wallet-b",
        amount=30.0,
        currency="USD"
    )

    # First request
    res1 = use_case.execute(command)
    assert res1.success is True
    first_tx_id = res1.transaction_id

    # Second request
    res2 = use_case.execute(command)
    assert res2.success is True
    assert res2.transaction_id == first_tx_id  # Returns cached response!

    wallet_a = wallet_repo.find_by_id("wallet-a")
    wallet_b = wallet_repo.find_by_id("wallet-b")

    # Only deducted once ($100 - $30 = $70)
    assert wallet_a.balance.amount == 70.0
    assert wallet_b.balance.amount == 80.0


def test_concurrency_disabled(setup_services):
    wallet_repo, idempotency_repo, transfer_service = setup_services
    
    # Seed wallets
    wallet_repo.seed("wallet-a", 100.0, "USD")
    wallet_repo.seed("wallet-b", 50.0, "USD")

    # Disable optimistic locking and inject 50ms delay
    wallet_repo.use_optimistic_locking = False
    wallet_repo.simulated_delay_seconds = 0.05

    use_case = TransferMoneyUseCase(
        wallet_repo, idempotency_repo, transfer_service, use_idempotency=False
    )

    command1 = TransferMoneyCommand(
        idempotency_key="key-c1",
        source_wallet_id="wallet-a",
        target_wallet_id="wallet-b",
        amount=80.0,
        currency="USD"
    )

    command2 = TransferMoneyCommand(
        idempotency_key="key-c2",
        source_wallet_id="wallet-a",
        target_wallet_id="wallet-b",
        amount=80.0,
        currency="USD"
    )

    # Execute concurrent transfers
    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(use_case.execute, command1)
        future2 = executor.submit(use_case.execute, command2)
        res1 = future1.result()
        res2 = future2.result()

    # Without optimistic locking, both requests report success!
    assert res1.success is True
    assert res2.success is True

    wallet_a = wallet_repo.find_by_id("wallet-a")
    wallet_b = wallet_repo.find_by_id("wallet-b")

    # Lost-update anomaly: both read $100 and write back $20. One transaction's updates are overwritten.
    assert wallet_a.balance.amount == 20.0
    assert wallet_b.balance.amount == 130.0


def test_concurrency_enabled(setup_services):
    wallet_repo, idempotency_repo, transfer_service = setup_services
    
    # Seed wallets
    wallet_repo.seed("wallet-a", 100.0, "USD")
    wallet_repo.seed("wallet-b", 50.0, "USD")

    # Enable optimistic locking and inject 50ms delay
    wallet_repo.use_optimistic_locking = True
    wallet_repo.simulated_delay_seconds = 0.05

    use_case = TransferMoneyUseCase(
        wallet_repo, idempotency_repo, transfer_service, use_idempotency=False
    )

    command1 = TransferMoneyCommand(
        idempotency_key="key-c3",
        source_wallet_id="wallet-a",
        target_wallet_id="wallet-b",
        amount=80.0,
        currency="USD"
    )

    command2 = TransferMoneyCommand(
        idempotency_key="key-c4",
        source_wallet_id="wallet-a",
        target_wallet_id="wallet-b",
        amount=80.0,
        currency="USD"
    )

    # Execute concurrent transfers
    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(use_case.execute, command1)
        future2 = executor.submit(use_case.execute, command2)
        res1 = future1.result()
        res2 = future2.result()

    # One succeeds, one fails
    results = [res1, res2]
    successes = [r for r in results if r.success]
    failures = [r for r in results if not r.success]

    assert len(successes) == 1
    assert len(failures) == 1
    assert "Optimistic locking conflict" in failures[0].error

    wallet_a = wallet_repo.find_by_id("wallet-a")
    wallet_b = wallet_repo.find_by_id("wallet-b")

    # Wallet is safely protected at $20 and target at $130, preventing balance mismatch
    assert wallet_a.balance.amount == 20.0
    assert wallet_b.balance.amount == 130.0
