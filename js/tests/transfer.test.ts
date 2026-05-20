import { TransferMoneyUseCase } from "../src/application/use-cases/TransferMoneyUseCase";
import { TransferService } from "../src/domain/services/TransferService";
import { InMemoryIdempotencyRepository } from "../src/infrastructure/repositories/InMemoryIdempotencyRepository";
import { InMemoryWalletRepository, ConcurrencyException } from "../src/infrastructure/repositories/InMemoryWalletRepository";

describe("DDD Wallet & Transfer System Tests", () => {
  let walletRepo: InMemoryWalletRepository;
  let idempotencyRepo: InMemoryIdempotencyRepository;
  let transferService: TransferService;

  beforeEach(() => {
    walletRepo = new InMemoryWalletRepository();
    idempotencyRepo = new InMemoryIdempotencyRepository();
    transferService = new TransferService();
  });

  describe("Idempotency Protection Tests", () => {
    it("should allow duplicate transfers (double spending) when idempotency protection is DISABLED", async () => {
      // Seed wallets
      walletRepo.seed("wallet-a", 100, "USD");
      walletRepo.seed("wallet-b", 50, "USD");

      // Set up UseCase with idempotency DISABLED
      const useCase = new TransferMoneyUseCase(
        walletRepo,
        idempotencyRepo,
        transferService,
        false // useIdempotency = false
      );

      const command = {
        idempotencyKey: "dup-key-123",
        sourceWalletId: "wallet-a",
        targetWalletId: "wallet-b",
        amount: 30,
        currency: "USD",
      };

      // Fire the first request
      const res1 = await useCase.execute(command);
      expect(res1.success).toBe(true);

      // Fire the second request (identical, simulating a retry)
      const res2 = await useCase.execute(command);
      expect(res2.success).toBe(true);

      // Check final balances
      const walletA = await walletRepo.findById("wallet-a");
      const walletB = await walletRepo.findById("wallet-b");

      // Balance was debited twice ($100 - $30 - $30 = $40)
      expect(walletA?.balance.amount).toBe(40);
      expect(walletB?.balance.amount).toBe(110);
    });

    it("should prevent duplicate transfers and return cached response when idempotency protection is ENABLED", async () => {
      // Seed wallets
      walletRepo.seed("wallet-a", 100, "USD");
      walletRepo.seed("wallet-b", 50, "USD");

      // Set up UseCase with idempotency ENABLED
      const useCase = new TransferMoneyUseCase(
        walletRepo,
        idempotencyRepo,
        transferService,
        true // useIdempotency = true
      );

      const command = {
        idempotencyKey: "dup-key-123",
        sourceWalletId: "wallet-a",
        targetWalletId: "wallet-b",
        amount: 30,
        currency: "USD",
      };

      // Fire first request
      const res1 = await useCase.execute(command);
      expect(res1.success).toBe(true);
      const firstTxId = res1.transactionId;

      // Fire second request (identical retry)
      const res2 = await useCase.execute(command);
      expect(res2.success).toBe(true);
      expect(res2.transactionId).toBe(firstTxId); // Returns same transaction ID!

      // Check final balances
      const walletA = await walletRepo.findById("wallet-a");
      const walletB = await walletRepo.findById("wallet-b");

      // Balance was only debited once ($100 - $30 = $70)
      expect(walletA?.balance.amount).toBe(70);
      expect(walletB?.balance.amount).toBe(80);
    });
  });

  describe("Concurrency & Invariant Protection Tests", () => {
    it("should violate balance invariant (drop below 0) when optimistic locking is DISABLED", async () => {
      // Set up wallets
      // Wallet A has $100. We will try to execute two concurrent transfers of $80.
      walletRepo.seed("wallet-a", 100, "USD");
      walletRepo.seed("wallet-b", 50, "USD");

      // Configure Repository: Disable optimistic locking & inject 50ms delay
      walletRepo.useOptimisticLocking = false;
      walletRepo.simulatedDelayMs = 50;

      const useCase = new TransferMoneyUseCase(
        walletRepo,
        idempotencyRepo,
        transferService,
        false // Disable idempotency so key check doesn't block parallel execution
      );

      const command1 = {
        idempotencyKey: "key-c1",
        sourceWalletId: "wallet-a",
        targetWalletId: "wallet-b",
        amount: 80,
        currency: "USD",
      };

      const command2 = {
        idempotencyKey: "key-c2",
        sourceWalletId: "wallet-a",
        targetWalletId: "wallet-b",
        amount: 80,
        currency: "USD",
      };

      // Run both transfers concurrently
      const results = await Promise.all([
        useCase.execute(command1),
        useCase.execute(command2)
      ]);

      // Both transfers succeeded despite insufficient funds!
      expect(results[0].success).toBe(true);
      expect(results[1].success).toBe(true);

      const walletA = await walletRepo.findById("wallet-a");
      const walletB = await walletRepo.findById("wallet-b");

      // Lost-update anomaly: both threads read source ($100) and target ($50),
      // compute new values ($20 and $130), and write them back.
      // Thus, one of the updates is completely lost. The database looks like only one transfer happened.
      expect(walletA?.balance.amount).toBe(20);
      expect(walletB?.balance.amount).toBe(130);
    });

    it("should maintain balance invariant and fail second transaction when optimistic locking is ENABLED", async () => {
      // Set up wallets
      walletRepo.seed("wallet-a", 100, "USD");
      walletRepo.seed("wallet-b", 50, "USD");

      // Configure Repository: Enable optimistic locking & inject 50ms delay
      walletRepo.useOptimisticLocking = true;
      walletRepo.simulatedDelayMs = 50;

      const useCase = new TransferMoneyUseCase(
        walletRepo,
        idempotencyRepo,
        transferService,
        false // Disable idempotency so key check doesn't block parallel execution
      );

      const command1 = {
        idempotencyKey: "key-c3",
        sourceWalletId: "wallet-a",
        targetWalletId: "wallet-b",
        amount: 80,
        currency: "USD",
      };

      const command2 = {
        idempotencyKey: "key-c4",
        sourceWalletId: "wallet-a",
        targetWalletId: "wallet-b",
        amount: 80,
        currency: "USD",
      };

      // Run both transfers concurrently
      const results = await Promise.all([
        useCase.execute(command1),
        useCase.execute(command2)
      ]);

      // One transfer should succeed, and one should fail due to optimistic locking conflict
      const successCount = results.filter(r => r.success).length;
      const failureCount = results.filter(r => !r.success).length;

      expect(successCount).toBe(1);
      expect(failureCount).toBe(1);

      // Verify the failing result reports a concurrency issue
      const failedResult = results.find(r => !r.success);
      expect(failedResult?.error).toContain("Optimistic locking conflict");

      const walletA = await walletRepo.findById("wallet-a");
      const walletB = await walletRepo.findById("wallet-b");

      // Balance remains correct ($100 - $80 = $20)
      // It never drops below zero, preserving the invariant!
      expect(walletA?.balance.amount).toBe(20);
      expect(walletB?.balance.amount).toBe(130);
    });
  });
});
