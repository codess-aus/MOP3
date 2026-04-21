/**
 * Minimal structured JSON logger.
 * Writes newline-delimited JSON to stdout/stderr to comply with
 * the project requirement of structured JSON logging (no console.log).
 */

const LEVELS = { debug: 10, info: 20, warn: 30, error: 40 };

/**
 * Emits a structured log entry to the appropriate stream.
 * @param {string} level
 * @param {object|string} dataOrMsg
 * @param {string} [msg]
 */
function log(level, dataOrMsg, msg) {
  const entry =
    typeof dataOrMsg === "string"
      ? { level, time: new Date().toISOString(), msg: dataOrMsg }
      : { level, time: new Date().toISOString(), ...dataOrMsg, msg: msg ?? dataOrMsg.msg ?? "" };

  const line = JSON.stringify(entry);
  if (LEVELS[level] >= LEVELS.error) {
    process.stderr.write(line + "\n");
  } else {
    process.stdout.write(line + "\n");
  }
}

const logger = {
  /** @param {object|string} dataOrMsg @param {string} [msg] */
  debug: (dataOrMsg, msg) => log("debug", dataOrMsg, msg),
  /** @param {object|string} dataOrMsg @param {string} [msg] */
  info: (dataOrMsg, msg) => log("info", dataOrMsg, msg),
  /** @param {object|string} dataOrMsg @param {string} [msg] */
  warn: (dataOrMsg, msg) => log("warn", dataOrMsg, msg),
  /** @param {object|string} dataOrMsg @param {string} [msg] */
  error: (dataOrMsg, msg) => log("error", dataOrMsg, msg),
};

module.exports = { logger };
