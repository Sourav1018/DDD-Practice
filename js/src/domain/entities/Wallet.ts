import { Money } from "../value-objects/Money";

export class Wallet {
  constructor(
    public readonly id: string,
    private _balance: Money,
    private _version: number = 0
  ) {}

  public get balance(): Money {
    return this._balance;
  }

  public get version(): number {
    return this._version;
  }

  /**
   * Debits money from the wallet. Enforces the business rule that balance cannot drop below zero.
   */
  public debit(amount: Money): void {
    if (!this._balance.isGreaterThanOrEqual(amount)) {
      throw new Error(`Insufficient funds: Wallet ${this.id} has ${this._balance.amount} ${this._balance.currency.code}, requested ${amount.amount}`);
    }
    this._balance = this._balance.subtract(amount);
  }

  /**
   * Credits money to the wallet.
   */
  public credit(amount: Money): void {
    this._balance = this._balance.add(amount);
  }

  /**
   * Increments the entity version (for optimistic locking).
   */
  public incrementVersion(): void {
    this._version += 1;
  }
}
