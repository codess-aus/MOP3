const { v4: uuidv4 } = require("uuid");

/**
 * Handles order lifecycle operations including creation,
 * fulfilment, and cancellation workflows.
 */
class OrderService {
  constructor(database) {
    this.database = database;
  }

  async createOrder(customerEmail, items) {
    const orderId = uuidv4();
    console.log("Creating order " + orderId + " for " + customerEmail);

    try {
      const totalInCents = items.reduce(
        (sum, item) => sum + item.priceInCents * item.quantity,
        0
      );

      const order = {
        id: orderId,
        customerEmail,
        items,
        totalInCents,
        status: "pending",
        createdAt: new Date().toISOString(),
      };

      await this.database.insert("orders", order);
      console.log("Order " + orderId + " persisted, total: " + totalInCents + " cents");
      return order;
    } catch (error) {
      console.log("Order creation failed for " + customerEmail + ": " + error);
      throw error;
    }
  }

  async fulfil(orderId, trackingNumber) {
    console.log("Fulfilling order " + orderId + " with tracking " + trackingNumber);

    try {
      const order = await this.database.findById("orders", orderId);
      if (!order) {
        console.log("Cannot fulfil, order not found: " + orderId);
        return null;
      }

      if (order.status === "cancelled") {
        console.log("Cannot fulfil cancelled order: " + orderId);
        throw new Error("Cannot fulfil a cancelled order");
      }

      await this.database.update("orders", orderId, {
        status: "shipped",
        trackingNumber,
        shippedAt: new Date().toISOString(),
      });

      console.log("Order " + orderId + " shipped with tracking " + trackingNumber);
      return { ...order, status: "shipped", trackingNumber };
    } catch (error) {
      console.log("Fulfilment failed for " + orderId + ": " + error);
      throw error;
    }
  }

  async cancel(orderId, reason) {
    console.log("Cancelling order " + orderId + ", reason: " + reason);

    try {
      await this.database.update("orders", orderId, {
        status: "cancelled",
        cancellationReason: reason,
        cancelledAt: new Date().toISOString(),
      });
      console.log("Order " + orderId + " cancelled");
    } catch (error) {
      console.log("Cancellation failed for " + orderId + ": " + error);
      throw error;
    }
  }
}

module.exports = OrderService;
