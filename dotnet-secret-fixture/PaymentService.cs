namespace Finance.Demo;

/// <summary>
/// Payment processing service with hardcoded AWS & Stripe credentials for scanner testing.
/// FAKE credentials for testing purposes only.
/// </summary>
public class PaymentService
{
    // Hardcoded Stripe Secret Key
    public const string StripeSecretKey = "sk_live_51DotNetFinanceFakeStripeSecretKey99Xyz";

    // Hardcoded AWS Access & Secret Keys
    public const string AwsAccessKey = "AKIA9DOTNET7EXAMPLE88";
    public const string AwsSecretKey = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYDotNetKey99";

    public void ProcessPayment(string customerId, decimal amount)
    {
        Console.WriteLine($"Initializing Stripe gateway with key: {StripeSecretKey[..12]}...");
        Console.WriteLine($"Processing payment of ${amount:F2} for customer: {customerId}");
    }

    public void ArchiveReceipt(string receiptId)
    {
        Console.WriteLine($"Uploading receipt {receiptId} to AWS S3 using access key {AwsAccessKey}");
    }
}

