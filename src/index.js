const express = require("express");
const orderRoutes = require("./routes/orders");
const { logger } = require("./logger");

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

app.use("/api/orders", orderRoutes);

app.get("/health", (req, res) => {
  res.json({ status: "ok", timestamp: new Date().toISOString() });
});

// eslint-disable-next-line no-unused-vars
app.use((err, req, res, next) => {
  logger.error({ err: { message: err.message, stack: err.stack }, method: req.method, url: req.url }, "Unhandled error");
  res
    .status(500)
    .set("Content-Type", "application/problem+json")
    .json({
      type: "https://meridian.internal/errors/server-error",
      title: "Internal Server Error",
      status: 500,
      detail: "An unexpected error occurred while processing your request.",
    });
});

if (require.main === module) {
  app.listen(PORT, () => {
    logger.info({ port: PORT }, "Meridian API listening");
  });
}

module.exports = app;
