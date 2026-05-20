import { Wallet } from "../entities/Wallet";

export interface IWalletRepository {
  findById(id: string): Promise<Wallet | null>;
  save(wallet: Wallet): Promise<void>;
}
