export class Currency {
  private constructor(public readonly code: string) {}

  public static fromCode(code: string): Currency {
    const cleanCode = code.trim().toUpperCase();
    if (cleanCode.length !== 3) {
      throw new Error("Currency code must be a 3-letter ISO code.");
    }
    // For our system, we support USD, EUR, and INR
    const supported = ["USD", "EUR", "INR"];
    if (!supported.includes(cleanCode)) {
      throw new Error(`Unsupported currency code: ${cleanCode}. Supported: ${supported.join(", ")}`);
    }
    return new Currency(cleanCode);
  }

  public equals(other: Currency): boolean {
    return this.code === other.code;
  }
}
