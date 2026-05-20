import { Wallet } from "../entities/Wallet";
import { Money } from "../value-objects/Money";
import { Transaction } from "../entities/Transaction";

export class TransferService {
  public transfer(source: Wallet, target: Wallet, amount: Money): Transaction {
    if (source.id === target.id) {
      throw new Error("Source and target wallets must be different.");
    }

    // Debit source
    source.debit(amount);

    // Credit target
    target.credit(amount);

    // Create and return transaction
    const transactionId = `tx_${Math.random().toString(36).substring(2, 11)}`;
    return new Transaction(transactionId, source.id, target.id, amount);
  }
}
