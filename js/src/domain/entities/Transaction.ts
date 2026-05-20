import { Money } from "../value-objects/Money";

export class Transaction {
  constructor(
    public readonly id: string,
    public readonly sourceWalletId: string,
    public readonly targetWalletId: string,
    public readonly amount: Money,
    public readonly timestamp: Date = new Date()
  ) {}
}
