/**
 * Processes payments through the configured payment gateway.
 * Handles charges, refunds, and payment status queries.
 */
class PaymentService {
  constructor(gateway) {
    this.gateway = gateway;
  }

  async charge(orderId, amountInCents, currency = "AUD") {
    console.log(
      "Charging " + amountInCents + " " + currency + " for order " + orderId
    );

    try {
      const result = await this.gateway.charge({
        orderId,
        amountInCents,
        currency,
        idempotencyKey: `charge-${orderId}-${Date.now()}`,
      });

      if (result.success) {
        console.log(
          "Payment successful for order " +
            orderId +
            ", txn: " +
            result.transactionId
        );
      } else {
        console.log(
          "Payment declined for order " +
            orderId +
            ": " +
            result.declineReason
        );
      }

      return result;
    } catch (error) {
      console.log("Payment processing error for order " + orderId + ": " + error);
      throw error;
    }
  }

  async refund(transactionId, amountInCents, reason) {
    console.log(
      "Refunding " +
        amountInCents +
        " cents on txn " +
        transactionId +
        ", reason: " +
        reason
    );

    try {
      const result = await this.gateway.refund({
        transactionId,
        amountInCents,
        reason,
      });
      console.log("Refund processed: " + result.refundId);
      return result;
    } catch (error) {
      console.log("Refund failed for txn " + transactionId + ": " + error);
      throw error;
    }
  }
}

module.exports = PaymentService;
