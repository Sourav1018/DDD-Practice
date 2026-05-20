import { TransferMoneyResponse } from "../dtos/TransferMoneyCommand";

export interface IIdempotencyRepository {
  find(key: string): Promise<TransferMoneyResponse | null>;
  save(key: string, response: TransferMoneyResponse): Promise<void>;
}
