import { Wallet } from "../../domain/entities/Wallet";
import { IWalletRepository } from "../../domain/repositories/IWalletRepository";
import { Currency } from "../../domain/value-objects/Currency";
import { Money } from "../../domain/value-objects/Money";

export class ConcurrencyException extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ConcurrencyException";
  }
}

interface WalletRecord {
  id: string;
  amount: number;
  currencyCode: string;
  version: number;
}

export class InMemoryWalletRepository implements IWalletRepository {
  private records = new Map<string, WalletRecord>();
  
  constructor(
    public useOptimisticLocking: boolean = true,
    public simulatedDelayMs: number = 0
  ) {}

  public async findById(id: string): Promise<Wallet | null> {
    const record = this.records.get(id);
    if (!record) return null;

    const currency = Currency.fromCode(record.currencyCode);
    const balance = new Money(record.amount, currency);
    
    // Reconstruct Wallet aggregate root with its current version
    return new Wallet(record.id, balance, record.version);
  }

  public async save(wallet: Wallet): Promise<void> {
    // 1. Simulate DB query/write latency
    if (this.simulatedDelayMs > 0) {
      await new Promise((resolve) => setTimeout(resolve, this.simulatedDelayMs));
    }

    const currentRecord = this.records.get(wallet.id);
    if (!currentRecord) {
      // If it's a new wallet, just insert it
      this.records.set(wallet.id, {
        id: wallet.id,
        amount: wallet.balance.amount,
        currencyCode: wallet.balance.currency.code,
        version: wallet.version,
      });
      return;
    }

    // 2. Perform Optimistic Locking check if enabled
    if (this.useOptimisticLocking) {
      if (currentRecord.version !== wallet.version) {
        throw new ConcurrencyException(
          `Optimistic locking conflict: Wallet ${wallet.id} was updated by another request. Current DB version: ${currentRecord.version}, wallet version: ${wallet.version}`
        );
      }
      
      // Successful update: increment database version
      const newVersion = currentRecord.version + 1;
      this.records.set(wallet.id, {
        id: wallet.id,
        amount: wallet.balance.amount,
        currencyCode: wallet.balance.currency.code,
        version: newVersion,
      });
      
      // Update in-memory aggregate version to stay in sync
      wallet.incrementVersion();
    } else {
      // Save without optimistic locking (overwriting version)
      this.records.set(wallet.id, {
        id: wallet.id,
        amount: wallet.balance.amount,
        currencyCode: wallet.balance.currency.code,
        version: currentRecord.version, // keep same version (or update it, but ignore checks)
      });
    }
  }

  /**
   * Helper to seed initial wallet data.
   */
  public seed(id: string, amount: number, currencyCode: string): void {
    this.records.set(id, {
      id,
      amount,
      currencyCode,
      version: 0,
    });
  }

  public clear(): void {
    this.records.clear();
  }
}
