import { IWalletRepository } from "../../domain/repositories/IWalletRepository";
import { TransferService } from "../../domain/services/TransferService";
import { Currency } from "../../domain/value-objects/Currency";
import { Money } from "../../domain/value-objects/Money";
import { TransferMoneyCommand, TransferMoneyResponse } from "../dtos/TransferMoneyCommand";
import { IIdempotencyRepository } from "../repositories/IIdempotencyRepository";

export class TransferMoneyUseCase {
  constructor(
    private walletRepository: IWalletRepository,
    private idempotencyRepository: IIdempotencyRepository,
    private transferService: TransferService,
    private useIdempotency: boolean = true
  ) {}

  public async execute(command: TransferMoneyCommand): Promise<TransferMoneyResponse> {
    // 1. Check idempotency first if enabled
    if (this.useIdempotency && command.idempotencyKey) {
      const cachedResponse = await this.idempotencyRepository.find(command.idempotencyKey);
      if (cachedResponse) {
        return cachedResponse;
      }
    }

    try {
      // 2. Parse and validate inputs
      const currency = Currency.fromCode(command.currency);
      const amount = new Money(command.amount, currency);

      // 3. Load aggregates
      const sourceWallet = await this.walletRepository.findById(command.sourceWalletId);
      if (!sourceWallet) {
        throw new Error(`Source wallet not found: ${command.sourceWalletId}`);
      }

      const targetWallet = await this.walletRepository.findById(command.targetWalletId);
      if (!targetWallet) {
        throw new Error(`Target wallet not found: ${command.targetWalletId}`);
      }

      // 4. Delegate to Domain Service to perform transfer business rules
      const transaction = this.transferService.transfer(sourceWallet, targetWallet, amount);

      // 5. Save the updated aggregates
      // Note: Repository updates need to be sequential or transaction-based depending on implementation.
      // We will save both. In memory database we save one by one.
      await this.walletRepository.save(sourceWallet);
      await this.walletRepository.save(targetWallet);

      const response: TransferMoneyResponse = {
        success: true,
        transactionId: transaction.id,
        balanceAfterTransfer: sourceWallet.balance.amount
      };

      // 6. Cache the response for idempotency if enabled
      if (this.useIdempotency && command.idempotencyKey) {
        await this.idempotencyRepository.save(command.idempotencyKey, response);
      }

      return response;
    } catch (error: any) {
      const errorResponse: TransferMoneyResponse = {
        success: false,
        error: error.message || "An unknown error occurred during transfer."
      };
      return errorResponse;
    }
  }
}
