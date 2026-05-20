export interface TransferMoneyCommand {
  idempotencyKey: string;
  sourceWalletId: string;
  targetWalletId: string;
  amount: number;
  currency: string;
}

export interface TransferMoneyResponse {
  success: boolean;
  transactionId?: string;
  error?: string;
  balanceAfterTransfer?: number;
}
