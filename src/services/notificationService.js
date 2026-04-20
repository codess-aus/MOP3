/**
 * Sends transactional emails to customers at key points
 * in the order lifecycle. Uses the configured email transport.
 */
class NotificationService {
  constructor(emailTransport) {
    this.emailTransport = emailTransport;
  }

  async sendOrderConfirmation(order) {
    console.log("Sending order confirmation to " + order.customerEmail);

    try {
      await this.emailTransport.send({
        to: order.customerEmail,
        subject: `Meridian - Order Confirmed (#${order.id})`,
        template: "order-confirmation",
        data: {
          orderId: order.id,
          items: order.items,
          totalInCents: order.totalInCents,
        },
      });
      console.log("Confirmation sent for order " + order.id);
    } catch (error) {
      console.log(
        "Failed to send confirmation for order " + order.id + ": " + error
      );
    }
  }

  async sendShippingNotification(order, trackingNumber) {
    console.log(
      "Sending shipping notification for order " +
        order.id +
        " to " +
        order.customerEmail
    );

    try {
      await this.emailTransport.send({
        to: order.customerEmail,
        subject: `Meridian - Your Order Has Shipped (#${order.id})`,
        template: "shipping-notification",
        data: {
          orderId: order.id,
          trackingNumber,
          estimatedDelivery: this._estimateDelivery(),
        },
      });
      console.log("Shipping notification sent for order " + order.id);
    } catch (error) {
      console.log(
        "Failed to send shipping notification for order " + order.id + ": " + error
      );
    }
  }

  async sendCancellationNotice(order, reason) {
    console.log("Sending cancellation notice for order " + order.id);

    try {
      await this.emailTransport.send({
        to: order.customerEmail,
        subject: `Meridian - Order Cancelled (#${order.id})`,
        template: "order-cancelled",
        data: { orderId: order.id, reason },
      });
      console.log("Cancellation notice sent for order " + order.id);
    } catch (error) {
      console.log(
        "Failed to send cancellation notice for order " + order.id + ": " + error
      );
    }
  }

  _estimateDelivery() {
    const delivery = new Date();
    delivery.setDate(delivery.getDate() + 5);
    return delivery.toISOString().split("T")[0];
  }
}

module.exports = NotificationService;
