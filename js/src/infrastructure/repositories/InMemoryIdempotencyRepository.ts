import { TransferMoneyResponse } from "../../application/dtos/TransferMoneyCommand";
import { IIdempotencyRepository } from "../../application/repositories/IIdempotencyRepository";

export class InMemoryIdempotencyRepository implements IIdempotencyRepository {
  private cache = new Map<string, TransferMoneyResponse>();

  public async find(key: string): Promise<TransferMoneyResponse | null> {
    const cached = this.cache.get(key);
    return cached ? { ...cached } : null;
  }

  public async save(key: string, response: TransferMoneyResponse): Promise<void> {
    this.cache.set(key, { ...response });
  }

  public clear(): void {
    this.cache.clear();
  }
}
