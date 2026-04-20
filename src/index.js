const express = require("express");
const orderRoutes = require("./routes/orders");

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

app.use("/api/orders", orderRoutes);

app.get("/health", (req, res) => {
  res.json({ status: "ok", timestamp: new Date().toISOString() });
});

app.use((err, req, res, next) => {
  console.error(`[${new Date().toISOString()}] Unhandled error:`, err.message);
  res.status(500).json({
    type: "https://meridian.internal/errors/server-error",
    title: "Internal Server Error",
    status: 500,
    detail: "An unexpected error occurred while processing your request.",
  });
});

app.listen(PORT, () => {
  console.log(`Meridian API listening on port ${PORT}`);
});

module.exports = app;
