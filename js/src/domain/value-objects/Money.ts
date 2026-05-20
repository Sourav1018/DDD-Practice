import { Currency } from "./Currency";

export class Money {
  constructor(
    public readonly amount: number,
    public readonly currency: Currency
  ) {
    if (amount < 0) {
      throw new Error("Money amount cannot be negative.");
    }
    // Prevent floating point issue by validating up to 2 decimal places
    if (Number.isFinite(amount) && Math.round(amount * 100) / 100 !== amount) {
      throw new Error("Money amount cannot have more than 2 decimal places.");
    }
  }

  public static zero(currency: Currency): Money {
    return new Money(0, currency);
  }

  public add(other: Money): Money {
    this.checkSameCurrency(other);
    // Use integer math to prevent floating point issues
    const newAmount = (Math.round(this.amount * 100) + Math.round(other.amount * 100)) / 100;
    return new Money(newAmount, this.currency);
  }

  public subtract(other: Money): Money {
    this.checkSameCurrency(other);
    if (this.amount < other.amount) {
      throw new Error("Insufficient funds for subtraction.");
    }
    const newAmount = (Math.round(this.amount * 100) - Math.round(other.amount * 100)) / 100;
    return new Money(newAmount, this.currency);
  }

  public isGreaterThanOrEqual(other: Money): boolean {
    this.checkSameCurrency(other);
    return this.amount >= other.amount;
  }

  public equals(other: Money): boolean {
    return this.amount === other.amount && this.currency.equals(other.currency);
  }

  private checkSameCurrency(other: Money): void {
    if (!this.currency.equals(other.currency)) {
      throw new Error(
        `Currency mismatch: cannot perform operation between ${this.currency.code} and ${other.currency.code}`
      );
    }
  }
}
